groupadd -r sd
adduser -r -g sd sd-daemon
adduser -r -g sd sd-gui

mkdir /etc/service-discovery/

cp  config/config.dtd           /etc/service-discovery/
cp  config/config.xml           /etc/service-discovery/
cat config/avahi-daemon.conf >  /etc/avahi/avahi-daemon.conf
touch /var/log/service-discovery.log

chown sd-gui    /etc/service-discovery/
chown sd-gui    /etc/service-discovery/config.dtd
chown sd-gui    /etc/service-discovery/config.xml
chown sd-daemon /var/log/service-discovery.log

chgrp sd        /etc/service-discovery/
chgrp sd        /etc/service-discovery/config.dtd
chgrp sd        /etc/service-discovery/config.xml
chgrp sd        /var/log/service-discovery.log

chmod 640 /etc/service-discovery/config.xml # Group can read, user write and others: nothing because holds passwords
chmod 444 /etc/service-discovery/config.dtd # one may only read the DTD
chmod 664 /var/log/service-discovery.log # Everybody may read the log but only u/g write

/opt/lampp/lampp start

echo "Creating MySQL user amo using root."
/opt/lampp/bin/mysql -u root -p < sql/root_init.sql
echo "Creating tables using amo."
/opt/lampp/bin/mysql -u amo -p < sql/user_init.sql

# Restart avahi to reload configuration.
avahi-daemon --kill
avahi-daemon -D
