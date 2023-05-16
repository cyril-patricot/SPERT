# -*- coding: utf-8 -*-
import medcoupling as mc


def make_mesh_cart(x_coords, y_coords, z_coords):
    array_X = mc.DataArrayDouble(x_coords)
    array_X.setInfoOnComponent(0, "X [m]")
    array_Y = mc.DataArrayDouble(y_coords)
    array_Y.setInfoOnComponent(0, "Y [m]")
    array_Z = mc.DataArrayDouble(z_coords) if z_coords else None
    mesh = mc.MEDCouplingCMesh("CartesianMesh")
    mesh.setCoords(array_X, array_Y, array_Z)
    return mesh.buildUnstructured()


def make_field(nature, mesh):
    field = mc.MEDCouplingFieldDouble.New(mc.ON_CELLS)
    field.setMesh(mesh)
    num_cells = mesh.getNumberOfCells()
    values = [1.] * num_cells
    array = mc.DataArrayDouble.New()
    array.setValues(values, len(values), 1)
    field.setArray(array)
    field.setName("cartesianField")
    field.setNature(nature)
    return field


def make_fuel_assembly_mesh():
    pitch = 1.4859
    num_cells = 5
    z_coords = [0., 97.282]
    x_coords = [- pitch * num_cells / 2.]
    for i in range(5):
        x_coords.append(x_coords[-1] + pitch)
    y_coords = []
    y_coords[:] = x_coords[:]
    return make_mesh_cart(x_coords, y_coords, z_coords)
