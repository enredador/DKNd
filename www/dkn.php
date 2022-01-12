<html><head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
</head>
<style>
  * {
      font-size: 18pt;
      font-family; sans-serif;
      padding: 2px;
  }

  td {
      padding: 10px 30px 10px 30px;
      vertical-align: middle;
  }
  select {
      appearance: none;
      font-size:0.6em;
      -webkit-appearance: none;
      -moz-appearance: none;
      border-radius: 0;
      border-style:none none solid none;
      border-bottom: 1px solid #aaa;
      background-color:none;
      background-image: url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%23007CB2%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E') ; #, linear-gradient(to bottom, #ffffff 0%,#f7f7f7 100%);
      background-repeat: no-repeat, repeat;
      background-position: right .2em top 50%, 0 0;
      background-size: .4em auto, 100%;
      padding-right: 15px;
  }
  option {
      text-align: center;
  }
</style>
<?php
  $DIR = "/var/www/html/lib/";
  $BIN = "/home/pi/bin/";
  $CNF = $DIR . "DKN.yaml";
  $DCT = $DIR . "DKN.dict";
  $DKN = $BIN . "DKN.py";
  $D2J = $BIN . "DKNdict2json.py";
  $J2D = $BIN . "DKNjson2dict";
  $JSN = $DIR . "DKN.json";
#  $SCH = "CHlistCool CHlistHeat DHWlistHeat";
  $SCH = "DHWlistHeat";

  $LOADSCRIPT  = $DKN . " --config " . $CNF . " schedules_get " . $SCH . " | " .
                   $D2J . " > " . $JSN;
  $STORESCRIPT = $BIN . "DKNupload";

  function compare_times ($arg1, $arg2) {
    return ($arg1["h"]*100 + $arg1["m"]) - ($arg2["h"]*100 + $arg2["m"]);
  }

  function key_h_m ($arg) {
    return ($arg["h"]*100 + $arg["m"]);
  }

  if ($_POST["reload"] != "") {
    exec($LOADSCRIPT);
  }

  if ($_POST["upload"] != "") {
    exec($STORESCRIPT);
  }

  $pr  = $_POST["pr"];
  $gestor = fopen ($JSN, "r");
  $json = fread($gestor, filesize($JSN));
  fclose($gestor);
  $diccionario = json_decode($json, true);
  $maxactions = array('CHlistHeat' => 6, 'CHlistCool' => 6, 'DHWlistHeat' => 4);
  $temps_dhw = array( '0' => 'ECO', '1' => 'COM');
  $temps_calef = array( '0' => 'ECO', '1' => 'COM');
  for( $i = 150; $i < 255; $i = $i + 5){
    $temps_calef[$i] = $i/10 . ' ºC';
  }
  $temps_ref = array( '0' => 'ECO', '1' => 'COM');
  for( $i = 220; $i < 355; $i = $i + 5){
    $temps_ref[$i] = $i/10 . ' ºC';
  }
  $temps = array('CHlistHeat'  => $temps_calef,
  	           'CHlistCool'  => $temps_ref,
  	     	   'DHWlistHeat' => $temps_dhw);

  $days = explode("," , "L,M,X,J,V,S,D");
  for( $i = 0; $i < 24; $i++){
    $hors[$i] = $i . ' h';
  }
  $mins = array (0 => '00 m', 10 => '10 m', 20 => '20 m', 30 => '30 m', 40 => '40 m', 50 => '50 m');

  if ($pr != ""){
     $type   = explode(":",$pr)[0];
     $typet  = explode(":",$pr)[1];
     $progid =  explode(":",$pr)[2];
     $maxact = $maxactions[$type];
  }       
  if ( $_POST["new"] != "") {
    for ($day = 0; $day < 7; $day++){
      for ($i = 0; $i< $maxact; $i++){
	  if (($_POST['h'.$day.$i] != "") && ($_POST['m'.$day.$i] != "") && ($_POST['t'.$day.$i] != "")) {
	       $diccionario[$type][$progid]["actions"][$day][$i]["h"] = intval($_POST['h'.$day.$i]);
	       $diccionario[$type][$progid]["actions"][$day][$i]["m"] = intval($_POST['m'.$day.$i]);
	       $diccionario[$type][$progid]["actions"][$day][$i]["t"] = $_POST['t'.$day.$i];
	  }
	  if ( $_POST['d'.$day.$i] != "")
	       unset($diccionario[$type][$progid]["actions"][$day][$i]);
      }
      usort($diccionario[$type][$progid]["actions"][$day], 'compare_times');
      if (count($diccionario[$type][$progid]["actions"][$day]) > 1) {
        $temp = array();
        $new = array();
        foreach ( $diccionario[$type][$progid]["actions"][$day] as $key=>$value) {
          $k = key_h_m($value);
          if ( !in_array($k , $temp)){
            $temp[] = $k;
            $new[] = $value;
          }
        }
        $diccionario[$type][$progid]["actions"][$day] = $new;
      }
    }
  $out_json = json_encode($diccionario, JSON_FORCE_OBJECT|JSON_PRETTY_PRINT);
  $out_json = $out_json . "\n";
  $gestor = fopen ($JSN, "w");
  fwrite($gestor, $out_json, strlen($out_json));
  fclose($gestor);
  }
?>
<body>
<!--<h1 style="text-align: center;font-size: 24pt;">Detalles de los programas</h1>-->

