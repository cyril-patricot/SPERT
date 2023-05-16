# -*- coding: utf-8 -*-
import c3po

from icoco_openmc import ICoCo_OpenMC
from icoco_dummy_thermic import ICoCo_dummy_thermique


class One_iteration(c3po.Coupler):
    def __init__(self, physics, exchangers, dataManagers=[]):
        c3po.Coupler.__init__(self, physics, exchangers, dataManagers)

    def solveTimeStep(self):
        self._physicsDrivers["neutro"].solve()
        self._exchangers["neutro_2_thermo"].exchange()
        self._physicsDrivers["thermo"].solve()
        return self.getSolveStatus()


def run():
    neutro = ICoCo_OpenMC("fuel_assembly")
    thermo = ICoCo_dummy_thermique("fuel_assembly", T0=300., alpha=0.002)
    data = c3po.LocalDataManager()

    remapper = c3po.Remapper()
    thermo_2_neutro_method = c3po.SharedRemapping(remapper, reverse=False)
    neutro_2_thermo_method = c3po.SharedRemapping(remapper, reverse=True)

    neutro_2_thermo = c3po.LocalExchanger(neutro_2_thermo_method, [(neutro, "power")], [(thermo, "power")])
    thermo_2_data = c3po.LocalExchanger(thermo_2_neutro_method, [(thermo, "fuel_temperature")], [(data, "fuel_temperature")])
    data_2_neutro = c3po.LocalExchanger(thermo_2_neutro_method, [(data, "fuel_temperature")], [(neutro, "fuel_temperature")])

    coupling_iteration = One_iteration({"neutro" : neutro, "thermo" : thermo}, {"neutro_2_thermo" : neutro_2_thermo})

    picard_coupling = c3po.FixedPointCoupler([coupling_iteration], [thermo_2_data, data_2_neutro], [data])
    picard_coupling.setDampingFactor(1.)
    picard_coupling.setConvergenceParameters(1E-2, 100)
    picard_coupling.setNormChoice(c3po.NormChoice.norm2)

    picard_coupling.init()
    neutro.setInputDoubleValue("power", 1.E6)
    picard_coupling.setStationaryMode(True)
    picard_coupling.initTimeStep(0.)
    picard_coupling.solve()
    picard_coupling.validateTimeStep()
    picard_coupling.term()
