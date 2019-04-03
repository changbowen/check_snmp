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
_parser.add_argument('host', help='The host to connect to.')
_args = _parser.parse_args()
args_Host = _args.host
args_Version = _args.version
args_Community = _args.community
args_RespectImp = _args.respect


# get base folder
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# definitions
Config = {
    'dell': {
        'mib_dir': 'mibs/default:mibs/iana:mibs/ietf:mibs/dell',
        'mib': 'IDRAC-MIB-SMIv2',
        'oids': OrderedDict([
            ('globalSystemStatus',                          {'description': 'Overall system status', 'important': True}),
            ('systemStateProcessorDeviceStatusCombined',    {'description': 'Processor status'}),
            ('memoryDeviceStatus',                          {'description': 'Memory status'}),
            ('physicalDiskState',                           {'description': 'Physical disk status'}),
            ('virtualDiskState',                            {'description': 'Virtual disk status'}),
            ('controllerComponentStatus',                   {'description': 'Storage controller status'}),
            ('coolingUnitStatus',                           {'description': 'Cooling status'}),
            ('temperatureProbeStatus',                      {'description': 'Temperature status'}),
            ('powerSupplyStatus',                           {'description': 'Power supply status'}),
            ('systemStateBatteryStatusCombined',            {'description': 'Battery status'}),
        ])
    },
    'hpe': {
        'mib_dir': 'mibs/default:mibs/iana:mibs/ietf:mibs/hpe',
        'mib': 'CPQSINFO-MIB:CPQHLTH-MIB:CPQIDA-MIB',
        'oids': OrderedDict([
            ('cpqHeMibCondition',                   {'description': 'Overall system status', 'important': True}),
            ('cpqHeResilientMemCondition',          {'description': 'Memory status'}),
            ('cpqDaPhyDrvCondition',                {'description': 'Physical disk status'}),
            ('cpqDaMibCondition',                   {'description': 'Virtual disk status'}),
            ('cpqDaCntlrCondition',                 {'description': 'Storage controller status'}),
            ('cpqHeThermalSystemFanStatus',         {'description': 'Cooling status'}),
            ('cpqHeThermalTempStatus',              {'description': 'Temperature status'}),
            ('cpqHeFltTolPowerSupplyCondition',     {'description': 'Power supply status'}),
            ('cpqHeEventLogCondition',              {'description': 'Integrated Management Log status'}),
        ])
    }
}
StatusOK = ('ok', 'true', 'yes', 'on', 'online', 'spunup', 'full', 'ready', 'enabled', 'presence', 'non-raid', 'nonraid', 0)
StatusWarning = ('noncritical', 'removed', 'foreign', 'offline')
StatusCritical = ('fail', 'failed', 'critical', 'nonrecoverable', 'notredundant', 'lost', 'degraded', 'redundancyoffline')
StatusMap = {
    0: {'status': 'ok',         'color': '\033[32m{}\033[00m',  'severity': 0},  # green
    1: {'status': 'warning',    'color': '\033[33m{}\033[00m',  'severity': 2},  # orange
    2: {'status': 'critical',   'color': '\033[31m{}\033[00m',  'severity': 3},  # red
    3: {'status': 'unknown',    'color': '\033[37m{}\033[00m',  'severity': 1},  # lightgrey
}

SnmpCommand = NamedTuple('SnmpCommand', [('command', str), ('host', str), ('oid', str), ('mib_dir', str), ('mib', str), ('value_only', bool)])
SnmpResult = NamedTuple('SnmpResult', [('stdout', str), ('stderr', str)])
CombinedStatus = NamedTuple('CombinedStatus', [('code', int), ('formatted', str)])


def run(cmd: SnmpCommand) -> SnmpResult:
    cmdlst = [cmd.command, '-v', args_Version, '-c', args_Community]
    if cmd.value_only: cmdlst.append('-O'); cmdlst.append('qv')
    if cmd.mib_dir: cmdlst.append('-M'); cmdlst.append(cmd.mib_dir)
    if cmd.mib: cmdlst.append('-m'); cmdlst.append(cmd.mib)
    cmdlst.append(cmd.host); cmdlst.append(cmd.oid)

    _proc = subprocess.run(cmdlst, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _result = SnmpResult(str(_proc.stdout, 'utf-8').strip().lower(), str(_proc.stderr, 'utf-8').strip().lower())
    return _result


def print_and_exit(msg: str, code: int):
    print(msg)
    sys.exit(code)


def status_converter(status: any) -> int:
    if status in StatusOK:
        return 0  # ok
    elif status in StatusWarning:
        return 1  # warning
    elif status in StatusCritical:
        return 2  # critical
    else:
        return 3  # unknown


def multi_status_converter(status_str: str) -> CombinedStatus:
    combined, formatted = 0, ''
    for s in status_str.splitlines():
        formatted += s + '|'
        combined = update_status_code(combined, status_converter(s))

    if len(formatted) > 1: formatted = formatted[:-1]
    return CombinedStatus(combined, formatted)


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
for oid in Config[Vendor]['oids']:
    vendor = Config[Vendor]
    mib_dir = vendor['mib_dir']
    mib = vendor['mib']
    desc = vendor['oids'][oid]['description']
    imp = vendor['oids'][oid].get('important') is True

    result = run(SnmpCommand('snmpwalk', args_Host, oid, mib_dir, mib, True))
    cs = multi_status_converter(result.stdout)
    if imp: exitCodeImp = update_status_code(exitCodeImp, cs.code)
    exitCode = update_status_code(exitCode, cs.code)

    result_status = StatusMap[cs.code]
    print('{desc}: {status} ({formatted})'.format(desc=desc,
                                                  status=result_status['color'].format(result_status['status']),
                                                  formatted=cs.formatted))

if args_RespectImp and exitCodeImp > -1:
    sys.exit(exitCodeImp)
else:
    sys.exit(exitCode)

