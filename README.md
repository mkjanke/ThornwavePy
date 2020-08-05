Python script(s) to read data from Thornwave BT DCPM BlueTooth battery monitor <https://www.thornwave.com/>.

  * Requires functioning BlueTooth stack & gatttool.
  * Tested on Raspberry Pi 3b+ Raspbian 5.4 with default BT stack.

Inspiration and data format credit to Stuart Wilde via this forum post:
    https://www.irv2.com/forums/f54/thornwave-battery-monitor-375463.html#post4215155

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

Data Format:

  Fields
  
     0 - 2:  Unknown
     3    :  Pect Charged, LSB must be stripped
     7 - 4:  V1 volts, LSB, 32-bit float
    11 - 8:  V2 volts, LSB, 32-bit float
    15 - 12: Current (amps), LSB, 32-bit float
    19 - 16: Power (watts), LSB, 32-bit float
    23 - 20: Temperature (C), LSB, 32-bit float
    31 - 24: Power Meter (watts * 1000), 64-bit int
    39 - 32: Charge Meter (Amp-hours * 1000), 64-bit int
    43 - 40: Uptime (seconds), unsigned 32-bit int
    47 - 44: Date/Time (unknown format)
    51 - 48: Peak Current, 32-bit float
    52+    : Unknown

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
  * To create log, run periodically from cron & pipe outputto a file with >>

