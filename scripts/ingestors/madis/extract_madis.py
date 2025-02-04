"""extract_madis.py Get the latest MADIS numbers from the data file!"""
from __future__ import print_function
import datetime
import os
import warnings

import pytz
import numpy as np
from netCDF4 import chartostring
from pyiem.datatypes import temperature
from pyiem.util import get_dbconn, ncopen
warnings.simplefilter("ignore", UserWarning)


def figure(val, qcval):
    """hack"""
    if qcval > 1000:
        return None
    if np.ma.is_masked(val) or np.ma.is_masked(qcval):
        return None
    return temperature(val + qcval,
                       'K').value('F') - temperature(val, 'K').value('F')


def figure_alti(qcval):
    """hack"""
    if qcval > 100000.:
        return None
    return float(qcval / 100.0)


def check(val):
    """hack"""
    if val > 1000000.:
        return None
    return float(val)


def main():
    """GO Main Go"""
    pgconn = get_dbconn('iem')
    icursor = pgconn.cursor()

    utcnow = datetime.datetime.utcnow()
    for i in range(10):
        now = utcnow - datetime.timedelta(hours=i)
        fn = "/mesonet/data/madis/mesonet1/%s.nc" % (
            now.strftime("%Y%m%d_%H00"), )
        if os.path.isfile(fn):
            break

    if not os.path.isfile(fn):
        print('extract_madis.py found no files? last: %s' % (fn, ))
        return

    with ncopen(fn) as nc:
        providers = chartostring(nc.variables["dataProvider"][:])
        stations = chartostring(nc.variables['stationId'][:])
        nc_tmpk = nc.variables["temperature"][:]
        nc_dwpk = nc.variables["dewpoint"][:]
        nc_alti = nc.variables["altimeter"][:]
        tmpkqcd = nc.variables["temperatureQCD"][:]
        dwpkqcd = nc.variables["dewpointQCD"][:]
        altiqcd = nc.variables["altimeterQCD"][:]
        times = nc.variables["observationTime"][:]

    for p in range(providers.shape[0]):
        provider = providers[p]
        if provider not in ['IEM', 'IADOT']:
            continue
        ticks = int(times[p])
        ts = datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=ticks)
        ts = ts.replace(tzinfo=pytz.UTC)

        (tmpf, tmpf_qc_av, tmpf_qc_sc) = (None, None, None)
        (dwpf, dwpf_qc_av, dwpf_qc_sc) = (None, None, None)
        (alti, alti_qc_av, alti_qc_sc) = (None, None, None)

        if not np.ma.is_masked(nc_tmpk[p]):
            tmpf = check(temperature(nc_tmpk[p], 'K').value('F'))
            tmpf_qc_av = figure(nc_tmpk[p], tmpkqcd[p, 0])
            tmpf_qc_sc = figure(nc_tmpk[p], tmpkqcd[p, 6])
        if not np.ma.is_masked(nc_dwpk[p]):
            dwpf = check(temperature(nc_dwpk[p], 'K').value('F'))
            dwpf_qc_av = figure(nc_dwpk[p], dwpkqcd[p, 0])
            dwpf_qc_sc = figure(nc_dwpk[p], dwpkqcd[p, 6])
        if not np.ma.is_masked(nc_alti[p]):
            alti = check((nc_alti[p] / 100.0) * 0.0295298)
            alti_qc_av = figure_alti(altiqcd[p, 0] * 0.0295298)
            alti_qc_sc = figure_alti(altiqcd[p, 6] * 0.0295298)
        sql = """
            UPDATE current_qc SET tmpf = %s, tmpf_qc_av = %s,
            tmpf_qc_sc = %s, dwpf = %s, dwpf_qc_av = %s,
            dwpf_qc_sc = %s, alti = %s, alti_qc_av = %s,
            alti_qc_sc = %s, valid = %s WHERE station = %s
        """
        args = (tmpf, tmpf_qc_av, tmpf_qc_sc, dwpf, dwpf_qc_av,
                dwpf_qc_sc, alti, alti_qc_av, alti_qc_sc,
                ts, stations[p])
        icursor.execute(sql, args)

    icursor.close()
    pgconn.commit()
    pgconn.close()


if __name__ == '__main__':
    main()
