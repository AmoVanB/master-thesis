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
        $src_add = htmlspecialchars($_POST["src-address-".$id]);
        $src_msk = htmlspecialchars($_POST["src-prefix-length-".$id]);
        $name    = htmlspecialchars($_POST["name-".$id]);
        $type    = htmlspecialchars($_POST["type-".$id]);
        $router  = htmlspecialchars($_POST["router-".$id]);
        $action  = htmlspecialchars($_POST["action-".$id]);

        // We create the 'rule' tag and each attribute.
        $elem = $dom->createElement('rule', $action);

        $attr = $dom->createAttribute('src-address');
        $attr->value = $src_add;
        $elem->appendChild($attr);

        $attr = $dom->createAttribute('src-prefix-length');
        $attr->value = $src_msk;
        $elem->appendChild($attr);

        $attr = $dom->createAttribute('name');
        $attr->value = $name;
        $elem->appendChild($attr);

        $attr = $dom->createAttribute('type');
        $attr->value = $type;
        $elem->appendChild($attr);

        $attr = $dom->createAttribute('router');
        $attr->value = $router;
        $elem->appendChild($attr);

        $rules->appendChild($elem);
      }
    }
    
    // Saving config file.
    if ($dom->save('/etc/policy-manager/config.xml') != FALSE)
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
