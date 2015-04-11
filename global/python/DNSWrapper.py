#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
/global/python/DNSWrapper.py

Part of master's thesis "Using Service Discovery to Apply Policies in Networks"
at University of Liège 2014-2015.
Amaury Van Bemten.

Entreprise: Cisco
Contact entreprise: Eric Vyncke
Advisor: Guy Leduc
"""

import dns.resolver
import dns.exception
import dns.query
import dns.name
import socket          # To catch socket errors.

LABEL_NAME_ERROR  = 11
NS_UNRESOLVED     = 12
NS_QUERYING_ERROR = 13
SOCKET_ERROR      = 14

class DNSWrapper:
  """A wrapper around the python-dns library to allow to easily perform
     DNS requests on a particular domain.
  """

  def __init__(self, domain):
    self.domain = domain

  def getSerial(self):
    try:
      answers = dns.resolver.query(self.domain, 'SOA')

      for rdata in answers:
        soa = rdata.serial
    except (dns.resolver.NXDOMAIN, 
            dns.resolver.NoAnswer,
            dns.resolver.NoNameservers,
            dns.exception.Timeout,
            dns.exception.DNSException) as e:
      soa = 0

    return soa

  def getServices(self):
    
    services = dict()

    # Getting subdomains
    try:
      subdomains_answer = dns.resolver.query('b._dns-sd._udp.' + self.domain.strip("."), 'PTR')
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.DNSException) as e:
      return None

    # For each subdomain, getting the different types.
    for subdomains in subdomains_answer:
      subdomain = str(subdomains.target)
      services[subdomain] = dict()
      
      try:
        types_answer = dns.resolver.query('_services._dns-sd._udp.' + subdomain.strip("."), 'PTR')
      except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.DNSException) as e:
        return None

      # For each type, getting the different services.
      for types in types_answer:
        type = str(types.target)
        services[subdomain][type] = []

        try:
          instances_answer = dns.resolver.query(type, 'PTR')
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.DNSException) as e:
          return None

        # For each instance, getting host, ip and port
        for instances in instances_answer:
          services[subdomain][type].append(dict())
          instance = str(instances.target)
          services[subdomain][type][-1]['name'] = instance

          try:
            srv_answer = dns.resolver.query(instances.target, 'SRV')
          except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.DNSException) as e:
            return None

          # Should be only one.
          for srv in srv_answer:
            services[subdomain][type][-1]['port'] = srv.port
            services[subdomain][type][-1]['host'] = str(srv.target)

          # Getting the IP addresses.
          addresses = []
          try:
            answers_IPv6 = dns.resolver.query(srv.target, 'AAAA')

            for rdata in answers_IPv6:
              addresses.append(rdata.address)
          except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers, dns.exception.Timeout, dns.exception.DNSException):
            pass

          try:
            answers_IPv4 = dns.resolver.query(srv.target, 'A')

            for rdata in answers_IPv4:
              addresses.append(rdata.address)
          except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers, dns.exception.Timeout, dns.exception.DNSException):
            pass

          services[subdomain][type][-1]['addresses'] = addresses

    return services

  def getPublicInterfaces(self, router):
    interfaces = []
    try:
      answer = dns.resolver.query(router + "." + self.domain.strip("."), 'TXT')

      for rdata in answer:
        for string in rdata.strings:
          if string.startswith("public="):
            ifcs = string[7:].split(",")
            for ifc in ifcs:
              interfaces.append(ifc)
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers, dns.exception.Timeout, dns.exception.DNSException):
      return None

    return interfaces
