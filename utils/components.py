from dataclasses import dataclass

import gns3fy


class GNode():
    def __init__(self, project, node):
        self.project = project  # gns3fy.Project
        project.get_nodes()
        self.node = project.get_node(node)  # gns3fy.Node Object

    def position_backbone(self, type, grid_pos):
        """
        :param type: "core" | "edge"
        :param grid_pos: x | (x,y)
        """
        if type == "edge":
            x = (grid_pos[0]%2) * 200 - 100
            y = grid_pos[1] * 200 - 350
        elif type == "core":
            x = 0
            y = grid_pos * 200 - 250
        else:
            raise TypeError

        self.node.update(x=x, y=y)

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
            return [template["template_id"] for template in self.project.templates if template["name"] == name][0]

    def get_free_port(self):
        self.project.get_nodes()
        self.project.get_links()

        links = self.get_node_links()
        all_ports = [n["short_name"] for n in self.node.ports]

        busy_ports = []
        for link in links:
            info = [info for info in link.nodes if info['node_id'] == self.node.node_id][0]
            busy_ports.append(
                [n["short_name"] for n in self.node.ports if n["adapter_number"] == info["adapter_number"]][0])

        return list(set(all_ports) - set(busy_ports))[0]  # Get the first port not busy

    def get_port_from_name(self, port_name):
        return [port for port in self.node.ports if port["short_name"] == port_name][0]

    def get_node_links(self):
        """
        Returns the node links
        """
        self.node.get_links()
        return self.node.links

    def get_link_between(self, gnode2):
        """
        Return a Link object between 2 given nodes
        """
        links1 = self.get_node_links()
        links2 = gnode2.get_node_links()

        return list(set(links1) & set(links2))


@dataclass
class Router:
    rid: int
    type: str
    AS: int
    neighbors: ['Router'] # Inside AS neighbors
    exterior: ['Router']  # Different AS neighbors
