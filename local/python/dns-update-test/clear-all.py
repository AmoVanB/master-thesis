#!/usr/bin/python
import sys
import dns.resolver
import dns.query
import dns.update
import dns.exception
import dns.tsigkeyring

# version: http://www.dnspython.org/kits/1.12.0/

server = 'ks.vyncke.org'
key_name = 'amoupdate.'
key_value = 'BK1wQkLhDySTEMhLDeDSdg=='
zone = 'amo.vyncke.org'
algorithm = 'HMAC_MD5'

def clearall(server, key_name, key_value, zone, algorithm):
  """
    Peut generer desq exceptions
  """
  # Getting name server's IP address (IPv6 first, IPv4 if none).
  server_address = None 
  try:
    answers_IPv6 = dns.resolver.query(server, 'AAAA')

    for rdata in answers_IPv6:
      server_address = rdata.address
      break

    if (server_address == None):
      answers_IPv4 = dns.resolver.query(sever, 'A')
      for rdata in answers_IPv4:
        server_address = rdata.address
        break

  except dns.resolver.NXDOMAIN as e:
    print("The query name does not exist.")
    return
  except dns.resolver.NoAnswer as e:
    print("The response did not contain an answer.")
    return
  except dns.resolver.NoNameservers as e:
    print("No non-broken nameservers are available to answer the question.")
    return
  except dns.exception.Timeout as e:
    print("No answers could be found in the specified lifetime: %s.")
    return
  except dns.exception.DNSException as e:
    print("unexpected error (%s)", e.message)
    return

  if (server_address == None):
    print("Impossible to get IP address of the name server.")

  # Creating the Update object
  key = dns.tsigkeyring.from_text({key_name: key_value})
  if (algorithm == 'HMAC_MD5'):
    kalg = dns.tsig.HMAC_MD5
  elif (algorithm == 'HMAC_SHA1'):
    kalg = dns.tsig.HMAC_SHA1
  elif (algorithm == 'HMAC_SHA224'):
    kalg = dns.tsig.HMAC_SHA224
  elif (algorithm == 'HMAC_SHA256'):
    kalg = dns.tsig.HMAC_SHA256
  elif (algorithm == 'HMAC_SHA384'):
    kalg = dns.tsig.HMAC_SHA384
  elif (algorithm == 'HMAC_SHA512'):
    kalg = dns.tsig.HMAC_SHA512
  else:
    print ("Key algorithm unsupported.")
    return

  update = dns.update.Update(zone, keyring=key, keyalgorithm=kalg)

  # We need to clear all the announced services.
  # Each services his announced thanks to 5 RRs:
  # 
  # PTR  _services._dns-sd._udp.<domain> -> <stype>.<domain>             [1]
  # PTR  <stype>.<domain>                -> <instance>.<stype>.<domain>  [2]
  # SRV  <instance>.<stype>.<domain>     -> SRV (<hostname>.<domain)     [3]
  # TXT  <instance>.<stype>.<domain>     -> TXT                          [4]
  # AAAA <hostname>.<domain>             -> IPv6 addr                    [5]
  # A    <hostname>.<domain>             -> IPv4 addr                    [6]
  #
  # A service running on IPv6 will announce 5 while 4 if running on IPv4.
  #
  # To clear all these RRs, we proceed as follows:
  # 1. [1] allows us to retrieve all announced types ([2]).
  # 2. We can now delete [1].
  # 3. From the different announced types ([2]), we retrieve the different
  #    instances of those types ([3] and [4]).
  # 4. We can now delete all [2].
  # 5. From all [3], we retrieve the different hostnames ([5] or [6])
  # 6. We can now delete all [3] and [4].
  # 7. We can now delete all [5] or [6].

  # 1. Getting all types that have been announced.


  try:
    types_answer = dns.resolver.query('_services._dns-sd._udp.%s' % zone, 'PTR')
  except dns.resolver.NoAnswer as e:
    return

  # 2. Deleting [1]
  update.delete('_services._dns-sd._udp.%s' % zone, 'PTR')

  # 3. For each type, getting the different instances.
  for service_type in types_answer:
    s = str(service_type.target) 
    stype = s.split('.%s' % zone, 1)[0] # getting '_http._tcp'

    try:
      instances_answer = dns.resolver.query('%s.%s' % (stype, zone), 'PTR')
    except dns.resolver.NoAnswer as e:
      continue

    # 4. Deleting [2]
    update.delete(stype, 'PTR') 

    # 5. For each instance, getting the hostnames.
    for instance in instances_answer:
      s = str(instance.target)
      name = s.split('.%s' % zone, 1)[0] # getting 'name._http._tcp'
      
      try:
        host_answer = dns.resolver.query('%s.%s' % (name, zone), 'SRV')
      except dns.resolver.NoAnswer as e:
        continue  

      # 6. Deleting [3] and [4]
      update.delete(name, 'SRV')
      update.delete(name, 'TXT')

      # 7. Deleting A and AAAA of each host.
      for host in host_answer:
        s = str(host.target)
        hostname = s.split('.%s' % zone, 1)[0] # getting 'hostname'
        update.delete(hostname, 'AAAA')
        update.delete(hostname, 'A')

  response = None

  try:
    response = dns.query.tcp(update, server_address)
  except dns.tsig.PeerBadKey:
    print("the peer didn't know the key we used (invalid algo or invalid name)")
    return
  except dns.tsig.PeerBadSignature:
    print("the peer didn't like the signature we sent (invalid key val)")
    return

  rcode = response.rcode()
  if (rcode == 0): # NOERROR
    print ("Success.")
  elif (rcode == 1): #FORMERR
    print ("The name server was unable to interpret the request due to a format error.")
  elif (rcode == 2): #SERVFAIL
    print ("The name server encountered an internal failure while processing this request.")
  elif (rcode == 3): #NXDOMAIN
    print ("Some name that ought to exist, does not exist.")
  elif (rcode == 4): #NOTIMP
    print ("The name server does not support the specified opcode (UPDATE).")
  elif (rcode == 5): #REFUSE
    print ("The name server refuses to perform the specified operation for policy or security reasons.")
  elif (rcode == 6): #YXDOMAIN
    print ("Some name that ought not to exist, does exist.")
  elif (rcode == 7): #YXRRSET
    print ("Some RRset that ought not to exist, does exist.")
  elif (rcode == 8): #NXRRSET
    print ("Some RRset that ought to exist, does not exist.")
  elif (rcode == 9): #NOTAUTH
    print ("The server is not authoritative for the zone.")
  elif (rcode == 10): #NOTZONE
    print ("A name used in the Prerequisite or Update Section is not within the zone.")

  return

clearall(server, key_name, key_value, zone, algorithm)

