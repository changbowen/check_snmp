import os
import sys
import subprocess
import argparse
from collections import OrderedDict
from typing import NamedTuple


_parser = argparse.ArgumentParser()
_parser.add_argument('host', help='The host to connect to.')
_args = _parser.parse_args()
Host = _args.host

# get base folder
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# definitions
Config = {
    'dell': {
        'mib_dir': 'mibs/default:mibs/iana:mibs/ietf:mibs/dell',
        'mib': 'IDRAC-MIB-SMIv2',
        'oids': OrderedDict([
            ('globalSystemStatus', 'Overall system status'),
            ('systemStateProcessorDeviceStatusCombined', 'Processor status'),
            ('memoryDeviceStatus', 'Memory status'),
            ('physicalDiskState', 'Physical disk status'),
            ('virtualDiskState', 'Virtual disk status'),
            ('controllerComponentStatus', 'Storage controller status'),
            ('coolingUnitStatus', 'Cooling status'),
            ('temperatureProbeStatus', 'Temperature status'),
            ('powerSupplyStatus', 'Power supply status'),
            ('systemStateBatteryStatusCombined', 'Battery status'),
        ])
    },
    'hpe': {
        'mib_dir': 'mibs/default:mibs/iana:mibs/ietf:mibs/hpe',
        'mib': 'CPQSINFO-MIB:CPQHLTH-MIB:CPQIDA-MIB',
        'oids': OrderedDict([
            ('cpqHeMibCondition', 'Overall system status'),
            ('cpqHeResilientMemCondition', 'Memory status'),
            ('cpqDaPhyDrvCondition', 'Physical disk status'),
            ('cpqDaMibCondition', 'Virtual disk status'),
            ('cpqDaCntlrCondition', 'Storage controller status'),
            ('cpqHeThermalSystemFanStatus', 'Cooling status'),
            ('cpqHeThermalTempStatus', 'Temperature status'),
            ('cpqHeFltTolPowerSupplyCondition', 'Power supply status'),
            ('cpqHeEventLogCondition', 'Integrated Management Log status'),
        ])
    }
}
StatusOK = ('ok', 'true', 'yes', 'on', 'online', 'spunup', 'full', 'ready', 'enabled', 'presence', 'non-raid', 'nonraid', 0)
StatusWarning = ('noncritical')
StatusCritical = ('fail', 'failed', 'critical', 'nonrecoverable', 'notredundant', 'lost', 'degraded', 'redundancyoffline')
StatusMap = {
    0: {'status': 'ok', 'color': '\033[32m{}\033[00m'},  # green
    1: {'status': 'warning', 'color': '\033[33m{}\033[00m'},  # orange
    2: {'status': 'critical', 'color': '\033[31m{}\033[00m'},  # red
    3: {'status': 'unknown', 'color': '\033[37m{}\033[00m'},  # lightgrey
}

SnmpCommand = NamedTuple('SnmpCommand', [('command', str), ('host', str), ('oid', str), ('mib_dir', str), ('mib', str), ('value_only', bool)])
SnmpResult = NamedTuple('SnmpResult', [('stdout', str), ('stderr', str)])
CombinedStatus = NamedTuple('CombinedStatus', [('ok', int), ('warning', int), ('critical', int), ('unknown', int)])


def run(cmd: SnmpCommand) -> SnmpResult:
    cmdlst = [cmd.command, '-v', '2c', '-c', 'public']
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


def status_converter(status: any) -> str:
    if status in StatusOK:
        return 'ok'
    elif status in StatusWarning:
        return 'warning'
    elif status in StatusCritical:
        return 'critical'
    else:
        return 'unknown'


def multi_status_converter(status_str: str) -> CombinedStatus:
    ok, warning, critical, unknown = 0, 0, 0, 0
    for s in status_str.splitlines():
        status = status_converter(s)
        if status == 'ok':
            ok += 1
        elif status == 'warning':
            warning += 1
        elif status == 'critical':
            critical += 1
        else:
            unknown += 1

    return CombinedStatus(ok, warning, critical, unknown)


def status_merger(ok: int, warning: int, critical: int, unknown: int) -> int:
    if critical > 0:
        return 2
    elif warning > 0:
        return 1
    elif unknown > 0:
        return 3
    elif ok > 0:
        return 0
    else:
        return 3


# execution
# get vendor
VendorResult = run(SnmpCommand('snmpgetnext', Host, '1.3.6.1.4.1', '', '', False))
if VendorResult.stderr:
    print_and_exit(VendorResult.stderr, 3)

if '674' in VendorResult.stdout:
    Vendor = 'dell'
elif '232' in VendorResult.stdout:
    Vendor = 'hpe'
else:
    print_and_exit('Unknown vendor information.', 3)


combinedOk, combinedWarning, combinedCritical, combinedUnknown, exitCode = 0, 0, 0, 0, 3
for oid in Config[Vendor]['oids']:
    vendor = Config[Vendor]
    mib_dir = vendor['mib_dir']
    mib = vendor['mib']
    desc = vendor['oids'][oid]
    result = run(SnmpCommand('snmpwalk', Host, oid, mib_dir, mib, True))

    cs = multi_status_converter(result.stdout)
    combinedOk += cs.ok
    combinedWarning += cs.warning
    combinedCritical += cs.critical
    combinedUnknown += cs.unknown

    merged_status = StatusMap[status_merger(cs.ok, cs.warning, cs.critical, cs.unknown)]
    print('{desc}: {status}'.format(desc=desc, status=merged_status['color'].format(merged_status['status'])))


exitCode = status_merger(combinedOk, combinedWarning, combinedCritical, combinedUnknown)
sys.exit(exitCode)
# print_and_exit('Query completed.', exitCode)

