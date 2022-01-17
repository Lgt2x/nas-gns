from utils.components import Router


class Config:
    @staticmethod
    def generate_config_router(router: Router, filename: str, bb_routers: [Router]):
        """
        Stateless function writing a router config to a file, given its characteristics
        :param bb_routers: list of backbone routers
        :param router: Router object
        :param filename: config file path to write to
        """
        file = open(filename, 'w')

        # Common config
        file.write("version 15.2\n"
                   "service timestamps debug datetime msec\n"
                   "service timestamps log datetime msec\n\n")

        file.write(f"hostname R{router.rid}\n"
                   "boot-start-marker\n"
                   "boot-end-marker\n"
                   "no aaa new-model\n"
                   "no ip icmp rate-limit unreachable\n\n")

        file.write(f"ip cef\n"
                   "no ip domain lookup\n"
                   "no ipv6 cef\n\n")

        # Only backbone routers run MPLS
        if type != "client":
            file.write(f"mpls label protocol ldp\n")

        file.write("multilink bundle-name authenticated\n"
                   "ip tcp synwait-time 5\n\n")

        # Configure loopback adress
        if router.type != "client":
            file.write(f"interface Loopback0\n"
                       f"ip address {router.rid}.{router.rid}.{router.rid}.{router.rid} 255.255.255.255\n"
                       "ip ospf 1 area 1\n\n")

        # Interface FastEthernet is never used
        file.write("interface FastEthernet0/0\n"
                   "no ip address\n"
                   "duplex full\n\n")

        # Counting the used ports
        port = 1

        # Configure interfaces with other routers inside of the AS
        for neighbor in router.neighbors:
            file.write(f"interface GigabitEthernet{port}/0\n"
                       f" ip address 10.10.{min(neighbor, router.rid)}{max(neighbor, router.rid)}."
                       f"{router.rid} 255.255.255.0\n")

            # Backbone routers only run OSPF protocol
            if router.type != "client":
                file.write("ip ospf 1 area 1\n")

            file.write(" negotiation auto\n")

            if router.type != "client":
                file.write(" mpls ip\n")

            file.write("\n")
            port += 1

        # Configure interfaces with peers in other ASes
        if router.type != "core":
            for i in range(len(router.exteriors)):
                file.write(f"interface GigabitEthernet{port}/0\n"
                           f" ip address 10.10.{min(router.exteriors[i].rid, router.rid)}"
                           f"{max(router.exteriors[i].rid, router.rid)}.{router.rid} "
                           f"255.255.255.0\n")

                if router.type != "client":
                    file.write("ip ospf 1 area 1\n")

                file.write(" negotiation auto\n\n")
                port += 1

        # Internal interfaces in client routers
        if router.type == "client":
            file.write(f"interface GigabitEthernet{port}/0\n"
                       f" ip address 10.10.10{router.rid}.{router.rid} 255.255.255.0\n")
            file.write(" negotiation auto\n\n")
            port += 1

        # OSPF configuration for backbone routers
        if router.type != "client":
            file.write("router ospf 1\n"
                       f" router-id {router.rid}.{router.rid}.{router.rid}.{router.rid}\n\n")

        # Configure OSPF passive interfaces on edge routers linking peers or clients
        if router.type == "edge":
            file.write(f" passive-interface GigabitEthernet{port - 1}/0\n\n")

        # Configure BGP on edge routers & clients
        if router.type != "core":
            file.write(f"router bgp {router.AS}\n"
                       f"bgp router-id {router.rid}.{router.rid}.{router.rid}.{router.rid}\n"
                       "bgp log-neighbor-changes\n\n")

            # BGP neighbor inside AS : all other edge routers
            if router.type == "edge":
                for neighbor in bb_routers:  # Iterate over backbone routers
                    if neighbor.type == 'edge':
                        file.write(f"neighbor {neighbor.rid}.{neighbor.rid}.{neighbor.rid}.{neighbor.rid} "
                                   f"remote-as {router.AS}\n")
                        file.write(f"neighbor {neighbor.rid}.{neighbor.rid}.{neighbor.rid}.{neighbor.rid} "
                                   f"update-source Loopback0\n\n")

            # BGP with client on their connected interface
            for i in range(len(router.exteriors)):
                file.write(
                    f"neighbor 10.10.{min(router.exteriors[i].rid, router.rid)}"
                    f"{max(router.exteriors[i].rid, router.rid)}."
                    f"{router.exteriors[i].rid} remote-as {router.exteriors[i].AS}\n")

            file.write("\naddress-family ipv4\n")

            if router.type == "client":
                file.write(f"network 10.10.10{router.rid}.0 mask 255.255.255.0\n")

            # Activate BGP neighbors, same as above
            if router.type == "edge":
                for neighbor in bb_routers:
                    if neighbor.type == 'edge':
                        file.write(f" neighbor {neighbor.rid}.{neighbor.rid}.{neighbor.rid}.{neighbor.rid} activate\n")
                        file.write(
                            f" neighbor {neighbor.rid}.{neighbor.rid}.{neighbor.rid}.{neighbor.rid} send-community\n")

            # Activate neighbors and apply filters on routes to and from clients
            for exterior in router.exteriors:
                file.write(
                    f" neighbor 10.10.{min(exterior.rid, router.rid)}"
                    f"{max(exterior.rid, router.rid)}.{exterior.rid} activate\n")
                if exterior.type == "client":  # client type "client" : filter in
                    if exterior.client_type == "client":
                        file.write(f" neighbor 10.10.{min(exterior.rid, router.rid)}"
                                   f"{max(exterior.rid, router.rid)}.{exterior.rid} route-map client-in in\n")
                    else:  # Peer or provider : filter out
                        file.write(
                            f"neighbor 10.10.{min(exterior.rid, router.rid)}"
                            f"{max(exterior.rid, router.rid)}.{exterior.rid} route-map filter-out out\n")
            file.write("exit-address-family\n\n")

        if router.type == "edge":
            file.write(f"ip community-list 1 permit {router.AS}:1\n")

        file.write("ip forward-protocol nd\n"
                   "no ip http server\n"
                   "no ip http secure-server\n\n")

        # Define the route-map rules used above
        if router.type == "edge":
            for exterior in router.exteriors:
                if exterior.type == "client" and exterior.client_type == "client":
                    file.write(f"route-map client-in permit 10\n"
                               f"set community {router.AS}:1\n")
                if exterior.type == "client" and (
                        exterior.client_type == "peering" or exterior.client_type == "provider"):
                    file.write(f"route-map filter-out permit 10\n"
                               "match community 1\n")

        # Force loopback adress for MPLS
        if router.type != "client":
            file.write("\nmpls ldp router-id Loopback0 force\n\n")

        # Common directives
        file.write("control-plane\n"
                   "line con 0\n"
                   " exec-timeout 0 0\n"
                   " privilege level 15\n"
                   " logging synchronous\n"
                   " stopbits 1\n"
                   "line aux 0\n"
                   " exec-timeout 0 0\n"
                   " privilege level 15\n"
                   " logging synchronous\n"
                   " stopbits 1\n"
                   "line vty 0 4\n"
                   "login\n")

        file.write("end\n")
        file.close()

    @staticmethod
    def generate_config_pc(filename: str, router: Router, pc_id: int) -> None:
        file = open(filename, 'w')

        file.write(f"set pcname PC{router.rid}{pc_id}\n"
                   f"ip 10.10.10{router.rid}.{pc_id} 255.255.255.0 gateway 10.10.10{router.rid}.{router.rid}")

        file.close()
