<?php
  /* Performing "security" checks. */
  $domain   = htmlspecialchars($_POST['domain']);
  $loglevel = htmlspecialchars($_POST['loglevel']);
  $rate     = htmlspecialchars($_POST['rate']);

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
    $dom->load('/etc/policy-manager/config.xml');
    $dom->formatOutput = true;
  
    // Save a backup of the current cfg file if asked by user.
    if ($save)
    {
      if ($dom->save('/etc/policy-manager/'.$backup) != FALSE)
        echo '<p>Old configuration file successfully saved to <code>'.$backup.'</code>.</p>';
      else
        echo '<p>Error while saving previous configuration file.</p>';
    }

    // Updating tags with new values.
    $log        = $dom->getElementsByTagName('log')->item(0);
    $domain_tag = $dom->getElementsByTagName('domain')->item(0);
    $update     = $dom->getElementsByTagName('update')->item(0);

    if ($log == null || $domain == null || $update == null)
      throw new DOMException('Invalid configuration file.');
    
    $log->setAttribute('level', $loglevel);
    $domain_tag->setAttribute('name', $domain);
    $update->setAttribute('rate', $rate);

    // Saving config file.
    if ($dom->save('/etc/policy-manager/config.xml') != FALSE)
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
