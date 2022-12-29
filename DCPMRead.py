#!/usr/bin/python3

#	Copyright 2020, 2022 Michael Janke
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
#	2021-07-11	V 0.4 - round() some variables and handle '-0' special case
#	2022-05-29	V 0.5 - Change bluetooth library from bluepy to bluezero
#	2022-07-18	V 0.6 - Initial support for firmware version > 2.03 (PowermonX)
#
#	Reads characteristic 0x15 from Thornwave Bluetooth Battery Monitor 
#	Outputs in various formats
#
# 	Data format for Thornwave firmware version <= 2.03 characteristic 0x15
#
#       	 Struct
# 	Fields   Type      Desc
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
# Example:
#  e0 ff 0f c8 47 04 4e 41 b7 09 dd 3c 97 ca 4e 3f 7a 6a 26 41 7c 01 0e 42 6c 7b 0f 00 00 00 00 00 6d 2e 01 00 00 00 00 00 ff 89 06 00 14 c1 e4 15 59 57 0b 42

# Data Format (Version > 2.03):
# Fields
#    0 - 4:  Unknown
#    8 - 5:  Date/Time Unix Epoc, LSB, 32-bit Uint 
#    9 - 12: Unknown
#   16 - 13: V1 volts, LSB, 32-bit float
#   20 - 17: V2 volts, LSB, 32-bit float
#   24 - 21: Current (amps), LSB, 32-bit float
#   28 - 25: Power (watts), LSB, 32-bit float
#	  36 - 29: Power Meter (watts * 1000), 64-bit int
#	  44 - 37: Charge Meter (Amp-hours * 1000), 64-bit int
#   48 - 45: Temperature (C), LSB, 32-bit float
#   48 +   : Unknown

# Example:
# 00 08 31 02 23 bb 78 ad 63 01 01 01 25 40 6b 57 41 17 52 57 41 73 12 d8 be 04 d2 b5 c0 8f fe ff ff ff ff ff ff a5 ec ff ff ff ff ff ff 87 dd 95 40 01 01 01 01 00
#  0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53
#                |---------|             |---------| |---------| |---------| |---------| |---------------------| |---------------------| |---------|
#                 Date/Time                  V1          V2        Current      Power        PowerMeter               ChargeMeter          Temp (C)


import argparse
import struct
import time
from datetime import datetime
from datetime import timedelta
from bluezero import central

# Slurp up command line arguments
__author__ = 'Michael Janke'
parser = argparse.ArgumentParser(description='Thornwave BT DCPM slurper. Reads and outputs BT DCPM data')
group = parser.add_mutually_exclusive_group()
parser.add_argument("-b", "--BLEaddress", help="BT DCPM BLE Address", required=True)

group.add_argument("-P", "--Parsable", help="Machine parsable output (default)", action="store_true")
group.add_argument("-H", "--Human", help="Human readable output", action="store_true")
group.add_argument("-J", "--JSON", help="JSON output", action="store_true")

parser.add_argument("-v", "--verbose", help="debug output", action="store_true")

parser.add_argument("-X", "--PowermonX", help="PowermonX version >2.03 format", action="store_true")

args = parser.parse_args()

timeNow = (datetime.now()).strftime("%x %X")

# Connect to thornwave. Try twice, then fail 
try:
  my_Sensor = central.Central(device_addr=args.BLEaddress)

except:
  if args.verbose:
    print("Read failed. ")
  time.sleep(10)
  try:
     my_Sensor = central.Central(device_addr=args.BLEaddress)
  except:
     if args.verbose:
       print("Read failed. ")
     exit

else:
  if args.PowermonX:
    ch = my_Sensor.add_characteristic("ec7c0000-2c7b-1539-172f-29d041beab3e", "ec7c0001-2c7b-1539-172f-29d041beab3e")
  else:
    ch = my_Sensor.add_characteristic("7a95ce00-0ea8-1bcc-71a2-fc7539b81c9c", "7a95ce01-0ea8-1bcc-71a2-fc7539b81c9c")

  my_Sensor.load_gatt()
  my_Sensor.connect()
  if args.verbose:
    print(my_Sensor.services_available)

  result=bytes(ch.read_raw_value())

  if args.verbose:
    print("".join(format(x, '02x') + ' ' for x in result))

  # Unpack fields from BLE characteristic
  if args.PowermonX:
    TimeSinceStart=0     # Zero out unhandled fields
    PeakCurrent=0
    i = 5                # Offset of first known field
    CurrentTime, V1Volts, V2Volts, Current, Power, ChargeMeter, PowerMeter, Temperature, PctCharged = struct.unpack_from('<IxxxxffffqqfxB', result, i)
  else:
    i = 3                # Offset of first known field
    PctCharged, V1Volts, V2Volts, Current, Power, Temperature, PowerMeter, ChargeMeter, TimeSinceStart, CurrentTime, PeakCurrent = struct.unpack_from('<BfffffqqIIf', result, i)

  if args.verbose:
    print(PctCharged, V1Volts, V2Volts, Current, Power, Temperature, PowerMeter, ChargeMeter, TimeSinceStart, CurrentTime, PeakCurrent)

  # Clean up vars
  V1Volts = round(V1Volts, 2)
  V2Volts = round(V2Volts, 2)
  Temperature = round(Temperature, 1)
  PctCharged = round(PctCharged/2, 0)
  PowerMeter = round(PowerMeter/1000, 1)
  ChargeMeter = round(ChargeMeter/1000, 1)

  # Handle '-0' special cases
  Power = round(Power, 0)
  if Power > -1 and Power < 1 :
    Power = 0
  Current = round(Current, 2)
  if Current > -1 and Current <1 :
    Current = 0

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
        'Power Meter:     {PowerMeter:>18.1f}Wh\n'
        'Charge Meter:    {ChargeMeter:>18.1f}Ah\n'
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
