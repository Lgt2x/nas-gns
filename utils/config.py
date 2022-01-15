from utils.components import Router


class Config:
    @staticmethod
    def generate_config(router: Router, filename: str, bb_routers: [Router]):
        """
        Stateless function writing a router config to a file
        :param router: Router object
        :param filename: file path to write to
        """
        file = open(filename, 'w')

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

        file.write(f"mpls label protocol ldp\n"
                   "multilink bundle-name authenticated\n"
                   "ip tcp synwait-time 5\n\n")

        # Configure loopback adress
        if router.type != "client":
            file.write(f"interface Loopback0\n"
                       f"ip address {router.rid}.{router.rid}.{router.rid}.{router.rid} 255.255.255.255\n"
                       "ip ospf 1 area 1\n\n")

        file.write("interface FastEthernet0/0\n"
                   "no ip address\n"
                   "duplex full\n\n")

        port = 1

        # Other edge and core routers
        for neighbor in router.neighbors:
            file.write(f"interface GigabitEthernet{port}/0\n"
                       f" ip address 10.10.{min(neighbor, router.rid)}{max(neighbor, router.rid)}."
                       f"{router.rid} 255.255.255.0\n")

            if router.type != "client":
                file.write("ip ospf 1 area 1\n")

            file.write(" negotiation auto\n")

            if router.type != "client":
                file.write(" mpls ip\n")

            file.write("\n")
            port += 1

        if router.type != "core":
            # Client routers linked
            for i in range(len(router.exteriors)):
                file.write(f"interface GigabitEthernet{port}/0\n"
                           f" ip address 10.10.{min(router.exteriors[i].rid, router.rid)}{max(router.exteriors[i].rid, router.rid)}.{router.rid} "
                           f"255.255.255.0\n")

                if router.type != "client":
                    file.write("ip ospf 1 area 1\n")

                file.write(" negotiation auto\n\n")
                port += 1

        # Internal interfaces
        if router.type == "client":
            file.write(f"interface GigabitEthernet{port}/0\n"
                       f" ip address 10.10.10{router.rid}.{router.rid} 255.255.255.0\n")
            file.write(" negotiation auto\n\n")
            port += 1

        if router.type == "edge" or router.type == "core":
            file.write("router ospf 1\n"
                       f" router-id {router.rid}.{router.rid}.{router.rid}.{router.rid}\n\n")
        if router.type == "edge":
            file.write(f" passive-interface GigabitEthernet{port - 1}/0\n\n")

        # Config BGP
        if router.type != "core":

            file.write(f"router bgp {router.AS}\n"
                       f"bgp router-id {router.rid}.{router.rid}.{router.rid}.{router.rid}\n"
                       "bgp log-neighbor-changes\n\n")

            # BGP neighbor inside AS : all edge routers
            if router.type == "edge":
                for neighbor in bb_routers:
                    if neighbor.type == 'edge':
                        file.write(f"neighbor {neighbor.rid}.{neighbor.rid}.{neighbor.rid}.{neighbor.rid} "
                                   f"remote-as {router.AS}\n")
                        file.write(f"neighbor {neighbor.rid}.{neighbor.rid}.{neighbor.rid}.{neighbor.rid} "
                                   f"update-source Loopback0\n\n")

            # BGP with client on their interface
            for i in range(len(router.exteriors)):
                file.write(
                    f"neighbor 10.10.{min(router.exteriors[i].rid, router.rid)}"
                    f"{max(router.exteriors[i].rid, router.rid)}."
                    f"{router.exteriors[i].rid} remote-as {router.exteriors[i].AS}\n")

            file.write("\naddress-family ipv4\n")

            if router.type == "client":
                file.write(f"network 10.10.10{router.rid}.0 mask 255.255.255.0\n")

            for neighbor in router.neighbors:
                file.write(f"neighbor {neighbor}.{neighbor}.{neighbor}.{neighbor} activate\n")
            for exterior in router.exteriors:
                file.write(
                    f"neighbor 10.10.{min(exterior.rid, router.rid)}{max(exterior.rid, router.rid)}.{exterior.rid} activate\n")
            file.write("exit-address-family\n\n")

        file.write("ip forward-protocol nd\n"
                   "no ip http server\n"
                   "no ip http secure-server\n\n")

        # Force loopback adress
        if router.type != "client":
            file.write("\nmpls ldp router-id Loopback0 force\n\n")

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
