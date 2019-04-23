# check_snmp
## Python script / nagios plug-in that checks components status of Dell or HP servers with snmpwalk command

```
usage: check_snmp.py [-h] [-v VERSION] [-c COMMUNITY] [-r] [-f] [-b]
                     [--config [CONFIG]]
                     host [category [category ...]]

positional arguments:
  host                  The host to connect to.
  category              One or more of the categories from the configuration
                        separated by spaces.

optional arguments:
  -h, --help            show this help message and exit
  -v VERSION, --version VERSION
                        The SNMP version to use.
  -c COMMUNITY, --community COMMUNITY
                        The community string to use.
  -r, --respect         Respect properties marked as important when other
                        results contain errors.
  -f, --format          Include additional format like colors in the output.
  -b, --brief           Output brief information (only description and
                        combined status).
  --config [CONFIG]     The configuration file to load.


```

For example `check_snmp.py -r -f 192.168.1.120`

By default SNMP version **v2c** and community string **public** will be used. Different values can be specified with `-v` and `-c` respectively.
The script will decide the manufacturer based on the OID returned on a initial call to snmpgetnext.

The script will load configurations from file `config_default.json` in the same directory by default. It is possible to pass a custom config file with the correct format to tune the output as you wish.
**If you won't specify another config file, keep the default one in the same directory as the script.**

The mibs folder contains lots of MIB files downloaded from Dell and HPE websites, also the ones downloaded by `snmp-mibs-downloader`.
Only a few are used by the script. The rest are kept for completeness. Also they are no so big.
**Keep the folder at the same directory with the script so the MIB files can be loaded correctly.**

The script is developed and tested on Python 3.5 against a few Dell PowerEdge servers (iDRAC 9) and HPE ProLiant DL380 Gen9 (iLO 4).

And of course you need to have snmp installed with `sudo apt install snmp`.

As one of my earliest Python projects, feel free to fork and make your own improvements.

--------------

