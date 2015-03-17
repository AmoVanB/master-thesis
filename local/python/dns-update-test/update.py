#!/usr/bin/python
import sys
import dns.resolver
import dns.query
import dns.update
import dns.exception
import dns.tsigkeyring

# version: http://www.dnspython.org/kits/1.12.0/

try:
answers_IPv6 = dns.resolver.query('ks.vyncke.org', 'AAAA')
nsserver_address = None 

for rdata in answers_IPv6:
  nsserver_address = rdata.address
  break

if (nsserver_address == None):
  answers_IPv4 = dns.resolver.query('ks.vyncke.org', 'A')
  for rdata in answers_IPv4:
    nsserver_address = rdata.address
    break
except dns.resolver.NXDOMAIN as e:
  print("The query name does not exist.")
  sys.exit(0)
except dns.resolver.YXDOMAIN as e:
  print("The query name is too long after DNAME substitution.")
  sys.exit(0)
except dns.resolver.NoAnswer as e:
  print("The response did not contain an answer.")
  sys.exit(0)
except dns.resolver.NoNameservers as e:
  print("No non-broken nameservers are available to answer the question.")
  sys.exit(0)
except dns.exception.Timeout as e:
  print("No answers could be found in the specified lifetime: %s.")
  sys.exit(0)
except dns.exception.DNSException as e:
  print("unexpected error (%s)", e.message)
  sys.exit(0)

key = dns.tsigkeyring.from_text({'amoupdate.': 'BK1wQkLhDySTEMhLDeDSdg=='})
update = dns.update.Update("amo.vyncke.org", keyring=key, keyalgorithm=dns.tsig.HMAC_MD5)

# After name:
# arg1: TTL
# arg2: rdtype
# arg3: string containing description
#       A(AAA): IP address
#       PTR: link
#       SRV: priority, weight, port, hostname
#       TXT  string of values separated by spaces
update.add('b._dns-sd._udp',                 5, 'PTR',  'amo.vyncke.org.')
update.add('db._dns-sd._udp',                5, 'PTR',  'amo.vyncke.org.')
update.add('_services._dns-sd._udp',         5, 'PTR', '_http._tcp')
update.add('_http._tcp',                     5, 'PTR', 'WebServer._http._tcp')
update.add('WebServer._http._tcp', 5, 'SRV', '0 0 80 amo-laptop')
update.add('WebServer._http._tcp', 5, 'TXT', 'path=/thesis')
update.add('amo-laptop',                     5, 'AAAA', '2001:6a8:2d80:2460::babe')
update.add('amo-laptop',                     5, 'A', '10.12.11.9')


update.delete('b._dns-sd._udp',         'PTR',  'amo.vyncke.org.')
update.delete('db._dns-sd._udp',         'PTR',  'amo.vyncke.org.')
update.delete('_services._dns-sd._udp', 'PTR', '_http._tcp')
update.delete('_http._tcp',             'PTR', 'WebServer._http._tcp')
update.delete('WebServer._http._tcp', 'SRV', '0 0 80 amo-laptop')
update.delete('WebServer._http._tcp', 'TXT', 'path=/thesis')
update.delete('amo-laptop',             'AAAA', '2001:6a8:2d80:2460::babe')
update.delete('amo-laptop',                     'A', '10.12.11.9')

update.delete('b._dns-sd._udp',                                 'PTR',  'kot.amo.vyncke.org.')
update.delete('_services._dns-sd._udp.kot.amo.vyncke.org.',     'PTR',  '_ipp._tcp.kot.amo.vyncke.org.')
update.delete('_ipp._tcp.kot.amo.vyncke.org.',                  'PTR',  'Imprimante\ \(Kot\)._ipp._tcp.kot.amo.vyncke.org.')
update.delete('Imprimante (Kot)._ipp._tcp.kot.amo.vyncke.org.', 'SRV',  '0 0 80 amo-laptop-12.kot.amo.vyncke.org.')
update.delete('Imprimante (Kot)._ipp._tcp.kot.amo.vyncke.org.', 'TXT',  'path=/thesis')
update.delete('amo-laptop-12.kot.amo.vyncke.org.',              'AAAA', '2001:6a8:2d80:2460::cafe')
update.delete('amo-laptop-12.kot.amo.vyncke.org.',              'A', '1.2.3.4')

update.add('b._dns-sd._udp',                                 5, 'PTR',  'kot.amo.vyncke.org.')
update.add('_services._dns-sd._udp.kot.amo.vyncke.org.',     5, 'PTR',  '_ipp._tcp.kot.amo.vyncke.org.')
update.add('_ipp._tcp.kot.amo.vyncke.org.',                  5, 'PTR',  'Imprimante\ \(Kot\)._ipp._tcp.kot.amo.vyncke.org.')
update.add('Imprimante (Kot)._ipp._tcp.kot.amo.vyncke.org.', 5, 'SRV',  '0 0 80 amo-laptop-12.kot.amo.vyncke.org.')
update.add('Imprimante (Kot)._ipp._tcp.kot.amo.vyncke.org.', 5, 'TXT',  'path=/thesis')
update.add('amo-laptop-12.kot.amo.vyncke.org.',              5, 'AAAA', '2001:6a8:2d80:2460::cafe')
update.add('amo-laptop-12.kot.amo.vyncke.org.',              5, 'A', '1.2.3.4')

