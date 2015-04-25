<?php

  if (isset($_POST['loglevel']) && isset($_POST['domain']) && isset($_POST['save']) && ($_POST['save'] == "no" || isset($_POST['backup'])))
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

