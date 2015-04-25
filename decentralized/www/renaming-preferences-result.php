<?php
  /* Performing security checks. */
  $usedIDs = htmlspecialchars($_POST["usedIDs"]);
  $name    = htmlspecialchars($_POST["name"]);
  $alias   = htmlspecialchars($_POST["alias"]);
 
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

    $dom->documentElement->setAttribute('name', $name);
    $dom->documentElement->setAttribute('alias', $alias);
    
    // First we remove all the previous aliases.
    $ip_aliases = $dom->getElementsByTagName('ip');
    $if_aliases = $dom->getElementsByTagName('interface');

    while ($ip_aliases->length > 0)
    {
      $ip = $ip_aliases->item(0);
      $ip->parentNode->removeChild($ip);
    }

    while ($if_aliases->length > 0)
    {
      $if = $if_aliases->item(0);
      $if->parentNode->removeChild($if);
    }

    // Then, if there are some, we add all the sent aliases.
    if ($usedIDs != 0)
    {      
      // Addition of all the interface aliases.
      $IDs = explode(',', $usedIDs);

      foreach ($IDs as $id)
      {
        $if_name  = htmlspecialchars($_POST["name-".$id]);
        $if_alias = htmlspecialchars($_POST["alias-".$id]);

        // Creation of the tag and the attributes.
        $elem = $dom->createElement('interface');

        $attr = $dom->createAttribute('name');
        $attr->value = $if_name;
        $elem->appendChild($attr);

        $attr = $dom->createAttribute('alias');
        $attr->value = $if_alias;
        $elem->appendChild($attr);

        /* 'interface' has to be inserted before 'rules'. If no 'rules' tag, it
           has to be inserted at the end. */
        $rules = $dom->getElementsByTagName("rules");
        if($rules->length != 0)
          $dom->documentElement->insertBefore($elem, $rules->item(0));
        else
          $dom->documentElement->appendChild($elem);
      }
    }

    // Addition of the IP versions aliases.
    $v4alias = htmlspecialchars($_POST["ipv4"]);
    $v6alias = htmlspecialchars($_POST["ipv6"]);

    // Creation of the 'ip' tags and their attributes.
    $elem4 = $dom->createElement('ip');
    $elem6 = $dom->createElement('ip');
    
    $attr = $dom->createAttribute('version');
    $attr->value = "4";
    $elem4->appendChild($attr);

    $attr = $dom->createAttribute('version');
    $attr->value = "6";
    $elem6->appendChild($attr);

    $attr = $dom->createAttribute('alias');
    $attr->value = $v4alias;
    $elem4->appendChild($attr);

    $attr = $dom->createAttribute('alias');
    $attr->value = $v6alias;
    $elem6->appendChild($attr);

    /* 'ip' has to be inserted before 'interface'. If none, before 'rules'. If
       none, at the end. */
    $if = $dom->getElementsByTagName("interface");
    $rules = $dom->getElementsByTagName("rules");

    if($if->length != 0)
    {
      $dom->documentElement->insertBefore($elem4, $if->item(0));
      $dom->documentElement->insertBefore($elem6, $if->item(0));
    }
    elseif($rules->length != 0)
    {
      $dom->documentElement->insertBefore($elem4, $rules->item(0));
      $dom->documentElement->insertBefore($elem6, $rules->item(0));
    }
    else
    {
      $dom->documentElement->appendChild($elem4);
      $dom->documentElement->appendChild($elem6);
    }
    
    // Saving config file.
    if ($dom->save('/etc/service-discovery/config.xml') != FALSE)
      echo '<p>Configuration file successfully updated with aliases.</p>';
    else
      echo '<p>Error while saving new configuration file.</p>';
  }
  catch (Exception $e)
  {
    echo '<p>Error: '.$e->getMessage().'</p>';
  }
?>

  <p><a href="index.php">Back to home</a>.</p>