update.delete('b._dns-sd._udp',                                 'PTR',  'kot.amo.vyncke.org.')
update.delete('_services._dns-sd._udp.kot.amo.vyncke.org.',     'PTR',  '_ipp._tcp.kot.amo.vyncke.org.')
update.delete('_ipp._tcp.kot.amo.vyncke.org.',                  'PTR',  'Imprimante\ \(Kot\)._ipp._tcp.kot.amo.vyncke.org.')
update.delete('Imprimante (Kot)._ipp._tcp.kot.amo.vyncke.org.', 'SRV',  '0 0 80 amo-laptop-12.kot.amo.vyncke.org.')
update.delete('Imprimante (Kot)._ipp._tcp.kot.amo.vyncke.org.', 'TXT',  'path=/thesis')
update.delete('amo-laptop-12.kot.amo.vyncke.org.',              'AAAA', '2001:6a8:2d80:2460::cafe')
update.delete('amo-laptop-12.kot.amo.vyncke.org.',              'A', '1.2.3.4')

update.delete('b._dns-sd._udp',                                  'PTR',  'home.amo.vyncke.org.')
update.delete('_services._dns-sd._udp.home.amo.vyncke.org.',     'PTR',  '_ipp._tcp.kot.amo.vyncke.org.')
update.delete('_ipp._tcp.home.amo.vyncke.org.',                  'PTR',  'Imprimante\ \(Home\)._ipp._tcp.home.amo.vyncke.org.')
update.delete('Imprimante (Home)._ipp._tcp.home.amo.vyncke.org.','SRV',  '0 0 80 amo-laptop-12.home.amo.vyncke.org.')
update.delete('Imprimante (Home)._ipp._tcp.home.amo.vyncke.org.','TXT',  'path=/thesis')
update.delete('amo-laptop-12.home.amo.vyncke.org.',              'AAAA', '2001:6a8:2d80:2460::cafe')
update.delete('amo-laptop-12.home.amo.vyncke.org.',              'A', '1.2.3.4')

update.add('b._dns-sd._udp',                                   5, 'PTR',  'home.amo.vyncke.org.')
update.add('_services._dns-sd._udp.home.amo.vyncke.org.',      5, 'PTR',  '_ipp._tcp.kot.amo.vyncke.org.')
update.add('_ipp._tcp.home.amo.vyncke.org.',                   5, 'PTR',  'Imprimante\ \(Home\)._ipp._tcp.home.amo.vyncke.org.')
update.add('Imprimante (Home)._ipp._tcp.home.amo.vyncke.org.', 5, 'SRV',  '0 0 80 amo-laptop-12.home.amo.vyncke.org.')
update.add('Imprimante (Home)._ipp._tcp.home.amo.vyncke.org.', 5, 'TXT',  'path=/thesis')
update.add('amo-laptop-12.home.amo.vyncke.org.',               5, 'AAAA', '2001:6a8:2d80:2460::cafe')
update.add('amo-laptop-12.home.amo.vyncke.org.',               5, 'A', '1.2.3.4')


update.delete('Drucker._ipp._tcp.dell','TXT')

update.delete('b._dns-sd._udp',                                  'PTR',  'home.amo.vyncke.org.')
update.delete('_services._dns-sd._udp.home.amo.vyncke.org.',     'PTR',  '_ipp._tcp.kot.amo.vyncke.org.')
update.delete('_ipp._tcp.home.amo.vyncke.org.',                  'PTR',  'Imprimante\ \(Home\)._ipp._tcp.home.amo.vyncke.org.')
update.delete('Imprimante (Home)._ipp._tcp.home.amo.vyncke.org.','SRV',  '0 0 80 amo-laptop-12.home.amo.vyncke.org.')
update.delete('Imprimante (Home)._ipp._tcp.home.amo.vyncke.org.','TXT',  'path=/thesis')
update.delete('amo-laptop-12.home.amo.vyncke.org.',              'AAAA', '2001:6a8:2d80:2460::cafe')
update.delete('amo-laptop-12.home.amo.vyncke.org.',              'A', '1.2.3.4')


response = None

try:
  response = dns.query.tcp(update, nsserver_address)
except dns.tsig.PeerBadKey:
  print("the peer didn't know the key we used (invalid algo or invalid name)")
  sys.exit(0)
except dns.tsig.PeerBadSignature:
  print("the peer didn't like the signature we sent (invalid key val)")
  sys.exit(0)

rcode = response.rcode()
# FROM RFC2136:
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

