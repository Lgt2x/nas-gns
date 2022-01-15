import gns3fy
import sys
import json

from utils.components import GNode, Router
from utils.config import Config


class GNS_project:
    def __init__(self, url, project):
        self.gns_url = url
        self.project_name = project
        self.backbone_routers = []
        self.client_routers = []

        try:
            self.server = gns3fy.Gns3Connector(url=url)
            print(f"Connecting to GNS3 version {self.server.get_version()['version']}")
        except Exception:
            sys.exit(f"Could not connect to GNS3 on {url}, exiting.\nOpen the software before running this program.")

        try:
            self.project = gns3fy.Project(name=self.project_name, connector=self.server)
            self.project.get()
        except Exception:
            print(f"Could not get the project `{self.project_name}`, exiting.\nPlease open the project.")
            sys.exit(1)

        print(f"Loaded project \"{self.project.name}\" -- Status: {self.project.status}")

        self.project_id = self.project.project_id
        self.templates = self.server.get_templates()

    def create_backbone(self, file):
        """
        Create a backbone router scheme given a decription file
        """

        config_file = open(file)
        config = json.load(config_file)

        # Clear existing nodes
        print("Clearing existing nodes and links")
        self.project.get_nodes()
        for node in self.project.nodes:
            node.delete()

        # Create nodes
        nodes = config["routers"]
        for node in nodes:
            self.create_node("c7200", f"R{node['rid']}")
            print(f"Created node {node['rid']}")

            # Write configuration to file

        self.project.get_nodes()  # Update node list

        # Create links
        links = config["links"]
        for link in links:
            self.create_link(link["rid1"], link["rid2"])
            print(f"Created link between R{link['rid1']} and R{link['rid2']}")

        config_file.close()

    def create_backbone_auto(self, core_routers=2):
        """
        Create a backbone router scheme automatically
        """

        # Clear existing nodes
        print("Clearing existing nodes")
        self.project.get_nodes()
        for node in self.project.nodes:
            node.delete()

        print("Creating backbone...")
        # Create edge routers
        for y in range(core_routers + 1):
            for x in (0, 1):
                name = f"RE{2 * y + x + 1}"
                self.create_node("c7200", name)
                GNode(self.project, name).position_backbone(type="edge", grid_pos=(x, y))
                print(f"Created edge router {name}")

        # Create core routers
        for i in range(core_routers):
            self.create_node("c7200", f"RC{i}")
            GNode(self.project, f"RC{i}").position_backbone(type="core", grid_pos=i)
            print(f"Created core router RC{i}")

        self.project.get_nodes()  # Update node list

        # Link everything
        nb_edge = 2 * core_routers + 2
        for i in range(1, nb_edge + 1):
            # Link to the right router
            if i % 2 == 1:
                self.create_link(f"RE{i}", f"RE{i + 1}")

            # Link with the down router
            if i < nb_edge - 1:
                self.create_link(f"RE{i}", f"RE{i + 2}")

            # Link to the down core router
            if i < nb_edge - 1:
                self.create_link(f"RE{i}", f"RC{(i - 1) // 2}")

            # Link to the up core router
            if i > 2:
                self.create_link(f"RE{i}", f"RC{(i - 1) // 2 - 1}")

        print("---- Backbone setup completed\n")

    def create_client(self, name, router=True, pc=2, switch=True, AS=False, redundancy=False):
        print(
            f"Creating client `{name}` {'with' if router else 'without'} router, {pc} PC, {'with' if switch else 'without'} switch, "
            f"{'with' if AS else 'without'} its own AS, {'with' if redundancy else 'without'} redundancy")

        # Select our edge router
        edge = GNode(self.project, "RE1")
        if int(edge.node.name[-1]) % 2 == 0:
            right = True  # Position visually the client on the right
        else:
            right = False  # Position visually on the left

        # Create client router
        self.create_node("c7200", name)
        self.create_link(name, edge.node.name)
        GNode(self.project, name).node.update(x=edge.node.x - 150, y=edge.node.y)

        # Create client PC/Switch
        self.create_node("Ethernet switch", f"{name}Switch")
        self.create_link(f"{name}Switch", name)  # Link Router & switch
        GNode(self.project, f"{name}Switch").node.update(x=edge.node.x - 300, y=edge.node.y)

        for i in range(pc):
            self.create_node("VPCS", f"{name}PC{i}")
            # self.create_link(f"{name}Switch", f"{name}PC{i}")
            GNode(self.project, f"{name}PC{i}").node.update(x=edge.node.x - 450,
                                                            y=edge.node.y + i * 80 - (pc // 2) * 80)

    def create_link(self, node1, node2):
        """
        Create a link between 2 nodes
        """
        nodes = (GNode(self.project, node1), GNode(self.project, node2))
        interfaces = (nodes[0].get_free_port(), nodes[1].get_free_port())
        links = (nodes[0].get_port_from_name(interfaces[0]),
                 nodes[1].get_port_from_name(interfaces[1]))

        link_info = [
            {"node_id": nodes[0].node.node_id, "adapter_number": links[0]['adapter_number'],
             "port_number": links[0]['port_number']},
            {"node_id": nodes[1].node.node_id, "adapter_number": links[1]['adapter_number'],
             "port_number": links[1]['port_number']}
        ]

        new_link = gns3fy.Link(project_id=self.project_id, connector=self.server, nodes=link_info)
        new_link.create()
        self.project.get_links()

        print(f"Linked {node1}:{interfaces[0]}, {node2}:{interfaces[1]}")

    def create_node(self, type, name):
        node = gns3fy.Node(
            project_id=self.project_id,
            connector=self.server,
            name=name,
            template=type
        )
        node.create()
        self.project.get_nodes()

    def load_config(self, file, type):
        with open(file, 'r') as config_file:
            config = json.load(config_file)

            if type == "backbone":
                for router in config["routers"]:
                    neigh = []
                    for link in config["links"]:
                        if link["rid1"] == router["rid"]:
                            neigh.append(link["rid2"])
                        elif link["rid2"] == router["rid"]:
                            neigh.append(link["rid1"])

                    self.backbone_routers.append(Router(AS=config["AS"],
                                                        rid=router["rid"],
                                                        type=router["type"],
                                                        neighbors=neigh,
                                                        exteriors=[],
                                                        peers=[]))
            elif type == "client":
                self.client_routers.append(Router(AS=config["AS"],
                                                  rid=config["rid"],
                                                  type="client",
                                                  neighbors=[],
                                                  exteriors=[self.get_router(r) for r in config["peers"]],
                                                  peers=config["peers"]))
                for router in self.backbone_routers:  # Update backbone exterior relatioins
                    router.exteriors += [r for r in self.client_routers if router.rid in r.peers]
            else:
                raise TypeError

    def config_all(self) -> None:
        self.project.get_nodes()
        for router in self.backbone_routers + self.client_routers:
            Config.generate_config(router, self.get_config_path(router.rid))

    def get_router(self, rid):
        for r in self.backbone_routers + self.client_routers:
            if r.rid == rid:
                return r

    def get_config_path(self, node):
        rid = self.project.get_node(f'R{node}').node_id
        return f"{self.project.path}/project-files/dynamips/{rid}/configs/i{node}_startup-config.cfg"


if __name__ == "__main__":
    project = GNS_project("http://localhost:3080", "autoconf2")
    # project.create_backbone("archi/backbone.json")
    # project.create_backbone_auto(1)
    project.load_config('archi/backbone.json', 'backbone')
    project.load_config('archi/client1.json', 'client')
    project.load_config('archi/client2.json', 'client')
    project.config_all()