### Sample Output
![sample](https://i.imgur.com/QowbHdr.png)

To be used as a nagios plugin, do not specify the `-f` option so that the output is not embedded with the ANSI color codes. If the renderer does not support parsing the color codes, it will pollute the output.

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

### Config File Structure
Fields indicated by `xxxxx` is customizable. 

```
{
  "config": {
    "global-list-bullet": "xxxx",                # bullet string prepended for each item in a category
                                                 # E.g. each disk item returned. Default is "  - "
    "global-oid-separator": "xxxx",              # string to separate each sub item in an oid entry.
                                                 # E.g. each piece of info of a disk. Default is ", "
  },
  "dell": {
    "mib_dir": "xxxxxxxxxxxxxxxxxxxxxxxx",       # do not change these unless you know what you are doing
    "mib": "xxxxxxxxxxxxxxx",                    # do not change these unless you know what you are doing
    "categories": {
      "xxxxxxxxx": {                             # category name can be any string
                                                 # used in the command line for category selection
        "description": "xxxxxxxxxxxxxxxxxx",
        "oids": [
          {
            "oid": "xxxxxxxxxxxxxxxx",
            "type": "status",                    # type can be "text" or "status"
            "prefix": "xxxxxxxxxxxx"             # (optional) used to annotate this oid and customize output
            "suffix": "xxxxxxxxxxxx"             # (optional) used to annotate this oid and customize output
          },
          ...
          "list-bullet": "xxxx"                  # (optional) string to override the global list bullet
          "oid-separator": "xxx",                # (optional) string to override the global oid separator
        ],
        "important": true                        # (optional) true or false
      },
      ...
    }
  },
  "hpe": {
    ...                                          # same structure as dell
  }
}
```

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
1.3.6.1.4.1.674.10892.5.4.300.40.1.7 | eventLogSeverityStatus
1.3.6.1.4.1.674.10892.5.1.3.12 | systemModelName
1.3.6.1.4.1.674.10892.5.1.3.2 | systemServiceTag
1.3.6.1.4.1.674.10892.5.2.1 | globalSystemStatus
1.3.6.1.4.1.674.10892.5.4.1100.30.1.23 | processorDeviceBrandName
1.3.6.1.4.1.674.10892.5.4.1100.30.1.5 | processorDeviceStatus
1.3.6.1.4.1.674.10892.5.4.1100.50.1.8 | memoryDeviceLocationName
1.3.6.1.4.1.674.10892.5.4.1100.50.1.5 | memoryDeviceStatus
1.3.6.1.4.1.674.10892.5.5.1.20.130.4.1.55 | physicalDiskDisplayName
1.3.6.1.4.1.674.10892.5.5.1.20.130.4.1.4 | physicalDiskState
1.3.6.1.4.1.674.10892.5.5.1.20.140.1.1.36 | virtualDiskDisplayName
1.3.6.1.4.1.674.10892.5.5.1.20.140.1.1.4 | virtualDiskState
1.3.6.1.4.1.674.10892.5.5.1.20.130.1.1.2 | controllerName
1.3.6.1.4.1.674.10892.5.5.1.20.130.1.1.38 | controllerComponentStatus
1.3.6.1.4.1.674.10892.5.4.700.10.1.7 | coolingUnitName
1.3.6.1.4.1.674.10892.5.4.700.10.1.8 | coolingUnitStatus
1.3.6.1.4.1.674.10892.5.4.700.20.1.8 | temperatureProbeLocationName
1.3.6.1.4.1.674.10892.5.4.700.20.1.5 | temperatureProbeStatus
1.3.6.1.4.1.674.10892.5.4.600.12.1.8 | powerSupplyLocationName
1.3.6.1.4.1.674.10892.5.4.600.12.1.5 | powerSupplyStatus
1.3.6.1.4.1.674.10892.5.4.600.50.1.7 | systemBatteryLocationName
1.3.6.1.4.1.674.10892.5.4.600.50.1.5 | systemBatteryStatus

#### HPE
HPE OIDs are much harder to collect since they are scattered into multiple MIBs and there are fewer clear support documents online.

OID (numeric format) | OID Translation | Description
---| --- | ---
1.3.6.1.4.1.232.6.1.3.0 | cpqHeMibCondition | Overall health condition
1.3.6.1.4.1.232.3.1.3.0 | cpqDaMibCondition | Disk array condition
1.3.6.1.4.1.232.6.2.11.2.0 | cpqHeEventLogCondition | Integrated Management Log condition
1.3.6.1.4.1.232.18.1.3.0 | cpqNicMibCondition | NIC condition
1.3.6.1.4.1.232.9.1.3.0 | cpqSm2MibCondition | iLO condition
1.3.6.1.4.1.232.2.1.3.0 | cpqSiMibCondition | System information condition
1.3.6.1.4.1.232.2.2.4.2 | cpqSiProductName | Model
1.3.6.1.4.1.232.2.2.2.1 | cpqSiSysSerialNum | Serial number
1.3.6.1.4.1.232.1.2.2.1.1.3 | cpqSeCpuName | CPU Model
1.3.6.1.4.1.232.1.2.2.1.1.6 | cpqSeCpuStatus | CPU status
1.3.6.1.4.1.232.6.2.14.13.1.13 | cpqHeResMem2ModuleHwLocation | Memory location
1.3.6.1.4.1.232.6.2.14.13.1.20 | cpqHeResMem2ModuleCondition | Memory condition
1.3.6.1.4.1.232.3.2.5.1.1.64 | cpqDaPhyDrvLocationString | Physical disk location
1.3.6.1.4.1.232.3.2.5.1.1.37 | cpqDaPhyDrvCondition | Physical disk condition
1.3.6.1.4.1.232.3.2.3.1.1.11 | cpqDaLogDrvCondition | Virtual disk condition
1.3.6.1.4.1.232.3.2.2.1.1.2 | cpqDaCntlrModel | Storage controller model
1.3.6.1.4.1.232.3.2.2.1.1.6.0 | cpqDaCntlrCondition | Storage controller condition
1.3.6.1.4.1.232.3.2.2.2.1.9.0 | cpqDaAccelCondition | Disk accelerator condition 
1.3.6.1.4.1.232.6.2.6.7.1.3 | cpqHeFltTolFanLocale | Fan location
1.3.6.1.4.1.232.6.2.6.7.1.9 | cpqHeFltTolFanCondition | Fan condition
1.3.6.1.4.1.232.6.2.6.8.1.3 | cpqHeTemperatureLocale | Temperature probe location
1.3.6.1.4.1.232.6.2.6.8.1.6 | cpqHeTemperatureCondition | Temperature condition
1.3.6.1.4.1.232.6.2.9.3.1.10 | cpqHeFltTolPowerSupplyModel | Power supply model
1.3.6.1.4.1.232.6.2.9.3.1.4.0 | cpqHeFltTolPowerSupplyCondition | Power supply condition

### Links
[OID repository - HPE root (Compaq)](http://www.oid-info.com/get/1.3.6.1.4.1.232)

[OID repository - Dell root (Dell Inc.)](http://www.oid-info.com/get/1.3.6.1.4.1.674)

[IDRAC-MIB-SMIv2 treeview](http://www.oidview.com/mibs/674/IDRAC-MIB-SMIv2.html)

[CPQHLTH-MIB treeview](http://www.oidview.com/mibs/232/CPQHLTH-MIB.html)

[Perl check_hp](https://github.com/lairsdragon/check_hp/blob/master/check_hp)
