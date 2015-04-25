#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
/global/python/PolicyManager.py

Part of master's thesis "Using Service Discovery to Apply Policies in Networks"
at University of Liège 2014-2015.
Amaury Van Bemten.

Entreprise: Cisco
Contact entreprise: Eric Vyncke
Advisor: Guy Leduc
"""

import sys                     # for sys.exit
import logging                 # for logging
import re                      # for regular expressions 
import time
import os
import netaddr

from DNSWrapper import DNSWrapper

import netaddr                 # for manipulation of IP addresses
from lxml import etree         # to parse .xml and .dtd files

class ConfigError(Exception):
  """Exception raised when encountering an error in the configuration file."""
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return repr(self.value)


class PolicyManager:
  """Class allowing to establish iptables rules based on user-defined
  preferences and on the content of a DNS zone.

  To start the process, simply call the start() method.
  """

  def __init__(self, logger, domain, rate):
    """Constructor.
    """
    self.run = False
    self.logger = logger
    self.domain = domain
    self.rate = rate

  def start(self):
    """Starts the process.
    """

    self.run = True

    wrapper = DNSWrapper(self.domain)

    config_last_change = time.gmtime(0) # Initial modification: epoch time.
    dns_last_change    = 0              # Initial serial: zero.

    while(self.run):
      print("iteration")
      # Retrieving SOA and modification time
      dns_current_serial = wrapper.getSerial()
      config_current_change = os.path.getmtime('/etc/policy-manager/config.xml')

      if (dns_current_serial    > dns_last_change or
          config_current_change > config_last_change):

        rules = self.getRules()
        services = wrapper.getServices()

        for router_fqdn in services.keys():
          router = router_fqdn.split(".")[0]

          input_ifcs = wrapper.getPublicInterfaces(router)
          if not input_ifcs or len(input_ifcs) == 0:
            self.logger.warning("No public interface found for router %s. No rules applied." % router)
            break

          iptables_file = open('/etc/policy-manager/iptables_' + router + '.sh', 'w')

          # Deny by default
          iptables_file.write("iptables  -t filter -P FORWARD DROP # Deny by default\n")
          iptables_file.write("ip6tables -t filter -P FORWARD DROP # Deny by default\n")

          # Removing rules not concerning the current router.
          rules_routers_filtered = []
          for rule in rules:
            if rule['router'] == router or rule['router'] == "*":
              rules_routers_filtered.append(rule)

          for stype_fqdn in services[router_fqdn].keys():
            stype = stype_fqdn.strip(".")[:-len(router_fqdn.strip("."))-1]

            # Removing rules not concerning the current service type.
            rules_stype_filtered = []
            for rule in rules_routers_filtered:
              if re.match(rule['type'], stype):
                rules_stype_filtered.append(rule)

            for rule in rules_stype_filtered:
              match_services = []
              for service in services[router_fqdn][stype_fqdn]:
                ip_ok = False
                ip_version = netaddr.IPAddress(rule['src-address']).version
                for add in service['addresses']:
                  if ip_version == netaddr.IPAddress(add).version:
                    ip_ok = True
                    break

                if ip_ok and re.match(rule['name'], service['name']):
                  match_services.append(service)
    
              for match_service in match_services:
                # Create IP table rules. One for each input interface and for each ip address.

                for ifc in input_ifcs:
                  for address in match_service['addresses']:
                    if ip_version == netaddr.IPAddress(address).version:
                      string = ""
                      if (ip_version == 4):
                        string = string + "iptables -t filter -A FORWARD "
                      else:
                        string = string + "ip6tables -t filter -A FORWARD  "
  
                      if (stype.split(".")[-1][1:]) == 'tcp':
                        string = string + "-p tcp "
                      else:
                        string = string + "-p !tcp " # Because DNS-SD RFC specifies that _udp is for any other protocol than _tcp

                      string = string + "-s %s/%s " % (rule['src-address'], rule['src-mask'])
    
                      string = string + "-i %s " % ifc
        
                      string = string + "-d %s " % address
    
                      string = string + "--dport %i " % match_service['port']
  
                      if (rule['action'] == 'allow'):
                        string = string + "-j ACCEPT"
                      else:
                        string = string + "-j DROP"

                      iptables_file.write(string + "\n")

          iptables_file.close()

        if services and rules:
          dns_last_change = dns_current_serial
          config_last_change = config_current_change  

      time.sleep(int(self.rate)) # every 30 sec

  def stop(self):
    self.run = False

  def getRules(self):
    # Checking configuration file versus DTD.
    try:
      dtd = etree.DTD("/etc/policy-manager/config.dtd")
      xml = etree.parse("/etc/policy-manager/config.xml")
      if (not dtd.validate(xml)):
        self.logger.error("Configuration file is not a valid instance of DTD. Firewall rules not generated.")
        return None
    except etree.LxmlError as e:
      self.logger.error("Error while parsing config.xml and/or config.dtd: %s" % e)
      return None      

    # Since we performed the DTD validation, we are sure the requested tags
    # will exist. Note that this is only valid if the config.dtd file is not 
    # corrupted, of course.

    # Getting name and alias.
    config = xml.getroot()

    # List of filtering rules.
    rules = []
    rules_tag = xml.find("./rules")
    if (rules_tag == None):
      pass # Rules are not mandatory.
    else:
      for el in rules_tag:
        action = el.text.strip() # Remove leading/trailing blanks.
        if (action.lower() != "allow" and action.lower() != "deny"):
          self.logger.warning("Action '%s' is neither 'allow' nor 'deny'. Rule ignored.", action)
          continue

        d = dict(el.items())
        d["action"] = action.lower()
        rules.append(d)

    if (len(rules) == 0):
      self.logger.warning("No rules found. No services will be available publicly.")

    return rules
