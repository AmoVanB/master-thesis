<?php
  /* Performing "security" checks. */
  $pub_ifcs = htmlspecialchars($_POST['pub_ifcs']);
  $dbname   = htmlspecialchars($_POST['dbname']);
  $dbuser   = htmlspecialchars($_POST['dbuser']);
  $dbpwd    = htmlspecialchars($_POST['dbpwd']);
  $dbsocket = htmlspecialchars($_POST['dbsocket']);
  $dbhost   = htmlspecialchars($_POST['dbhost']);
  $dbport   = (int) ($_POST['dbport']);

  $server   = htmlspecialchars($_POST['server']);
  $zone     = htmlspecialchars($_POST['zone']);
  $keyname  = htmlspecialchars($_POST['keyname']);
  $keyval   = htmlspecialchars($_POST['keyval']);
  $algo     = htmlspecialchars($_POST['algo']);
  $ttl      = (int) ($_POST['ttl']);

  $loglevel = htmlspecialchars($_POST['loglevel']);

  if (isset($_POST['backup']))
    $backup = htmlspecialchars($_POST['backup']);

  if ($_POST['save'] == 'yes')
    $save = true;  
  else
    $save = false;

  try
  {
    $dom = new DomDocument();
    $dom->preserveWhiteSpace = false;
    $dom->load('/etc/service-discovery/config.xml');
    $dom->formatOutput = true;
  
    // Save a backup of the current cfg file if asked by user.
    if ($save)
    {
      if ($dom->save('/etc/service-discovery/'.$backup) != FALSE)
        echo '<p>Old configuration file successfully saved to <code>'.$backup.'</code>.</p>';
      else
        echo '<p>Error while saving previous configuration file.</p>';
    }

    // Updating tags with new values.
    $log    = $dom->getElementsByTagName('log')->item(0);
    $db     = $dom->getElementsByTagName('database')->item(0);
    $domain = $dom->getElementsByTagName('domain')->item(0);
    $cfg    = $dom->getElementsByTagName('config')->item(0);

    if ($cfg == null || $db == null || $log == null || $domain == null)
      throw new DOMException('Invalid configuration file.');
    
    $cfg->setAttribute('public-interfaces', $pub_ifcs);
    $log->setAttribute('level', $loglevel);
    $db->setAttribute('name', $dbname);
    $db->setAttribute('password', $dbpwd);
    $db->setAttribute('host', $dbhost);
    $db->setAttribute('socket', $dbsocket);
    $db->setAttribute('port', $dbport);
    $db->setAttribute('user', $dbuser);
    $domain->setAttribute('server', $server);
    $domain->setAttribute('zone', $zone);
    $domain->setAttribute('keyname', $keyname);
    $domain->setAttribute('keyvalue', $keyval);
    $domain->setAttribute('algorithm', $algo);
    $domain->setAttribute('ttl', $ttl);

    // Saving config file.
    if ($dom->save('/etc/service-discovery/config.xml') != FALSE)
      echo '<p>Configuration file successfully updated with new values.</p>';
    else
      echo '<p>Error while saving new configuration file.</p>';
  }
  catch (Exception $e)
  {
    echo '<p>Error: '.$e->getMessage().'</p>';
  }
?>

<p><a href="index.php">Back to home</a>.</p>
