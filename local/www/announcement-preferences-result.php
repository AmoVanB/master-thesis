<?php
  /* Performing security checks. */
  $usedIDs = htmlspecialchars($_POST["usedIDs"]);

  if (isset($_POST['backup']))
    $backup = htmlspecialchars($_POST['backup']);

  if ($_POST['save'] == 'yes')
    $save = true;  
  else
    $save = false;

  $IDs = explode(',', $_POST["usedIDs"]);

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

    // Getting the 'rules' tag. If none: we create one.
    $rules = $dom->getElementsByTagName('rules');
    if ($rules->length == 0)
    {
      $rootNode = $dom->documentElement;
      $rootNode->appendChild($dom->createElement('rules'));
    }
    $rules = $dom->getElementsByTagName('rules')->item(0);

    // If no rules have been sent, we remove the rules tag.
    if ($usedIDs == 0)
    {
      $dom->getElementsByTagName('config')->item(0)->removeChild($rules);
    }
    else
    {      
      // Otherwise, we remove all the previous rules.
      while ($rules->hasChildNodes())
      {
        $rules->removeChild($rules->firstChild);
      }

      // And we add the new ones one by one.
      $IDs = explode(',', $usedIDs);

      foreach ($IDs as $id)
      {
        $if_name = htmlspecialchars($_POST["if-name-".$id]);
        $if_ip   = htmlspecialchars($_POST["if-ip-".$id]);
        $name    = htmlspecialchars($_POST["name-".$id]);
        $type    = htmlspecialchars($_POST["type-".$id]);
        $host    = htmlspecialchars($_POST["host-".$id]);
        $port    = htmlspecialchars($_POST["port-".$id]);
        $action  = htmlspecialchars($_POST["action-".$id]);

        // We create the 'service' tag and each attribute.
        $elem = $dom->createElement('service', $action);

        $attr = $dom->createAttribute('interface-name');
        $attr->value = $if_name;
        $elem->appendChild($attr);

        $attr = $dom->createAttribute('interface-ip');
        $attr->value = $if_ip;
        $elem->appendChild($attr);

        $attr = $dom->createAttribute('name');
        $attr->value = $name;
        $elem->appendChild($attr);

        $attr = $dom->createAttribute('type');
        $attr->value = $type;
        $elem->appendChild($attr);

        $attr = $dom->createAttribute('hostname');
        $attr->value = $host;
        $elem->appendChild($attr);

        $attr = $dom->createAttribute('port');
        $attr->value = $port;
        $elem->appendChild($attr);

        $rules->appendChild($elem);
      }
    }
    
    // Saving config file.
    if ($dom->save('/etc/service-discovery/config.xml') != FALSE)
      echo '<p>Configuration file successfully updated with new announcement preferences.</p>';
    else
      echo '<p>Error while saving new configuration file.</p>';
  }
  catch (Exception $e)
  {
    echo '<p>Error: '.$e->getMessage().'</p>';
  }
?>

  <p><a href="index.php">Back to home</a>.</p>
