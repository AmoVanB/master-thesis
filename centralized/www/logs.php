<?php
  if (isset($_POST['nlines']))
    $nlines = (int) ($_POST['nlines']);
  else
    $nlines = 50;
?>

<!-- Form to change the number of printed lines -->
<form action="index.php?page=logs" method="POST">
  <p>
    Showing the <input type="text" name="nlines" value="<?php echo $nlines; ?>" size="3" required /> last lines.
    <button class="btn-link" type="submit">Change</button>
  </p>
</form>

<?php

  $file = '/var/log/policy-manager.log';
  $nlines = escapeshellarg($nlines);
  $file = escapeshellarg($file);
  $file = `tail -n $nlines $file`;

  // Labeling each message type.
  $file = str_replace('- CRITICAL -', '<span class="label label-danger">CRITICAL</span>', $file);
  $file = str_replace('- ERROR -', '<span class="label label-danger">ERROR</span>', $file);
  $file = str_replace('- WARNING -', '<span class="label label-warning">WARNING</span>', $file);
  $file = str_replace('- INFO -', '<span class="label label-info">INFO</span>', $file);
  $file = str_replace('- DEBUG -', '<span class="label label-default">DEBUG</span>', $file);

  echo '<div class="file-content">';
  echo '<p>';
  echo nl2br($file);
  echo '</p>';
  echo '</div>';

?>
