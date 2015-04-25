#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
/global/python/policy-manager-daemon.py
 
Part of master's thesis "Using Service Discovery to Apply Policies in Networks"
at University of Liège 2014-2015.
Amaury Van Bemten.

Entreprise: Cisco
Contact entreprise: Eric Vyncke
Advisor: Guy Leduc
"""

import sys
import signal
import logging
import os
import pwd, grp

if (os.getuid() != 0):
  print("Daemon command must be issued as root.")
  sys.exit(1)

logger = logging.getLogger("policy-manager")
logger.setLevel(logging.DEBUG)    
formatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s",
                              datefmt='%d-%m-%Y %H:%M:%S %Z')
logfile = "/var/log/policy-manager.log"
handler = logging.FileHandler(logfile, encoding = 'utf-8')
handler.setFormatter(formatter)
logger.addHandler(handler)

try:
  from PolicyManager import PolicyManager

  from daemon import runner
  import lockfile
  from lxml import etree # for XML parsing
except ImportError as e:
  logger.error("Sorry, to use this tool you need to install python-daemon, " +
               "python-dns, netaddr and lxml.")
  logger.error("%s" % e)
  sys.exit(1)

class PolicyManagerDaemon():
  """Daemon running the PolicyManager class to generate firewall rules for
  routers involved in the system.
  """

  def __init__(self, logger, pidpath, domain, rate):
    self.stdin_path = '/dev/null'
    self.stdout_path = '/dev/stdout'
    self.stderr_path = '/dev/stderr'
    self.pidfile_path =  pidpath
    self.pidfile_timeout = 5
    self.pm = None       
    self.logger = logger 
    self.domain = domain  
    self.rate   = rate

  def run(self):
    """Starts the daemon.
    """
    self.pm = PolicyManager(self.logger, self.domain, self.rate)
    self.logger.info("Policy manager daemon startup.")
    self.pm.start()

    self.logger.info("Daemon stopped.")

  def stop(self):
    """Stops the daemon.
    """
    self.logger.info("Policy manager daemon shutdown.")
    self.pm.stop()


if __name__ == '__main__':
  if ((len(sys.argv) < 2) or (not sys.argv[1] in ['start', 'stop', 'restart'])):
    logger.error("Bad usage. Usage: %s start|stop|restart" % sys.argv[0])
    sys.exit(2)

  try:
    dtd = etree.DTD("/etc/policy-manager/config.dtd")
    xml = etree.parse("/etc/policy-manager/config.xml")
    if (not dtd.validate(xml)):
      raise etree.LxmlError("Configuration file is not a valid instance of " +
                            "DTD.")

    level   = xml.find("./log").get("level")
    domain  = xml.find("./domain").get("name")
    rate    = xml.find("./update").get("rate")
  except etree.LxmlError as e:
    logger.error("Error while parsing configuration file: %s" % e)
    logger.error("Daemon not started.")
    sys.exit(1)

  if (level.lower() == 'debug'):
    logger.setLevel(logging.DEBUG)    
  elif (level.lower() == 'info'):
    logger.setLevel(logging.INFO)    
  elif (level.lower() == 'warning'):
    logger.setLevel(logging.WARNING)    
  elif (level.lower() == 'error'):
    logger.setLevel(logging.ERROR)    

  if not os.path.exists('/var/run/policy-manager/'):
    os.makedirs('/var/run/policy-manager/')

  try:
    uid = pwd.getpwnam("pm-daemon").pw_uid
    gid = grp.getgrnam("pm").gr_gid
  except KeyError:
    logger.error("Daemon has not been correctly set up. Run setup.sh.")
    sys.exit(1)

  os.chown('/var/run/policy-manager/', uid, gid)
  os.chmod('/var/run/policy-manager/', 0755)

  app = PolicyManagerDaemon(logger, "/var/run/policy-manager/pid", domain, rate)
  daemon_runner = runner.DaemonRunner(app)
  daemon_runner.daemon_context.files_preserve=[handler.stream]
  daemon_runner.daemon_context.uid = uid
  daemon_runner.daemon_context.gid = gid
  daemon_runner.daemon_context.umask = 022
  daemon_runner.daemon_context.signal_map = \
                            {signal.SIGTERM:lambda signum, frame: app.stop(),
                             signal.SIGINT: lambda signum, frame: app.stop(),
                             signal.SIGABRT:lambda signum, frame: app.stop(),
                             signal.SIGQUIT:lambda signum, frame: app.stop(),
                             signal.SIGHUP: lambda signum, frame: app.stop()}

  logger.info("Command %s issued." % sys.argv[1])

  try:
    daemon_runner.do_action()
  except runner.DaemonRunnerStopFailureError:
    logger.error("Error stopping the daemon. Is it running?")
    sys.exit(1)
  except runner.DaemonRunnerStartFailureError:
    logger.error("Error starting the daemon. Is it already running?")
    sys.exit(1)
  except lockfile.LockTimeout as e:
    logger.error("Daemon seems to be already running. %s" % e)
    sys.exit(1)
  except lockfile.AlreadyLocked as e:
    logger.error("Daemon seems to be already running. %s" % e)
    sys.exit(1)
  except lockfile.LockFailed as e:
    logger.error("Problem occured locking PID file. %s" % e)
    sys.exit(1)
  except lockfile.UnlockError as e:
    logger.error("Error while unlocking PID file lock. Was it locked? " +
                 "Is it yours? %s" % e)
    sys.exit(1)
  except Exception as e:
    logger.error("Unexpected error. %s" % e)
    logger.error("Daemon stopped.")
    sys.exit(1)
