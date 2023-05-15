# -*- coding: utf-8 -*-
import c3po

from icoco_openmc import ICoCo_OpenMC
from icoco_dummy_thermic import ICoCo_dummy_thermique

def run():
    neutro = ICoCo_OpenMC("fuel_assembly")
    thermo = ICoCo_dummy_thermique("fuel_assembly")

    remapper = c3po.Remapper()
    thermo_2_neutro_method = c3po.SharedRemapping(remapper)

    thermo_2_neutro = c3po.LocalExchanger(thermo_2_neutro_method, [(thermo, "fuel_temperature")], [(neutro, "fuel_temperature")])

    neutro.init()
    thermo.init()

    neutro.setStationaryMode(True)
    thermo.setStationaryMode(True)

    neutro.initTimeStep(0.)
    thermo.initTimeStep(0.)

    thermo.solveTimeStep()
    thermo_2_neutro.exchange()
    neutro.solveTimeStep()

    neutro.validateTimeStep()
    thermo.validateTimeStep()

    neutro.term()
    thermo.term()
