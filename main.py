import sys

import gns3fy
import os
import sys
import json

from utils.components import GNode


class GNS:
    def __init__(self, url, project):
        self.gns_url = url
        self.project_name = project

        try:
            self.server = gns3fy.Gns3Connector(url=url)
            print(f"Connecting to GNS3 version {self.server.get_version()['version']}")
        except Exception:
            sys.exit(f"Could not connect to GNS3 on {url}, exiting")

        try:
            self.project = gns3fy.Project(name=self.project_name, connector=self.server)
            self.project.get()
        except Exception:
            print("Could not get project, exiting")
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
        print("Clearing existing nodes")
        self.project.get_nodes()
        for node in self.project.nodes:
            node.delete()

        # Create nodes
        nodes = config["nodes"]
        for node in nodes:
            gns_node = gns3fy.Node(
                project_id=self.project_id,
                connector=self.server,
                name=node["name"],
                template=node["type"]
            )
            gns_node.create()
            print(f"Created node {node['name']} of type {node['type']}")

        self.project.get_nodes()  # Update node list

        # Create links
        links = config["links"]
        for link in links:
            self.create_link(link["node1"], link["node2"])
            print(f"Created link between {link['node1']} and {link['node1']}")

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

        # Create edge routers
        for y in range(core_routers+1):
            for x in (0, 1):
                gns_node = GNode(self.project, gns3fy.Node(
                    project_id=self.project_id,
                    connector=self.server,
                    name=f"RE{2*y+x+1}",
                    template="c7200"
                ))
                gns_node.node.create()
                gns_node.position(type="edge", grid_pos=(x,y))
                print(f"Created edge router {gns_node.node.name}")

        # Create core routers
        for i in range(core_routers):
            gns_node = GNode(self.project, gns3fy.Node(
                project_id=self.project_id,
                connector=self.server,
                name=f"RC{i}",
                template="c7200"
            ))
            gns_node.node.create()
            gns_node.position(type="core", grid_pos=i)
            print(f"Created core router {gns_node.node.name}")

        self.project.get_nodes()  # Update node list

        # Link tout le bazar
        nb_edge = 2 * core_routers + 2
        for i in range(1, nb_edge+1):
            # Link to the right router
            if i%2 == 1:
                self.create_link(f"RE{i}", f"RE{i+1}")

            # Link with the down router
            if i != nb_edge-1:
                self.create_link(f"RE{i}", f"RE{i+2}")

            # Link to the down core router
            if i < nb_edge - 2:
                self.create_link(f"RE{i}", f"RC{(i-1)//2}")

            # Link to the up core router
            if i > 2:
                self.create_link(f"RE{i}", f"RC{(i-1) // 2 - 1}")



    def create_link(self, node1, node2):
        """
        Create a link between 2 nodes
        """
        nodes = (self.project.get_node(node1), self.project.get_node(node2))
        interfaces = (self.get_free_port(nodes[0].name), self.get_free_port(nodes[1].name))
        links = (self.get_port_from_name(node1, interfaces[0]),
                 self.get_port_from_name(node2, interfaces[1]))

        link_info = [
            {"node_id": nodes[0].node_id, "adapter_number": links[0]['adapter_number'],
             "port_number": links[0]['port_number']},
            {"node_id": nodes[1].node_id, "adapter_number": links[1]['adapter_number'],
             "port_number": links[1]['port_number']}
        ]

        new_link = gns3fy.Link(project_id=self.project_id, connector=self.server, nodes=link_info)
        new_link.create()

    def get_template_id(self, name: str):
        """
        c7200, 9f18b658-772c-4aeb-a1e2-88351d6e3e8e
        Cloud, 39e257dc-8412-3174-b6b3-0ee3ed6a43e9
        NAT, df8f4ea9-33b7-3e96-86a2-c39bc9bb649c
        VPCS, 19021f99-e36f-394d-b4a1-8aaa902ab9cc
        Ethernet switch, 1966b864-93e7-32d5-965f-001384eec461
        Ethernet hub, b4503ea9-d6b6-3695-9fe4-1db3b39290b0
        Frame Relay switch, dd0f6f3a-ba58-3249-81cb-a1dd88407a47
        ATM switch, aaa764e2-b383-300f-8a0e-3493bbfdb7d2
        """
        return [template["template_id"] for template in project.templates if template["name"] == name][0]

    def get_node_links(self, node_name):
        """
        Returns a node links
        """
        node = self.project.get_node(node_name)
        node.get_links()
        return node.links

    def get_link_between(self, node_name1, node_name2):
        """
        Return a Link object between 2 given nodes
        """
        links1 = self.get_node_links(node_name1)
        links2 = self.get_node_links(node_name2)

        return list(set(links1) & set(links2))

    def get_free_port(self, node_name):
        """
        Returns a random free port on a given node
        """
        node = self.project.get_node(node_name)
        links = self.get_node_links(node_name)
        all_ports = [n["short_name"] for n in node.ports]

        busy_ports = []
        for link in links:
            info = [info for info in link.nodes if info['node_id'] == node.node_id][0]
            busy_ports.append([n["short_name"] for n in node.ports if n["adapter_number"] == info["adapter_number"]][0])

        return list(set(all_ports) - set(busy_ports))[0]  # Get the first port not busy

    def get_port_from_name(self, node_name, port_name):
        """
        Return port info given a node & a port name
        """
        return [port for port in self.project.get_node(node_name).ports if port["short_name"] == port_name][0]


if __name__ == "__main__":
    project = GNS("http://localhost:3080", "autoconf")
    # project.create_backbone("archi/backbone.json")
    project.create_backbone_auto(3)
