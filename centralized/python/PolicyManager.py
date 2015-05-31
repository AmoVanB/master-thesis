#!/usr/bin/python2
# -*- coding: utf-8 -*-

"""
/centralized/python/PolicyManager.py

Part of master thesis "Using Service Discovery to Apply Policies in Networks"
at University of Liège 2014-2015.
by Amaury Van Bemten.

Entreprise: Cisco
Contact entreprise: Eric Vyncke
Advisor: Guy Leduc
"""

import sys             # for sys.exit
import logging         # for logging
import re              # for regular expressions 
import time            # to compare config modification times and time.sleep
import os              # to get config modification time

import netaddr         # for manipulation of IP addresses
from lxml import etree # to parse .xml and .dtd files

import DNSWrapper      # to communicate with the DNS

class ConfigError(Exception):
  """Exception raised when encountering an error in the configuration file."""
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

class PolicyManager:
  """Class allowing to establish iptables rules based on user-defined
  preferences and on the content of a DNS zone.

  To start the process, simply call the start() method."""

  def __init__(self, logger, domain, rate):
    """Constructor."""

    self.run    = False  # Currently not running.
    self.logger = logger
    self.domain = domain
    self.rate   = rate

  def start(self):
    """Starts the process."""

    self.run = True
    wrapper = DNSWrapper.DNSWrapper(self.domain)

    config_last_change = time.gmtime(0) # Initial modification: epoch time.
    dns_last_change    = 0              # Initial serial: zero.

    while(self.run):
      self.logger.debug("Checking for changes.")

      # Retrieving SOA and modification time.
      dns_current_serial    = wrapper.getSerial()
      config_current_change = os.path.getmtime('/etc/policy-manager/config.xml')

      if (dns_current_serial    > dns_last_change or
          config_current_change > config_last_change):
        self.logger.info("Change detected. Generating new rules.")

        rules = self.getRules()
        services = wrapper.getServices()

        # Implementation of Algorithm 1 Section 5.1.4.3 of the report. 

        # For each router.
        for router_fqdn in services.keys():
          # Getting only the name of the router.
          router = router_fqdn.split(".")[0]

          # Getting public interfaces of the router.
          input_ifcs = wrapper.getPublicInterfaces(router)
          if not input_ifcs or len(input_ifcs) == 0:
            self.logger.warning("No public interface found for router %s. " +
                                "No rules applied." % router)
            break

          # Creating iptables file.
          iptables_file = open('/etc/policy-manager/iptables_' + router + '.sh',
                               'w')

          # Removing rules not concerning the current router.
          rules_routers_filtered = []
          for rule in rules:
            if rule['router'] == router or rule['router'] == "*":
              rules_routers_filtered.append(rule)

          # For each rule.
          for rule in rules_routers_filtered:
            try:
              ip_version = netaddr.IPAddress(rule['src-address']).version
            except netaddr.core.AddrFormatError:
              self.logger.warning("%s is not a valid address. Rule " +
                                  "ignored." % rule['src-address'])
              break

            # Computing the services matching the rule.
            match_services = []
            for stype_fqdn in services[router_fqdn].keys():
              # Keeping only service name.
              stype = stype_fqdn.strip(".")[:-len(router_fqdn.strip("."))-1]

              for service in services[router_fqdn][stype]:
                # Check if IP versions are the same.
                ip_ok = False
                for add in service['addresses']:
                  if ip_version == netaddr.IPAddress(add).version:
                    ip_ok = True
                    break

                # Check if the regular expressions match the name and type of
                # the service.
                if (ip_ok and re.match(rule['name'], service['name'])
                          and re.match(rule['type'], stype):
                  match_services.append(service)
  
            # For each service matching the rule.
            for match_service in match_services:
              # For each interface.
              for ifc in input_ifcs:
                # For each address.
                for address in match_service['addresses']:

                  # Creation of the rule (only if IP addresses match).
                  if ip_version == netaddr.IPAddress(address).version:

                    # Choosing between iptables and ip6tables.
                    string = ""
                    if (ip_version == 4):
                      string += "iptables -t filter -A FORWARD "
                    else:
                      string += "ip6tables -t filter -A FORWARD "

                    # Choosing between tcp and !tcp. Indeed, RFC6763 specifies
                    # that _udp is for any other protocol than TCP. It does 
                    # not mean UDP.
                    if (stype.split(".")[-1][1:]) == 'tcp':
                      string += "-p tcp "
                    else:
                      string += "-p !tcp "

                    # Specifying source address and prefix from the rule.
                    string += "-s %s/%s " % (rule['src-address'],
                                             rule['src-prefix-length'])
  
                    # Interface.
                    string += "-i %s " % ifc
      
                    # Destination is the address of the service.
                    string += "-d %s " % address
  
                    # Port is the port on which the service is running.
                    string += "--dport %i " % match_service['port']

                    # ACCEPT or DROP based on the rule.
                    if (rule['action'] == 'allow'):
                      string += "-j ACCEPT"
                    else:
                      string += "-j DROP"

                    iptables_file.write(string + "\n")

          # Deny by default
          iptables_file.write("iptables  -t filter -P FORWARD DROP\n")
          iptables_file.write("ip6tables -t filter -P FORWARD DROP\n")
          iptables_file.close()

        self.logger.info("Rules updated.")

        # Update SOA and modification time only if we computed the new rules.
        if services and rules:
          dns_last_change = dns_current_serial
          config_last_change = config_current_change  

      time.sleep(int(self.rate)) # every x seconds.

  def stop(self):
    """Stops the computations."""

    self.run = False

  def getRules(self):
    """Gets rules from the configuration file.

    Returns:
      An array of the rules (which are dictionaries) or None in case of failure.
    """

    # Checking configuration file versus DTD.
    try:
      dtd = etree.DTD("/etc/policy-manager/config.dtd")
      xml = etree.parse("/etc/policy-manager/config.xml")
      if (not dtd.validate(xml)):
        self.logger.error("Configuration file is not a valid instance of DTD. "+
                          "Firewall rules not generated.")
        return None
    except etree.LxmlError as e:
      self.logger.error("Error while parsing configuration file: %s" % e)
      return None      

    # Since we performed the DTD validation, we are sure the requested tags

    rules = []
    rules_tag = xml.find("./rules")
    if (rules_tag == None):
      pass # Rules are not mandatory.
    else:
      # For each rule.
      for el in rules_tag:
        action = el.text.strip() # Remove leading/trailing blanks.
        if (action.lower() != "allow" and action.lower() != "deny"):
          self.logger.warning("Action '%s' is neither 'allow' nor 'deny'. " +
                              "Rule ignored.", action)
          continue

        # Add each rule in the 'rules' array.
        d = dict(el.items())
        d["action"] = action.lower()
        rules.append(d)

    if (len(rules) == 0):
      self.logger.warning("No rules found.")

    return rules
