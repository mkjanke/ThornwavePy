Python script(s) to read data from Thornwave BT DCPM BlueTooth battery monitor <https://www.thornwave.com/>.

  * Requires functioning BlueTooth stack & gatttool.
  * Tested on Raspberry Pi 3b+ Raspbian 5.4 with default BT stack.

Setup:
  Use bluetoothctl to find BlueTooth MAC address of Thornwave device(s)
  
    sudo bluetoothctl
    [bluetooth]# scan on
    [NEW] Device D2:07:06:05:CB:1A
    
  Use bluetoothctl 'info' command to check for correct Thornwave.

  Test access to Thornwave using gatttool 

    sudo gatttool -b D2:07:06:05:CB:1A -I -t random
    [D2:07:06:05:CB:1A][LE]> connect
    Attempting to connect to D2:07:06:05:CB:1A
    Connection successful
    [D2:07:06:05:CB:1A][LE]> primary
    attr handle: 0x0001, end grp handle: 0x0009 uuid: 00001800-0000-1000-8000-00805f9b34fb
    attr handle: 0x000a, end grp handle: 0x000d uuid: 00001801-0000-1000-8000-00805f9b34fb
    attr handle: 0x000e, end grp handle: 0x0012 uuid: 0000180a-0000-1000-8000-00805f9b34fb
    attr handle: 0x0013, end grp handle: 0xffff uuid: 7a95ce00-0ea8-1bcc-71a2-fc7539b81c9c

  Verify UUID and handle

    [D2:07:06:05:CB:1A][LE]> char-desc
    [...lots of stuff...]
    handle: 0x0015, uuid: 7a95ce01-0ea8-1bcc-71a2-fc7539b81c9c
    [...lots more stuff...]

    [D2:07:06:05:CB:1A][LE]> char-read-hnd 0x15
    Characteristic value/descriptor: e0 ff 0f c6 51 a6 5b 41 02 b9 4d 41 5b 20 44 40 19 47 28 42 2d ed d7 41 d2 d2 02 00 00 00 00 00 fa 1f 00 00 00 00 00 00 31 70 23 00 a9 d2 0a 0e 91 dc 68 42

  The script will read and parse the data in 0x15.

Help:

    sudo ./thornwavepy -h
    
    usage: thornwave.py [-h] -b BLEADDRESS [-P | -H]
    Thornwave BT DCPM slurper. Reads and outputs BT DCPM data
    optional arguments:
      -h, --help            show this help message and exit
      -b BLEADDRESS, --BLEaddress BLEADDRESS
                            BT DCPM BLE Address
      -P, --Parsable        Machine parsable output (default)
      -H, --Human           Human readable output

To run:

    sudo ./thornwavepy -b <bluetooth address>

Notes:

  * bluetoothctl and gatttool may require sudo privs. The python script may also need sudo privs. 

