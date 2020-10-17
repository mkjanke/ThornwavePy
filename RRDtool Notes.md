# Using RRDTool

Example of how to use RRDTool to collect and chart the output from DCPMRead.py. This example assumes two Thornwave monitors each monitoring one battery bank 'Lithium' and 'AGM'. The RRD parameters are:

```
# 5 Min interval
# Five minute points for 48+ hours
# 30 minute points for 30 days
# AVERAGE, MIN MAX on 30 day

# Percent Charged: -200 - 200 %
# Voltage 1: 0 - 18 V
# Voltage 2: 0 - 18 V
# Current: -200 - 200 A
# Power: -2000 - 2000 watts
# Temperature: -60 - 60 C
# Watt-hours: -6000 - 6000
# Amp-hours: -600 - 600 
```
These may be adjusted to suit. RRD must be run from cron at whatever your interval is when you create the RRD

## Creating RRD data files 

I use one RRD file per monitor. That allows me to add or remove battery banks and monitors as needed. You can name the files whatever you want.

```
rrdtool create ./rrd/Lithium.rrd -b now -s 300 \
	DS:PCTCharged:GAUGE:600:-200:200 \
	DS:V1:GAUGE:600:0:18 \
	DS:V2:GAUGE:600:0:18 \
	DS:Current:GAUGE:600:-200:200 \
	DS:Power:GAUGE:600:-2000:2000 \
	DS:Temperature:GAUGE:600:-60:60 \
	DS:WattHours:GAUGE:600:-6000:6000 \
	DS:AmpHours:GAUGE:600:-600:600 \
	RRA:AVERAGE:0.5:1:600 \
	RRA:AVERAGE:0.5:6:1440 \
	RRA:MIN:0.5:6:1440 \
	RRA:MAX:0.5:6:1440

```
```
rrdtool create ./rrd/AGM.rrd -b now -s 300 \
	DS:PCTCharged:GAUGE:600:-200:200 \
	DS:V1:GAUGE:600:0:18 \
	DS:V2:GAUGE:600:0:18 \
	DS:Current:GAUGE:600:-200:200 \
	DS:Power:GAUGE:600:-2000:2000 \
	DS:Temperature:GAUGE:600:-60:60 \
	DS:WattHours:GAUGE:600:-6000:6000 \
	DS:AmpHours:GAUGE:600:-600:600 \
	RRA:AVERAGE:0.5:1:600 \
	RRA:AVERAGE:0.5:6:1440 \
	RRA:MIN:0.5:6:1440 \
	RRA:MAX:0.5:6:1440

```
To pipe the output from DCPMRead.py to RRD, I used a simple script that 

* accepts the output of DCPMRead.py to stdin
* parses the output and runs RRD
* mirrors the DCPMRead output to stdout

```
#!/usr/bin/python3
#rrdSplit.py

#pass rrd file in argv[1]

import sys
import os

input = sys.stdin.read().rstrip()
line = input.split()
print (input)

if len(line) > 9:
  rrd = "rrdtool update " + sys.argv[1] + ' N:'+line[3]+':'+line[4]+':'+line[5]+':'+line[6]+':'+line[7]+':'+line[8]+':'+line[9]+':'+line[10]
  os.system(rrd)
else:
  print(error)
```

##Crontab

I run the scripts every 5 minutes, piping the output of DCMPRead.py to the RRD script, and then to a log file.
```
*/5 * * * *  cd /home/pi/; ./thornwavepy/master/DCPMRead.py -b D2:0A:06:06:CB:1D | ./rrdSplit.py ./rrd/AGM.rrd >> AGM
*/5 * * * *  cd /home/pi/; ./thornwavepy/master/DCPMRead.py -b FB:45:68:6F:44:59 | ./rrdSplit.py ./rrd/Lithium.rrd >> Lithium
```

## Charting RRD data

I decided to create one chart for Current and one for Voltage, with both banks on the same chart. I'm only charting once per hour.  

The RRD charts are generated using a simple shell script.
```
#!/bin/bash
#rrdChart.sh

#Generate charts
rrdtool graph ./rrd/Volts.png \
        -w 900 -h 400 -A --left-axis-format "%3.1lf" \
        --vertical-label "Volts" \
        --watermark "Generated on `date`" \
        --font AXIS:14 --font LEGEND:16 --font UNIT:24 \
        --end now -s now-1d \
        DEF:ds01=./rrd/AGM.rrd:V1:AVERAGE \
        DEF:ds02=./rrd/Lithium.rrd:V1:AVERAGE \
        LINE1:ds01#00ff00:"AGM Volts" \
        LINE1:ds02#0000ff:"Lithium Volts"

rrdtool graph ./rrd/Current.png \
        -w 900 -h 400 \
        --vertical-label "Amps" \
        --watermark "Generated on `date`" \
        --font AXIS:14 --font LEGEND:16 --font UNIT:24 \
        --end now -s now-1d \
        DEF:ds03=./rrd/AGM.rrd:Current:AVERAGE \
        DEF:ds04=./rrd/Lithium.rrd:Current:AVERAGE \
        LINE1:ds03#ff0000:"AGM Amps" \
        LINE1:ds04#0000ff:"Lithium Amps" \
        HRULE:0#0a0a0a::dashes
```
Adjust as you see fit. 

The RRD's creaetd above have data to support daily charts showing max, min and averages for one month. You can adjust that when you create the RRD, but not after they are created. 

Crontab:
```
3   * * * *  cd /home/pi; ./rrd/rrdChart.sh >>./rrd/rrdchart.log 2>&1
```
