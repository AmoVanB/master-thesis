<!DOCTYPE html>
<html>
<head>
  <title>GUI for Policy Configuration</title>
  <meta charset="utf-8">
  <meta name="description" content="Web GUI for Service Discovery Configuration">
  <meta name="keywords" content="ulg,montefiore,vanbemten,van,bemten,amaury,master,thesis,service,mdns,dnssd,bonjour,zeroconf,cisco,vyncke,eric,leduc,guy">
  <meta name="author" content="Amaury Van Bemten">

  <!-- Image edited from 
  https://www.apple.com/support/assets/images/products/Bonjour/hero_bonjour.jpg
  -->
  <link rel="icon" href="style/images/bonjour.png">
  
  <!-- For mobiles: no initial zoom, use all space available. -->
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <!-- Bootstrap -->
  <link href="style/bootstrap/css/bootstrap.min.css" rel="stylesheet">
  <!-- Custom style -->
  <link href="style/style.css" rel="stylesheet">
</head>

<body>

  <!-- The header contains only the title 
       In a container-fluid so that it takes all available width. -->
  <div class="container-fluid">
    <div class="row">
      <header class="col-xs-12">
        <h1>Policy Configuration</h1>
        <?php
          // Advertise user if daemon is not running.
          if (!file_exists("/var/run/policy-manager/pid"))
          {
            echo '<p>Note: policy manager daemon is not running.</p>';
          }
          else
          {
            // Advertise user if config file has been changed.
            if (file_exists("/etc/policy-manager/config.xml")) // Should always be true.
              if (filemtime("/var/run/policy-manager/pid") < filemtime("/etc/policy-manager/config.xml"))
                echo '<p>Note: configuration file has been changed since daemon startup.</p>';
          }
        ?>
      </header>
    </div>
  </div>

  <!-- Rest of page in a container so that it does not necessarily take the
       entire width (visual effect). -->
  <div class="container">

    <!-- Navigation menu -->
    <div class="row">
      <nav class="col-xs-12">
        <ul class="nav nav-tabs nav-justified">
          <li role="presentation"<?php 
                if (!isset($_GET['page']))
                  echo ' class="active"';
              ?>>
            <a href="index.php">Index</a>
          </li>
          <li role="presentation"<?php
                if (isset($_GET['page']) && $_GET['page'] == 'status')
                  echo ' class="active"';
              ?>>
            <a href="index.php?page=status">Status</a>
          </li>
          <li role="presentation"<?php 
                if (isset($_GET['page']) && $_GET['page'] == 'policy')
                  echo ' class="active"';
              ?>>
            <a href="index.php?page=policy">Policy</a>
          </li>
          <li role="presentation"<?php 
                if (isset($_GET['page']) && $_GET['page'] == 'basic-configuration')
                  echo ' class="active"';
              ?>>
            <a href="index.php?page=basic-configuration">Basic Configuration</a>
          </li>
          <li role="presentation"<?php 
                if (isset($_GET['page']) && $_GET['page'] == 'logs')
                  echo ' class="active"';
              ?>>
              <a href="index.php?page=logs">Logs</a>
          </li>
        </ul>
      </nav>
    </div>

    <!-- Content -->
    <div class="row">
      <section class="col-xs-12">
      <?php
        /* Content included depending on $_GET['page']. If set to a valid value
           we include the corresponding page. Otherwise: welcome.php. */
        if((isset($_GET['page'])))
        {
          switch ($_GET['page'])
          {
            case 'policy':
            case 'status':
            case 'logs':
            case 'welcome':
            case 'basic-configuration':
              include $_GET['page'].'.php';
            break;

            default:
              include 'welcome.php';
            break;
          }
        }
        else
        {
          include 'welcome.php';
        }
      ?>
      </section>
    </div>

    <!-- Footer -->
    <div class="row">
      <footer class="col-xs-12">
        <p>Web interface developed as part of my master thesis <em>Using Service Discovery to Apply Policies in Networks</em> submitted in partial fulfillment of the requirements for the degree of MSc in Computer Science and Engineering at the University of Liège (2014-2015). <em>Amaury Van Bemten</em>.</p>
      </footer>
    </div>
  </div>

  <!-- Bootstrap core JS.
       Placed at the end of the document so the pages load faster. -->
  <script src="style/bootstrap/js/jquery.min.js"></script>
  <script src="style/bootstrap/js/bootstrap.min.js"></script>

</body>
</html>
