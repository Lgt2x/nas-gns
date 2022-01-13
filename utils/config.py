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
        file.write("version 15.2"
                   "service timestamps debug datetime msec"
                   "service timestamps log datetime msec")

        file.write(f"hostname R{rid}"
                   "boot-start-marker"
                   "boot-end-marker"
                   "no aaa new-model"
                   "no ip icmp rate-limit unreachable")

        file.write(f"ip cef"
                   "no ip domain lookup"
                   "no ipv6 cef")

        file.write(f"mpls label protocol ldp"
                   "multilink bundle-name authenticated"
                   "ip tcp synwait-time 5")

        # Configure loopback adress
        file.write(f"interface Loopback0"
                   f"ip address {rid}.{rid}.{rid}.{rid} 255.255.255.255"
                   "ip ospf 1 area 1")

        file.write("interface FastEthernet0/0"
                   "no ip address"
                   "duplex full")

        file.write("interface FastEthernet0/0"
                   "no ip address"
                   "duplex full")

        port = 1

        # Other edge and core routers
        for neighbor in neighbors:
            file.write(f"interface GigabitEthernet{port}/0"
                       f" ip address 10.10.{min(neighbor, rid)}{max(neighbor, rid)}.{rid} 255.255.255.0"
                       " ip ospf 1 area 1"
                       " negotiation auto")

            if type != "client":
                file.write(" mpls ip")

            port += 1

        if type != "core":
            # Client routers linked
            for exterior in exteriors:
                file.write(f"interface GigabitEthernet{port}/0"
                           f" ip address 10.10.{min(exterior, rid)}{max(exterior, rid)}.{rid} 255.255.255.0"
                           " ip ospf 1 area 1"
                           " negotiation auto")

                file.write("router ospf 1"
                           f" router-id {rid}.{rid}.{rid}.{rid}"
                           f" passive-interface GigabitEthernet{port}/0")
                port += 1

            # Config BGP
            file.write(f"router bgp {AS}"
                       f"bgp router-id {rid}.{rid}.{rid}.{rid}"
                       "bgp log-neighbor-changes")

            # BGP neighbor : loopback adress
            for neighbor in neighbors:
                file.write(f"neighbor {neighbor}.{neighbor}.{neighbor}.{neighbor} remote-as {AS}")
                file.write(f"neighbor {neighbor}.{neighbor}.{neighbor}.{neighbor} update-source Loopback0")

            # BGP with client on their interface
            for i in range(len(exteriors)):
                file.write(
                    f"neighbor 10.10.{min(exteriors[i], rid)}{max(exteriors[i], rid)}.{exteriors[i]} remote-as {exteriors_as[i]}")

            file.write("address-family ipv4")
            for neighbor in neighbors:
                file.write(f"neighbor {neighbor}.{neighbor}.{neighbor}.{neighbor} activate")
            for exterior in exteriors:
                file.write(f"neighbor 10.10.{min(exterior, rid)}{max(exterior, rid)}.{exterior} activate")
            file.write("exit-address-family")

        file.write("ip forward-protocol nd"
                   "no ip http server"
                   "no ip http secure-server")

        # Force loopback adress
        if type != "client":
            file.write("mpls ldp router-id Loopback0 force")

        file.write("control-plane"
                   "line con 0"
                   " exec-timeout 0 0"
                   " privilege level 15"
                   " logging synchronous"
                   " stopbits 1"
                   "line aux 0"
                   " exec-timeout 0 0"
                   " privilege level 15"
                   " logging synchronous"
                   " stopbits 1"
                   "line vty 0 4"
                   "login")

        file.write("end")
