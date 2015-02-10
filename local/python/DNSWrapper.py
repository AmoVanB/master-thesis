#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
/python/DNSWrapper.py

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
import dns.update
import dns.tsigkeyring
import dns.name
import socket          # To catch socket errors.
import Miscellaneous

LABEL_NAME_ERROR  = 11
NS_UNRESOLVED     = 12
NS_QUERYING_ERROR = 13
SOCKET_ERROR      = 14

class DNSWrapper:
  """A wrapper around the python-dns library to allow to easily perform
     DNS updates on a particular zone.
  """

  def __init__(self, server, key_name, key_value, zone, algorithm):
    """Constructor.

      Args:
        server:    Server name to contact.
        key_name:  Name of the TSIG key to use to authenticate to the server.
        key_value: TSIG key value.
        zone:      Name of the zone to update.
        algorithm: Name of the signature algorithm to use.
                   HMAC-MD5.SIG-ALG.REG.INT., hmac-sha1, hmac-sha224,
                   hmac-sha256, hmac-sha384, hmac-sha512 are supported.
    """
    ## Server name.
    self.server = server
    ## TSIG key's name.
    self.key_name = key_name
    ## TSIG key's value.
    self.key_value = key_value
    ## Zone to update.
    self.zone = zone
    ## TSIG algorithm used to sign.
    self. algorithm = algorithm

    ## DNS Update (RFC2136) error codes based on their number.
    self.DNSUpdateErrorCodes = {1: 'FORMERR',
                                2: 'SERVFAIL',
                                3: 'NXDOMAIN',
                                4: 'NOTIMP',
                                5: 'REFUSED',
                                6: 'YXDOMAIN',
                                7: 'YXRRSET',
                                8: 'NXRRSET', 
                                9: 'NOTAUTH', 
                               10: 'NOTZONE'}

    ## DNS Update (RFC2136) error strings based on their number.
    # From RFC2136 - Section 2.2.
    self.DNSUpdateErrorStrings = {1: 'The name server was unable to interpret '+
                                     'the request due to a format error.',
                                  2: 'The name server encountered an internal '+
                                     'failure while processing this request, ' +
                                     'for example an operating system error '  +
                                     'or a forwarding timeout.',
                                  3: 'Some name that ought to exist, '         +
                                     'does not exist.',
                                  4: 'The name server does not support '       +
                                     'the specified Opcode.',
                                  5: 'The name server refuses to perform the ' +
                                     'specified operation for policy or '      +
                                     'security reasons.',
                                  6: 'Some name that ought not to exist, '     +
                                     'does exist.',
                                  7: 'Some RRset that ought not to exist, '    +
                                     'does exist.',
                                  8: 'Some RRset that ought to exist, '        +
                                     'does not exist.',
                                  9: 'The server is not authoritative for '    +
                                     'the zone named in the Zone Section.',
                                 10: 'A name used in the Prerequisite or '     +
                                     'Update Section is not within the '       +
                                     'zone denoted by the Zone Section.'}

    ## Description of the error the class may return based on their integer
    # representation.
    self.errors = self.DNSUpdateErrorStrings
    self.errors[LABEL_NAME_ERROR]  = 'Label or name too long or empty.'
    self.errors[NS_UNRESOLVED]     = 'Nameserver unresolved.'
    self.errors[NS_QUERYING_ERROR] = 'Error querying nameserver. ' +\
                                     'Probably do to the key.' 
    self.errors[SOCKET_ERROR]      = 'Socket error.'


  def resolve(self, name):
    """Resolves a DNS name to its IP addresses.

    Args:
        name:   DNS name to resolve.

    Returns:
        A size 2 array containing the IPv6 and IPv4 addresses of the DNS name.
        If one of them is not found, None is placed at the corresponding
        element.
    """

    addresses = [None, None]
    try:
      # First trying IPv6.
      answers_IPv6 = dns.resolver.query(name, 'AAAA')

      for rdata in answers_IPv6:
        addresses[0] = rdata.address
    except (dns.resolver.NXDOMAIN, 
            dns.resolver.NoAnswer,
            dns.resolver.NoNameservers,
            dns.exception.Timeout,
            dns.exception.DNSException) as e:
      addresses[0] = None

    try:
      # Try IPv4.
      answers_IPv4 = dns.resolver.query(name, 'A')
      for rdata in answers_IPv4:
        addresses[1] = rdata.address
    except (dns.resolver.NXDOMAIN, 
            dns.resolver.NoAnswer,
            dns.resolver.NoNameservers,
            dns.exception.Timeout,
            dns.exception.DNSException) as e:
      addresses[1] = None

    return addresses


  def removeRecord(self, name, rtype, rdata = None):
    """Removes a record from the DNS zone.

    Args:
      name:  Name of the record to remove.
      rtype: Type of the record to remove.
      rdata: Rdata of the record to remove. If None, the removal is done
             independently of the rdata value.

    Returns:
      Integer code whose signification can be retrieved in DNSWrapper.errors.
      0 is successful, another value represents a particular error.
    """

    # Getting name server's IP address.
    server_addresses = self.resolve(self.server)
    if (server_addresses[0] == None and server_addresses[1] == None):
      return NS_UNRESOLVED

    key = dns.tsigkeyring.from_text({self.key_name: self.key_value})
    update = dns.update.Update(self.zone,
                               keyring      = key,
                               keyalgorithm = self.algorithm)

    if (rdata == None):
      update.delete(name, rtype)
    else:
      update.delete(name, rtype, rdata)

    response = None

    try:
      # Use IPv6 if possible. If no IPv6 address, use IPv4.
      if (server_addresses[0] != None):
        response = dns.query.tcp(update, server_addresses[0])
      else:
        response = dns.query.tcp(update, server_addresses[1])
    except (dns.tsig.PeerBadKey,
            dns.tsig.PeerBadSignature,
            dns.exception.DNSException) as e: 
      return NS_QUERYING_ERROR
    except (socket.error):
      # Socket error may occur if the host does not support IPv[46] and we try
      # to connect to IPv[46] address of the name server. We thus try the other
      # IP version address. This can be done by first trying IPv4.
      try:
        if (server_addresses[1] != None):
          response = dns.query.tcp(update, server_addresses[1])
        else:
          response = dns.query.tcp(update, server_addresses[0])
      except (dns.tsig.PeerBadKey,
              dns.tsig.PeerBadSignature,
              dns.exception.DNSException) as e: 
        return NS_QUERYING_ERROR
      except (socket.error):
        return SOCKET_ERROR

    return response.rcode()


  def addRecord(self, name, ttl, rtype, rdata):
    """Adds a record to the DNS zone.

    Args:
      name:  Name of the record to add.
      ttl:   TTL of the record to add.
      rtype: Type of the record to add.
      rdata: Rdata of the record to add.

    Returns:
      Integer code whose signification can be retrieved in DNSWrapper.errors.
      0 is successful, another value represents a particular error.
    """

    # Getting name server's IP address.
    server_addresses = self.resolve(self.server)
    if (server_addresses[0] == None and server_addresses[1] == None):
      return NS_UNRESOLVED

    key = dns.tsigkeyring.from_text({self.key_name: self.key_value})
    update = dns.update.Update(self.zone,
                               keyring      = key,
                               keyalgorithm = self.algorithm)

    update.add(name, ttl, rtype, rdata)

    response = None

    try:
      # Use IPv6 if possible. If no IPv6 address, use IPv4.
      if (server_addresses[0] != None):
        response = dns.query.tcp(update, server_addresses[0])
      else:
        response = dns.query.tcp(update, server_addresses[1])
    except (dns.tsig.PeerBadKey,
            dns.tsig.PeerBadSignature,
            dns.exception.DNSException) as e: 
      return NS_QUERYING_ERROR
    except (socket.error):
      # Socket error may occur if the host does not support IPv[46] and we try
      # to connect to IPv[46] address of the name server. We thus try the other
      # IP version address. This can be done by first trying IPv4.
      try:
        if (server_addresses[1] != None):
          response = dns.query.tcp(update, server_addresses[1])
        else:
          response = dns.query.tcp(update, server_addresses[0])
      except (dns.tsig.PeerBadKey,
              dns.tsig.PeerBadSignature,
              dns.exception.DNSException) as e: 
        return NS_QUERYING_ERROR
      except (socket.error):
        return SOCKET_ERROR

    return response.rcode()


  def addService(self, name, stype, host, addresses, port, txt, ttl):
    """Announces a given service on the public DNS zone.

    Args:
      name:      Name of the service.
      stype:     Type of the service.
      host:      Name of the host hosting the service.
      addresses: Array of tuples. Each tuple represents an address to be
                 announced. Tuple are (int, string) with the int giving the IP
                 version of the address represented by string.
      port:      Port of the service on the host.
      txt:       Array of strings each of them containing a single
                 key=value pair.
      ttl:       TTL value to set to the added records.

    Returns:
      Integer code whose signification can be retrieved in DNSWrapper.errors.
      0 is successful, another value represents a particular error.
    """

    # Getting name server's IP address.
    server_addresses = self.resolve(self.server)
    if (server_addresses[0] == None and server_addresses[1] == None):
      return NS_UNRESOLVED

    key = dns.tsigkeyring.from_text({self.key_name: self.key_value})
    update = dns.update.Update(self.zone,
                               keyring      = key,
                               keyalgorithm = self.algorithm)

    # Transforming TXT array in string ("key=val key2=val2")
    txt_string = ''
    for elem in txt:
      txt_string = txt_string + elem + ' '
    if (len(txt_string) == 0):
      txt_string = '""'
    else:
      txt_string = txt_string[:-1] # Remove last space character
    

    try:
      name_type = Miscellaneous.escape("%s.%s" % (name, stype))
      update.add('_services._dns-sd._udp', ttl, 'PTR', stype)
      update.add(stype,                    ttl, 'PTR', name_type)
      update.add(name_type,                ttl, 'SRV', '0 0 %i %s'%(port, host))
      update.add(name_type,                ttl, 'TXT', txt_string)
      for t in addresses:
        if (t[0] == 6):
          update.add(host, ttl, 'AAAA', t[1])
        elif (t[0] == 4):
          update.add(host, ttl, 'A'   , t[1])

    except (dns.name.LabelTooLong,dns.name.NameTooLong,dns.name.EmptyLabel) as e:
      return LABEL_NAME_ERROR
    
    response = None

    try:
      # Use IPv6 if possible. If no IPv6 address, use IPv4.
      if (server_addresses[0] != None):
        response = dns.query.tcp(update, server_addresses[0])
      else:
        response = dns.query.tcp(update, server_addresses[1])
    except (dns.tsig.PeerBadKey,
            dns.tsig.PeerBadSignature,
            dns.exception.DNSException) as e: 
      return NS_QUERYING_ERROR
    except (socket.error):
      # Socket error may occur if the host does not support IPv[46] and we try
      # to connect to IPv[46] address of the name server. We thus try the other
      # IP version address. This can be done by first trying IPv4.
      try:
        if (server_addresses[1] != None):
          response = dns.query.tcp(update, server_addresses[1])
        else:
          response = dns.query.tcp(update, server_addresses[0])
      except (dns.tsig.PeerBadKey,
              dns.tsig.PeerBadSignature,
              dns.exception.DNSException) as e: 
        return NS_QUERYING_ERROR
      except (socket.error):
        return SOCKET_ERROR

    return response.rcode()


  def removeService(self, name, stype, host, delete_stype, delete_host):
    """Removes a given service from the public DNS zone.

    Args:
      name:         Name of the service.
      stype:        Type of the service.
      host:         Name of the host hosting the service.
      delete_stype: Boolean telling whether or not to delete the
                    record announcing the service type 'stype'.
      delete_host:  Boolean telling whether or not to delete the addresses of 
                    'host'.
    Returns:
      Integer code whose signification can be retrieved in DNSWrapper.errors.
      0 is successful, another value represents a particular error.
    """

    # Getting name server's IP address.
    server_addresses = self.resolve(self.server)
    if (server_addresses[0] == None and server_addresses[1] == None):
      return NS_UNRESOLVED

    key = dns.tsigkeyring.from_text({self.key_name: self.key_value})
    update = dns.update.Update(self.zone,
                               keyring = key,
                               keyalgorithm = self.algorithm)

    name_type = Miscellaneous.escape("%s.%s" % (name, stype))
    update.delete(stype,     'PTR', name_type)
    update.delete(name_type, 'SRV')
    update.delete(name_type, 'TXT')

    if (delete_host):
      update.delete(host, 'AAAA')
      update.delete(host, 'A')

    if (delete_stype):
      update.delete('_services._dns-sd._udp', 'PTR', stype)

    response = None

    try:
      # Use IPv6 if possible. If no IPv6 address, use IPv4.
      if (server_addresses[0] != None):
        response = dns.query.tcp(update, server_addresses[0])
      else:
        response = dns.query.tcp(update, server_addresses[1])
    except (dns.tsig.PeerBadKey,
            dns.tsig.PeerBadSignature,
            dns.exception.DNSException) as e: 
      return NS_QUERYING_ERROR
    except (socket.error):
      # Socket error may occur if the host does not support IPv[46] and we try
      # to connect to IPv[46] address of the name server. We thus try the other
      # IP version address. This can be done by first trying IPv4.
      try:
        if (server_addresses[1] != None):
          response = dns.query.tcp(update, server_addresses[1])
        else:
          response = dns.query.tcp(update, server_addresses[0])
      except (dns.tsig.PeerBadKey,
              dns.tsig.PeerBadSignature,
              dns.exception.DNSException) as e: 
        return NS_QUERYING_ERROR
      except (socket.error):
        return SOCKET_ERROR

    return response.rcode()


  def clearDNSServices(self):
    """Clears all services announced on the zone, given that the services
      have been announced correctly.

    Returns:
      Integer code whose signification can be retrieved in DNSWrapper.errors.
      0 is successful, another value represents a particular error.
    """

    # Getting name server's IP address.
    server_addresses = self.resolve(self.server)
    if (server_addresses[0] == None and server_addresses[1] == None):
      return NS_UNRESOLVED

    key = dns.tsigkeyring.from_text({self.key_name: self.key_value})
    update = dns.update.Update(self.zone,
                               keyring      = key,
                               keyalgorithm = self.algorithm)

    # We need to clear all the announced services.
    # Each services is announced thanks to 5 RRs:
    # 
    # PTR  _services._dns-sd._udp.<domain> -> <stype>.<domain>             [1]
    # PTR  <stype>.<domain>                -> <instance>.<stype>.<domain>  [2]
    # SRV  <instance>.<stype>.<domain>     -> SRV (<hostname>.<domain)     [3]
    # TXT  <instance>.<stype>.<domain>     -> TXT                          [4]
    # AAAA <hostname>.<domain>             -> IPv6 addr                    [5]
    # A    <hostname>.<domain>             -> IPv4 addr                    [6]
    #
    # A service running on IPv6 will announce [5],
    # A service running on IPv4 will announce [6].
    #
    # To clear all these RRs, we proceed as follows:
    # 1. [1] allows us to retrieve all announced types ([2]).
    # 2. We can now delete [1].
    # 3. From the different announced types ([2]), we retrieve the different
    #    instances of those types ([3] and [4]).
    # 4. We can now delete all [2].
    # 5. From all [3], we retrieve the different hostnames ([5] or [6]).
    # 6. We can now delete all [3] and [4].
    # 7. We can now delete all [5] or [6].
    # 8. Clear the 'b._dns-sd._udp' and 'db._dns-sd._udp' records.

    # 1. Getting all types that have been announced.
    try:
      types_answer = dns.resolver.query('_services._dns-sd._udp.%s' % self.zone,
                                        'PTR')
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN) as e:
      return 0 # No services announced: no clearing.
    except dns.exception.DNSException as e:
      return NS_QUERYING_ERROR

    # 2. Deleting [1]
    update.delete('_services._dns-sd._udp', 'PTR')

    # 3. For each type, getting the different instances.
    for service_type in types_answer:
      s = str(service_type.target) 
      stype = s.split('.%s' % self.zone, 1)[0] # getting '_http._tcp'

      try:
        instances_answer = dns.resolver.query('%s.%s'%(stype,self.zone), 'PTR')
      except dns.exception.DNSException as e:
        continue

      # 4. Deleting [2]
      update.delete(stype, 'PTR') 

      # 5. For each instance, getting the hostnames.
      for instance in instances_answer:
        s = str(instance.target)
        name = s.split('.%s' % self.zone, 1)[0] # getting 'name._http._tcp'
        
        try:
          host_answer = dns.resolver.query('%s.%s'%(name, self.zone), 'SRV')
        except dns.exception.DNSException as e:
          continue

        # 6. Deleting [3] and [4]
        update.delete(name, 'SRV')
        update.delete(name, 'TXT')

        # 7. Deleting A and AAAA of each host.
        for host in host_answer:
          s = str(host.target)
          hostname = s.split('.%s' % self.zone, 1)[0] # getting 'hostname'
          update.delete(hostname, 'AAAA')
          update.delete(hostname, 'A')

    # 8.
    update.delete('db._dns-sd._udp', 'PTR')
    update.delete('b._dns-sd._udp', 'PTR')

    response = None

    try:
      # Use IPv6 if possible. If no IPv6 address, use IPv4.
      if (server_addresses[0] != None):
        response = dns.query.tcp(update, server_addresses[0])
      else:
        response = dns.query.tcp(update, server_addresses[1])
    except (dns.tsig.PeerBadKey,
            dns.tsig.PeerBadSignature,
            dns.exception.DNSException) as e: 
      return NS_QUERYING_ERROR
    except (socket.error):
      # Socket error may occur if the host does not support IPv[46] and we try
      # to connect to IPv[46] address of the name server. We thus try the other
      # IP version address. This can be done by first trying IPv4.
      try:
        if (server_addresses[1] != None):
          response = dns.query.tcp(update, server_addresses[1])
        else:
          response = dns.query.tcp(update, server_addresses[0])
      except (dns.tsig.PeerBadKey,
              dns.tsig.PeerBadSignature,
              dns.exception.DNSException) as e: 
        return NS_QUERYING_ERROR
      except (socket.error):
        return SOCKET_ERROR

    return response.rcode()
