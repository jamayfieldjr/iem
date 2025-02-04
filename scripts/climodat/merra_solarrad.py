"""
 Sample the MERRA solar radiation analysis into estimated values for the
 COOP point archive

 1 langley is 41840.00 J m-2 is 41840.00 W s m-2 is 11.622 W hr m-2

 So 1000 W m-2 x 3600 is 3,600,000 W s m-2 is 86 langleys

 Dr Arritt wants MJ m-2 dy-1
"""
from __future__ import print_function
import datetime
import sys
import os

import numpy as np
from pyiem.util import get_dbconn, ncopen


def get_gp(xc, yc, x, y):
    """ Return the grid point closest to this point """
    distance = []
    xidx = (np.abs(xc-x)).argmin()
    yidx = (np.abs(yc-y)).argmin()
    dx = x - xc[xidx]
    dy = y - yc[yidx]
    movex = -1
    if dx >= 0:
        movex = 1
    movey = -1
    if dy >= 0:
        movey = 1
    gridx = [xidx, xidx+movex, xidx+movex, xidx]
    gridy = [yidx, yidx, yidx+movey, yidx+movey]
    for myx, myy in zip(gridx, gridy):
        d = ((y - yc[myy])**2 + (x - xc[myx])**2)**0.5
        distance.append(d)
    return gridx, gridy, distance


def do(date):
    """ Process for a given date."""
    pgconn = get_dbconn('coop')
    ccursor = pgconn.cursor()
    ccursor2 = pgconn.cursor()
    sts = date.replace(hour=6)  # 6z
    ets = sts + datetime.timedelta(days=1)

    fn = sts.strftime("/mesonet/merra2/%Y/%Y%m%d.nc")
    fn2 = ets.strftime("/mesonet/merra2/%Y/%Y%m%d.nc")
    if not os.path.isfile(fn):
        print(("merra_solarrad %s miss[%s] -> fail"
               ) % (sts.strftime("%Y%m%d"), fn))
        return
    with ncopen(fn, timeout=300) as nc:
        rad = nc.variables['SWGDN'][7:, :, :]
        cs_rad = nc.variables['SWGDNCLR'][7:, :, :]
        xc = nc.variables['lon'][:]
        yc = nc.variables['lat'][:]

    if not os.path.isfile(fn2):
        print(("merra_solarrad %s miss[%s] -> zeros"
               ) % (sts.strftime("%Y%m%d"), fn2))
        rad2 = 0
        cs_rad2 = 0
    else:
        with ncopen(fn2, timeout=300) as nc:
            rad2 = nc.variables['SWGDN'][:7, :, :]
            cs_rad2 = nc.variables['SWGDNCLR'][:7, :, :]

    # W m-2 -> J m-2 s-1 -> J m-2 dy-1
    total = (np.sum(rad, 0) + np.sum(rad2, 0)) * 3600.0
    cs_total = (np.sum(cs_rad, 0) + np.sum(cs_rad2, 0)) * 3600.0

    ccursor.execute("""
        SELECT station, ST_x(geom), ST_y(geom), temp24_hour
        from alldata a JOIN stations t on
        (a.station = t.id) where day = %s and network ~* 'CLIMATE'
    """, (date.strftime("%Y-%m-%d"), ))
    for row in ccursor:
        (x, y) = (row[1], row[2])
        (gridxs, gridys, distances) = get_gp(xc, yc, x, y)

        z0 = total[gridys[0], gridxs[0]]
        z1 = total[gridys[1], gridxs[1]]
        z2 = total[gridys[2], gridxs[2]]
        z3 = total[gridys[3], gridxs[3]]

        val = ((z0/distances[0] + z1/distances[1] + z2/distances[2] +
                z3/distances[3]) / (1./distances[0] + 1./distances[1] +
                                    1./distances[2] + 1./distances[3]))
        # MJ m-2 dy-1
        rad_mj = float(val) / 1000000.0

        z0 = cs_total[gridys[0], gridxs[0]]
        z1 = cs_total[gridys[1], gridxs[1]]
        z2 = cs_total[gridys[2], gridxs[2]]
        z3 = cs_total[gridys[3], gridxs[3]]

        cs_val = ((z0/distances[0] + z1/distances[1] + z2/distances[2] +
                   z3/distances[3]) / (1./distances[0] + 1./distances[1] +
                                       1./distances[2] + 1./distances[3]))
        # MJ m-2 dy-1
        cs_rad_mj = float(cs_val) / 1000000.0

        if rad_mj < 0:
            print('WHOA! Negative RAD: %.2f, station: %s' % (rad_mj, row[0]))
            continue
        # if our station is 12z, then this day's data goes into 'tomorrow'
        # if our station is not, then this day is today
        date2 = date.strftime("%Y-%m-%d")
        if row[3] in range(4, 13):
            date2 = (date + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        ccursor2.execute("""
            UPDATE alldata_"""+row[0][:2]+""" SET merra_srad = %s,
            merra_srad_cs = %s WHERE
            day = %s and station = %s
        """, (rad_mj, cs_rad_mj, date2, row[0]))
    ccursor2.close()
    pgconn.commit()
    pgconn.close()


def main(argv):
    """Go Main Go"""
    if len(argv) == 4:
        do(datetime.datetime(int(argv[1]), int(argv[2]),
                             int(argv[3])))
    if len(argv) == 3:
        # Run for a given month!
        sts = datetime.datetime(int(argv[1]), int(argv[2]), 1)
        # run for last date of previous month as well
        sts = sts - datetime.timedelta(days=1)
        ets = sts + datetime.timedelta(days=45)
        ets = ets.replace(day=1)
        now = sts
        while now < ets:
            do(now)
            now += datetime.timedelta(days=1)


if __name__ == '__main__':
    main(sys.argv)
