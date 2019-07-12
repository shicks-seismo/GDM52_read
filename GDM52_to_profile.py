#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 11 15:10:13 2019
Read in GDM52 surface wave model .mat file and Rayleigh wave 
Model info: https://www.ldeo.columbia.edu/~ekstrom/Projects/SWP/GDM52.html
This was made for analysis of surface wave velocities for Mach cone analysis
@author: S. Hicks
"""

from scipy import io
import numpy as np
import subprocess
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
import os

# Start of parameters to define
e_lat = -0.02  # Event latitude
e_lon = -17.80  # Event longitude
az = [320, 200]  # Azimuth for each path
dist = [82, 60]  # Max dist for each path
input_mat = "GDM52.mat"
periods = [25, 31.25, 50]  # List of periods (s) to include
# End of parameters to define

# Make interpolated grid of velocities
gdm52 = io.loadmat(input_mat)

# Find index of periods of interest
period_idx = [n for period in periods for n, freq in enumerate(gdm52["f"])
              if freq == 1/(period*1e-3)]

# Prepare figure
fig = plt.figure(figsize=(10, 10))

# Make 2D grid file containing velocities for each period
for n_per, period in enumerate(periods):
    w = open("gdm52_T.tmp", "w")
    vels = []
    lats = gdm52["lat"]
    lons = gdm52["lon"]
    for x, lon in enumerate(lons[0]):
        for y, lat in enumerate(lats[0]):
            w.write("{:4.0f} {:3.0f} {:5.1f}\n".format(
                    lon, lat, float(gdm52["c_all"][y, x, period_idx[n_per]])))
    w.close()
    cmd = ["gmt", "surface", "gdm52_T.tmp", "-I1", "-Rg",
           "-GT{:}.grd".format(period)]
    subprocess.check_call(cmd)
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         executable='/bin/bash')
    os.remove("gdm52_T.tmp")

# Make track of lon, lat points
for n_path in range(0, len(az)):
    w = open("track.in", "w")
    cmd = ["gmt", "project", "-C{:}/{:}".format(e_lon, e_lat), "-G1",
           "-A{:}".format(az[n_path]), "-L0/{:}".format(str(dist[n_path]))]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    output, error = p.communicate()
    for n, l in enumerate(output.decode('utf-8').split("\n")[:-1]):
        w.write("{:} {:} {:}\n".format(l.split("\t")[0],
                l.split("\t")[1], l.split()[2]))
    w.close()

    # Now track through velocity grid to get 1-D profile along each azimuth
    color = iter(cm.rainbow(np.linspace(0, 1, len(periods))))
    for period in periods:
        cmd = ["gmt", "grdtrack", "track.in".format(n_path),
               "-GT{:}.grd".format(period)]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        output, error = p.communicate()
        output = output.decode('utf-8').split("\n")[:-1]
        dist_all, vs = zip(*[[float(l.split()[2]), float(l.split()[3])]
                             for l in output])

        # Now plot
        ax = plt.subplot(2, 1, n_path+1)
        c = next(color)
        ax.plot(dist_all, vs, label="T={:4.1f}s".format(period), c=c,
                linewidth=2)
        if 180 <= az[n_path] <= 270:
            dir = "SW"
        elif 270 <= az[n_path] <= 360:
            dir = "NW"
        ax.axhline(np.mean(vs), linestyle="--", c=c)
        ax.set_title("{:} azimuth {:}$^\u00b0$".format(dir, az[n_path]))
        ax.set_xlabel("Epicentral distance($^{\u00b0}$)")
        ax.set_ylabel("Rayleigh wave phase velocity (km/s)")
        ax.set_ylim([3.5, 4.2])
        ax.set_xlim([0, 85])
        ax.legend()
    
plt.suptitle("Rayleigh wave velocites from GDM52 model "
             "(Ekstrom et al., 2011)\n"
             "Epicentral distances relative to 2016 Romanche hypocentre")
plt.show()
