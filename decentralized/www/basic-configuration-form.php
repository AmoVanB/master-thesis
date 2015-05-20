<?php
  /* Getting current configuration. */
  try
  {
    $dom = new DomDocument();
    $dom->load('/etc/service-discovery/config.xml');
    $log    = $dom->getElementsByTagName('log')->item(0);
    $db     = $dom->getElementsByTagName('database')->item(0);
    $cfg    = $dom->getElementsByTagName('config')->item(0);
    $domain = $dom->getElementsByTagName('domain')->item(0);

    if ($db == null || $cfg == null || $log == null || $domain == null)
      throw new DOMException('Invalid configuration file.');
    
    $pub_ifcs = $cfg->getAttribute('public-interfaces');
    $loglevel = $log->getAttribute('level');
    $dbname   = $db->getAttribute('name');
    $dbpwd    = $db->getAttribute('password');
    $dbhost   = $db->getAttribute('host');
    $dbsocket = $db->getAttribute('socket');
    $dbport   = $db->getAttribute('port');
    $dbuser   = $db->getAttribute('user');
    $server   = $domain->getAttribute('server');
    $zone     = $domain->getAttribute('zone');
    $keyname  = $domain->getAttribute('keyname');
    $keyval   = $domain->getAttribute('keyvalue');
    $algo     = $domain->getAttribute('algorithm');
    $ttl      = $domain->getAttribute('ttl');
  }
  catch (Exception $e)
  {
    echo '<p>Note: '.$e->getMessage().'</p>';
  }
?>

<p>The router name must consist only of lower-case letters and numbers. <br />
The public interfaces must be separated by commas if several ones have to be provided.</p>

<form class="well" action="index.php?page=basic-configuration" method="POST">
  <fieldset>
  <legend>General</legend>
    <label for="pub_ifcs">Router Public Interface(s)</label><br />
    <input type="text" id="pub_ifcs" name="pub_ifcs" value="<?php echo $pub_ifcs; ?>" size="30" required /><br />
  </fieldset>

  <fieldset>
  <legend>Database</legend>

    <label for="dbname">Name</label><br />
    <input type="text"     id="dbname"   name="dbname"   value="<?php echo $dbname; ?>"   size="30" required /><br />

    <label for="dbuser">User</label><br />
    <input type="text"     id="dbuser"   name="dbuser"   value="<?php echo $dbuser; ?>"   size="30" required /><br />

    <label for="dbpwd">Password</label><br />
    <input type="password" id="dbpwd"    name="dbpwd"    value="<?php echo $dbpwd; ?>"    size="30" required /><br />

    <label for="dbhost">Host</label><br />
    <input type="text"     id="dbhost"   name="dbhost"   value="<?php echo $dbhost; ?>"   size="30" required /><br />

    <label for="dbsocket">Socket</label><br />
    <input type="text"     id="dbsocket" name="dbsocket" value="<?php echo $dbsocket; ?>" size="30"  required /><br />
    
    <label for="dbport">Port</label><br />
    <input type="text"     id="dbport"   name="dbport"   value="<?php echo $dbport; ?>" min="0" max="65535" required /><br />

  </fieldset>

  <fieldset>
  <legend>Log file</legend>

    <label for="loglevel">Level</label><br /> 
    <select id="loglevel" name="loglevel">
      <option value="error"   <?php if ($loglevel == 'error')   echo 'selected'; ?>>Error</option>
      <option value="warning" <?php if ($loglevel == 'warning') echo 'selected'; ?>>Warning</option>
      <option value="info"    <?php if ($loglevel == 'info')    echo 'selected'; ?>>Info</option>
      <option value="debug"   <?php if ($loglevel == 'debug')   echo 'selected'; ?>>Debug</option>
    </select><br />

  </fieldset>

  <fieldset>
  <legend>Domain</legend>

    <label for="server">Server</label><br />
    <input type="text"     id="server"  name="server"  value="<?php echo $server; ?>"  size="30" required /><br />

    <label for="zone">Zone</label><br />
    <input type="text"     id="zone"    name="zone"    value="<?php echo $zone; ?>"    size="30" required /><br />

    <label for="keyname">Key name</label><br />
    <input type="text"     id="keyname" name="keyname" value="<?php echo $keyname; ?>" size="30" required /><br />

    <label for="keyval">Key value</label><br />
    <input type="password" id="keyval"  name="keyval"  value="<?php echo $keyval; ?>"  size="30" required /><br />

    <label for="ttl">TTL</label><br />
    <input type="text"     id="ttl"     name="ttl"     value="<?php echo $ttl; ?>" min="0" max="4294967295" required /><br />

    <label for="algo">Algorithm</label><br />
    <select id="algo" name="algo">
      <option value="hmac_md5"    <?php if (strtolower($algo) == 'hmac_md5')    echo 'selected'; ?>>HMAC-MD5</option>
      <option value="hmac_sha1"   <?php if (strtolower($algo) == 'hmac_sha1')   echo 'selected'; ?>>HMAC-SHA1</option>
      <option value="hmac_sha224" <?php if (strtolower($algo) == 'hmac_sha224') echo 'selected'; ?>>HMAC-SHA224</option>
      <option value="hmac_sha256" <?php if (strtolower($algo) == 'hmac_sha256') echo 'selected'; ?>>HMAC-SHA256</option>
      <option value="hmac_sha384" <?php if (strtolower($algo) == 'hmac_sha384') echo 'selected'; ?>>HMAC-SHA384</option>
      <option value="hmac_sha512" <?php if (strtolower($algo) == 'hmac_sha512') echo 'selected'; ?>>HMAC-SHA512</option>
    </select><br />
    
  </fieldset>

  <fieldset>
  <legend>Backup</legend>

    <p>Submitting this form will override the current configuration file.</p>

    Save current configuration file in another file?<br />
    <input type="radio" name="save" id="yes" value="yes" onclick="backup.disabled=false"        /><label for="yes"> Yes </label>
    <input type="radio" name="save" id="no"  value="no"  onclick="backup.disabled=true" checked /><label for="no" > No </label>
    <br />
    <label for="backup">Backup file name</label><br />
    <input type="text" id="backup" name="backup" value="config-old.xml" required disabled />
    <br />
  </fieldset>

  <input type="submit" value="Submit" class="btn btn-danger"  />
  <input type="reset"  value="Reset"  class="btn btn-default" />  

</form>
