groupadd -r    sd
adduser  -r -g sd sd-daemon
adduser  -r -g sd sd-gui

mkdir /etc/service-discovery/

cp ./config/config.dtd        /etc/service-discovery/
cp ./config/config.xml        /etc/service-discovery/
cp ./config/avahi-daemon.conf /etc/avahi/avahi-daemon.conf
cp ./config/system-local.conf /etc/dbus-1/system-local.conf

touch /var/log/service-discovery.log

chown sd-gui    /etc/service-discovery/
chown sd-gui    /etc/service-discovery/config.dtd
chown sd-gui    /etc/service-discovery/config.xml
chown sd-daemon /var/log/service-discovery.log

chgrp sd        /etc/service-discovery/
chgrp sd        /etc/service-discovery/config.dtd
chgrp sd        /etc/service-discovery/config.xml
chgrp sd        /var/log/service-discovery.log

# sd-gui (user) can modify the configuration file,
# sd-gui and sd-daemon (group) can read the configuration file,
# others cannot do anything because the file holds passwords.
chmod 640 /etc/service-discovery/config.xml
# DTD cannot be edited by anybody but can be read.
chmod 444 /etc/service-discovery/config.dtd
# Everybody may read the logs but only sd-daemon (user) may write in them.
chmod 644 /var/log/service-discovery.log

/opt/lampp/lampp start

echo "Creating MySQL user amo using root."
/opt/lampp/bin/mysql -u root -p < sql/root_init.sql
echo "Creating tables using amo."
/opt/lampp/bin/mysql -u amo -p  < sql/user_init.sql

# Restart Avahi to reload configuration.
avahi-daemon --kill
avahi-daemon -D
