#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 16 08:36:11 2021

@author: prenaud
"""
import sys
from datetime import datetime


if __name__ == "__main__":
	name = "coucou" #name codé en dur
	cfgFile = open(r"config.cfg","w")
	str1 = "!\n! Last configuration change at "
	cfgFile.write(str1)
	now = datetime.now()
	date = now.strftime("%H:%M:%S UTC+1 %a %b %-d %Y")
	#should do something like : 13:24:18 UTC Sun Nov 28 2021
	#CF https://www.programiz.com/python-programming/datetime/strftime
	str1=(f"{date}\n!\nversion 15.2\nservice timestamps debug datetime msec\nservice timestamps log datetime msec\n!\n")
	cfgFile.write(str1)
	print(date)
	if sys.argv[1] == "PE" :
		print("Provider Edge Router")
		cfgFile.write("#Provider Edge router\n")
				
	cfgFile.write(f"hostname {name}\n"	
	           "!\n"
			   "boot-start-marker\nboot-end-marker\n"
			   "!\n"
			   "!\n"
			   "!\n"
			   "no aaa new-model\n"
			   "no ip icmp rate-limit unreachable\n"
			   "#On active ip cef pour faire fonctionner BGP\nip cef\n"
			   "!\n"
			   "!\n"
			   "no ip domain lookup\n"
			   "no ipv6 cef\n"
			   "!\n"
			   "!\n"
			   "multilink bundle-name authenticated\n"
			   "!\n"
			   "ip tcp synwait-time 5\n"
			   "!\n"
			   "#Configuration des interfaces (TODO)\n")
	#Config des interfaces à base de boucle for
	for i in range(3):
		cfgFile.write(f"interface GigabitEthernet{i}/0\n"
				" ip address 10.10.1.2 255.255.255.0 (hard-coded)...\n"
				" ip ospf 1 area 1\n"
				" negotiation auto\n"
				" mpls ip\n"
				"!\n")
	
	#Config OSPF
	cfgFile.write("router ospf 1\n"
			   " router-id x.x.x.x (hard-coded)\n"
			   "!\n")
	
	#Config BGP du routeur avec ses voisins
	
	cfgFile.write(" address-family ipv4\n")
	
	cfgFile.write(" exit address-family\n")
	
	cfgFile.write("ip forward-protocol nd\n"
			   "!\n"
			   "no ip http server\n"
			   "no ip http secure-server\n"
			   "!\n"
			   "!\n"
			   "control-plane\n"
			   "!\n"
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
			   " login\n"
			   "!\n"
			   "end\n")
			   
	
	
	
	
	cfgFile.close()
	