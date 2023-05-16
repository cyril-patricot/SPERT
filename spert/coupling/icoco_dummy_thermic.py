# -*- coding: utf-8 -*-
import medcoupling as mc
import c3po

import spert.coupling.med_builder as med_builder


class ICoCo_dummy_thermique(c3po.PhysicsDriver):

    def __init__(self, case, T0=300., alpha=1.):
        super().__init__()
        if case != "fuel_assembly":
            raise ValueError("Only fuel_assembly is supported.")
        self._case = case
        self._T0 = T0
        self._alpha = alpha
        self._field_T = None
        self._field_P = None
        self._stationaryMode = False
        self._time = 0.
        self._dt = None

    def initialize(self):
        if self._case == "fuel_assembly":
            self._mesh = med_builder.make_fuel_assembly_mesh()
        self._mesh.scale([0., 0., 0.], 0.01)    #cm -> m
        self._field_T = med_builder.make_field(mc.IntensiveMaximum, self._mesh)
        self._field_P = med_builder.make_field(mc.ExtensiveMaximum, self._mesh)
        self._field_P.getArray().fillWithZero()
        self._stationaryMode = False
        self._time = 0.
        self._dt = None
        return True

    def terminate(self):
        self._field_T = None
        self._field_P = None
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
            array_T = self._field_T.getArray()
            for i, value_P in enumerate(self._field_P.getArray()):
                array_T.setIJ(i, 0, self._T0 + self._alpha * value_P[0])
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
        return ["power"]

    def getOutputFieldsNames(self):
        return["fuel_temperature"]

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
        if name == "power":
            fielTemplate = med_builder.make_field(mc.ExtensiveMaximum, self._mesh.deepCopy())
            fielTemplate.setName("power")
            return fielTemplate
        raise ValueError(f"Unknown field {name}.")

    def setInputMEDDoubleField(self, name, field):
        if name == "power":
            self._field_P = field
        else:
            raise ValueError(f"Unknown field {name}.")

    def getOutputMEDDoubleField(self, name):
        if name == "fuel_temperature":
            return self._field_T.deepCopy()
        raise ValueError(f"Unknown field {name}.")

    def updateOutputMEDDoubleField(self, name, field):
        if name == "fuel_temperature":
            field.setArray(self._field_T.getArray().deepCopy)
        else:
            raise ValueError(f"Unknown field {name}.")
