<?php
  /* If the form as been entirely submitted, we call the recipient script.
     Otherwise, we show the form. */
  if (isset($_POST["name"]) && isset($_POST["alias"]) && isset($_POST["ipv4"]) && isset($_POST["ipv6"]) && isset($_POST["usedIDs"]) && isset($_POST['save']) && ($_POST['save'] == "no" || isset($_POST['backup'])))
  {
    $_POST["usedIDs"] = htmlspecialchars($_POST["usedIDs"]);

    // Now we must check that all the field for all IDs have been defined.
    $IDs = explode(',', $_POST["usedIDs"]);

    $condition = true;

    foreach ($IDs as $id)
    {
      $condition = $condition && isset($_POST["name-".$id]);
      $condition = $condition && isset($_POST["alias-".$id]);
    }

    /* If $_POST["usedIDs"] is 0 it means that there is no rule. Hence, condition
       variable is meaningless (there will be no rule-0). */
    if ($condition || $_POST["usedIDs"] == 0)
      include 'renaming-preferences-result.php';
    else
      include 'renaming-preferences-form.php';
  }
  else
  {
    include 'renaming-preferences-form.php';
  }
?>

