USE service_discovery;

/* Deletion of previous tables */
DROP TABLE IF EXISTS services;
DROP TABLE IF EXISTS addresses;

CREATE TABLE IF NOT EXISTS services
(
  if_name  VARCHAR(255) NOT NULL,
  if_ip    TINYINT      NOT NULL,
  name     VARCHAR(255) NOT NULL,
  type     VARCHAR(255) NOT NULL,
  hostname VARCHAR(255),
  port     SMALLINT UNSIGNED, /* Enough as port is on 16 bits */
  TXT      BLOB, /* RFC6763: "A DNS TXT record can be up to 65535
                              (0xFFFF) bytes long.".
                             So a BLOB is big enough (max 65535 bytes)
            http://dev.mysql.com/doc/refman/5.6/en/storage-requirements.html */
  resolved  BOOL         NOT NULL,
  announced BOOL         NOT NULL,
  PRIMARY KEY (if_name, if_ip, name, type)
)ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS addresses
(
  if_name  VARCHAR(255) NOT NULL,
  if_ip    TINYINT      NOT NULL,
  hostname VARCHAR(255) NOT NULL,
  ip       TINYINT      NOT NULL,
  address  VARCHAR(39)  NOT NULL, /* longest addresses (IPv6) are 39 characters
                                     long (including colons) when represented
                                     in their longest usual format. */
  PRIMARY KEY (if_name, if_ip, hostname, ip, address)
)ENGINE=InnoDB;
