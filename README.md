## check_snmp
#### Python script that checks components status against Dell or HPE servers with snmpwalk command

Usage: `check_snmp.py [-h] [-r] host`

For example `check_snmp.py -r 192.168.1.120`

The script will decide the manufacturer based on the OID returned on a initial call to snmpgetnext.

The mibs folder contains lots of MIB files downloaded from Dell and HPE websites, also the ones downloaded by `snmp-mibs-downloader`.
Only a few are used by the script. The rest are kept for completeness. Also they are no so big.
**Keep the folder at the same directory with the script so the MIB files can be loaded correctly.**

The script is developed and tested on Python 3.5 against a few Dell PowerEdge servers (iDRAC 9) and HPE ProLiant DL380 Gen9 (iLO 4).
As one of my earliest Python projects, feel free to fork and make your own improvements.

--------------

### Sample Output
```
sample@sample:~$ check_snmp.py -r 192.168.1.120
Overall system status: critical (critical)
Processor status: ok (ok)
Memory status: ok (ok|ok)
Physical disk status: critical (online|online|removed|removed|removed|failed|online)
Virtual disk status: critical (degraded)
Storage controller status: ok (ok|ok)
Cooling status: ok (ok)
Temperature status: ok (ok|ok)
Power supply status: ok (ok)
Battery status: ok (ok)
```

### Return Value
Integer value that is inline with the Nagios exit codes.

For each OID, if there are multiple results (e.g. there may be more than one disk in the system), the most severe status is preserved and used as return value.
By default the exit code will be the most severe one of all the results from the OIDs.
If `-r` option is specified, the script will only check the OIDs marked as **important** when returning.  

Exit Code | Status
--- | ---
0 | OK
1 | WARNING
2 | CRITICAL
3 | UNKNOWN

### Loading MIB
For Dell only one MIB module `IDRAC-MIB-SMIv2` needs to be specified in the snmpwalk command with `-m` option.

For HPE depending on the components you may need to specify more than one MIB to get a meaningful return value.

Since the script parse the result as a string, it is necessary to load appropriate MIB with the `-m` option.
As you can see in the dictionary Config, multiple MIB modules and search folders are separated with a colon.

You can of course directly pass OID in the numeric format but it would be harder to maintain and the returned integer can have different meanings if they are of different enumeration types.

### Useful OIDs
#### Dell
Dell OIDs are more self-explanatory and easier to collect because they are all inside one MIB.

OID (numeric format) | OID Translation | Description
---| --- | ---
1.3.6.1.4.1.674.10892.5.4.200.10.1.9 | systemStatePowerSupplyStatusCombined
1.3.6.1.4.1.674.10892.5.4.200.10.1.12 | systemStateVoltageStatusCombined
1.3.6.1.4.1.674.10892.5.4.200.10.1.15 | systemStateAmperageStatusCombined
1.3.6.1.4.1.674.10892.5.4.200.10.1.21 | systemStateCoolingDeviceStatusCombined
1.3.6.1.4.1.674.10892.5.4.200.10.1.24 | systemStateTemperatureStatusCombined
1.3.6.1.4.1.674.10892.5.4.200.10.1.27 | systemStateMemoryDeviceStatusCombined
1.3.6.1.4.1.674.10892.5.4.200.10.1.30 | systemStateChassisIntrusionStatusCombined
1.3.6.1.4.1.674.10892.5.4.200.10.1.42 | systemStatePowerUnitStatusCombined
1.3.6.1.4.1.674.10892.5.4.200.10.1.44 | systemStateCoolingUnitStatusCombined
1.3.6.1.4.1.674.10892.5.4.200.10.1.50 | systemStateProcessorDeviceStatusCombined
1.3.6.1.4.1.674.10892.5.4.200.10.1.52 | systemStateBatteryStatusCombined
1.3.6.1.4.1.674.10892.5.4.200.10.1.54 | systemStateSDCardUnitStatusCombined
1.3.6.1.4.1.674.10892.5.4.200.10.1.56 | systemStateSDCardDeviceStatusCombined
1.3.6.1.4.1.674.10892.5.4.200.10.1.58 | systemStateIDSDMCardUnitStatusCombined
1.3.6.1.4.1.674.10892.5.4.200.10.1.60 | systemStateIDSDMCardDeviceStatusCombined
1.3.6.1.4.1.674.10892.5.4.200.10.1.63 | systemStateTemperatureStatisticsStatusCombined
1.3.6.1.4.1.674.10892.5.4.300.40.1.7.1 | eventLogSeverityStatus
1.3.6.1.4.1.674.10892.5.2.1 | globalSystemStatus | Overall system status
1.3.6.1.4.1.674.10892.5.4.1100.50.1.5 | memoryDeviceStatus | Memory status
1.3.6.1.4.1.674.10892.5.5.1.20.130.4.1.4 | physicalDiskState | Physical disk status
1.3.6.1.4.1.674.10892.5.5.1.20.130.1.1.38 | controllerComponentStatus | Storage controller status
1.3.6.1.4.1.674.10892.5.4.700.10.1.8 | coolingUnitStatus | Cooling status
1.3.6.1.4.1.674.10892.5.4.700.20.1.5 | temperatureProbeStatus | Temperature status
1.3.6.1.4.1.674.10892.5.4.600.12.1.5 | powerSupplyStatus | Power supply status

#### HPE
HPE OIDs are much harder to collect since they are scattered into multiple MIBs and there are few clear support documents online.

OID (numeric format) | OID Translation | Description
---| --- | ---
1.3.6.1.4.1.232.6.1.3.0 | cpqHeMibCondition | Overall system condition
1.3.6.1.4.1.232.6.2.6.5.0 | cpqHeThermalCpuFanStatus | CPU fan condition
1.3.6.1.4.1.232.6.2.6.4.0 | cpqHeThermalSystemFanStatus | System fan condition
1.3.6.1.4.1.232.3.1.3.0 | cpqDaMibCondition | Disk array condition
1.3.6.1.4.1.232.3.2.2.1.1.6.0 | cpqDaCntlrCondition | Disk controller condition
1.3.6.1.4.1.232.3.2.2.2.1.9.0 | cpqDaAccelCondition | Disk accelerator condition 
1.3.6.1.4.1.232.6.2.9.3.1.4.0 | cpqHeFltTolPowerSupplyCondition | Power supply condition
1.3.6.1.4.1.232.6.2.6.3.0 | cpqHeThermalTempStatus | Temperature condition
1.3.6.1.4.1.232.6.2.6.1.0 | cpqHeThermalCondition | Thermal condition
1.3.6.1.4.1.232.6.2.11.2.0 | cpqHeEventLogCondition | Integrated Management Log condition
1.3.6.1.4.1.232.18.1.3.0 | cpqNicMibCondition | NIC condition
1.3.6.1.4.1.232.1.1.3.0 | cpqSeMibCondition | CPU?
1.3.6.1.4.1.232.9.1.3.0 | cpqSm2MibCondition | iLO condition
1.3.6.1.4.1.232.2.1.3.0 | cpqSiMibCondition | System information condition

### Links
[OID repository - HPE root (Compaq)](http://www.oid-info.com/get/1.3.6.1.4.1.232)

[OID repository - Dell root (Dell Inc.)](http://www.oid-info.com/get/1.3.6.1.4.1.674)

[IDRAC-MIB-SMIv2 treeview](http://www.oidview.com/mibs/674/IDRAC-MIB-SMIv2.html)

[CPQHLTH-MIB treeview](http://www.oidview.com/mibs/232/CPQHLTH-MIB.html)

