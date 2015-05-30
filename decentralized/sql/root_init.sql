/* Create service_discovery database. */
DROP   DATABASE IF EXISTS service_discovery;
CREATE DATABASE service_discovery CHARACTER SET utf8 COLLATE utf8_bin;

/* Create user amo with password cisco123. */
CREATE USER 'amo'@'localhost' IDENTIFIED BY PASSWORD '*3D39CFCA5E4CBDB378ED0ADD0381A355955F0F30';
GRANT ALL PRIVILEGES ON service_discovery.* TO 'amo'@'localhost' WITH GRANT OPTION;
