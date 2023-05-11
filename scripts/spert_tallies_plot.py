# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import numpy as np
import matplotlib.pyplot as plt
import openmc

# plot energy and mesh tally
sp_file_name = 'statepoint.150.h5'
sp = openmc.StatePoint(sp_file_name)
for i in range(1, len(sp.tallies)+1):
    tal = sp.get_tally(id=i)
    val_mean = tal.get_values(value='mean').squeeze()
    plt.figure()
    if tal.name.find('Energy') != -1:  # energy tallies
        energy = tal.filters[0].values    
        plt.semilogx(energy[1:],val_mean)
        plt.xlabel('energy [eV]')
        plt.ylabel('reactions per source particle')
        plt.grid()
    if tal.name.find('Mesh') != -1:  # mesh tallies
        pt = int(np.sqrt(len(val_mean)))  # number of mesh point in each direction
        val_mean = val_mean.reshape(pt, pt)
        pf = int(pt/8)  # number of mesh point for each fuel assembly
        val_mean[:pf, :pf] = np.nan
        val_mean[:pf, -pf:] = np.nan
        val_mean[-pf:, :pf] = np.nan
        val_mean[-pf:, -pf:] = np.nan
        x, y = np.meshgrid(np.linspace(-12*2.54, 12*2.54, pt), np.linspace(-12*2.54,12*2.54, pt))
        cmap = plt.get_cmap('Spectral')
        plt.pcolormesh(x, y, val_mean, cmap=cmap)
        plt.xlabel('x [cm]')
        plt.ylabel('y [cm]')
        plt.colorbar()
    plt.title(tal.name)
    plt.savefig(tal.name)
