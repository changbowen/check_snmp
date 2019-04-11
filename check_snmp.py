#!/usr/bin/env python3

import os
import sys
import subprocess
import argparse
from collections import OrderedDict
from typing import NamedTuple

_parser = argparse.ArgumentParser()
_parser.add_argument('-v', dest='version', help='The SNMP version to use.', default='2c')
_parser.add_argument('-c', dest='community', help='The community string to use.', default='public')
_parser.add_argument('-r', dest='respect', help='Respect properties marked as important when other results contain errors.', action='store_true')
_parser.add_argument('-f', dest='more_format', help='Include additional format like colors in the output.', action='store_true')
_parser.add_argument('host', help='The host to connect to.')
_args = _parser.parse_args()
args_Host = _args.host
args_Version = _args.version
args_Community = _args.community
args_RespectImp = _args.respect
args_MoreFormat = _args.more_format

# get base folder
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# definitions
Config = {
    'dell': {
        'mib_dir': 'mibs/default:mibs/iana:mibs/ietf:mibs/dell',
        'mib': 'IDRAC-MIB-SMIv2',
        'categories': OrderedDict([
            ('global', {
                'description': 'Overall System Status',
                'oids': [
                    {'oid': 'systemModelName', 'type': 'text'},
                    {'oid': 'systemServiceTag', 'type': 'text'},
                    {'oid': 'systemOSName', 'type': 'text'},
                    {'oid': 'globalSystemStatus', 'type': 'status'},
                ],
                'important': True
            }),
            ('processor', {
                'description': 'Processor Status',
                'oids': [
                    {'oid': 'processorDeviceBrandName', 'type': 'text'},
                    {'oid': 'processorDeviceStatus', 'type': 'status'},
                ],
            }),
            ('memory', {
                'description': 'Memory Status',
                'oids': [
                    {'oid': 'memoryDeviceLocationName', 'type': 'text'},
                    {'oid': 'memoryDeviceStatus', 'type': 'status'},
                ],
            }),
            ('physicalDisk', {
                'description': 'Physical Disk Status',
                'oids': [
                    {'oid': 'physicalDiskDisplayName', 'type': 'text'},
                    {'oid': 'physicalDiskState', 'type': 'status'},
                ],
            }),
            ('virtualDisk', {
                'description': 'Virtual Disk Status',
                'oids': [
                    {'oid': 'virtualDiskDisplayName', 'type': 'text'},
                    {'oid': 'virtualDiskState', 'type': 'status'},
                ],
            }),
            ('storageController', {
                'description': 'Storage Controller Status',
                'oids': [
                    {'oid': 'controllerName', 'type': 'text'},
                    {'oid': 'controllerComponentStatus', 'type': 'status'},
                ],
            }),
            ('cooling', {
                'description': 'Cooling Status',
                'oids': [
                    {'oid': 'coolingUnitName', 'type': 'text'},
                    {'oid': 'coolingUnitStatus', 'type': 'status'},
                ],
            }),
            ('temperature', {
                'description': 'Temperature Status',
                'oids': [
                    {'oid': 'temperatureProbeLocationName', 'type': 'text'},
                    {'oid': 'temperatureProbeStatus', 'type': 'status'},
                ],
            }),
            ('powerSupply', {
                'description': 'Power Supply Status',
                'oids': [
                    {'oid': 'powerSupplyLocationName', 'type': 'text'},
                    {'oid': 'powerSupplyStatus', 'type': 'status'},
                ],
            }),
            ('battery', {
                'description': 'Battery Status',
                'oids': [
                    {'oid': 'systemBatteryLocationName', 'type': 'text'},
                    {'oid': 'systemBatteryStatus', 'type': 'status'},
                ],
            }),
        ])
    },
    'hpe': {
        'mib_dir': 'mibs/default:mibs/iana:mibs/ietf:mibs/hpe',
        'mib': 'CPQSINFO-MIB:CPQHLTH-MIB:CPQIDA-MIB',
        'categories': OrderedDict([
            ('global', {
                'description': 'Overall System Status',
                'oids': [
                    {'oid': 'cpqHeMibCondition', 'type': 'status'},
                ],
                'important': True
            }),
            ('memory', {
                'description': 'Memory Status',
                'oids': [
                    {'oid': 'cpqHeResilientMemCondition', 'type': 'status'},
                ],
            }),
            ('physicalDisk', {
                'description': 'Physical Disk Status',
                'oids': [
                    {'oid': 'cpqDaPhyDrvLocationString', 'type': 'text'},
                    {'oid': 'cpqDaPhyDrvCondition', 'type': 'status'},
                ],
            }),
            ('virtualDisk', {
                'description': 'Virtual Disk Status',
                'oids': [
                    {'oid': 'cpqDaMibCondition', 'type': 'status'},
                ],
            }),
            ('storageController', {
                'description': 'Storage Controller Status',
                'oids': [
                    {'oid': 'cpqDaCntlrCondition', 'type': 'status'},
                ],
            }),
            ('cooling', {
                'description': 'Cooling Status',
                'oids': [
                    {'oid': 'cpqHeThermalSystemFanStatus', 'type': 'status'},
                ],
            }),
            ('temperature', {
                'description': 'Temperature Status',
                'oids': [
                    {'oid': 'cpqHeThermalTempStatus', 'type': 'status'},
                ],
            }),
            ('powerSupply', {
                'description': 'Power Supply Status',
                'oids': [
                    {'oid': 'cpqHeFltTolPowerSupplyCondition', 'type': 'status'},
                ],
            }),
            ('battery', {
                'description': 'Integrated Management Log Status',
                'oids': [
                    {'oid': 'cpqHeEventLogCondition', 'type': 'status'},
                ],
            }),
        ]),
    }
}
StatusOK = ('ok', 'true', 'yes', 'on', 'online', 'spunup', 'full', 'ready', 'enabled', 'presence', 'non-raid', 'nonraid', '0')
StatusWarning = ('noncritical', 'removed', 'foreign', 'offline')
StatusCritical = ('fail', 'failed', 'critical', 'nonrecoverable', 'notredundant', 'lost', 'degraded', 'redundancyoffline')
StatusMap = {
    0: {'status': 'OK',         'color': '\033[32m{}\033[00m',  'severity': 0},  # green
    1: {'status': 'WARNING',    'color': '\033[33m{}\033[00m',  'severity': 2},  # orange
    2: {'status': 'CRITICAL',   'color': '\033[31m{}\033[00m',  'severity': 3},  # red
    3: {'status': 'UNKNOWN',    'color': '\033[37m{}\033[00m',  'severity': 1},  # lightgrey
}

