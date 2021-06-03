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
#	2021-01-23	V 0.2 - Swtich from gatttool to bluepy
#	2021-06-03	V 0.3 - Reduce precision on measurement outputs to reflect precision of devices
#
#	Reads characteristic 0x15 from Thornwave Bluetooth Battery Monitor 
#	Outputs in various formats
#
# 	Data format for Thornwave characteristic 0x15
#
#       	 Struct
# 	Fields   Type      Desc
#
#	  0 - 2:  Unknown
#	  3    :  B         Pct Charged, LSB must be stripped
#	  7 - 4:  f         V1 volts, LSB, 32-bit float
#	 11 - 8:  f         V2 volts, LSB, 32-bit float
#	 15 - 12: f         Current (amps), LSB, 32-bit float
#	 19 - 16: f         Power (watts), LSB, 32-bit float
#	 23 - 20: f         Temperature (C), LSB, 32-bit float
#	 31 - 24: q         Power Meter (watts * 1000), 64-bit int
#	 39 - 32: q         Charge Meter (Amp-hours * 1000), 64-bit int
#	 43 - 40: I         Uptime (seconds), unsigned 32-bit int
#	 47 - 44: I         Date/Time (unknown format)
#	 51 - 48: f         Peak Current, 32-bit float
#	 52+    : Unknown
#
#	Example:
#	b'\xe0\xff\x0f\xc8;X\\A\xd7;\\A\x8a\xb1\x90=\xe2\x14y?B\xd7\xcf\xc0Lk\xfb\xff\xff\xff\xff\xff\x93\xa7\xff\xff\xff\xff\xff\xff\x0eS\x85\x00 \xcen\x10i\x85\xc4A'
#

import argparse
import struct
import time
from datetime import datetime
from datetime import timedelta
from bluepy.btle import Peripheral, BTLEException

# Slurp up command line arguments
__author__ = 'Michael Janke'
parser = argparse.ArgumentParser(description='Thornwave BT DCPM slurper. Reads and outputs BT DCPM data')
group = parser.add_mutually_exclusive_group()
parser.add_argument("-b", "--BLEaddress", help="BT DCPM BLE Address", required=True)

group.add_argument("-P", "--Parsable", help="Machine parsable output (default)", action="store_true")
group.add_argument("-H", "--Human", help="Human readable output", action="store_true")
group.add_argument("-J", "--JSON", help="JSON output", action="store_true")

parser.add_argument("-v", "--verbose", help="debug output", action="store_true")

args = parser.parse_args()

timeNow = (datetime.now()).strftime("%x %X")

# Connect to thornwave. Try twice, then fail 
try:
  p = Peripheral(args.BLEaddress, addrType="random")

except BTLEException as ex:
  if args.verbose:
    print("Read failed. ", ex)
  time.sleep(10)
  try:
     p = Peripheral(args.BLEaddress, addrType="random")
  except:
     if args.verbose:
       print("Read failed. ", ex)
     exit

else:
  result=p.readCharacteristic(0x15)
  if args.verbose:
    print(result)

  # Unpack into variables, skipping bytes 0-2
  i = 3
  PctCharged, V1Volts, V2Volts, Current, Power, Temperature, PowerMeter, ChargeMeter, TimeSinceStart, CurrentTime, PeakCurrent = struct.unpack_from('<BfffffqqIIf', result, i)

  if args.verbose:
    print(PctCharged, V1Volts, V2Volts, Current, Power, Temperature, PowerMeter, ChargeMeter, TimeSinceStart, CurrentTime, PeakCurrent)

  # Clean up vars
  PctCharged = PctCharged/2
  PowerMeter = PowerMeter/1000
  ChargeMeter = ChargeMeter/1000

  delta = str(timedelta(seconds=TimeSinceStart))

  if args.Human:
  # Output in somewhat human readable format.

    print (
	'Time:            {timeNow:>20s}\n'
	'Device:          {args.BLEaddress:>20s}\n'
	'Pct Charged:     {PctCharged:>19.0f}%\n'
	'V1 Volts:        {V1Volts:>19.2f}V\n'
	'V2 Volts:        {V2Volts:>19.2f}V\n'
        'Current:         {Current:>19.2f}A\n'
        'Power:           {Power:>19.0f}W\n'
        'Temperature:     {Temperature:>19.1f}C\n'
        'Power Meter:     {PowerMeter:>18.1f}Ah\n'
        'Charge Meter:    {ChargeMeter:>19.1f}W\n'
        'Uptime:          {delta:>20s}\n'
        'Device Time:     {CurrentTime:>20d}\n'
        'Peak Current:    {PeakCurrent:>18.1f}Ah'.format(**vars()))

  elif args.JSON:
  # Output in JSON
  # split timeNow into separate fields
    dateSplit=timeNow.split()[0]
    timeSplit=timeNow.split()[1]

    print('{ ', end =" ")
    print(
	'"Date": "{dateSplit}", '
        '"GMT": "{timeSplit}", '
        '"Address": "{args.BLEaddress}", '
        '"Charge": "{PctCharged:.0f}", '
        '"V1": "{V1Volts:.2f}", '
        '"V2": "{V2Volts:.2f}", '
        '"Current": "{Current:.2f}", '
        '"Watts": "{Power:.0f}", '
        '"Temperature": "{Temperature:.1f}", '
        '"PowerMeter": "{PowerMeter:.1f}", '
        '"ChargeMeter": "{ChargeMeter:.1f}", '
        '"Uptime": "{delta}", '
        '"DeviceTime": "{CurrentTime:d}", '
        '"PeakCurrent": "{PeakCurrent:.2f}" '.format(**vars()), end =" ")
    print('}')

  else:
  # Output formatted as parsable plain text I.E.:
  # 05/08/2020 04:34:47 80.0 13.411 12.524 -0.33  -4.48 24.5  -242.17 -17.98 727181 235497645 50.09

    print (
	'{timeNow} '
	'{args.BLEaddress} '
        '{PctCharged:6.0f} '
        '{V1Volts:6.2f} '
        '{V2Volts:6.2f} '
        '{Current:6.2f} '
        '{Power:6.0f} '
        '{Temperature:6.1f} '
        '{PowerMeter:8.1f} '
        '{ChargeMeter:6.1f} '
        '{TimeSinceStart} '
        '{CurrentTime} '
        '{PeakCurrent:6.2f}'.format(**vars()))
