<p>This page displays the current status of the network, i.e. the list of routers involved in the system and the services announced in their subdomain.</p>


<div class="table-responsive panel panel-default">

<?php

$domain = 'amo.vyncke.org.';

$routers_results = dns_get_record( '_routers._dns-sd._udp.'.$domain, DNS_PTR);

if (sizeof($routers_results) == 0)
    echo '<div class="panel-heading">No routers found.</div>';
else
{
  $i = 0;
  foreach ($routers_results as $router_entry)
  {
    $i++;
    echo '<div class="panel-heading" onclick="$(\'#routers-'.$i.'\').toggle();">'.$router_entry['target'].'</div>';

    echo '<table class="table table-bordered table-condensed" id="routers-'.$i.'">';

    $type_results = dns_get_record('_services._dns-sd._udp.'.$router_entry['target'], DNS_PTR);

    if (sizeof($type_results) == 0)
      echo '<thead><tr><th>No types found.</th></tr></thead>';
    else
    {
      $j = 0;
      foreach ($type_results as $type_entry)
      {
        $j++;
        echo '<thead onclick="$(\'#types-'.$j.'\').toggle();">';
        echo '<tr><th colspan="4"><em>'.$type_entry['target'].'</em></th></td>';
        echo '</thead>';

        echo '<tbody id="types-'.$j.'">';

        $service_results = dns_get_record($type_entry['target'], DNS_PTR);

        if (sizeof($service_results) == 0)
          echo '<tr><td>No services found.</td></tr>';
        else
        {
          foreach ($service_results as $service_entry)
          {
            $srv_results  = dns_get_record($service_entry['target'], DNS_SRV);
            $aaaa_results = dns_get_record($srv_results[0]['target'], DNS_AAAA);
            $a_results    = dns_get_record($srv_results[0]['target'], DNS_A);

            if (sizeof($srv_results) == 0)
            {
              $hostname = 'Not found.';
              $port     = 'Not found.';
            }
            else
            {
              $hostname = $srv_results[0]['target'];
              $port     = $srv_results[0]['port'];
            }
    
            $addresses = "";  
            if (!(sizeof($aaaa_results) == 0))
              foreach($aaaa_results as $aaaa_entry)
                $addresses = $addresses . $aaaa_entry['ipv6'] . ', ';

            if (!(sizeof($a_results) == 0))
              foreach($a_results as $a_entry)
                $addresses = $addresses . $a_entry['ip'] . ', ';

            $addresses = substr($addresses, 0, -2);          

            echo '<tr>';
            echo '<td>'.urldecode(substr($service_entry['target'], 0, - 1 - strlen($type_entry['target']))).'</td>';
            echo '<td>'.substr($hostname, 0, - 1 - strlen($router_entry['target'])).'</td>';
            echo '<td>'.$port.'</td>';
            echo '<td>'.$addresses.'</td>';
            echo '</tr>';
          }
        }

        echo '</tbody>';
      }

    }

    echo '</table>';
  }
}

?>

</div>
