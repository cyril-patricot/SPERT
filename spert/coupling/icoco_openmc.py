# -*- coding: utf-8 -*-
import openmc.lib

import medcoupling as mc
import c3po

import spert.coupling.med_builder as med_builder


class ICoCo_OpenMC(c3po.PhysicsDriver):

    def __init__(self, case):
        super().__init__()
        if case != "fuel_assembly":
            raise ValueError("Only fuel_assembly is supported.")
        self._case = case
        self._tallies = {}
        self._total_power = 1.
        self._mesh = None
        self._cells = []
        self._instances = []
        self._stationaryMode = False
        self._time = 0.
        self._dt = None

    def initialize(self):
        openmc.lib.init()
        if self._case == "fuel_assembly":
            self._mesh = med_builder.make_fuel_assembly_mesh()
        centers_of_mass = self._mesh.computeCellCenterOfMass()
        self._mesh.scale([0., 0., 0.], 0.01)    #cm -> m
        self._cells = []
        self._instances = []
        for center in centers_of_mass:
            cell, instance = openmc.lib.find_cell(center)
            self._cells.append(cell)
            self._instances.append(instance)
        self._tallies["heating"] = openmc.lib.Tally(uid=1, new=False)
        self._tallies["fission"] = openmc.lib.Tally(uid=2, new=False)
        self._stationaryMode = False
        self._time = 0.
        self._dt = None
        return True

    def terminate(self):
        openmc.lib.finalize()
        self._tallies = {}
        self._total_power = 1.
        self._mesh = None
        self._cells = []
        self._instances = []
        self._stationaryMode = False
        self._time = 0.
        self._dt = None

    def presentTime(self):
        return self._time

    def computeTimeStep(self):
        return(1.E30, False)

    def initTimeStep(self, dt):
        if not self._stationaryMode:
            raise ValueError("Only stationary mode is supported.")
        if dt != 0:
            raise ValueError("Only steady-states are supported.")
        self._dt = dt
        return True

    def solveTimeStep(self):
        if self._dt == 0:
            openmc.lib.run()
            return True
        else:
            raise ValueError("This kind of calculation is not supported.")

    def validateTimeStep(self):
        self._time += self._dt
        self._dt = None

    def abortTimeStep(self):
        self._dt = None

    def setStationaryMode(self, stationaryMode):
        self._stationaryMode = stationaryMode

    def getStationaryMode(self):
        return self._stationaryMode

    def resetTime(self, time_):
        self._time = time_

    def getInputFieldsNames(self):
        return ["fuel_temperature"]

    def getOutputFieldsNames(self):
        return["power"]

    def getFieldType(self, name):
        if name in ["fuel_temperature", "power"]:
            return 'Double'
        raise ValueError(f"Unknown field {name}.")

    def getMeshUnit(self):
        return "m"

    def getFieldUnit(self, name):
        if name == "fuel_temperature":
            return 'K'
        elif name == "power":
            return 'W'
        raise ValueError(f"Unknown field {name}.")

    def getInputMEDDoubleFieldTemplate(self, name):
        if name == "fuel_temperature":
            fielTemplate = med_builder.make_field(mc.IntensiveMaximum, self._mesh.deepCopy())
            array = fielTemplate.getArray()
            for i, _ in enumerate(array):
                array.setIJ(i, 0, self._instances[i])
            fielTemplate.setName("fuel_temperature")
            return fielTemplate
        raise ValueError(f"Unknown field {name}.")

    def setInputMEDDoubleField(self, name, field):
        if name == "fuel_temperature":
            array = field.getArray()
            for i, value in enumerate(array):
                self._cells[i].set_temperature(value, instance=self._instances[i])
        else:
            raise ValueError(f"Unknown field {name}.")

    def getOutputMEDDoubleField(self, name):
        if name == "power":
            field_P = med_builder.make_field(mc.ExtensiveMaximum, self._mesh.deepCopy())
            self.updateOutputMEDDoubleField(name, field_P)
            return field_P
        raise ValueError(f"Unknown field {name}.")

    def updateOutputMEDDoubleField(self, name, field):
        if name == "power":
            array = field.getArray()
            sum_power = 0.
            for i in range(len(array)):
                local_power = self._tallies["heating"].mean[self._instances[i]][0]
                sum_power += local_power
                array.setIJ(i, 0, local_power)
            array *= (self._total_power / sum_power)
        else:
            raise ValueError(f"Unknown field {name}.")

    def getInputValuesNames(self):
        return ["power"]

    def getValueType(self, name):
        if name == "power":
            return 'Double'
        raise ValueError(f"Unknown value {name}.")

    def getValueUnit(self, name):
        if name == "power":
            return 'W'
        raise ValueError(f"Unknown value {name}.")

    def setInputDoubleValue(self, name, value):
        if name == "power":
            self._total_power = value
        else:
            raise ValueError(f"Unknown value {name}.")
