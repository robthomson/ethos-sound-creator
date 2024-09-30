<?php


$volume = 0.4;


$file_list[] = 'user.csv';
$file_list[] = 'rfsuite.csv'; 
$file_list[] = 'en.csv'; 


print "Checking for csv files...";
foreach($file_list as $k=>$v){
        if(!file_exists($v)){
                print "\nError: Missing " . $v . "\n";
                exit;        
        } else {
                 print " [" . $v . "]";
                 $csv_list[] = $v;
        }
}


print "\n";

foreach ($csv_list as $file) {
        // widgets
        $count=0;
        if (($handle = fopen($file, "r")) !== FALSE) {
                while (($data = fgetcsv($handle, 1000, ",")) !== FALSE) {

                        if($data[1] != ""){
                                
                                

                        $filename = "output/" . $data[0];
                        $pathinfo = pathinfo($filename);
                        
                        $dirname = $pathinfo['dirname'];

                        if(!is_dir($dirname)){
                                mkdir($dirname,0777,true);        
                        }                
                
                        if(count($data) > 1){
                
                                $text = $data[1];
                                
                                        if(trim($filename) != '' && trim($text) != ''){
                                                
                                                print $count ." - ".  $filename . "\n";
                                                flush();

                                                if(file_exists('tmpfile.wav')){
                                                        unlink('tmpfile.wav');
                                                }
                                                if(file_exists('tmpfile.wav')){
                                                        unlink('tmpfile2.wav');
                                                }
                                                
                                                if(file_exists($filename)){
                                                        unlink($filename);
                                                }
                                                
                                                
                                                $cmd0 = 'ttscmd.exe  /ttw "'.$text.'" tmpfile.wav -v 16 -r 32 -b 32 -m m -s -2 -w 32 -q 0';                
                                                ob_start();
                                                system($cmd0);
                                                $out = ob_get_clean();
                                                
                                                $cmd1 = 'sox -v '.$volume.' tmpfile.wav -b 16 -r 32000  tmpfile2.wav';        
                                                ob_start();
                                                system($cmd1);
                                                $out = ob_get_clean();

                                                $cmd2 = 'ffmpeg -y -i tmpfile2.wav -af "firequalizer=gain_entry=\'entry(0,20);entry(250,10);entry(1000,10);entry(4000,8);entry(16000,5)\'" ' . $filename;        
                                                ob_start();
                                                system($cmd2);
                                                $out = ob_get_clean();

                                                if(file_exists("tmpfile.wav")){
                                                        unlink("tmpfile.wav");
                                                }                                                                
                                                
                                        }        

                                }
                        }        
                        $count++;
                }
                fclose($handle);
        }
}





?>