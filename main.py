import sys

import gns3fy
import os
import sys
import json


class GNS:
    def create_backbone(self, file):
        f = open(file)
        config = json.load(f)

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

        # Create links
        links = config["links"]
        for link in links:
            node1 = self.get_node(link["node1"])
            node2 = self.get_node(link["node2"])







        f.close()

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
        for template in self.templates:
            if name == template["name"]:
                return template["template_id"]
        return ""

    def get_node(self, name):
        for node in self.project.nodes:
            if node.name == name:
                return node
        return None

    def get_port(self, nodes, short_name):
        for port in nodes.ports:
            if port["short_name"] == short_name:
                return port
        return None

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


if __name__ == "__main__":
    project = GNS("http://localhost:3080", "autoconf")
    project.create_backbone("archi/backbone.json")
