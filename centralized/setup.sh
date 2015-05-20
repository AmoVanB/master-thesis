groupadd -r    pm
adduser  -r -g pm pm-daemon
adduser  -r -g pm pm-gui

mkdir /etc/policy-manager/

cp   ./config/config.dtd   /etc/policy-manager/
cp   ./config/config.xml   /etc/policy-manager/

touch /var/log/policy-manager.log

chown pm-gui    /etc/policy-manager/
chown pm-gui    /etc/policy-manager/config.dtd
chown pm-gui    /etc/policy-manager/config.xml
chown pm-daemon /var/log/policy-manager.log

chgrp pm        /etc/policy-manager/
chgrp pm        /etc/policy-manager/config.dtd
chgrp pm        /etc/policy-manager/config.xml
chgrp pm        /var/log/policy-manager.log

# User (pm-gui) and group (pm) can read and write,
# others can only access.
chmod -R 775 /etc/policy-manager/
# User (pm-gui) can read and write the configuration file,
# group (pm) can only read the configuration file,
# others cannot access configuration file.
chmod 640    /etc/policy-manager/config.xml
# DTD cannot be edited by anybody but can be read.
chmod 444    /etc/policy-manager/config.dtd
# Everybody may read the logs but only pm-daemon (user) may write in them.
chmod 644    /var/log/policy-manager.log
