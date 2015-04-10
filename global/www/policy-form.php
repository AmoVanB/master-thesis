<?php
  /* Getting current configuration. */
  try
  {
    $dom = new DomDocument();
    $dom->load('/etc/policy-manager/config.xml');
    $rules = $dom->getElementsByTagName('rule');
    $numberOfRules = $rules->length;
    $domain = $dom->getElementsByTagName('domain')->item(0)->getAttribute("name");
  }
  catch (Exception $e)
  {
    echo '<p>Note: '.$e->getMessage().'</p>';
  }

  $routers_results = dns_get_record( 'b._dns-sd._udp.'.$domain, DNS_PTR);
  $routers = array();

  if (sizeof($routers_results) == 0)
      echo '<div class="panel-heading">No routers found.</div>';
  else
    foreach ($routers_results as $router_entry)
      array_push($routers, explode(".", $router_entry['target'])[0]);

  /* Javascript script creates two vars. The listed rules will be arranged in
     a table. Each rule will be assigned an ID. The maxID variable keeps the
     highest ID. usedIDs is an array of all the used IDs. The usedIDs is 
     an ordered array. It keeps the order of the rules, which is not necessarily
     in increasing order of IDs, as the user can swap rules. It does not 
     necessarily contain all the IDs either, as the user can remove rules. */
    echo '<script>';
      echo 'var maxID = '.$numberOfRules.';';
      echo 'var usedIDs = [';
      for ($i = 1; $i <= $numberOfRules; $i++)
      {
        if ($i == $numberOfRules)
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

  // Return the index of the last occurence of 'item' in 'array'.
  function indexOf(array, item)
  {
    for(var i = array.length; i--;)
    {
      if(array[i] === item)
      {
        return i;
      }
    }
  }

  // Swaps elements at indices 'a' and 'b' in 'array'.
  function swap(array, a, b)
  {
    var tmp = array[b];
    array[b] = array[a];
    array[a] = tmp;
  }

// Adds a row in the table of rules.
  function addRule()
  {

    var row = '<tr id="rule-' + ++maxID + '">';
    row += '<td><input type="text" name="src-address-'+ maxID +'" value="0.0.0.0" required /\></td>';
    row += '<td><input type="number" value="0" name="src-mask-'+ maxID +'" min="0" max="128" required /\></td>';
    row += '<td><input type="text" name="name-'+ maxID +'"    value=".*" required         /\></td>';
    row += '<td><input type="text" name="type-'+ maxID +'"    value=".*" required         /\></td>';
    row += '<td><input type="text" name="router-'+ maxID +'"    value="*" list="routers"        required /\></td>';
    row += '<datalist id="routers">';
    <?php
      foreach ($routers as $router)
        echo "row += '<option value=\"".$router."\">';\n";
    ?>
    row += '<option value="*">';
    row += '</datalist>';
    row += '<td><select name="action-'+ maxID +'">';
    row += '    <option value="allow" selected>Allow</option>';
    row += '    <option value="deny">Deny</option>';
    row += '    </select>';
    row += '</td>';
    row += '<td><span class="text-info glyphicon glyphicon-arrow-up" onclick="moveRuleUp('+ maxID +')"></span></td>';
    row += '<td><span class="text-info glyphicon glyphicon-arrow-down" onclick="moveRuleDown('+ maxID +')"></span></td>';
    row += '<td><span class="text-danger glyphicon glyphicon-remove" onclick="removeRule('+ maxID +')"></span></td>';
    row += '</tr>';

    if ($('#rules-table tbody').length > 0) {
      $('#rules-table tbody').append(row);
    }
    else {
      $('#rules-table').append(row);
    }
    
    /* We update usedIDs and the #usedIDs-field. This is a hidden field which
       lists the elements of usedIDs so that the recipient script knows which
       aliases have been defined. */
    usedIDs[usedIDs.length] = maxID;
    $('#usedIDs-field').attr('value', usedIDs);
  }

  // Removes the row with id 'id' from the table of rules.
  function removeRule(id)
  {
    // Remove the id from the usedIDs array.
    removeFromArray(usedIDs, id);

    // Remove the row from the table.
    $('#rule-' + id).remove();

    // Update usedIDs.
    if (usedIDs.length === 0)
    {
      /* If no rules are defined, we set the field value to 0 so that the
         recipient script knows that there is no rule defined. */
      $('#usedIDs-field').attr('value', "0");
    }
    else
    {
      $('#usedIDs-field').attr('value', usedIDs);
    }
  }

  // Moves rule with id 'id' one row up.
  function moveRuleUp(id)
  {
    // Impossible if the 'id' is the first rule.
    if (indexOf(usedIDs, id) === 0)
    {
      alert('Cannot move the first rule up.');
    }
    else
    {
      // id2 is the id of the rule above. We must hence now swap id and id2.
      var id2 = usedIDs[indexOf(usedIDs, id) - 1];

      // Swapping rows.
      $('#rule-' + id).after($('#rule-' + id2));

      // Updating usedIDs and the hidden field.
      swap(usedIDs, indexOf(usedIDs, id), indexOf(usedIDs, id2));
      $('#usedIDs-field').attr('value', usedIDs);
    }
  }

  // Moves rule with id 'id' one row down.
  function moveRuleDown(id)
  {
    // Impossible if the 'id' is the last rule.
    if (indexOf(usedIDs, id) === usedIDs.length - 1)
    {
      alert('Cannot move the last rule down.');
    }
    else
    {
      // Get a rule down is equivalent to getting the rule below up.
      moveRuleUp(usedIDs[indexOf(usedIDs, id) + 1]);
    }
  }
</script>

<p>Each service announced on the public domain will go through the following list of rules to know whether connections to it have to be accepted or not. The first rule that is matched determines the action. If no rule is matched, connections for the service will be denied.</p>

<p>The application will automatically distinguish IPv6 from IPv4 addresses and those can hence be entered freely.</p>

<p>The <em>mask</em> field specifies the number of bit in the IP address that will be checked for matching. A mask of 0 means that any address will match, i.e. no filtering will be done based on source IP address.</p>

<p><em>Matching</em> of the <em>name</em> and <em>type</em> fields is based on regular expressions. The regular expressions syntax is the one defined by the <code>re</code> Python package whose documentation is available <a href="https://docs.python.org/2/library/re.html">here</a>. For example <code>.*</code> matches any expression.</p>

<p>The <em>router</em> field allow to apply a rule only on a particular router's services. The field is free text so that the user can specify routers that are possibly not currently part of the system. However, the interface proposes the routers currently involved in the system as hints. The <code>*</code> character must be used to specify that no filtering based on the router is wanted.</p>

<form class="well table-responsive" action="index.php?page=policy" method="POST">
  <fieldset>
  <legend>Rules</legend>

    <div class="table-responsive">
      <table id="rules-table" class="table table-bordered table-condensed">
      <thead>
        <tr>
          <th>Source IP</th>
          <th>Source Mask</th>
          <th>Name</th>
          <th>Type</th>
          <th>Router</th>
          <th>Action</th>
          <th colspan="3">Actions</th>
        </tr>
      </thead>

      <tbody>
        <?php
          // From http://stackoverflow.com/questions/2087103/innerhtml-in-phps-domdocument
          function DOMinnerHTML(DOMNode $element) 
          { 
              $innerHTML = ""; 
              $children  = $element->childNodes;

              foreach ($children as $child) 
              { 
                  $innerHTML .= $element->ownerDocument->saveHTML($child);
              }

              return $innerHTML; 
          } 

          for ($i = 1; $i <= $numberOfRules; $i++)
          {
            echo '<tr id="rule-'.$i.'">';
            echo '  <td><input type="text" name="src-address-'.$i.'" value="'.$rules->item($i-1)->getAttribute("src-address").'" required ></td>';
            echo '  <td><input type="number" value="'.$rules->item($i-1)->getAttribute("src-mask").'" name="src-mask-'.$i.'" min="0" max="128" required></td>';
            echo '  <td><input type="text" name="name-'.$i.'"    value="'.$rules->item($i-1)->getAttribute("name").'"           required /></td>';
            echo '  <td><input type="text" name="type-'.$i.'"    value="'.$rules->item($i-1)->getAttribute("type").'"           required /></td>';
            echo '  <td><input type="text" name="router-'.$i.'"    value="'.$rules->item($i-1)->getAttribute("router").'" list="routers"        required /></td>';
            echo '  <datalist id="routers">';
            foreach ($routers as $router)
              echo '   <option value="'.$router.'">';
            echo '     <option value="*">';
            echo '  </datalist>';
            echo '  <td><select name="action-'.$i.'">';
            echo '        <option value="allow"'; if (strtolower(trim(DOMinnerHTML($rules->item($i-1)))) == 'allow') echo 'selected'; echo '>Allow</option>';
            echo '        <option value="deny"';  if (strtolower(trim(DOMinnerHTML($rules->item($i-1)))) == 'deny')  echo 'selected'; echo '>Deny</option>';
            echo '      </select>';
            echo '  </td>';
            echo '  <td><span class="text-info glyphicon glyphicon-arrow-up"   onclick="moveRuleUp('.$i.');"></span></td>';
            echo '  <td><span class="text-info glyphicon glyphicon-arrow-down" onclick="moveRuleDown('.$i.');"></span></td>';
            echo '  <td><span class="text-danger glyphicon glyphicon-remove"   onclick="removeRule('.$i.');"></span></td>';
            echo '</tr>';
          }
        ?>
      </tbody>

      <tfoot>
        <tr>
          <td colspan="6"></td>
          <td colspan="3"><span onclick="addRule()" class="text-success glyphicon glyphicon-plus"></span></td>
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
    for ($i = 1; $i <= $numberOfRules; $i++)
    {
      if ($i == $numberOfRules)
        echo $i;
      else
        echo $i.',';
    }
    echo '"';
  ?>
  />
  <input type="submit" value="Submit" class="btn btn-primary" />
  <input type="reset"  value="Reset"  class="btn btn-default" onclick="location.reload();" />  

</form>
