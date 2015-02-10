<?php
  /* Getting current configuration. */
  try
  {
    $dom = new DomDocument();
    $dom->load('/etc/service-discovery/config.xml');
    $aliases = $dom->getElementsByTagName('interface');
    $numberOfAliases = $aliases->length;

    $ip = $dom->getElementsByTagName('ip');
    // Default IP versions aliases.
    $v4alias = " (IPv4)";
    $v6alias = " (IPv6)";
    
    foreach ($ip as $v)
    {
      if ($v->getAttribute('version') == "4")
        $v4alias = $v->getAttribute('alias');
      elseif ($v->getAttribute('version') == "6")
        $v6alias = $v->getAttribute('alias');
    }
  }
  catch (Exception $e)
  {
    echo '<p>Note: '.$e->getMessage().'</p>';
  }

  /* Javascript script creates two vars. The listed aliases will be arranged in
     a table. Each alias will be assigned an ID. The maxID variable keeps the
     highest ID. usedIDs is an array of all the used IDs. The usedIDs is 
     an ordered array. It keeps the order of the rules, which does not
     necessarily contain all the IDs, as the user can remove aliases. */
  echo '<script>';
    echo 'var maxID = '.$numberOfAliases.';';

    echo 'var usedIDs = [';
    for ($i = 1; $i <= $numberOfAliases; $i++)
    {
      if ($i == $numberOfAliases)
        echo $i;
      else
        echo $i.',';
    }
    echo                '];';
  echo '</script>';
?>

<!-- Javascript functions -->
<script>
  // Remove all the occurences of 'item' in 'array'.
  function removeFromArray(array, item)
  {
    for(var i = array.length; i--;)
    {
      if(array[i] === item)
      {
        array.splice(i, 1);
      }
    }
  }

  // Adds a row in the table of aliases.
  function addAlias()
  {
    var row = '<tr id="alias-' + ++maxID + '">';
    row += '<td><input type="text" name="name-'+ maxID +'" value=""  size=20 required /\></td>';
    row += '<td><input type="text" name="alias-'+ maxID +'" value="" size=20 /\></td>';
    row += '<td><span class="text-danger glyphicon glyphicon-remove" onclick="removeAlias('+ maxID +')"></span></td>';
    row += '</tr>';

    if ($('#aliases-table tbody').length > 0) {
      $('#aliases-table tbody').append(row);
    }
    else {
      $('#aliases-table').append(row);
    }
    
    /* We update usedIDs and the #usedIDs-field. This is a hidden field which
       lists the elements of usedIDs so that the recipient script knows which
       aliases have been defined. */
    usedIDs[usedIDs.length] = maxID;
    $('#usedIDs-field').attr('value', usedIDs);
  }

  // Removes the row with id 'id' from the table of aliases.
  function removeAlias(id)
  {
    // Remove the id from the usedIDs array.
    removeFromArray(usedIDs, id);

    // Remove the row from the table.
    $('#alias-' + id).remove();

    // Update usedIDs.
    if (usedIDs.length === 0)
    {
      /* If no aliases are defined, we set the field value to 0 so that the
         recipient script knows that there is no alias defined. */
      $('#usedIDs-field').attr('value', "0");
    }
    else
    {
      $('#usedIDs-field').attr('value', usedIDs);
    }
  }
</script>

<p>Each service that is published on the public DNS will be appended a string containing information about the interface name and IP version on which it has been discovered by the router. If <code>name</code> is the service name, it will be published as <code>"name" + "if_alias" + "ip_alias"</code> where <code>if_alias</code> and <code>ip_alias</code> are the aliases of the interface name and IP version that can be configured throughout this page. If no alias is defined for an interface, <code>" @ " + "if_name"</code>, where <code>if_name</code> is the interface's classical name, will be used as alias.</p>

<form class="well table-responsive" action="index.php?page=renaming-preferences" method="POST">
  <fieldset>
  <legend>IP Versions</legend>

    <label for="ipv4">IPv4</label><br />
    <input type="text" id="ipv4" name="ipv4" value="<?php echo $v4alias; ?>" size="20" /><br />

    <label for="ipv6">IPv6</label><br />
    <input type="text" id="ipv6" name="ipv6" value="<?php echo $v6alias; ?>" size="20" /><br />

  </fieldset>

  <fieldset>
  <legend>Interfaces</legend>

    <div class="table-responsive">
    <table id="aliases-table" class="table table-bordered table-condensed">
      <thead>
        <tr>
          <th>Interface name</th>
          <th>Interface alias</th>
          <th>Actions</th>
        </tr>
      </thead>

      <tbody>
        <?php
          for ($i = 1; $i <= $numberOfAliases; $i++)
          {
            echo '<tr id="alias-'.$i.'">';
            echo '  <td><input type="text" name="name-'.$i.'"  value="'.$aliases->item($i-1)->getAttribute("name").'"  size=20 required /></td>';
            echo '  <td><input type="text" name="alias-'.$i.'" value="'.$aliases->item($i-1)->getAttribute("alias").'" size=20 /></td>';
            echo '  <td><span class="text-danger glyphicon glyphicon-remove" onclick="removeAlias('.$i.');"></span></td>';
            echo '</tr>';
          }
        ?>
      </tbody>
      <tfoot>
        <tr>
          <td colspan="2"></td>
          <td><span onclick="addAlias()" class="text-success glyphicon glyphicon-plus"></span></td>
        </tr>
      </tfoot>
      </table>
    </div>
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

  <input type="hidden" name="usedIDs" id="usedIDs-field" value=
    <?php
      echo '"';
      for ($i = 1; $i <= $numberOfAliases; $i++)
      {
        if ($i == $numberOfAliases)
          echo $i;
        else
          echo $i.',';
      }
      echo '"';
    ?>
  />
  <input type="submit" value="Submit" class="btn btn-danger" />
  <input type="reset"  value="Reset" class="btn btn-default" onclick="location.reload();" />  

</form>
