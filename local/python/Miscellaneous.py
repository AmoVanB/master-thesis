#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
/python/Miscellaneous.py
 
Module providing miscellaneous functions.

Part of master's thesis "Using Service Discovery to Apply Policies in Networks"
at University of Liège 2014-2015.
Amaury Van Bemten.

Entreprise: Cisco
Contact entreprise: Eric Vyncke
Advisor: Guy Leduc
"""

def int_to_hex_string(integer):
  """From an integer, returns its hexademical representation, as a string.
    '0x' is not prepended.
    '0' is prepended if the integer can be represented by one single hex digit.
    That is, the returned string is always of length >= 2.
  
  Args:
    integer:  The integer to be converted.
  
  Returns:
    The hexadecimal representation of the integer.   
  """

  string = hex(integer)
  string = string[2:]
  if (len(string) < 2):
    string = '0' + string
  return string


def bytes_to_hex_string(bytes):
  """From a bytearray, returns its hexadecimal representation.

  Args:
    bytes: A Python bytearray.

  Returns:
    The hexadecimal representation of the bytearray.
  """

  return ''.join('{:02x}'.format(x) for x in bytes)

def escape(value):
  """Escapes spaces, parenthesises, new lines, CR and quotes from a string.
    Inspired from mysql.connector.conversion.MySQLConverter

  Args:
    value: The string to be escaped.

  Returns:
    The escaped string.
  """
  if isinstance(value, (bytes, bytearray)):
      value = value.replace(b'\\', b'\\\\')
      value = value.replace(b'\n', b'\\n')
      value = value.replace(b'\r', b'\\r')
      value = value.replace(b' ', b'\ ')
      value = value.replace(b'(', b'\(')
      value = value.replace(b')', b'\)')
      value = value.replace(b'\047', b'\134\047')  # single quotes
      value = value.replace(b'\042', b'\134\042')  # double quotes
      value = value.replace(b'\032', b'\134\032')  # for Win32
  else:
      value = value.replace('\\', '\\\\')
      value = value.replace('\n', '\\n')
      value = value.replace('\r', '\\r')
      value = value.replace(' ', '\ ')
      value = value.replace('(', '\(')
      value = value.replace(')', '\)')
      value = value.replace('\047', '\134\047')  # single quotes
      value = value.replace('\042', '\134\042')  # double quotes
      value = value.replace('\032', '\134\032')  # for Win32
  return value
