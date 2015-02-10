<?php

  if (isset($_POST['dbname']) && isset($_POST['dbuser']) && isset($_POST['dbpwd']) && isset($_POST['dbsocket']) && isset($_POST['dbhost']) && isset($_POST['dbport']) && isset($_POST['loglevel']) && isset($_POST['server']) && ($_POST['zone']) && ($_POST['keyname']) && ($_POST['keyval']) && ($_POST['ttl']) && ($_POST['algo']) && isset($_POST['save']) && ($_POST['save'] == "no" || isset($_POST['backup'])))
  {
    // If the form has been entirely submitted, we call the recipient script.
    include 'basic-configuration-result.php';
  }
  else
  {
    // Otherwise we show the form.
    include 'basic-configuration-form.php';
  }

?>

