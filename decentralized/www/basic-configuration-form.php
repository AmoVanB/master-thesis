<?php
  /* Getting current configuration. */
  try
  {
    $dom = new DomDocument();
    $dom->load('/etc/policy-manager/config.xml');
    $log    = $dom->getElementsByTagName('log')->item(0);
    $domain = $dom->getElementsByTagName('domain')->item(0);

    if ($log == null || $domain == null)
      throw new DOMException('Invalid configuration file.');
    
    $loglevel = $log->getAttribute('level');
    $domain   = $domain->getAttribute('name');
  }
  catch (Exception $e)
  {
    echo '<p>Note: '.$e->getMessage().'</p>';
  }
?>

<form class="well" action="index.php?page=basic-configuration" method="POST">
  <fieldset>
  <legend>Configuration</legend>

    <label for="domain">Domain</label><br />
    <input type="text"     id="domain"  name="domain"  value="<?php echo $domain; ?>"  size="30" required /><br />

    <label for="loglevel">Log Level</label><br /> 
    <select id="loglevel" name="loglevel">
      <option value="error"   <?php if ($loglevel == 'error')   echo 'selected'; ?>>Error</option>
      <option value="warning" <?php if ($loglevel == 'warning') echo 'selected'; ?>>Warning</option>
      <option value="info"    <?php if ($loglevel == 'info')    echo 'selected'; ?>>Info</option>
      <option value="debug"   <?php if ($loglevel == 'debug')   echo 'selected'; ?>>Debug</option>
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

  <input type="submit" value="Submit" class="btn btn-primary"  />
  <input type="reset" value="Reset"   class="btn btn-default" />  

</form>
