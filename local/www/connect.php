<?php
  /* The connect.php script tries to connect to the database specified in the
   * /etc/service-discovery/config.xml file. It creates a 'connected' variable
   * which is true or false whether the script succeeded or not.
   * In case of success, the 'db' variable holds the PDO connection.
   */
  try
  {
    $dom = new DomDocument();
    $dom->load('/etc/service-discovery/config.xml');
    $db = $dom->getElementsByTagName('database')->item(0);

    if ($db == null)
      throw new DOMException();
    
    $user   = $db->getAttribute('user');
    $pwd    = $db->getAttribute('password');
    $dbname = $db->getAttribute('name');
    $socket = $db->getAttribute('socket');
    $host   = $db->getAttribute('host');
    $port   = $db->getAttribute('port');

    $db = new PDO('mysql:host='.$host.';dbname='.$dbname.';unix_socket='.$socket.';port='.$port.'', $user, $pwd);
    $db->query("SET NAMES UTF8");
    $connected = true;
  }
  catch (Exception $e)
  {
    $connected = false;
  }
?>
