#!/usr/bin/python2
# -*- coding: utf-8 -*-

"""
/decentralized/python/MySQLWrapper.py

Part of master thesis "Using Service Discovery to Apply Policies in Networks"
at University of Liège 2014-2015.
by Amaury Van Bemten.

Entreprise: Cisco
Contact entreprise: Eric Vyncke
Advisor: Guy Leduc
"""

import mysql.connector

class MySQLWrapper():
  """A wrapper around MySQL Python Connector library to allow to easily perform
    MySQL queries."""

  def __init__(self, db_user, db_pwd, db_name, db_host, db_socket, db_port):
    """Constructor.

    Args:
      db_user:   Database username.
      db_pwd:    Database password.
      db_name:   Database name.
      db_host:   Host hosting the database.
      db_socket: Database socket.
      db_port:   Port on which the database listens.
    """
    self.db_user   = db_user
    self.db_pwd    = db_pwd
    self.db_name   = db_name
    self.db_host   = db_host
    self.db_socket = db_socket
    self.db_port   = db_port


  def command(self, requests):
    """Issues several requests to a MySQL database. This method is only suited
      for operations which do not imply an answer. The server response is not 
      returned. No escaping is performed.

    Args:
      requests: An array of tuples. The first element of the tuple contains the
                string request and the second element a tuple of possible
                parameters to this request.

    Returns:
      0 in case of success and the MySQL error code in case of failure.
    """

    config = {
      'user'        : self.db_user,
      'password'    : self.db_pwd,
      'database'    : self.db_name,
      'host'        : self.db_host,
      'unix_socket' : self.db_socket,
      'port'        : self.db_port,
      'charset'     : 'utf8'
    }

    try: 
      cnx = mysql.connector.connect(**config)
      cursor = cnx.cursor()

      for request in requests:
        cursor.execute(request[0], request[1])

      cnx.commit()
    except mysql.connector.Error as err:
      return err.errno
    else:
      cursor.close()
      cnx.close()
      return 0


  def query(self, query):
    """Issues a MySQL query and return the result.

    Returns:
      None in case of failure and an array of dictionaries in case of success.
      Each row is represented as a dictionary. The keys for each dictionary
      object are the column names of the MySQL result.

    Args:
      query: A tuple. The first element contains the query and the second a
             tuple of possible parameters for this query.
    """

    config = {
      'user'        : self.db_user,
      'password'    : self.db_pwd,
      'database'    : self.db_name,
      'host'        : self.db_host,
      'unix_socket' : self.db_socket,
      'port'        : self.db_port,
      'charset'     : 'utf8'
    }

    try: 
      cnx = mysql.connector.connect(**config)
      cursor = cnx.cursor(dictionary=True) # To return rows as dictionaries.

      cursor.execute(query[0], query[1])
      
      # Putting the result rows in an array.
      result = []
      for row in cursor:
        result.append(row)

    except mysql.connector.Error as err:
      return None
    else:
      cursor.close()
      cnx.close()
      return result
