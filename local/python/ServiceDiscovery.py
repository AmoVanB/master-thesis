#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
/python/ServiceDiscovery.py

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

import netaddr                 # for manipulation of IP addresses
from lxml import etree         # to parse .xml and .dtd files

import avahi                   # for constants and TXT manipulation methods
import dbus                    # to communicate with the Avahi server via DBus
from dbus import DBusException
import dbus.mainloop.glib      # for setting up an event loop
import gobject                 # for setting up an event loop

import Miscellaneous           # various methods
import DNSWrapper              # to communicate with a DNS name server
import MySQLWrapper            # to communicate with a MySQL database

class ConfigError(Exception):
  """Exception raised when encountering an error in the configuration file."""
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return repr(self.value)


class AvahiError(Exception):
  """Exception raised when encountering an error while communicating with the
     avahi daemon."""
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return repr(self.value)


class ServiceDiscovery:
  """Class allowing to observe services on the local network and publish them
  on a given DNS zone.

  To start the process, simply call the start() method.
  """

  def __init__(self, logger):
    """Constructor.

    Checks the config.xml file versus its DTD config.dtd. Both files are
    supposed to be saved in /etc/service-discovery/ with read-access.
  
    Gets the database, domain and filtering parameters from config.xml.

    Note that the validity of database>port, domain>algorithm and domain>ttl 
    attributes are verified. The service>action field is also verified.    

    Args:
      logger: Logger object used for logging of various messages.

    Exceptions:
      ConfigError: Raised if a problem occurred in the processing of the
                   configuration file.
      AvahiError:  Raised if a problem occurred connecting to Avahi.
    """

    ## The logger used to log messages.
    self.logger = logger

    # Checking configuration file versus DTD.
    try:
      dtd = etree.DTD("/etc/service-discovery/config.dtd")
      xml = etree.parse("/etc/service-discovery/config.xml")
      if (not dtd.validate(xml)):
        raise ConfigError("Configuration file is not a valid instance of DTD.")
    except etree.LxmlError as e:
      raise ConfigError("Error while parsing config.xml and/or config.dtd: %s" %
                        e)

    # Since we performed the DTD validation, we are sure the requested tags
    # will exist. Note that this is only valid if the config.dtd file is not 
    # corrupted, of course.

    # Getting name and alias.
    config = xml.getroot()

    ## Name of the router added to the hostnames.
    self.name  = config.get("name")

    # We ensure the name is only composed of lower-case letters and numbers.
    if (not re.match("^[a-z0-9]+$", self.name)):
      raise ConfigError("Router name must contain only lower-case letters and "+
                        "numbers.")    
    
    ## Alias of the router added to the services names.
    self.alias = config.get("alias")


    # Getting database parameters.
    db = xml.find("./database")

    db_user   = db.get("user")
    db_pwd    = db.get("password")
    db_name   = db.get("name")
    db_socket = db.get("socket")
    db_host   = db.get("host")

    # Port will be saved as a string (to simplify the connection to the DB)
    # but we however check its value.
    port = int(db.get("port"))
    if (port < 1 or port > 65535):
      raise ConfigError("Database port number (%i) is not within the " +
                        "acceptable range [1-65535]." % port)      
    db_port = str(port)

    ## MySQLWrapper for fast SQL queries.
    self.db = MySQLWrapper.MySQLWrapper(db_user,
                                        db_pwd,
                                        db_name,
                                        db_host,
                                        db_socket,
                                        db_port)

    # Getting domain parameters.
    domain = xml.find("./domain")

    name_server = domain.get("server")
    zone        = domain.get("zone")
    keyname     = domain.get("keyname")
    keyvalue    = domain.get("keyvalue")
    algorithm   = domain.get("algorithm")
    if (algorithm.upper() == 'HMAC_MD5'):
      algorithm = "HMAC-MD5.SIG-ALG.REG.INT."
    elif (algorithm.upper() == 'HMAC_SHA1'):
      algorithm = "hmac-sha1."
    elif (algorithm.upper() == 'HMAC_SHA224'):
      algorithm = "hmac-sha224."
    elif (algorithm.upper() == 'HMAC_SHA256'):
      algorithm = "hmac-sha256."
    elif (algorithm.upper() == 'HMAC_SHA384'):
      algorithm = "hmac-sha384."
    elif (algorithm.upper() == 'HMAC_SHA512'):
      algorithm = "hmac-sha512."
    else:
      raise ConfigError("Specified TSIG signature algorithm is not within the "+
                        "supported set.")

    # Restricting TTL to min and max values (RFC2181).
    ## TTL value to set to the services/records published on the public DNS.
    self.ttl = int(domain.get("ttl"))
    if (self.ttl < 0):
      self.logger.warning("TTL not in [0-2^31-1]. Changed from %i to 0.",
                          self.ttl)
      self.ttl = 0
    if (self.ttl > 2147483647):
      self.logger.warning("TTL not in [0-2^31-1]. Changed from %i to " +
                          "2147483647.", self.ttl)
      self.ttl = 2147483647

    ## DNSWrapper for fast DNS Update messages.
    self.dns = DNSWrapper.DNSWrapper(name_server,
                                     keyname,
                                     keyvalue,
                                     zone,
                                     algorithm)

    ## List of filtering rules.
    self.rules = []
    rules_tag = xml.find("./rules")
    if (rules_tag == None):
      pass # Rules are not mandatory.
    else:
      for el in rules_tag:
        action = el.text.strip() # Remove leading/trailing blanks.
        if (action.lower() != "allow" and action.lower() != "deny"):
          self.logger.warning("Action '%s' is neither 'allow' nor 'deny'. " +
                              "Rule ignored.", action)
          continue

        d = dict(el.items())
        d["action"] = action.lower()
        self.rules.append(d)

    if (len(self.rules) == 0):
      self.logger.warning("No rules found. No services will be published.")

    # Getting the renaming preferences.
    ## IP renaming strings.
    self.ip_aliases = dict()

    r_ip = xml.findall("./ip")
    for r_ip_elem in r_ip:
      v     = r_ip_elem.get("version")
      alias = r_ip_elem.get("alias")

      if (v == "4"):
        self.ip_aliases[4] = alias
      elif (v == "6"):
        self.ip_aliases[6] = alias
      else:
        self.logger.warning("Trying to rename unknown IP version. Ingored.")

    ## Interfaces renaming strings.
    self.ifc_aliases = dict()

    r_ifc = xml.findall("./interface")
    for r_ifc_elem in r_ifc:
      ifc   = r_ifc_elem.get("name")
      alias = r_ifc_elem.get("alias")
  
      self.ifc_aliases[ifc] = alias

    ## Dictionary of the DBus Interfaces to service browsers.
    # Key: interface - protocol - stype
    self.service_browsers = {}

    ## Dictionary of the DBus Interfaces to record browsers.
    # Key: interface - protocol - hostname
    self.record_browsers = {}

    ## Dictionary of the DBus Interfaces to services resolvers.
    # Key: interface - protocol - name - stype
    self.service_resolvers = {}

    ## The DBus Interface to the browser for service types.
    self.service_type_browser = None


    # Setting up the event loop.
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    try:
      ## The system communication bus.
      self.bus = dbus.SystemBus()

      # Proxy to the avahi server.
      proxy = self.bus.get_object(bus_name = avahi.DBUS_NAME,
                             object_path = avahi.DBUS_PATH_SERVER)

      ## Interface to the Avahi server object.
      self.server = dbus.Interface(proxy,
                                   dbus_interface = avahi.DBUS_INTERFACE_SERVER)
    except Exception as e:
      raise AvahiError("Failed to connect to the Avahi server: %s." % e)

    ## The running loop.
    self.running_loop = gobject.MainLoop()


  def start(self):
    """Starts the process.

    Clears the DNS and SQL databases before starting to browse by entering a 
    loop. This loop can be stopped by calling the quit() method of the
    running_loop attribute. When the loop is quitted, the methods clears again
    the DNS and SQL databases before returning.
    """

    # Clear database and DNS in order to be sure to start the software in a
    # valid state.
    self.clear()

    self.browse()
    self.running_loop.run()
    self.logger.info("Loop quitted.")

    self.clear()

    # So that non terminated handlers do not perform any other actions on the
    # SQL and DNS databases.
    self.dns = None
    self.db  = None

    self.logger.info("Service discovery stopped.")

  def clear(self):
    """Clears the DNS and MySQL databases referenced by the dns & db attributes.
    """

    # Clear DB.
    ans = self.db.command(["DELETE FROM services;",
                           "DELETE FROM addresses;"])
    if (ans != 0):
      self.logger.error("Impossible to clear database correctly " +
                        "(MySQL error: %i).", ans)
    else:
      self.logger.info("Database cleared.")

    # Clear DNS.
    ans = self.dns.clearDNSServices()
    if (ans != 0):
      self.logger.error("DNS zone not cleared properly: %s",
                        self.dns.errors[ans])
    else:
      self.logger.info("DNS zone cleared.")


  def stop(self, info = None, error = None):
    """Logs an eventual message and quits the main loop.

    Args:
      info:  Info message to log. None to not log.
      error: Error message to log. None to not log.
    """

    if (info != None):
      self.logger.info(info)

    if (error != None):
      self.logger.error(error)

    if (self.running_loop != None):
      self.running_loop.quit()
      self.running_loop = None


  def browse(self):
    """Browses for announced services TYPES on all interfaces.

    The interfaces are those that Avahi observes (Avahi can be configured to
    ignore some interfaces or some IP versions).

    newServiceType and removeServiceType are set as handlers.
    """

    # Nothing to do if we are already browsing.
    if self.service_type_browser != None:
      return

    self.logger.debug("Browsing for services types.")

    # Creation of the ServiceTypeBrowser DBus object.
    # avahi.IF_UNSPEC:    browse all interfaces,
    # avahi.PROTO_UNSPEC: browse both IPv4 and IPv6,
    # 'local':            only browse the local domain,
    # dbus.Uint32(0):     no particular flags.
    try:
      path_to_browser = self.server.ServiceTypeBrowserNew(avahi.IF_UNSPEC,
                                                          avahi.PROTO_UNSPEC,
                                                          "local",
                                                          dbus.UInt32(0))
      proxy = self.bus.get_object(bus_name = avahi.DBUS_NAME,
                                  object_path = path_to_browser)
      ifc = dbus.Interface(proxy, avahi.DBUS_INTERFACE_SERVICE_TYPE_BROWSER)
    except DBusException as e:
      self.stop(error = "Error with the Avahi daemon. Is it still running? " +
                         "Error : %s." % e)
      return

    # Defining the callbacks methods in case of appearing or disappearing 
    # service type.
    ifc.connect_to_signal('ItemNew', self.newServiceType)
    #ifc.connect_to_signal('ItemRemove', self.removeServiceType)
    # Do nothing when a service of a given type disappears:
    # We will continue browsing this type.

    # Saving the interface to the browser.
    self.service_type_browser = ifc


  def newServiceType(self, interface, protocol, stype, domain, flags):
    """Browses for services of a given type on a given interface.

    newService and removeService are set as handlers.
    """

    # Nothing to do if already browsing this type.
    if self.service_browsers.has_key((interface, protocol, stype)):
      return

    self.logger.debug("Browsing type %s on %s." %
                      (stype, self.interface_desc(interface, protocol)))

    # Creation of the ServiceBrowser to browse for the services of the new
    # service type.
    try:
      path_to_browser = self.server.ServiceBrowserNew(interface,
                                                      protocol,
                                                      stype,
                                                      domain,
                                                      dbus.UInt32(0))
      proxy = self.bus.get_object(bus_name = avahi.DBUS_NAME,
                                  object_path = path_to_browser)
      ifc = dbus.Interface(proxy, avahi.DBUS_INTERFACE_SERVICE_BROWSER)
    except DBusException as e:
      self.logger.warning("Error when starting browsing type %s on %s: %s" % 
                          (stype, self.interface_desc(interface, protocol), e))
      return

    ifc.connect_to_signal('ItemNew', self.newService)
    ifc.connect_to_signal('ItemRemove', self.removeService)

    # Mentioning we are browsing the service of this stype.
    self.service_browsers[(interface, protocol, stype)] = ifc


  def newService(self, interface, protocol, name, stype, domain, flags):
    """Inserts the service in the SQL database (unresolved) and create a 
    ServiceResolver object to get the hostname, port and TXT of the service.

    serviceResolved is set as a handler.
    """

    # Nothing to do if we are already resolving this service.
    if self.service_resolvers.has_key((interface, protocol, name, stype)):
      return

    self.logger.debug("+ %s.%s on %s." %
                      (name, stype, self.interface_desc(interface, protocol)))

    # Insert in database.
    # Escaping and verifying values that will be part of the SQL query.
    name_    = Miscellaneous.escape(name)
    stype_   = Miscellaneous.escape(stype)
    if_name  = self.interface_name(interface)
    if_ip    = self.ip_version(protocol)

    ans = self.db.command(["INSERT INTO services " +
                           "VALUES ('%s', '%i', '%s', '%s', " %
                                   (if_name, if_ip, name_, stype_) +
                           "NULL, NULL, NULL, FALSE, FALSE);"])
    if (ans == 1062):
      # Duplicate entry. Should not occur, but it's not a problem.
      self.logger.warning("Duplicate service %s.%s on %s. Ignored." %
                          (name,stype,self.interface_desc(interface, protocol)))
    elif (ans != 0):
      self.stop(error = "Database insertion failed (MySQL error: %i). " % ans)
      return
    
    # Creation of the ServiceResolver object to resolve the service.
    try:
      # avahi.LOOKUP_NO_ADDRESS: we do not want the resolver to look for the
      #                          IP address. We'll do this by ourselves.
      path_to_resolver = self.server.ServiceResolverNew(interface,
                                                        protocol,
                                                        name,
                                                        stype,
                                                        domain,
                                                        avahi.PROTO_UNSPEC,
                                                        avahi.LOOKUP_NO_ADDRESS)
      proxy = self.bus.get_object(bus_name = avahi.DBUS_NAME,
                                  object_path = path_to_resolver)
      ifc = dbus.Interface(proxy, avahi.DBUS_INTERFACE_SERVICE_RESOLVER)
    except DBusException as e:
      self.logger.warning("Error when starting resolving %s.%s on %s: %s" % 
                          (name, stype,
                           self.interface_desc(interface, protocol), e))
      return

    ifc.connect_to_signal('Found', self.serviceResolved)

    # Mentioning we are resolving this service.
    self.service_resolvers[(interface, protocol, name, stype)] = ifc


  def removeService(self, interface, protocol, name, stype, domain, flags):
    """Removes the service from the SQL database. If it was announced, removes
    it from the DNS. 

    Addresses are managed so that we remove them only if not necessary anymore.
    Idem for the ServiceResolver and RecordBrowser objects: we free and remove
    them if they are not necessary anymore.
    """
    # Nothing to do if we are not resolving this service.
    if not self.service_resolvers.has_key((interface, protocol, name, stype)):
      return

    self.logger.debug("- %s.%s on %s." %
                      (name, stype, self.interface_desc(interface, protocol)))

    # Remove from database.
    # Escaping and verifying values that will be part of the SQL query.
    name_   = Miscellaneous.escape(name)
    stype_  = Miscellaneous.escape(stype)
    if_name = self.interface_name(interface)
    if_ip   = self.ip_version(protocol)
    
    # Getting the service's hostname and announced status before removal.
    response = self.db.query("SELECT hostname, announced FROM services " +
                             "WHERE name   ='%s' " % name_               +
                               "AND type   ='%s' " % stype_              +
                               "AND if_name='%s' " % if_name             +
                               "AND if_ip  ='%i';" % if_ip)
    if (response == None or len(response) == 0):
      self.stop(error = "Database failed.")
      return

    hostname = response[0]['hostname']
    announced = response[0]['announced']

    # Removal.    
    ans = self.db.command(["DELETE FROM services "                +
                           "WHERE name   ='%s' " % name_          +
                           "AND   type   ='%s' " % stype_         +
                           "AND   if_name='%s' " % if_name        +
                           "AND   if_ip  ='%i';" % if_ip])
    if (ans != 0):
      self.stop(error = "Database failed (MySQL error: %i)." % ans)
      return

    # Stop resolving the service.
    self.service_resolvers[(interface, protocol, name, stype)].Free()
    del self.service_resolvers[(interface, protocol, name, stype)]

    # Getting the number of
    # - services of the same type that are announced,
    # - services of the same hostname that are announced,
    # - services of the same hostname (announced or not).
    nb_type_announced_ans = self.db.query("SELECT COUNT(*) FROM services "  +
                                          "WHERE type='%s' " % stype_       +
                                          "AND   announced='1';")
    nb_host_announced_ans = self.db.query("SELECT COUNT(*) FROM services "  +
                                          "WHERE hostname='%s' " % hostname +
                                          "AND   announced='1';")
    nb_host_ans           = self.db.query("SELECT COUNT(*) FROM services "  +
                                          "WHERE hostname='%s';" % hostname)
    if (nb_type_announced_ans == None   or 
        nb_host_announced_ans == None   or
        nb_host_ans == None             or 
        len(nb_type_announced_ans) == 0 or
        len(nb_host_announced_ans) == 0 or
        len(nb_host_ans) == 0):
      self.stop(error = "Database failed.")
      return

    nb_host_announced = nb_host_announced_ans[0]['COUNT(*)']
    nb_type_announced = nb_type_announced_ans[0]['COUNT(*)']
    nb_host           = nb_host_ans[0]['COUNT(*)']
  
    # If the service was announced, we remove it from the DNS.
    if (announced):
      (name_, host_) = self.formatForDNS(name, hostname, if_name, if_ip)
      ans = self.dns.removeService(name_, stype.encode('utf-8'), host_, 
                                   # Remove type PTR if no more services of this
                                   # type that are announced.
                                   nb_type_announced == 0,
                                   # Remove host A/AAAA if no more services of
                                   # this host that are announced.
                                   nb_host_announced == 0)
      if (ans != 0):
        self.stop(error = "DNS Update failed. %s" % self.dns.errors[dns_ans])
        return
      
      self.logger.info("%s.%s removed from the DNS.", name_, stype)

    if (nb_host == 0 and hostname != None):
      # Stop browsing A/AAAA record for this hostname since he hosts no more 
      # services.
      self.record_browsers[(interface, protocol, unicode(hostname))][0].Free()
      self.record_browsers[(interface, protocol, unicode(hostname))][1].Free()
      del self.record_browsers[(interface, protocol, unicode(hostname))]

      # We do not need the addresses of the host anymore.
      ans = self.db.command(["DELETE FROM addresses WHERE hostname ='%s';" %
                             hostname])
      if (ans != 0):
        self.stop(error = "Database failed (MySQL error: %i)." % ans)
        return

      
  def serviceResolved(self, interface, protocol, name, stype, domain, host,
                            aprotocol, address, port, txt, flags):
    """Inserts the hostname, port and TXT in the database and browses for
    A(AAA) records for the hostname.

    A(AAA) records are not browsed if we already browse this hostname or if
    it is not a local host. This means that only hostnames ending in .local are
    considered. Indeed, it is useless to try to announce services which are
    already available publicly.
    """

    self.logger.debug("= Resolved %s.%s to %s on %s.", name, stype, host,
                      self.interface_desc(interface, protocol))

    hostname = host

    # Insertion in database.
    # Escaping and verifying values that will be part of the SQL query.
    host_    = Miscellaneous.escape(host)
    name_    = Miscellaneous.escape(name)
    stype_   = Miscellaneous.escape(stype)
    port     = int(port)
    txt_     = self.txt_to_byte_array_as_string(txt)
    if_name  = self.interface_name(interface)
    if_ip    = self.ip_version(protocol)
    resolved = 0 # Service considered resolved when we have an address for it.
    announced= 0

    # If we are already browsing for the hostname, maybe we already have an
    # address. We therefore look in the database.
    if self.record_browsers.has_key((interface, protocol, unicode(hostname))):
      ans = self.db.query("SELECT COUNT(*) FROM addresses WHERE hostname = " +
                          "'%s'" % host_ + " AND if_name = '%s'"  % if_name + 
                                           " AND if_ip =   '%i';" % if_ip) 
      if (ans == None or len(ans) == 0):
        self.stop(error = "Database failed.")
        return

      if (ans[0]['COUNT(*)'] >= 1):
        # We already have an address for the host.
        resolved = 1

        # We check if the service has to be announced or not.
        if (self.toAnnounce(name, stype, if_name, if_ip, host, port)):
          (name, host) = self.formatForDNS(name, host, if_name, if_ip)

          # decode/encode reason explained in formatForDNS comments.
          stype     = stype.decode('utf-8').encode('utf-8')
          ttl       = self.ttl
          dns_ans = self.dns.addService(name,
                                        stype,
                                        host,
                                        [], # addresses are already announced.
                                        port,
                                        avahi.txt_array_to_string_array(txt),
                                        ttl)
          if (dns_ans == DNSWrapper.LABEL_NAME_ERROR):
            # The new name is not anymore valid (length problem). We notify
            # the user but we do not abort.
            self.logger.error("Service " + name + "." + stype + " of " + host +
                              " presents a length problem. Service not"       +
                              " announced.")
            announced = 0
          elif (dns_ans != 0):
            self.stop(error = "DNS Update failed. %s"% self.dns.errors[dns_ans])
            return
          else:
            self.logger.info("%s.%s (%s) announced on DNS with existing " +
                             "address.", name, stype, host)
            announced = 1

    # Insertion.
    ans = self.db.command(["UPDATE services SET "          +
                           "hostname = '%s', " % host_     +
                           "port     = '%i', " % port      +
                           "TXT      = '%s', " % Miscellaneous.escape(txt_) +
                           "announced= '%i', " % announced +
                           "resolved = '%i'  " % resolved  +
                           "WHERE name   ='%s' " % name_   + 
                             "AND type   ='%s' " % stype_  +
                             "AND if_name='%s' " % if_name +
                             "AND if_ip  ='%i';" % if_ip])
    if (ans != 0):
      self.stop(error = "Database failed (MySQL error: %i)." % ans)
      return

    # If the host is not on the local LAN or if we already browse for it, we 
    # are done (no need to browse).
    if (not host.endswith(".local") or
        self.record_browsers.has_key((interface, protocol, unicode(hostname)))):
      return

    # Browse A/AAAA record.
    try:
      path_to_4_browser = self.server.RecordBrowserNew(interface,
                                                       protocol,
                                                       host,
                                                       1, # IN class
                                                       1, # A
                                                       dbus.UInt32(0))
      path_to_6_browser = self.server.RecordBrowserNew(interface,
                                                       protocol,
                                                       host,
                                                       1, # IN class
                                                       28, # AAAA
                                                       dbus.UInt32(0))

      proxy4 = self.bus.get_object(bus_name = avahi.DBUS_NAME,
                                   object_path = path_to_4_browser)
      proxy6 = self.bus.get_object(bus_name = avahi.DBUS_NAME,
                                   object_path = path_to_6_browser)
      ifc4 = dbus.Interface(proxy4, avahi.DBUS_INTERFACE_RECORD_BROWSER)
      ifc6 = dbus.Interface(proxy6, avahi.DBUS_INTERFACE_RECORD_BROWSER)
    except DBusException as e:
      self.logger.warning("Error when starting browsing A/AAAA records for %s "+
                          "on %s: %s" % 
                          (host, self.interface_desc(interface, protocol), e))
      return

    ifc4.connect_to_signal('ItemNew', self.newRecord)
    ifc6.connect_to_signal('ItemNew', self.newRecord)
    ifc4.connect_to_signal('ItemRemove', self.removeRecord)
    ifc6.connect_to_signal('ItemRemove', self.removeRecord)

    # Mentioning we are browsing the records for this host.
    self.record_browsers[(interface, protocol, unicode(hostname))] = (ifc4,ifc6)


  def newRecord(self, interface, protocol, name, clazz, type, rdata, flags):
    """If obtained address is global, inserts it in the database and sets all
    services of the hostname as resolved. If a service has to be announced,
    it is (along with the new address).
    """

    if (type == 1):
      serv_ip = 4
    elif (type == 28):
      serv_ip = 6
    else:
      return

    # Convert the byte represented address into a string.
    address = self.get_address_from_bytes(rdata, serv_ip)

    # Do nothing if the address is not global as it will be useless from outside
    # the subnet.
    if (netaddr.IPAddress(address).is_private()):
      return

    self.logger.debug("New IPv%i address (%s) for %s on %s.",
                      serv_ip, address, name,
                      self.interface_desc(interface, protocol))

    # Insertion in database.
    # Escaping and verifying values that will be part of the SQL query.
    name_    = Miscellaneous.escape(name)
    address_ = Miscellaneous.escape(address)
    if_name  = self.interface_name(interface)
    if_ip    = self.ip_version(protocol)

    # Insert the address and set the services of the hostname resolved.
    ans = self.db.command(["INSERT INTO addresses " +
                           "VALUES ('%s', '%i', '%s', '%i', '%s');" %
                                   (if_name, if_ip, name_, serv_ip, address_),

                           "UPDATE services SET " +
                                  "resolved='%i' " % 1       +  
                           "WHERE hostname ='%s' " % name_   + 
                             "AND if_name  ='%s' " % if_name +
                             "AND if_ip    ='%i';" % if_ip])
    if (ans == 1062):
      # Duplicate entry. Should not occur, but it's not a problem.
      self.logger.warning("Duplicate address %s for %s on %s. Ignored." %
                          (address_, name,
                           self.interface_desc(interface, protocol)))
    elif (ans != 0):
      self.stop(error = "Database failed (MySQL error: %i)." % ans)
      return

    # Selecting all the services of the hostname.
    ans = self.db.query("SELECT * FROM services WHERE " +
                        "hostname    ='%s' " % name_    + 
                        "AND if_name ='%s' " % if_name  +
                        "AND if_ip   ='%i';" % if_ip)
    if (ans == None):
      self.stop(error = "Database failed.")
      return

    # For each service, if it has to be, we announce it (as the service is now
    # resolved).
    for service in ans:
      if (self.toAnnounce(service['name'],
                          service['type'],
                          service['if_name'],
                          service['if_ip'],
                          service['hostname'],
                          service['port'])):
        (name, host) = self.formatForDNS(service['name'],
                                         service['hostname'],
                                         service['if_name'],
                                         service['if_ip'])
        # decode/encode reason explained in formatForDNS comments.
        stype     = service['type'].decode('utf-8').encode('utf-8')
        addresses = [(serv_ip, address.decode('utf-8').encode('utf-8'))]
        port      = int(service['port'])
        txt       = self.txt_to_string_array(service['TXT'])
        ttl       = self.ttl
        dns_ans = self.dns.addService(name,
                                      stype,
                                      host,
                                      addresses,
                                      port,
                                      txt,
                                      ttl)
        if (dns_ans == DNSWrapper.LABEL_NAME_ERROR):
          # The new name is not anymore valid (length problem). We notify
          # the user but we do not abort.
          # Note: decode to send the unicode string.
          self.logger.error("Service " + name.decode('utf-8') + "." + stype +
                            " of " + host + " presents a length problem. "  +
                            " Service not announced.")
          announced = 0
        elif (dns_ans != 0):
          self.stop(error = "DNS Update failed. %s" % self.dns.errors[dns_ans])
          return
        else:
          self.logger.info("%s.%s (%s) announced on DNS with address %s.",
                           name.decode('utf-8'), stype, host, address)
          announced = 1

        # Set the service announced. No need to escape since values come from
        # an SQL reply.
        sql_ans = self.db.command(["UPDATE services SET " +
                                   "announced='%i' "      % announced          +  
                                   "WHERE name    ='%s' " % service['name']    + 
                                    "AND  type    ='%s' " % service['type']    +
                                    "AND  if_name ='%s' " % service['if_name'] +
                                    "AND  if_ip   ='%i';" % service['if_ip']])
        if (sql_ans != 0):
          self.stop(error = "Database failed (MySQL error: %i)." % sql_ans)
          return  


  def removeRecord(self, interface, protocol, name, clazz, type, rdata, flags):
    """If address is global, removes it from the database and from the DNS
    if necessary. It removes also the associated services from the DNS if this
    was the last address of the hostname.
    """

    if (type == 1):
      serv_ip = 4
    elif (type == 28):
      serv_ip = 6
    else:
      return

    # Convert the byte represented address into a string.
    address = self.get_address_from_bytes(rdata, serv_ip)

    # Do nothing if the address is not global as it will be useless from outside
    # the subnet.
    if (netaddr.IPAddress(address).is_private()):
      return

    self.logger.debug("Remove IPv%i address (%s) of %s on %s.",
                      serv_ip, address, name,
                      self.interface_desc(interface, protocol))
    
    # Deletion from database.
    # Escaping and verifying values that will be part of the SQL query.
    name_   = Miscellaneous.escape(name)
    if_name = self.interface_name(interface)
    if_ip   = self.ip_version(protocol)

    ans = self.db.command(["DELETE FROM addresses " +
                           "WHERE if_name  ='%s' " % if_name +
                           "  AND if_ip    ='%i' " % if_ip   +
                           "  AND hostname ='%s' " % name_   +
                           "  AND ip       ='%i' " % serv_ip +
                           "  AND address  ='%s';" % address])
    if (ans != 0):
      self.stop(error = "Database failed (MySQL error: %i)." % ans)
      return

    # Removing address from the DNS if announced.
    ans = self.db.query("SELECT announced FROM services WHERE " +
                        "hostname    ='%s' " % name_    + 
                        "AND if_name ='%s' " % if_name  +
                        "AND if_ip   ='%i';" % if_ip)
    if (ans == None):
      self.stop(error = "Database failed.")
      return

    # If len(ans) == 0: The address removal has been handled by removeService.
    if len(ans) > 0 and ans[0]['announced']:
      (s, host) = self.formatForDNS("", name, if_name, if_ip)

      if (serv_ip == 4):
        ans = self.dns.removeRecord(host, 'A', address)
        if (ans != 0):
          self.stop(error = "DNS Update failed. %s" % self.dns.errors[ans])
          return
      elif (serv_ip == 6):
        ans = self.dns.removeRecord(host, 'AAAA', address)
        if (ans != 0):
          self.stop(error = "DNS Update failed. %s" % self.dns.errors[ans])
          return

      self.logger.info("IPv%i address (%s) of %s on %s removed from DNS.",
                        serv_ip, address, name,
                        self.interface_desc(interface, protocol))

    # Getting the number of remaining address for the hostname.
    nb_addr_host_ans = self.db.query("SELECT COUNT(*) FROM addresses " +
                                     "WHERE hostname ='%s' " % name_   +
                                       "AND if_name  ='%s' " % if_name +
                                       "AND if_ip    ='%s';" % if_ip)

    if (nb_addr_host_ans == None or len(nb_addr_host_ans) == 0):
      self.stop(error = "Database failed.")
      return

    nb_addr_host = nb_addr_host_ans[0]['COUNT(*)']
  
    # If the host has no more addresses: 
    # - Remove all its services from DNS.
    # - Set all its services not announced.
    # - Set all its services unresolved.
    if (nb_addr_host == 0):
      # Getting all the services of the host.
      ans = self.db.query("SELECT * FROM services WHERE " +
                          "hostname    ='%s' " % name_    + 
                          "AND if_name ='%s' " % if_name  +
                          "AND if_ip   ='%i';" % if_ip)
      if (ans == None):
        self.stop(error = "Database failed.")
        return

      # Removing from the DNS all services that are announced.
      for service in ans:
        if (service['announced']):
          response = self.db.command(["UPDATE services SET resolved ='0', "+
                                                          "announced='0'  "+
                                      "WHERE hostname ='%s' "% name_       + 
                                        "AND if_name  ='%s' "% if_name     +
                                        "AND if_ip    ='%i' "% if_ip       +
                                        "AND name     ='%s' "% service['name']+
                                        "AND type     ='%s';"% service['type']])
          if (response != 0):
            self.stop(error = "Database failed (MySQL error: %i)." % response)
            return
          
          # Looking if there are still services of this type.
          nb_type_ans = self.db.query("SELECT COUNT(*) FROM services "+
                                      "WHERE type      ='%s' "% service['type']+
                                        "AND announced ='1';")
          if (nb_type_ans == None or len(nb_type_ans) == 0):
            self.stop(error = "Database failed.")
            return

          # Remove the service.
          (name, host) = self.formatForDNS(service['name'],
                                           service['hostname'],
                                           service['if_name'],
                                           service['if_ip'])
          ans = self.dns.removeService(name,
                                       service['type'],
                                       host,
                                       nb_type_ans[0]['COUNT(*)'] == 0,
                                       True)
          if (ans != 0):
            self.stop(error = "DNS Update failed. %s" % self.dns.errors[ans])
            return

          self.logger.info("%s.%s removed from the DNS.", name, service['type'])


  def toAnnounce(self, name, stype, if_name, if_ip, hostname, port):
    """Looks up self.rules and tells whether or not the service has to be
    announced or not.

    Args:
      name:     name of the service.
      stype:    type of the service.
      if_name:  interface on which service is announced.
      if_ip:    protocol of the interface on which protocol is announced.
      hostname: name of the host hosting the service.
      port:     port on which the service runs.

    Returns: 
      true or false.
    """
    for element in self.rules:
      # continue (go to next rule) if something is not matched.
      try:
        if (not re.match(element["name"], name)):
          continue
        if (not re.match(element["type"], stype)):
          continue
        if (not re.match(element["interface-name"], if_name)):
          continue
        if (not re.match(element["interface-ip"], str(if_ip))):
          continue
        if (not re.match(element["hostname"], hostname)):
          continue
        if (not re.match(element["port"], str(port))):
          continue
      except re.error:
        self.stop(error = "Invalid regular expression.")
        return

      # If we reached here: rule is satisfied, we return the action value.
      if (element["action"] == "allow"):
        return True
      else:
        return False

    # If loops finishes without returning: no rule match -> deny
    return False


  def formatForDNS(self, sname, hostname, if_name, if_ip):
    """Formats the name and hostname of a service for DNS update purpose.

    Args:
      sname:    name of the service.
      hostname: name of the host (along with the .local).
      if_name:  name of the interface on which the service has announced itself.
      if_ip:    IP version of the interface on which the service has
                announced itself.

    Returns:
      tuple (sname, host) formatted.
    """

    # Decoding and encoding can seem silly but is not done on purpose.
    # The decode operations ensures to get the unicode string of the input
    # whatever the initial type (bytearray, string, unicode string).
    # The encode method then allows to get a string.
    sname    = sname.decode('utf-8').encode('utf-8')
    hostname = hostname.decode('utf-8').encode('utf-8')
    if_name  = if_name.decode('utf-8').encode('utf-8')

    if (self.ifc_aliases.has_key(str(if_name))):
      append_ifc = self.ifc_aliases[str(if_name)]
    else:
      append_ifc = " @ " + str(if_name)

    if (self.ip_aliases.has_key(int(if_ip))):
      append_ip = self.ip_aliases[int(if_ip)]
    else:
      append_ip = " (IPv" + str(if_ip) + ")"

    # Note that we remove the 6 last characters of hostname (.local)
    name_ = sname         +     self.alias +     append_ifc   +      append_ip
    host_ = hostname[:-6] +"-"+ self.name  +"-"+ str(if_name) +"-v"+ str(if_ip)

    return (name_, host_)


  def ip_name(self, protocol):
    """Returns IP protocol name based on avahi ID.

    Args:
      protocol:   Avahi protocol indentifier.

    Returns:
      String 'IPv4', 'IPv6' or 'n/a'
    """
    if protocol == avahi.PROTO_INET:
      return "IPv4"
    if protocol == avahi.PROTO_INET6:
      return "IPv6"
    return "n/a"


  def ip_version(self, protocol):
    """Returns IP protocol number based on avahi ID.

    Args:
      protocol: Avahi protocol indentifier.

    Returns:
      Integer 4, 6 or -1.
    """
    if protocol == avahi.PROTO_INET:
      return 4
    if protocol == avahi.PROTO_INET6:
      return 6
    return -1


  def interface_name(self, interface):
    """Returns interface name based on index.

    Args:
      interface: index of interface.

    Returns:
      interface name or 'n/a'.
    """
    if interface <= 0:
      return "n/a"
    else:
      return self.server.GetNetworkInterfaceNameByIndex(interface)


  def interface_desc(self, interface, protocol):
    """Returns interface description string based on interface/protocol IDs.

    Args:
      interface: the interface ID.
      protocol:  the protocol ID.

    Returns:
      interface description: "name:ip" or "n/a"
    """
    if interface == avahi.IF_UNSPEC and protocol == avahi.PROTO_UNSPEC:
      return "n/a"
    else:
      return (self.interface_name(interface) + ":" +
              str(self.ip_version(protocol)))


  def txt_to_byte_array_as_string(self, txt):
    """From a avahi TXT value, returns its representation as described in
    section 6.6 of RFC6763. The byte array is returned as a string.

    Args:
      txt: Avahi TXT value.

    Returns:
      string holding the representation of the TXT as described in RFC6763.
    """

    result = ''
    strings = avahi.txt_array_to_string_array(txt)
    for elem in strings:
      result = result + chr(len(elem))
      result = result + elem
    return result


  def txt_to_string_array(self, val):
    """From a raw TXT value (as described in section 6.6 of RFC6763), returns
    an array of key/value pairs.

    Args:
      val: the raw TXT.

    Returns:
      array of key/value pairs.
    """

    array = []
    
    i = 0
    while i < len(val):
      if isinstance(val[i], int):
        l = val[i]
      else:
        l = ord(val[i])

      array.append(str(val[i+1:i+1+l]))    
      i = i+1+l
    
    return array

  def get_address_from_bytes(self, bytes, ip_version):
    """From a bytearray, returns the usual IP address format of an
    IPv4/6 address.

    Args:
      bytes:      bytearray containing the raw representation of the address.
      ip_version: integer telling which type of address it is.

    Returns:
      a string holding the nice usual representation of IP addresses.
    """

    if (ip_version == 6):
      # If address is IPv6: the hexadecimal representation of the bytes give
      # the address in the desired format.
      address = ""
      addr = Miscellaneous.bytes_to_hex_string(bytes)
      # Insert a colon all four characters.
      parts = re.findall('....', addr) # divide string in 4 chars strings
      for elem in parts:
        address = address + elem + ':'
      address = address[:-1] # remove last colon
    else:
      # If address is IPv4: the bytes are simply the labels of the address.
      address = ""
      for elem in bytes:
        address = address + "%i" % elem + '.'
      address = address[:-1]

    return str(netaddr.IPAddress(address))
