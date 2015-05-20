<p>This page displays the current status of the network, i.e. the list of routers involved in the system and the services announced in their respective subdomains.</p>

<p>To ease debugging, no caching is implemented. Each time the page is refreshed, new DNS queries are performed.</p>

<p>Click on a router's subdomain or on a particular type to show/hide the corresponding services.</p>

<div class="table-responsive panel panel-default">

<?php

// Getting domain name.
try
{
  $dom = new DomDocument();
  $dom->load('/etc/policy-manager/config.xml');
  $domain_tag = $dom->getElementsByTagName('domain')->item(0);
  $domain = $domain_tag->getAttribute('name');
}
catch (Exception $e)
{
  echo '<p>Error: '.$e->getMessage().'</p>';
}

// Getting list of routers.
$routers_results = dns_get_record('b._dns-sd._udp.'.$domain, DNS_PTR);
if (sizeof($routers_results) == 0)
    echo '<div class="panel-heading">No routers found.</div>';
else
{
  $i = 0; // Routers indexes.
  $j = 0; // Service types indexes.
  foreach ($routers_results as $router_entry)
  {
    $i++;
    // For each router: a div containing a table.
    echo '<div class="panel-heading" onclick="$(\'#routers-'.$i.'\').toggle();">'.$router_entry['target'].'</div>';
    echo '<table class="table table-bordered table-condensed" id="routers-'.$i.'">';

    // Getting the service types at the router.
    $type_results = dns_get_record('_services._dns-sd._udp.'.$router_entry['target'], DNS_PTR);
    if (sizeof($type_results) == 0)
      echo '<thead><tr><th>No types found.</th></tr></thead>';
    else
    {
      foreach ($type_results as $type_entry)
      {
        $j++;
        // For each service type, a header in the table.
        echo '<thead onclick="$(\'#types-'.$j.'\').toggle();">';
        echo '<tr><th colspan="4"><em>'.$type_entry['target'].'</em></th></td>';
        echo '</thead>';

        echo '<tbody id="types-'.$j.'">';

        // Getting services names of the given type.
        $service_results = dns_get_record($type_entry['target'], DNS_PTR);
        if (sizeof($service_results) == 0)
          echo '<tr><td>No services found.</td></tr>';
        else
        {
          foreach ($service_results as $service_entry)
          {
            // For each service, a line in the table.
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
    
            // Concatenating addresses in a single string.
            $addresses = "";  
            if (!(sizeof($aaaa_results) == 0))
              foreach($aaaa_results as $aaaa_entry)
                $addresses = $addresses . $aaaa_entry['ipv6'] . ', ';

            if (!(sizeof($a_results) == 0))
              foreach($a_results as $a_entry)
                $addresses = $addresses . $a_entry['ip'] . ', ';

            // Removing the last ', '
            $addresses = substr($addresses, 0, -2);          

            echo '<tr>';
            // Manual unescaping of DNS name as no automatic function found.
            // Full table: http://www.utf8-chartable.de/unicode-utf8-table.pl
            $service_entry['target'] = str_replace('\032', ' ', $service_entry['target']);
            $service_entry['target'] = str_replace('\195\169', 'é', $service_entry['target']);
            $service_entry['target'] = str_replace('\195\168', 'è', $service_entry['target']);
            $service_entry['target'] = str_replace('\194\171', '«', $service_entry['target']);
            $service_entry['target'] = str_replace('\194\187', '»', $service_entry['target']);
            $service_entry['target'] = str_replace('\194\160', ' ', $service_entry['target']);
            echo '<td>'.substr(stripslashes($service_entry["target"]), 0, - 1 - strlen($type_entry['target'])).'</td>';
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
