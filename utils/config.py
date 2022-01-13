class Config():
    def generate_config(self, type, rid, neighbors, AS, exteriors, exteriors_as, file):
        """
        Stateless function writing a router config to a file

        :param type: "core"|"edge"|"client"
        :param rid: router id
        :param neighbors: array of neighbor rid
        :param AS: AS number of the router
        :param exteriors: array of client rid linked | edge routers for clients
        :param exteriors_as: array of client|edge  ASes corresponding to exterior array
        :param file: file to write to
        """
        file.write("version 15.2\n"
                   "service timestamps debug datetime msec\n"
                   "service timestamps log datetime msec\n\n")

        file.write(f"hostname R{rid}\n"
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
        if type != "client":
            file.write(f"interface Loopback0\n"
                       f"ip address {rid}.{rid}.{rid}.{rid} 255.255.255.255\n"
                       "ip ospf 1 area 1\n\n")

        file.write("interface FastEthernet0/0\n"
                   "no ip address\n"
                   "duplex full\n\n")

        port = 1

        # Other edge and core routers
        for neighbor in neighbors:
            file.write(f"interface GigabitEthernet{port}/0\n"
                       f" ip address 10.10.{min(neighbor, rid)}{max(neighbor, rid)}.{rid} 255.255.255.0\n")
            file.write("ip ospf 1 area 1\n")
            file.write(" negotiation auto\n")

            if type != "client":
                file.write(" mpls ip\n")

            file.write("\n")
            port += 1

        if type != "core":
            # Client routers linked
            for exterior in exteriors:
                file.write(f"interface GigabitEthernet{port}/0\n"
                           f" ip address 10.10.{min(exterior, rid)}{max(exterior, rid)}.{rid} 255.255.255.0\n")

                if type != "client":
                    file.write("ip ospf 1 area 1\n")

                file.write(" negotiation auto\n\n")
                port += 1

        # Internal interfaces
        if type == "client":
            file.write(f"interface GigabitEthernet{port}/0\n"
                       f" ip address 10.10.10{rid}.{rid} 255.255.255.0\n")
            file.write(" negotiation auto\n\n")
            port += 1

        if type == "edge" or type == "core":
            file.write("router ospf 1\n"
                       f" router-id {rid}.{rid}.{rid}.{rid}\n\n")
        if type == "edge":
            file.write(f" passive-interface GigabitEthernet{port-1}/0\n\n")

        if type != "core":
            # Config BGP
            file.write(f"router bgp {AS}\n"
                       f"bgp router-id {rid}.{rid}.{rid}.{rid}\n"
                       "bgp log-neighbor-changes\n\n")

            # BGP neighbor : loopback adress
            for neighbor in neighbors:
                file.write(f"neighbor {neighbor}.{neighbor}.{neighbor}.{neighbor} remote-as {AS}\n")
                file.write(f"neighbor {neighbor}.{neighbor}.{neighbor}.{neighbor} update-source Loopback0\n\n")

            # BGP with client on their interface
            for i in range(len(exteriors)):
                file.write(
                    f"neighbor 10.10.{min(exteriors[i], rid)}{max(exteriors[i], rid)}.{exteriors[i]} remote-as {exteriors_as[i]}\n")

            file.write("\naddress-family ipv4\n")

            if type == "client":
                file.write(f"network 10.10.10{rid}.0 mask 255.255.255.0\n")

            for neighbor in neighbors:
                file.write(f"neighbor {neighbor}.{neighbor}.{neighbor}.{neighbor} activate\n")
            for exterior in exteriors:
                file.write(f"neighbor 10.10.{min(exterior, rid)}{max(exterior, rid)}.{exterior} activate\n")
            file.write("exit-address-family\n\n")

        file.write("ip forward-protocol nd\n"
                   "no ip http server\n"
                   "no ip http secure-server\n\n")

        # Force loopback adress
        if type != "client":
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
