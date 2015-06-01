#!/usr/bin/python2
# -*- coding: utf-8 -*-

"""
/centralized/python/policy-manager-daemon.py

Part of master thesis "Using Service Discovery to Apply Policies in Networks"
at University of Liège 2014-2015.
by Amaury Van Bemten.

Entreprise: Cisco
Contact entreprise: Eric Vyncke
Advisor: Guy Leduc
"""

import sys      # for sys.exit and sys.arg
import signal   # for signal handling
import logging  # for logging
import os       # for os.getuid and file system management
import pwd, grp # to get UID and GID of sd-daemon and sd

if (os.getuid() != 0):
  print("Daemon command must be issued as root.")
  sys.exit(1)

# Creating a logger to log events in policy-manager.log file.
# Done here in order to be able to log the ImportError herebelow.
logger = logging.getLogger("policy-manager")
logger.setLevel(logging.DEBUG)    
formatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s",
                              datefmt='%d-%m-%Y %H:%M:%S %Z')
logfile = "/var/log/policy-manager.log"
handler = logging.FileHandler(logfile)
handler.setFormatter(formatter)
logger.addHandler(handler)

try:
  from PolicyManager import PolicyManager

  from daemon import runner # daemon module
  import lockfile
  from lxml import etree    # for XML parsing
except ImportError as e:
  logger.error("Sorry, to use this tool you need to install python-daemon, " +
               "dnspython, netaddr and lxml.")
  logger.error("%s" % e)
  sys.exit(1)

class PolicyManagerDaemon():
  """Daemon using the PolicyManager class to generate firewall rules for
  routers involved in the system."""

  def __init__(self, logger, pidpath, domain, rate):
    # We redirect the ouputs to /dev/null so that nothing is printed.
    # All information should be forwarded to the .log file via the logger.
    self.stdin_path  = '/dev/null'
    self.stdout_path = '/dev/null'
    self.stderr_path = '/dev/null'

    self.logger = logger 
    self.domain = domain  
    self.rate   = rate

    self.pidfile_path =  pidpath
    self.pidfile_timeout = 5 # Timeout before considering PID file is locked.

    self.pm = None # PolicyManager instance used.

  def run(self):
    """Starts the daemon."""

    self.pm = PolicyManager(self.logger, self.domain, self.rate)
    self.logger.info("Policy manager daemon startup.")
    self.pm.start()

    # Once the start() method returns it means that the daemon is stopped.
    self.logger.info("Daemon stopped.")

  def stop(self):
    """Stops the daemon."""

    self.logger.info("Policy manager daemon shutdown.")
    self.pm.stop()

if __name__ == '__main__':
  # Those steps will be performed each time 'policy-manager-daemon.py' will
  # be called. This is, at start, stop, restart and even for possible other
  # (unvalid) commands. To avoid unnecessary work, we first check that the 
  # command is either start, stop or restart.
  # Note that we only consider the first argument, others are ignored.
  if ((len(sys.argv) < 2) or (not sys.argv[1] in ['start', 'stop', 'restart'])):
    logger.error("Bad usage. Usage: %s start|stop|restart" % sys.argv[0])
    sys.exit(2)

  # Reading configuration file.
  try:
    dtd = etree.DTD("/etc/policy-manager/config.dtd")
    xml = etree.parse("/etc/policy-manager/config.xml")
    if (not dtd.validate(xml)):
      raise etree.LxmlError("Configuration file is not a valid instance of " +
                            "DTD.")

    level  = xml.find("./log").get("level")
    domain = xml.find("./domain").get("name")
    rate   = xml.find("./update").get("rate")
  except etree.LxmlError as e:
    logger.error("Error while parsing configuration file: %s" % e)
    logger.error("Daemon not started.")
    sys.exit(1)

  # Configuring the logger level.
  if (level.lower() == 'debug'):
    logger.setLevel(logging.DEBUG)    
  elif (level.lower() == 'info'):
    logger.setLevel(logging.INFO)    
  elif (level.lower() == 'warning'):
    logger.setLevel(logging.WARNING)    
  elif (level.lower() == 'error'):
    logger.setLevel(logging.ERROR)    
  else:
    logger.setLevel(logging.DEBUG)  

  # Initialization and configuration of daemon.
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

  # Ensuring logger file handler does not get closed during daemonization.
  daemon_runner.daemon_context.files_preserve=[handler.stream]

  # Running the daemon as pm-daemon of the pm group.
  daemon_runner.daemon_context.uid = uid
  daemon_runner.daemon_context.gid = gid

  # Everyone may read but only user may write files created by the process.
  # This is mainly intended for the PID file.
  daemon_runner.daemon_context.umask = 022

  daemon_runner.daemon_context.signal_map = \
                            {signal.SIGTERM:lambda signum, frame: app.stop(),
                             signal.SIGINT: lambda signum, frame: app.stop(),
                             signal.SIGABRT:lambda signum, frame: app.stop(),
                             signal.SIGQUIT:lambda signum, frame: app.stop(),
                             signal.SIGHUP: lambda signum, frame: app.stop()}

  logger.info("Command %s issued." % sys.argv[1])

  # Starting daemon action, and catching some well-known errors.
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
