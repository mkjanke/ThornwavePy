#!/usr/bin/python3

#	Copyright 2020 Michael Janke
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>
#
#	Inspiration and data format credit to Stuart Wilde via this forum post:
#		https://www.irv2.com/forums/f54/thornwave-battery-monitor-375463.html#post4215155
#
#	2020-08-05	V 0.1 - Initial
#

import argparse
import subprocess
import sys
import struct
from datetime import datetime

# Slurp up command line arguments
__author__ = 'Michael Janke'
parser = argparse.ArgumentParser(description='Thornwave BT DCPM slurper. Reads and outputs BT DCPM data')
group = parser.add_mutually_exclusive_group()
parser.add_argument("-b", "--BLEaddress", help="BT DCPM BLE Address", required=True)

group.add_argument("-P", "--Parsable", help="Machine parsable output (default)", action="store_true")
group.add_argument("-H", "--Human", help="Human readable output", action="store_true")

args = parser.parse_args()

timeNow = (datetime.now()).strftime("%d/%m/%Y %H:%M:%S")

# Shell out and use gatttool to read from Thornwave BT-DCPM
# -b is mac address of Thornwave 
# 0x15 is apparent attribute
#
result = subprocess.run(['sudo','gatttool','-b', args.BLEaddress,'-t','random','--char-read','-a','0x15'], capture_output=True, text=True )

# If no output, bail out silently
#
if len(result.stdout) < 64 :
	exit()

# Strip out leading descriptive text "Charateristic.... from gatttool output"
# Split string into byte representations
# Stuff into list
#
# stdout from gatttool is string of bytes with preceding text description:
# Characteristic value/descriptor: e0 81 03 a0 7f 91 56 41 a5 62 48 41 d6 e3 aa  ... ...
#
# Split string is a list of character pairs representing bytes:
# ['e0', '81', '03', 'a0', '7f', '91', '56', '41', 'a5', '62', '48', ... ... ...]
#
# Fields
#  0 - 2:  Unknown
#  3    :  Pect Charged, LSB must be stripped
#  7 - 4:  V1 volts, LSB, 32-bit float
# 11 - 8:  V2 volts, LSB, 32-bit float
# 15 - 12: Current (amps), LSB, 32-bit float
# 19 - 16: Power (watts), LSB, 32-bit float
# 23 - 20: Temperature (C), LSB, 32-bit float
# 31 - 24: Power Meter (watts * 1000), 64-bit int
# 39 - 32: Charge Meter (Amp-hours * 1000), 64-bit int
# 43 - 40: Uptime (seconds), unsigned 32-bit int
# 47 - 44: Date/Time (unknown format)
# 51 - 48: Peak Current, 32-bit float
# 52+    : Unknown
#
# Example:
# e0 81 03 a0 7f 91 56 41 a5 62 48 41 d6 e3 aa be 95 3b 8f c0 05 00 c4 41 09 4e fc ff ff ff ff ff c2 b9 ff ff ff ff ff ff 8d 18 0b 00 ad 68 09 0e 41 59 48 42
#
gattList = result.stdout.replace("Characteristic value/descriptor:", "").split()

#
#Parse list from gatttool and  convert text btye representations to  ints, floats, etc.
#
# Percent Charged - unsigned int, divide by two to throw away LSB
i=3
PctCharged = (struct.unpack('!B', bytes.fromhex(gattList[i]))[0])/2

# V1 Volts - 32 bit float LSB
i = 4
V1Volts = struct.unpack('!f', bytes.fromhex(gattList[i+3] + gattList[i+2] + gattList[i + 1] + gattList[i]))[0]

# V2 Volts -  32 bit float LSB
i = 8
V2Volts = struct.unpack('!f', bytes.fromhex(gattList[i+3] + gattList[i+2] + gattList[i + 1] + gattList[i]))[0]

# Current in Amps - 32 bit float LSB
i = 12
Current = struct.unpack('!f', bytes.fromhex(gattList[i+3] + gattList[i+2] + gattList[i + 1] + gattList[i]))[0]

# Power in Watts - 32 bit float LSB
i = 16
Power = struct.unpack('!f', bytes.fromhex(gattList[i+3] + gattList[i+2] + gattList[i + 1] + gattList[i]))[0]

# Temperature - 32 bit float LSB
i=20
Temperature = struct.unpack('!f', bytes.fromhex(gattList[i+3] + gattList[i+2] + gattList[i + 1] + gattList[i]))[0]

# Power Meter - int64  * 1000
i=24
PowerMeter = (struct.unpack('!q', bytes.fromhex(gattList[i+7] + gattList[i+6] + gattList[i+5] + gattList[i+4] + gattList[i+3] + gattList[i+2] + gattList[i + 1] + gattList[i]))[0])/1000

# Charge Meter  - int64 * 1000
i=32
ChargeMeter = (struct.unpack('!q', bytes.fromhex(gattList[i+7] + gattList[i+6] + gattList[i+5] + gattList[i+4] + gattList[i+3] + gattList[i+2] + gattList[i + 1] + gattList[i]))[0])/1000

# Time since start  - uint32
i=40
TimeSinceStart = struct.unpack('!I', bytes.fromhex(gattList[i+3] + gattList[i+2] + gattList[i + 1] + gattList[i]))[0]

#Time in packed format - uint32
i=44
CurrentTime = struct.unpack('!I', bytes.fromhex(gattList[i+3] + gattList[i+2] + gattList[i + 1] + gattList[i]))[0]

# Peak current - 32 bit float
i=48
PeakCurrent = struct.unpack('!f', bytes.fromhex(gattList[i+3] + gattList[i+2] + gattList[i + 1] + gattList[i]))[0]

if args.Human:
# Output in somewhat human readable format. 

    print (
	'Time:            {timeNow}\n'
	'Device:          {args.BLEaddress}\n'
	'Pct Charged:     {PctCharged:6.1f}%\n'
	'V1 Volts:        {V1Volts:6.3f}V\n'
	'V2 Volts:        {V2Volts:6.3f}V\n'
        'Current:         {Current:6.2f}A\n'
        'Power:           {Power:6.2f}W\n'
        'Temperature:     {Temperature:6.1f}C\n'
        'Power Meter:     {PowerMeter:8.2f}Ah\n'
        'Charge Meter:    {ChargeMeter:6.2f}W\n'
        'Uptime:          {TimeSinceStart}\n'
        'Date/Time:       {CurrentTime}\n'
        'Peak Current:    {PeakCurrent:6.2f}Ah'.format(**vars()))

else:
# Output formatted as parsable plain text I.E.:
# 05/08/2020 04:34:47 80.0 13.411 12.524 -0.33  -4.48 24.5  -242.17 -17.98 727181 235497645 50.09

    print (
	'{timeNow} '
	'{args.BLEaddress} '
        '{PctCharged:6.1f} '
        '{V1Volts:6.3f} '
        '{V2Volts:6.3f} '
        '{Current:6.2f} '
        '{Power:6.2f} '
        '{Temperature:6.1f} '
        '{PowerMeter:8.2f} '
        '{ChargeMeter:6.2f} '
        '{TimeSinceStart} '
        '{CurrentTime} '
        '{PeakCurrent:6.2f}'.format(**vars()))

