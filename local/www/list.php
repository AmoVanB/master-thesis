<script>
  // Statistics are initially hidden.
  window.onload = function() { $('#stats').hide(); };
</script>

<p><button class="btn-link" onclick="$('#stats').toggle();">Show/hide stats.</button></p>

<div id="stats" class="container-fluid">
  <div class="row">
    <div class="col-md-6">
      <div class="row">
        <div class="col-md-offset-1 col-md-10 stats-box">

          <h4>Interface stats</h4>
          <?php
            echo '<ul>'; 
            $sql = 'SELECT if_name, COUNT(*) AS nb FROM services GROUP BY if_name ORDER BY nb DESC';

            foreach ($db->query($sql) as $row)
            {
              $sql_v4  = 'SELECT COUNT(*) FROM services WHERE if_ip = 4 AND if_name = "'.$row['if_name'].'"';
              $v4 = $db->query($sql_v4)->fetchColumn();
              $sql_v6  = 'SELECT COUNT(*) FROM services WHERE if_ip = 6 AND if_name = "'.$row['if_name'].'"';
              $v6 = $db->query($sql_v6)->fetchColumn();
              $sql_v4_announced  = 'SELECT COUNT(*) FROM services WHERE if_ip = 4 AND announced = 1 AND if_name = "'.$row['if_name'].'"';
              $v4_announced = $db->query($sql_v4_announced)->fetchColumn();
              $sql_v6_announced  = 'SELECT COUNT(*) FROM services WHERE if_ip = 6 AND announced = 1 AND if_name = "'.$row['if_name'].'"';
              $v6_announced = $db->query($sql_v6_announced)->fetchColumn();

              $total = $v4 + $v6;
              $total_announced = $v4_announced + $v6_announced;

              if ($total == 0)
              {
                $perc_v4 = 0;
                $perc_v6 = 0;
              }
              else
              {
                $perc_v4 = round($v4/$total*100, 2);
                $perc_v6 = round($v6/$total*100, 2);
              }    

              if ($total_announced == 0)
              {
                $perc_v4_announced = 0;
                $perc_v6_announced = 0;
              }
              else
              {
                $perc_v4_announced = round($v4_announced/$total_announced*100, 2);
                $perc_v6_announced = round($v6_announced/$total_announced*100, 2);
              }    

              
              echo '<li><strong>'.$row["if_name"].'</strong>';

              echo '<ul>';
              echo '<li>'.$total.' ('.$perc_v4.'% IPv4, '.$perc_v6.'% IPv6) services discovered,</li>';
              echo '<li>'.$total_announced.' ('.$perc_v4_announced.'% IPv4, '.$perc_v6_announced.'% IPv6) services announced.</li>';
              echo '</ul>';
            }
            echo '</ul>';
          ?>
        </div>
      </div>
    </div>

    <div class="col-md-6">
      <div class="row">
        <div class="col-md-offset-1 col-md-10 stats-box">

          <h4>General stats</h4>
          <?php
            $tot = $db->query('SELECT COUNT(*) FROM services');
            $nb_services = $tot->fetchColumn();
            $resolved = $db->query('SELECT COUNT(*) FROM services WHERE resolved = 1');
            $nb_resolved = $resolved->fetchColumn();
            $announced = $db->query('SELECT COUNT(*) FROM services WHERE announced = 1');
            $nb_announced = $announced->fetchColumn();

            echo '<ul>';
            echo '<li>'.$nb_services.' discovered services';
            if ($nb_services == 0)
              echo '.</li>'; 
            else
            { 
              echo ' among which';
              echo '<ul>';
              echo '<li>'.$nb_resolved.' ('.round($nb_resolved/$nb_services*100, 2).'%) have been resolved,'
                 , '</li>';
              echo '<li>'.$nb_announced.' ('.round($nb_announced/$nb_services*100, 2).'%) have been announced.'
                 , '</li>';
              echo '</ul>';
              
              echo '</li>';
            }

            if ($nb_services != 0 && $nb_resolved != 0)
              echo '<li>'.round($nb_announced/$nb_resolved*100, 2).'% of the resolved services have been announced.</li>';

            $sql_v4  = 'SELECT COUNT(*) FROM addresses WHERE ip = 4';
            $v4 = $db->query($sql_v4)->fetchColumn();
            $sql_v6  = 'SELECT COUNT(*) FROM addresses WHERE ip = 6';
            $v6 = $db->query($sql_v6)->fetchColumn();

            $total = $v4 + $v6;

            if ($total == 0)
            {
              $perc_v4 = 0;
              $perc_v6 = 0;
            }
            else
            {
              $perc_v4 = round($v4/$total*100, 2);
              $perc_v6 = round($v6/$total*100, 2);
            }    
            echo '<li>'.$total.' ('.$perc_v4.'% IPv4, '.$perc_v6.'% IPv6) discovered addresses.</li>';
            echo '</ul>';
          ?>

        </div>
      </div>
    </div>

  </div>

  <div class="row">
    
    <div class="col-md-6">
      <div class="row">
        <div class="col-md-offset-1 col-md-10 stats-box">

          <h4>Services types stats</h4>
          <?php
            echo '<ul>'; 
            $sql = 'SELECT type, COUNT(*) AS nb FROM services GROUP BY type ORDER BY nb DESC';

            foreach ($db->query($sql) as $row)
            {
              $sql_v4  = 'SELECT COUNT(*) FROM services WHERE if_ip = 4 AND type = "'.$row['type'].'"';
              $v4 = $db->query($sql_v4)->fetchColumn();
              $sql_v6  = 'SELECT COUNT(*) FROM services WHERE if_ip = 6 AND type = "'.$row['type'].'"';
              $v6 = $db->query($sql_v6)->fetchColumn();
              $sql_v4_announced  = 'SELECT COUNT(*) FROM services WHERE if_ip = 4 AND announced = 1 AND type = "'.$row['type'].'"';
              $v4_announced = $db->query($sql_v4_announced)->fetchColumn();
              $sql_v6_announced  = 'SELECT COUNT(*) FROM services WHERE if_ip = 6 AND announced = 1 AND type = "'.$row['type'].'"';
              $v6_announced = $db->query($sql_v6_announced)->fetchColumn();

              $total = $v4 + $v6;
              $total_announced = $v4_announced + $v6_announced;

              if ($total == 0)
              {
                $perc_v4 = 0;
                $perc_v6 = 0;
              }
              else
              {
                $perc_v4 = round($v4/$total*100, 2);
                $perc_v6 = round($v6/$total*100, 2);
              }    

              if ($total_announced == 0)
              {
                $perc_v4_announced = 0;
                $perc_v6_announced = 0;
              }
              else
              {
                $perc_v4_announced = round($v4_announced/$total_announced*100, 2);
                $perc_v6_announced = round($v6_announced/$total_announced*100, 2);
              }    

              
              echo '<li><strong>'.$row["type"].'</strong>';

              echo '<ul>';
              echo '<li>'.$total.' ('.$perc_v4.'% IPv4, '.$perc_v6.'% IPv6) discovered,</li>';
              echo '<li>'.$total_announced.' ('.$perc_v4_announced.'% IPv4, '.$perc_v6_announced.'% IPv6) announced.</li>';
              echo '</ul>';
            }
            echo '</ul>';
          ?>
        </div>
      </div>
    </div>

    <div class="col-md-6">
      <div class="row">
        <div class="col-md-offset-1 col-md-10 stats-box">

          <h4>Hostnames stats</h4>
          <?php
            echo '<ul>'; 
            $sql = 'SELECT hostname, if_ip, if_name, COUNT(*) AS nb FROM services GROUP BY hostname, if_ip, if_name ORDER BY nb DESC';

            foreach ($db->query($sql) as $row)
            {
              if ($row["hostname"] == Null)
                continue;

              $sql_v4  = 'SELECT COUNT(*) FROM addresses WHERE if_ip = '.$row["if_ip"].' AND if_name = "'.$row["if_name"].'" AND hostname = "'.$row["hostname"].'" AND ip = 4';
              $v4 = $db->query($sql_v4)->fetchColumn();
              $sql_v6  = 'SELECT COUNT(*) FROM addresses WHERE if_ip = '.$row["if_ip"].' AND if_name = "'.$row["if_name"].'" AND hostname = "'.$row["hostname"].'" AND ip = 6';
              $v6 = $db->query($sql_v6)->fetchColumn();

              $sql_services_announced = 'SELECT COUNT(*) FROM services WHERE if_ip = '.$row["if_ip"].' AND if_name = "'.$row["if_name"].'" AND hostname = "'.$row["hostname"].'" AND announced = 1';
              $services_announced =  $db->query($sql_services_announced)->fetchColumn();

              echo '<li><strong>'.$row["hostname"].'</strong> ('.$row["if_name"].' - IPv'.$row["if_ip"].')';

              echo '<ul>';
              echo '<li>'.$v4.' IPv4 addresses,</li>';
              echo '<li>'.$v6.' IPv6 addresses,</li>';
              echo '<li>'.$row["nb"].' discovered services,</li>';
              echo '<li>'.$services_announced.' announced services.</li>';
              echo '</ul>';
            }
            echo '</ul>';
          ?>

        </div>
      </div>
    </div>
  </div>