<table>
<tr>
<!-- SELECT PROGRAM TO EDIT -->
<td><form action="#" method="post">
<label style="font-size:0.8em;" for="pr">Programa: </label>
<select id="pr" name="pr" style="width:250px" onchange="this.form.submit()">
<?php
  if ( $pr == "" ) echo '<option selected value="" name=""></option>';
  foreach ($diccionario as $ty=>$programlist) {
    if ($ty == "CHlistHeat")  $tyt = "Calefacción";
    if ($ty == "CHlistCool")  $tyt = "Refrescamiento";
    if ($ty == "DHWlistHeat") $tyt = "Agua caliente";
    ksort($diccionario[$ty]);
    foreach ($programlist as $key=>$value){
     if (! $value["predefined"]) {
       echo '<option';
       if ( $value["name"] == explode(":", $pr)[1]) echo ' selected ';
       echo ' value="' . $ty . ":" . $value["name"] . ":" . $key . '">' . $tyt . " - " .
            $value["name"]. '</option>' ;
     }  
    }
  }
?>
</select>
</form></td>
<?php
 if ($pr != "") {
   echo '<td><form  action="#" method="post">' .
        '<input type="submit" value="Reload">' .
        '<input type="hidden" name="reload" value="new">' .
        '</form></td>';

   echo '<td><form  action="#" method="post">' .
        '<input type="submit" value="Update Altherma">' .
        '<input type="hidden" name="upload" value="new">' .
        '</form></td>';
 }
?>
</tr></table>

<!-- SHOW PROGRAM DETAILS -->
<form  action="#" method="post">
<table cellspacing="5" cellpadding="0" border="0"> <tbody>
<?php
if ($pr != ""){
 echo '<tr><td/>';
 for ($i = 1; $i < $maxact + 1; $i++){
   echo '<td style="text-align: center;color: grey; font-size:1.5em">--- ' . $i . ' ---</td>';
 }
 echo '</tr>';

 foreach ($diccionario[$type] as $prid=>$program){
   if ( $prid == $progid ){
     ksort($diccionario[$type][$prid]["actions"]);
     foreach ($diccionario[$type][$prid]["actions"] as $day=>$actions){
        echo '<tr><td style="text-align: center;font-size: 2em; color: grey;">' .$days[$day] . '</td>';
	ksort($actions);
	for ($i = 0; $i < $maxact; $i++){
          if ( array_key_exists($i, $actions) ){
	    $h = $actions[$i]["h"];
	    $m = $actions[$i]["m"];
      	    $t = $actions[$i]["t"];
            echo '<td>' .
            '<label  for"h' . $day . $i . '" style="font-size:0.6em">At:</label>' .
	    '<select id="h' . $day . $i . '" name="h' . $day . $i . '">';
	    foreach ($hors as $key=>$value) {
	      echo '<option value="' . $key . '"';
	      if ($h == $key) echo ' selected ';
  	      echo '>' . $value . '</option>';
	    }
	    echo  '</select>';
	    echo ":".
	    '<select id="m' . $day . $i . '" name="m' . $day . $i . '">';
	    foreach ($mins as $key=>$value) {
	      echo '<option value="' . $key . '"';
	      if ($m == $key) echo ' selected ';
  	      echo '>' . $value . '</option>';
	    }
	    echo  '</select><br>';
	    echo "" .
            '<label  for"t' . $day . $i . '" style="font-size:0.6em">Set:</label>' .
	    '<select id="t' . $day . $i . '" name="t' . $day . $i . '">';
	    foreach ($temps[$type] as $key=>$value) {
	      echo '<option value="' . $key . '"';
	      if ($t == $key) echo ' selected ';
	      echo '>'. $value . '</option>';
	    }
	    echo  '</select>';
            echo '<input type="checkbox" id="d' . $day . $i . '" name="d' . $day . $i . '" value="on">' .
            '<label for="d' . $day . $i . '" style="font-size: .6em;">(borrar)</label>' .            
            '</td>';
	  } else {
              echo '<td>' .
              '<label  for"h' . $day . $i . '" style="font-size:0.6em">At:</label>' .
  	      '<select style="background-color:lightgrey;" id="h' . $day . $i . '" name="h' . $day . $i . '">';
	      echo '<option value=""></option>';
	      foreach ($hors as $key=>$value) {
	        echo '<option value="' . $key . '"';
  	        echo '>' . $value . '</option>';
	      }
	      echo  '</select>';
	      echo ":".
	      '<select style="background-color:lightgrey;" id="m' . $day . $i . '" name="m' . $day . $i . '">';
	      echo '<option value=""></option>';
	      foreach ($mins as $key=>$value) {
	        echo '<option value="' . $key . '"';
  	        echo '>' . $value . '</option>';
	      }
	      echo  '</select><br>';
 	      echo "" .
              '<label  for"t' . $day . $i . '" style="font-size:0.6em">Set:</label>' .
     	      '<select style="background-color:lightgrey;" id="t' . $day . $i . '" name="t' . $day . $i . '">';
	      echo '<option value=""></option>';
   	      foreach ($temps[$type] as $key=>$value) {
  	        echo '<option value="' . $key . '"';
  	        echo '>'. $value . '</option>';
	      }
   	      echo '</select></td>';
	  } 
	}
	echo  '</tr>';
     }  
   }
 }
}
?>
</tbody></table>
<?php
  if ($pr != "") {
  echo '<input type="hidden" name="pr" value="' . $pr .'">' .
       '<input type="hidden" name="new" value="new">' .
       '<input type="submit" value="Set" style="margin-left:4em; margin-top:2em;">';
  }
?>
</form>

</body>
</html>
