<?php



if(!file_exists("user.csv")){
	print "missing user.csv";
	exit;	
}
if(!file_exists("user.csv")){
	print "missing user.csv";
	exit;	
}

if(!file_exists("en.csv")){
	print "missing audio_en.csv";
	exit;	
}

if(!file_exists("widgets.csv")){
	print "missing widgets.csv";
	exit;	
}

$dir_ar[0] = "output";
$dir_ar[1] = "output/audio";
$dir_ar[2] = "output/audio/en";
$dir_ar[3] = "output/audio/en/rtrc";
$dir_ar[4] = "output/audio/en/rtrc/system";
$dir_ar[5] = "output/scripts";
$dir_ar[6] = "output/scripts/rf2status";
$dir_ar[7] = "output/scripts/rf2status/sounds";
$dir_ar[8] = "output/scripts/rf2status/sounds/adjfunc";
$dir_ar[9] = "output/scripts/rf2status/sounds/alerts";
$dir_ar[10] = "output/scripts/rf2status/sounds/events";
$dir_ar[11] = "output/scripts/rf2status/sounds/alerts";
$dir_ar[12] = "output/scripts/rf2status/sounds/gov";
$dir_ar[13] = "output/scripts/rf2status/sounds/switches";
$dir_ar[14] = "output/scripts/rf2ethos/";
$dir_ar[15] = "output/scripts/rf2ethos/sounds/";

foreach($dir_ar as $v){
	if(!is_dir($v)){
		print($v . "\n");
		mkdir($v);	
	}
}

if(file_exists("tmpfile.wav")){
	unlink("tmpfile.wav");
}


// widgets
$count=0;
if (($handle = fopen("widgets.csv", "r")) !== FALSE) {
    while (($data = fgetcsv($handle, 1000, ",")) !== FALSE) {

		if($count >= 1){

		$filename = "output/" . $data[0];
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
				
				$cmd1 = 'sox -v 0.2 tmpfile.wav -b 16 -r 32000  tmpfile2.wav';	
				ob_start();
				system($cmd1);
				$out = ob_get_clean();

				$cmd2 = 'ffmpeg -y -i tmpfile2.wav -af "firequalizer=gain_entry=\'entry(0,20);entry(250,10);entry(1000,10);entry(4000,8);entry(16000,5)\'" ' . $filename;	
				ob_start();
				system($cmd2);
				$out = ob_get_clean();

												
				
			}	

		}
		$count++;
    }
    fclose($handle);
}

// user files
$count=0;
if (($handle = fopen("user.csv", "r")) !== FALSE) {
    while (($data = fgetcsv($handle, 1000, ",")) !== FALSE) {

		if($count >= 1){

		$filename = "output/" .$data[0];
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
				
				$cmd1 = 'sox -v 0.2 tmpfile.wav -b 16 -r 32000  tmpfile2.wav';	
				ob_start();
				system($cmd1);
				$out = ob_get_clean();

				$cmd2 = 'ffmpeg -y -i tmpfile2.wav -af "firequalizer=gain_entry=\'entry(0,20);entry(250,10);entry(1000,10);entry(4000,8);entry(16000,5)\'" ' . $filename;	
				ob_start();
				system($cmd2);
				$out = ob_get_clean();
												
				
			}	

		}
		$count++;
    }
    fclose($handle);
}

// system files
$count = 0;
if (($handle = fopen("en.csv", "r")) !== FALSE) {
    while (($data = fgetcsv($handle, 1000, ",")) !== FALSE) {

		if($count >= 1){

		$filename = "output/" . $data[0];
		$text = $data[1];
		
			if(trim($filename) != '' && trim($text) != ''){
				
				print $count ." - ".  $filename . "\n";
				flush();
				
				if(file_exists($filename)){
					unlink($filename);
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
				
				$cmd1 = 'sox -v 0.2 tmpfile.wav -b 16 -r 32000  tmpfile2.wav';	
				ob_start();
				system($cmd1);
				$out = ob_get_clean();

				$cmd2 = 'ffmpeg -y -i tmpfile2.wav -af "firequalizer=gain_entry=\'entry(0,20);entry(250,10);entry(1000,10);entry(4000,8);entry(16000,5)\'" ' . $filename;	
				ob_start();
				system($cmd2);
				$out = ob_get_clean();
						
				
			}	 
			
		}
		$count++;
    }
    fclose($handle);
}



if(file_exists("tmpfile.wav")){
	unlink("tmpfile.wav");
}


?>