<?php
  // Here is where we start pulling station Information

  $connection = iemdb("mesosite");
  $query1 = "SELECT oid, *, to_char(valid, 'YYYY/MM/YYMMDD') as imageref, 
                to_char(valid, 'DD Mon YYYY HH:MI AM') as webdate from feature
                ORDER by valid DESC LIMIT 1";
  $result = pg_exec($connection, $query1);
  $row = @pg_fetch_array($result,0);
  $foid = $row["oid"];
  $good = intval($row["good"]);
  $bad = intval($row["bad"]);
  /* Hehe, check for a IEM vote! */
  if (array_key_exists('foid', $_SESSION) && $_SESSION["foid"] == $foid)
  {

  } elseif (getenv("REMOTE_ADDR") == "129.186.142.22") 
  {

  } elseif (isset($_GET["feature_good"]))
  {
    $_SESSION["foid"] = $foid;
    $isql = "UPDATE feature SET good = good + 1 WHERE oid = $foid";
    $good += 1;
    pg_exec($connection, $isql);
  } elseif (isset($_GET["feature_bad"]))
  {
    $_SESSION["foid"] = $foid;
    $isql = "UPDATE feature SET bad = bad + 1 WHERE oid = $foid";
    $bad += 1;
    pg_exec($connection, $isql);
  }


  $fref = "/mesonet/share/features/". $row["imageref"] ."_s.gif";
  list($width, $height, $type, $attr) = @getimagesize($fref);
  $width += 2;

  $s = "<b>". $row["title"] ."</b><br />\n";
  $s .= "<div style=\"float: right; border: 1px solid #000; padding: 3px; margin: 5px; width: ${width}px;\"><a href=\"$rooturl/onsite/features/". $row["imageref"] .".gif\"><img src=\"$rooturl/onsite/features/". $row["imageref"] ."_s.gif\" alt=\"Feature\" /></a>";

  $s .= "<br />". $row["caption"] ."</div>";

  $s .= $row["webdate"] ."\n";
  $s .= "<br /><div class='story'>". $row["story"] ."</div>";
  $s .= "<br style=\"clear: right;\" /><b>Rate Feature:</b> <a href=\"$rooturl/index.phtml?feature_good\">Good</a> ($good votes) or <a href=\"$rooturl/index.phtml?feature_bad\">Bad</a> ($bad votes) &nbsp; &nbsp;<a href=\"$rooturl/onsite/features/past.php\">Past Features</a>";

if (getenv("REMOTE_ADDR") == "206.61.97.204" )
{
 $s = "<img src=\"images/smokey_1021.jpg\" style=\"float: left; margin: 5px;\">
Smokey, muah! <br /> &nbsp; &nbsp; &nbsp; &nbsp; 79 weeks now!  I am glad you have having a great time in Oklahoma and I can't wait to have you back in Ames. I love you very much.  <br /> Muah! . <br />&nbsp; &nbsp; &nbsp; &nbsp;   &nbsp; &nbsp; &nbsp; &nbsp;  love, darly";
}

echo $s;
?>
