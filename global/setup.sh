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
chown pm-daemon /var/log/service-discovery.log

chgrp sd        /etc/policy-manager/
chgrp sd        /etc/policy-manager/config.dtd
chgrp sd        /etc/policy-manager/config.xml
chgrp sd        /var/log/policy-manager.log

# Group can read, user write and others: nothing.
chmod 640 /etc/policy-manager/config.xml
# DTD can't be edited by anybody.
chmod 444 /etc/policy-manager/config.dtd
# Everybody may read the logs but only user/group may write.
chmod 664 /var/log/policy-manager.log
