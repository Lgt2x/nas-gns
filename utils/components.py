import gns3fy


class GNode():
    def __init__(self, project, node):
        self.project = project  # gns3fy.Project
        self.node = node  # gns3fy.Node Object

    def position(self, type, grid_pos):
        """
        :param type: "core" | "edge"
        :param grid_pos: x | (x,y)
        """
        if type == "edge":
            x = (grid_pos[0]%2) * 200
            y = grid_pos[1] * 200 - 350
        elif type == "core":
            x = 100
            y = grid_pos * 200 - 250
        else:
            raise TypeError

        self.node.update(x=x, y=y)


    def get_free_port(self):
        links = self.get_node_links(self.node)
        all_ports = [n["short_name"] for n in node.ports]

        busy_ports = []
        for link in links:
            info = [info for info in link.nodes if info['node_id'] == node.node_id][0]
            busy_ports.append([n["short_name"] for n in node.ports if n["adapter_number"] == info["adapter_number"]][0])

        return list(set(all_ports) - set(busy_ports))[0]  # Get the first port not busy

    def get_port_from_name(self, port_name):
        return [port for port in self.node.ports if port["short_name"] == port_name][0]