</div>

<?php
  /* Getting the sorting value and order. */
  if (isset($_GET['sort']))
    $sort = htmlspecialchars($_GET['sort']);
  else
    $sort = 'instance_name';

  if (isset($_GET['order']))
    $order = htmlspecialchars($_GET['order']);
  else
    $order = 'asc';

  if ($order != 'desc')
    $order = 'asc';

  /* For the moment, the sorting value is not valid. We will compare it to
   * the table fields and if a match occurs, 'sort_valid' will be set to true
   */
  $sort_valid = false;
?>

<p>
  This page lists all the services discovered on the local network. <br />
  <strong class="text-default">Uncoloured</strong> services are resolved but not announced,<br />
  <strong class="text-success">green</strong> services are announced,<br />
  <strong class="text-danger">red</strong> services are unresolved and<br />
<strong class="text-warning">orange</strong> services are resolved except their IP address.
</p>


<!-- Displaying sorting value and order. -->
<p>
  Services are displayed in
  <?php if ($order == 'desc')
          echo 'decreasing';
        else
          echo 'increasing';
  ?> 
  order of 
  <?php echo '<code>'.$sort.'</code>.'; ?>
</p>

<!-- The table listing the services. -->
<div class="table-responsive">
  <table class="table table-bordered table-condensed">
    <thead>
      <?php
        // Displaying field names.
        echo '<tr>';
        foreach (array('if_name', 'if_ip', 'name', 'type', 'hostname', 'port') as $field)
        {
          // Variables to enable sorting when clicking on a column header.
          $supp = '';
          if ($sort == $field && $order == 'asc')
            $supp = "&order=desc";  
          elseif ($sort == $field && $order == 'desc')
            $supp = "&order=asc";  
          elseif ($sort == $field)
            $supp = "&order=desc";  

          echo '<th><a href="index.php?page=list&sort='.$field.$supp.'">'.$field.'</a></th>';

          // Checking if the sorting value matches the actual value.
          if ($sort == $field)
            $sort_valid = true;
        }
        echo '</tr>';
      ?>
    </thead>

    <tbody>
      <?php
        // We now know if the sorting value is valid or not. 
        if (!$sort_valid)
          $sort = 'name';

        // Displaying entries.
        $sql = 'SELECT * FROM services ORDER BY UPPER('.$sort.') '.$order;

        foreach ($db->query($sql) as $tuple)
        {
          if ($tuple['announced'] == 1)
            echo '<tr class="success">';
          else if ($tuple['resolved'] == 0 && $tuple['hostname'] != NULL)
            echo '<tr class="warning">';
          else if ($tuple['resolved'] == 0 && $tuple['hostname'] == NULL)
            echo '<tr class="danger">';
          else
            echo '<tr class="active">';

          foreach (array('if_name', 'if_ip', 'name', 'type', 'hostname', 'port') as $field)
            echo '<td>'.$tuple[$field].'</td>';

          echo '</tr>';
        }
      ?>
    </tbody>
  </table>
</div>
