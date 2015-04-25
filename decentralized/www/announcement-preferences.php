<?php

  /* If the form as been entirely submitted, we call the recipient script.
     Otherwise, we show the form. */
  if (isset($_POST["usedIDs"]) && isset($_POST['save']) && ($_POST['save'] == "no" || isset($_POST['backup'])))
  {
    $_POST["usedIDs"] = htmlspecialchars($_POST["usedIDs"]);

    // Now we must check that all the field for all IDs have been defined.
    $IDs = explode(',', $_POST["usedIDs"]);

    $condition = true;
    foreach ($IDs as $id)
    {
      $condition = $condition && isset($_POST["if-name-".$id]);
      $condition = $condition && isset($_POST["if-ip-".$id]);
      $condition = $condition && isset($_POST["name-".$id]);
      $condition = $condition && isset($_POST["type-".$id]);
      $condition = $condition && isset($_POST["host-".$id]);
      $condition = $condition && isset($_POST["port-".$id]);
      $condition = $condition && isset($_POST["action-".$id]);
    }

    /* If $_POST["usedIDs"] is 0 it means that there is no rule. Hence, condition
       variable is meaningless (there will be no rule-0). */
    if ($condition || $_POST["usedIDs"] == 0)
      include 'announcement-preferences-result.php';
    else
      include 'announcement-preferences-form.php';
  }
  else
  {
    include 'announcement-preferences-form.php';
  }

?>

