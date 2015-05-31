#!/usr/bin/python2
# -*- coding: utf-8 -*-

"""
/centralized/python/DNSWrapper.py

Part of master thesis "Using Service Discovery to Apply Policies in Networks"
at University of Liège 2014-2015.
by Amaury Van Bemten.

Entreprise: Cisco
Contact entreprise: Eric Vyncke
Advisor: Guy Leduc
"""

import dns.resolver
import dns.exception
import dns.query
import dns.name
import socket
import re

LABEL_NAME_ERROR  = 11
NS_UNRESOLVED     = 12
NS_QUERYING_ERROR = 13
SOCKET_ERROR      = 14


# Methods inspired from:
# http://stackoverflow.com/questions/21300996/process-decimal-escape-in-string
# unescape() uses replace() to unescape DNS names returned by dnspython.
def replace(match):
  return chr(int(match.group(1)))

def unescape(line):
  regex = re.compile(r"\\(\d{1,3})")
  new = regex.sub(replace, line)
  return new.replace("\\", "")

class DNSWrapper:
  """A wrapper around the dnspython library to allow to easily perform DNS
  requests on a particular domain."""

  def __init__(self, domain):
    """Constructor."""

    self.domain = domain

  def getSerial(self):
    """Gets the serial field of the SOA of the domain.

    Returns:
      The serial field of the SOA or 0 if query fails.
    """

    try:
      answers = dns.resolver.query(self.domain, 'SOA')

      for rdata in answers:
        soa = rdata.serial
    except (dns.resolver.NXDOMAIN, 
            dns.resolver.NoAnswer,
            dns.resolver.NoNameservers,
            dns.exception.Timeout,
            dns.exception.DNSException):
      soa = 0

    return soa

  def getServices(self):
    """Gets the services announced in the domain and its subdomains.

    Returns:
      A dictionary A whose keys are the different subdomains found. Elements of 
      A are dictionaries B whose keys are the different types found in the 
      subdomain. Elements of B are arrays of dictionaries C representing the
      services of the given type in the given subdomain. Those services are 
      represented by the keys: name, port, host, addresses (array of addresses). 

      None in case of failure.
    """
    
    services = dict()

    # Getting subdomains.
    try:
      subdomains_answer = dns.resolver.query('b._dns-sd._udp.' + self.domain.strip("."), 'PTR')
    except (dns.resolver.NoAnswer,
            dns.resolver.NXDOMAIN,
            dns.exception.DNSException):
      return None

    # For each subdomain, getting the different types.
    for subdomains in subdomains_answer:
      subdomain = str(subdomains.target)
      services[subdomain] = dict()
      
      try:
        types_answer = dns.resolver.query('_services._dns-sd._udp.' + subdomain.strip("."), 'PTR')
      except (dns.resolver.NoAnswer,
              dns.resolver.NXDOMAIN,
              dns.exception.DNSException):
        return None

      # For each type, getting the different services.
      for types in types_answer:
        type = str(types.target)
        services[subdomain][type] = []

        try:
          instances_answer = dns.resolver.query(type, 'PTR')
        except (dns.resolver.NoAnswer,
                dns.resolver.NXDOMAIN,
                dns.exception.DNSException):
          return None

        # For each instance, getting host, addresses and port.
        for instances in instances_answer:
          services[subdomain][type].append(dict())
          instance = unescape(str(instances.target))
          services[subdomain][type][-1]['name'] = instance

          # Host and port.
          try:
            srv_answer = dns.resolver.query(instances.target, 'SRV')
          except (dns.resolver.NoAnswer,
                  dns.resolver.NXDOMAIN,
                  dns.exception.DNSException):
            return None

          # Should be only one.
          for srv in srv_answer:
            services[subdomain][type][-1]['port'] = srv.port
            services[subdomain][type][-1]['host'] = str(srv.target)

          # IPv6 addresses.
          addresses = []
          try:
            answers_IPv6 = dns.resolver.query(srv.target, 'AAAA')

            for rdata in answers_IPv6:
              addresses.append(rdata.address)
          except (dns.resolver.NXDOMAIN,
                  dns.resolver.NoAnswer,
                  dns.resolver.NoNameservers,
                  dns.exception.Timeout,
                  dns.exception.DNSException):
            pass

          # IPv4 addresses.
          try:
            answers_IPv4 = dns.resolver.query(srv.target, 'A')

            for rdata in answers_IPv4:
              addresses.append(rdata.address)
          except (dns.resolver.NXDOMAIN,
                  dns.resolver.NoAnswer,
                  dns.resolver.NoNameservers,
                  dns.exception.Timeout,
                  dns.exception.DNSException):
            pass

          services[subdomain][type][-1]['addresses'] = addresses

    return services

  def getPublicInterfaces(self, router):
    """Gets the public interfaces announced by a router in the domain.

    Args:
      router: name of the router.

    Returns:
      An array of the interfaces announced by the router or None in case of 
      failure.
    """

    interfaces = []
    try:
      answer = dns.resolver.query(router + "." + self.domain.strip("."), 'TXT')

      for rdata in answer:
        for string in rdata.strings:
          if string.startswith("public="):
            # Remove "public=" and split interfaces (separated by commas).
            ifcs = string[7:].split(",")
            for ifc in ifcs:
              interfaces.append(ifc)
    except (dns.resolver.NXDOMAIN,
            dns.resolver.NoAnswer,
            dns.resolver.NoNameservers,
            dns.exception.Timeout,
            dns.exception.DNSException):
      return None

    return interfaces