SnmpCommand = NamedTuple('SnmpCommand', [('command', str), ('host', str), ('oid', str), ('mib_dir', str), ('mib', str), ('value_only', bool)])
SnmpResult = NamedTuple('SnmpResult', [('stdout', str), ('stderr', str)])
CombinedStatus = NamedTuple('CombinedStatus', [('combined', int), ('separated', list), ('raw', list)])


def run(cmd: SnmpCommand) -> SnmpResult:
    cmdlst = [cmd.command, '-v', args_Version, '-c', args_Community]
    if cmd.value_only: cmdlst.append('-O'); cmdlst.append('qv')
    if cmd.mib_dir: cmdlst.append('-M'); cmdlst.append(cmd.mib_dir)
    if cmd.mib: cmdlst.append('-m'); cmdlst.append(cmd.mib)
    cmdlst.append(cmd.host); cmdlst.append(cmd.oid)

    _proc = subprocess.run(cmdlst, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _result = SnmpResult(str(_proc.stdout, 'utf-8').strip(), str(_proc.stderr, 'utf-8').strip())
    return _result


def print_and_exit(msg: str, code: int):
    print(msg)
    sys.exit(code)


def status_converter(status: any) -> int:
    if type(status) is str: status = status.lower()
    if status in StatusOK:
        return 0  # ok
    elif status in StatusWarning:
        return 1  # warning
    elif status in StatusCritical:
        return 2  # critical
    else:
        return 3  # unknown


def multi_status_converter(status_str: str, bypass: bool = False) -> CombinedStatus:
    combined = -1
    separated = []
    raw = []
    for s in status_str.splitlines():
        raw.append(s)
        if not bypass:
            converted = status_converter(s)
            separated.append(converted)
            combined = update_status_code(combined, converted)

    return CombinedStatus(combined, separated, raw)


# def status_merger(ok: int, warning: int, critical: int, unknown: int) -> int:
#     if critical > 0:
#         return 2
#     elif warning > 0:
#         return 1
#     elif unknown > 0:
#         return 3
#     elif ok > 0:
#         return 0
#     else:
#         return 3


def update_status_code(old_status_code: int, status_code: int) -> int:
    if status_code not in StatusMap: print_and_exit('Unknown status code.', 3)
    if old_status_code not in StatusMap: return status_code

    if StatusMap[old_status_code]['severity'] < StatusMap[status_code]['severity']:
        return status_code
    else:
        return old_status_code


def status_formatter(status: int, alt_text: str = None, with_color: bool = True) -> str:
    result = StatusMap[status]['status'] if alt_text is None else alt_text
    if with_color:
        result = StatusMap[status]['color'].format(result)
    return result


def get_row_output(col_val_raw: str, col_type: str) -> str:
    if col_type == 'status':
        col_val = status_converter(col_val_raw)
        global category_code
        category_code = update_status_code(category_code, col_val)
        return status_formatter(col_val, StatusMap[col_val]['status'] + ' (' + col_val_raw + ')', args_MoreFormat)
    else:
        return col_val_raw


# execution
# get vendor
VendorResult = run(SnmpCommand('snmpgetnext', args_Host, '1.3.6.1.4.1', '', '', False))
if VendorResult.stderr:
    print_and_exit(VendorResult.stderr, 3)

if '674' in VendorResult.stdout:
    Vendor = 'dell'
elif '232' in VendorResult.stdout:
    Vendor = 'hpe'
else:
    print_and_exit('Unknown vendor information.', 3)


exitCode, exitCodeImp = -1, -1
vendor = Config[Vendor]
mib_dir = vendor['mib_dir']
mib = vendor['mib']
for category_key in vendor['categories']:
    category = vendor['categories'][category_key]
    description = category['description']
    imp = category.get('important') is True

    oids = category['oids']
    if len(oids) == 0: continue

    # get and reshape data
    category_output = description + ': {combined_status}\n'
    category_code = -1
    category_result_raw = []
    for oid in oids:
        oid_result_raw = run(SnmpCommand('snmpwalk', args_Host, oid['oid'], mib_dir, mib, True))
        if len(oid_result_raw.stderr) > 0: print_and_exit(oid_result_raw.stderr, 3)
        category_result_raw.append([(l.strip('" \n'), oid['type']) for l in oid_result_raw.stdout.splitlines()])
    category_result_raw = [i for i in zip(*category_result_raw)]  # swap axis

    if len(category_result_raw) == 1 and len(category_result_raw[0]) == 1:  # there is only one status item without anything else
        col = category_result_raw[0][0]
        category_output = category_output.format(combined_status=get_row_output(col[0], col[1]))

    else:
        for row in category_result_raw:  # row is like (('DIMM.Socket.A1', 'text'), ('failed', 'status'))
            cols = []
            for col in row:  # col is like ('DIMM.Socket.A1', 'text')
                cols.append(get_row_output(col[0], col[1]))

            category_output += '  - ' + ', '.join(cols) + '\n'
        category_output = category_output.format(combined_status=status_formatter(category_code, with_color=args_MoreFormat))

    print(category_output)

    if imp: exitCodeImp = update_status_code(exitCodeImp, category_code)
    exitCode = update_status_code(exitCode, category_code)


if args_RespectImp and exitCodeImp > -1:
    sys.exit(exitCodeImp)
else:
    sys.exit(exitCode)

