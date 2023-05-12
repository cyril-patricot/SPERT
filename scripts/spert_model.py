import numpy as np
from pathlib import Path
import openmc

energy_structure_filename = 'EG_SHEM_281.txt'
energy_structure_path = Path(__file__).parent / energy_structure_filename

###################
# Core parameters #
###################
# ALL UNITS: centimeters

# Pincell
pincell_fuel_radius = 0.21 * 2.54
pincell_airgap_width = 0.003 * 2.54
pincell_clad_width = 0.02 * 2.54

# Fuel Assembly (FA5X5)
num_pins = 5
pincell_pitch = 0.585 * 2.54
flux_suppr_width = 0.03 * 2.54  # width of flux suppressor
FA5X5_box_width = 0.025 * 2.54
FA_out_water_gap = 0.0125 * 2.54
FA5X5_box_in_sec = pincell_pitch * float(num_pins)  # FA5X5 box inner section
FA5X5_box_out_sec = pincell_pitch * float(num_pins) + 2 * FA5X5_box_width  # FA5X5 box outer section
FA5X5_total_sec = FA5X5_box_out_sec + 2 * FA_out_water_gap  # FA5X5 total outer section (3 inch)
FA_height = 38.3 * 2.54  # fuel assembly height (z direction)

# Control Rod (CR) - includes: guide tube (GT), absorber section (AS) and fuel follower (FF)
GT_width = 0.3  # guide tube width (0.11811 inch)
GT_out_sec = FA5X5_total_sec - FA_out_water_gap * 2.0  # guide tube outer section (2.975 inch)
GT_in_sec = GT_out_sec - GT_width * 2.0  # guide tube inner section (2.73878 inch)
absorber_out_sec = 2.496 * 2.54  # absorber (or FF clad) outer section
absorber_width = 0.186 * 2.54  # absorber width
absorber_in_sec = absorber_out_sec - 2.0 * absorber_width  # absorber inner section (2.124 inch)
water_strip_clad_FF = 0.00565 * 2.54  # water strip between box and pincells
FF_box_width = (absorber_out_sec - pincell_pitch * 4.0 - 2.0 * water_strip_clad_FF) / 2.0  # FF box width (0.07235 inch)
FF_box_in_sec = absorber_out_sec - 2.0 * FF_box_width  # FF box inner section (2.3513 inch)
FF_fuel_sec = pincell_pitch * 4.0 - flux_suppr_width * 2.0  # FF fuel section (2.34 inch)

# Transient Rod (TR)
FA4X4_lattice_pitch = pincell_pitch * 4.0  # fuel assembly 4X4 inside TR (2.34 inch)
FA4X4_inner_water_strip = 0.043 * 2.54  # between 4X4 pincells and cladding
FA4X4_outer_water_strip = 0.02014 * 2.54  # between 4X4 clad and GT
FA4X4_box_in_sec = FA4X4_lattice_pitch + 2.0 * FA4X4_inner_water_strip  # 2.426 inch
FA4X4_box_out_sec = FA4X4_box_in_sec + 2.0 * FA5X5_box_width  # 2.476 inch
FA4X4_GT_in_sec = FA4X4_box_out_sec + 2.0 * FA4X4_outer_water_strip  # 2.51628 inch
FA4X4_GT_out_sec = FA4X4_GT_in_sec + 2.0 * GT_width  # 2.7525 inch
orig_cor = FA5X5_total_sec / 2.0 - (
        FA4X4_GT_out_sec / 2.0 + FA_out_water_gap)  # origin correction for 4X4 (0.11125 inch)
TR_absorber_thick = 0.1875 * 2.54 / 2.0  # half thickness of cruciform transient rod (0.09375 inch)
TR_absorber_width = 5.1250 * 2.54 / 2.0  # half width of cruciform transient rod (2.5625 inch)

# Fillers
filler_box_width = 0.125 * 2.54  # thickness of filler box (0.3175 cm)
filler_box_out_sec = FA5X5_box_out_sec
filler_box_in_sec = filler_box_out_sec - 2.0 * filler_box_width

# Vessel layers
skirt_width = 0.625 * 2.54
skirt_in_rad = 32.0 / 2.0 * 2.54
skirt_out_rad = skirt_in_rad + skirt_width
SH1_width = 0.874 * 2.54
SH1_in_rad = 34.252 / 2.0 * 2.54
SH1_out_rad = SH1_in_rad + SH1_width
SH2_width = 1.0 * 2.54
SH2_in_rad = 36.87902 / 2.0 * 2.54
SH2_out_rad = SH2_in_rad + SH2_width
SH3_width = 1.25 * 2.54
SH3_in_rad = 39.75197 / 2.0 * 2.54
SH3_out_rad = SH3_in_rad + SH3_width
SH4_width = 2.0 * 2.54
SH4_in_rad = 43.25197 / 2.0 * 2.54
SH4_out_rad = SH4_in_rad + SH4_width
vessel_width = 3.25 * 2.54
vessel_in_rad = 48.0 / 2.0 * 2.54
vessel_out_rad = vessel_in_rad + vessel_width
bioShield_width = 6.0 * 2.54
bioShield_out_rad = vessel_out_rad + bioShield_width

# Axial spring and plug
spring_height = 2.5 * 2.54  # height of expansion spring
core_height = 52.75 * 2.54  # height of core (end plugs)


def gen_materials(config):
    """
    Generates HolosGen Reactor materials.

    Returns
    -------

    mat_dict : dictionary
        A dictionary of materials in the mats list
        constructed using the variable names of the
        materials generated below.
    """

    # Configuration Options
    use_sab = config.getboolean('use_sab')
    if config['core_condition'] == 'CZP':  # Cold Zero Power
        fuel_temp = 294.0
        core_temp = 294.0
    elif config['core_condition'] == 'HZP':  # Hot Zero Power
        fuel_temp = 560.0
        core_temp = 560.0
    elif config['core_condition'] == 'vartemp':  # choose temperatures
        #fuel_temp = config['fuel_temp']
        fuel_temp = 294.0
        #core_temp = config['core_temp']
        core_temp = 294.0


    materials = []

    # fuel: UO2, 4.8% enrichment (table A.1)
    mat_fuel = openmc.Material(name='fuel', temperature=fuel_temp, material_id=1)
    mat_fuel.add_nuclide('U234', 9.515411E-06, 'ao')
    mat_fuel.add_nuclide('U235', 1.138169E-03, 'ao')
    mat_fuel.add_nuclide('U236', 4.484248E-06, 'ao')
    mat_fuel.add_nuclide('U238', 2.227459E-02, 'ao')
    mat_fuel.add_nuclide('O16',  4.687800E-02, 'ao')
    mat_fuel.set_density('sum')
    materials.append(mat_fuel)

    # moderator: light water (table A.2)
    mat_mod = openmc.Material(name='moderator', temperature=core_temp, material_id=2)
    if config['core_condition'] == 'CZP':  # Cold Zero Power
        mat_mod.add_nuclide('H1',  6.625258E-02, 'ao')
        mat_mod.add_nuclide('O16', 3.340031E-02, 'ao')
    elif config['core_condition'] == 'HZP':  # Hot Zero Power
        mat_mod.add_nuclide('H1',  5.091219E-02, 'ao')
        mat_mod.add_nuclide('O16', 2.545609E-02, 'ao')
    elif config['core_condition'] == 'vartemp':  # choose temperatures
        #TODO This part needs correction for density depending on temperature!
        mat_mod.add_nuclide('H1', 6.625258E-02, 'ao')
        mat_mod.add_nuclide('O16', 3.340031E-02, 'ao')

    if use_sab:
        mat_mod.add_s_alpha_beta('c_H_in_H2O')
    mat_mod.set_density('sum')
    materials.append(mat_mod)

    # filler (and upper part of transient rod): SS304 stainless steel (table A.3)
    mat_filler = openmc.Material(name='filler', temperature=core_temp, material_id=3)
    mat_filler.add_nuclide('C0',   1.592403E-04, 'ao')
    mat_filler.add_element('Cr',   1.747206E-02, 'ao')
    mat_filler.add_nuclide('Mn55', 8.703382E-04, 'ao')
    mat_filler.add_element('N',    1.706850E-04, 'ao')
    mat_filler.add_element('Ni',   7.535529E-03, 'ao')
    mat_filler.add_element('P',    3.473360E-05, 'ao')
    mat_filler.add_element('Si',   8.927089E-04, 'ao')
    mat_filler.add_element('S',    2.236770E-05, 'ao')
    mat_filler.add_element('Fe',   6.014615E-02, 'ao')
    mat_filler.set_density('sum')
    materials.append(mat_filler)

    # radial shield: SS304L stainless steel (table A.4)
    mat_shield = openmc.Material(name='radial shield', temperature=core_temp, material_id=4)
    mat_shield.add_nuclide('C0',   5.971510E-05, 'ao')
    mat_shield.add_element('Cr',   1.747206E-02, 'ao')
    mat_shield.add_nuclide('Mn55', 8.703382E-04, 'ao')
    mat_shield.add_element('N',    1.706850E-04, 'ao')
    mat_shield.add_element('Ni',   8.146517E-03, 'ao')
    mat_shield.add_element('P',    3.473360E-05, 'ao')
    mat_shield.add_element('Si',   8.927089E-04, 'ao')
    mat_shield.add_element('S',    2.236770E-05, 'ao')
    mat_shield.add_element('Fe',   5.952540E-02, 'ao')
    mat_shield.set_density('sum')
    materials.append(mat_shield)

    # fuel clad: SS348 stainless steel (table A.5)
    mat_clad = openmc.Material(name='clad', temperature=core_temp, material_id=5)
    mat_clad.add_nuclide('C0',    1.604436E-04)
    mat_clad.add_element('Cr',    1.667756E-02)
    mat_clad.add_nuclide('Mn55',  8.769151E-04)
    mat_clad.add_element('Ni',    9.028886E-03)
    mat_clad.add_element('P',     3.499607E-05)
    mat_clad.add_element('Si',    8.994548E-04)
    mat_clad.add_element('S',     2.253672E-05)
    mat_clad.add_element('Nb',    2.074174E-04)
    mat_clad.add_nuclide('Ta181', 1.331212E-05)
    mat_clad.add_element('Co',    8.174680E-05)
    mat_clad.add_element('Fe',    5.952231E-02)
    mat_clad.set_density('sum')
    materials.append(mat_clad)

    # absorber: SS304B5 stainless steel (1.35% borated steel) (table A.6)
    mat_absorber = openmc.Material(name='absorber', temperature=core_temp, material_id=6)
    mat_absorber.add_nuclide('B10',  6.324854E-03, 'ao')
    mat_absorber.add_nuclide('C0',   1.562320E-04, 'ao')
    mat_absorber.add_element('Co',   7.960094E-05, 'ao')
    mat_absorber.add_element('Cr',   1.714198E-02, 'ao')
    mat_absorber.add_nuclide('Mn55', 8.538961E-04, 'ao')
    mat_absorber.add_element('N',    1.674605E-04, 'ao')
    mat_absorber.add_element('Ni',   1.079003E-02, 'ao')
    mat_absorber.add_element('P',    3.407742E-05, 'ao')
    mat_absorber.add_element('Si',   8.758441E-04, 'ao')
    mat_absorber.add_element('S',    2.194513E-05, 'ao')
    mat_absorber.add_element('Fe',   5.422173E-02, 'ao')
    mat_absorber.set_density('sum')
    materials.append(mat_absorber)

    # bioligical shield: lead (table A.7)
    mat_bioShield = openmc.Material(name='bio-shield', temperature=core_temp, material_id=7)
    mat_bioShield.add_nuclide('Pb207', 3.306467E-02, 'ao')
    mat_bioShield.add_nuclide('Sb121', 5.663191E-06, 'ao')
    mat_bioShield.add_nuclide('As75',  9.138906E-06, 'ao')
    mat_bioShield.add_nuclide('Sn119', 5.758472E-06, 'ao')
    # mat_bioShield.add_nuclide('Cu65', 1.581837E-05, 'ao')
    mat_bioShield.add_nuclide('Ag107', 3.202380E-06, 'ao')
    mat_bioShield.set_density('sum')
    materials.append(mat_bioShield)

    # guide tube: Zircaloy-2 (table A.8)
    mat_GT = openmc.Material(name='Guide tube', temperature=core_temp, material_id=8)
    mat_GT.add_nuclide('Fe54',  5.5735E-06, 'ao')
    mat_GT.add_nuclide('Fe56',  8.7491E-05, 'ao')
    mat_GT.add_nuclide('Fe57',  2.0205E-06, 'ao')
    mat_GT.add_nuclide('Fe58',  2.6890E-07, 'ao')
    mat_GT.add_nuclide('Cr50',  3.2962E-06, 'ao')
    mat_GT.add_nuclide('Cr52',  6.3563E-05, 'ao')
    mat_GT.add_nuclide('Cr53',  7.2075E-06, 'ao')
    mat_GT.add_nuclide('Cr54',  1.7941E-06, 'ao')
    mat_GT.add_nuclide('Ni58',  2.5163E-05, 'ao')
    mat_GT.add_nuclide('Ni60',  9.6927E-06, 'ao')
    mat_GT.add_nuclide('Ni61',  4.2137E-07, 'ao')
    mat_GT.add_nuclide('Ni62',  1.3432E-06, 'ao')
    mat_GT.add_nuclide('Ni64',  3.4228E-07, 'ao')
    mat_GT.add_nuclide('Sn114', 3.1317E-06, 'ao')
    mat_GT.add_nuclide('Sn115', 1.6381E-06, 'ao')
    mat_GT.add_nuclide('Sn116', 7.0006E-05, 'ao')
    mat_GT.add_nuclide('Sn117', 3.7002E-05, 'ao')
    mat_GT.add_nuclide('Sn118', 1.1674E-04, 'ao')
    mat_GT.add_nuclide('Sn119', 4.1387E-05, 'ao')
    mat_GT.add_nuclide('Sn120', 1.5702E-04, 'ao')
    mat_GT.add_nuclide('Sn122', 2.2308E-05, 'ao')
    mat_GT.add_nuclide('Sn124', 2.7897E-05, 'ao')
    mat_GT.add_nuclide('O16',   2.9581E-04, 'ao')
    mat_GT.add_element('Zr',    4.2435E-02, 'ao')
    mat_GT.set_density('sum')
    materials.append(mat_GT)

    mat_FA5X5box = openmc.Material(name='FA5X5 box', temperature=core_temp, material_id=9)
    mat_FA5X5box.add_nuclide('C0',    1.203327E-04, 'ao')
    mat_FA5X5box.add_element('Cr',    1.250817E-02, 'ao')
    mat_FA5X5box.add_nuclide('Mn55',  6.576863E-04, 'ao')
    mat_FA5X5box.add_element('Ni',    6.771664E-03, 'ao')
    mat_FA5X5box.add_element('P',     2.624705E-05, 'ao')
    mat_FA5X5box.add_element('Si',    6.745911E-04, 'ao')
    mat_FA5X5box.add_element('S',     1.690254E-05, 'ao')
    mat_FA5X5box.add_element('Nb',    1.555631E-04, 'ao')
    mat_FA5X5box.add_nuclide('Ta181', 9.984090E-06, 'ao')
    mat_FA5X5box.add_element('Co',    6.131010E-05, 'ao')
    mat_FA5X5box.add_element('Fe',    4.464173E-02, 'ao')
    mat_FA5X5box.add_nuclide('H1',    1.656315E-02, 'ao')
    mat_FA5X5box.add_nuclide('O16',   8.350076E-03, 'ao')
    if use_sab:
        mat_FA5X5box.add_s_alpha_beta('c_H_in_H2O')
    mat_FA5X5box.set_density('sum')
    materials.append(mat_FA5X5box)

    # helium: between fuel and clad
    mat_helium = openmc.Material(name='helium', temperature=core_temp, material_id=10)
    mat_helium.add_nuclide('He3', 4.80890E-10, 'ao')
    mat_helium.add_nuclide('He4', 2.40440E-04, 'ao')
    mat_helium.set_density('sum')
    materials.append(mat_helium)

    # expansion spring: clad with density 5% (homogenized)
    mat_spring = openmc.Material(name='expansion spring', temperature=core_temp, material_id=11)
    mat_spring.add_nuclide('C0',    8.022180E-06, 'ao')
    mat_spring.add_element('Cr',    8.338779E-04, 'ao')
    mat_spring.add_nuclide('Mn55',  4.384575E-05, 'ao')
    mat_spring.add_element('Ni',    4.514443E-04, 'ao')
    mat_spring.add_element('P',     1.749804E-06, 'ao')
    mat_spring.add_element('Si',    4.497274E-05, 'ao')
    mat_spring.add_element('S',     1.126836E-06, 'ao')
    mat_spring.add_element('Nb',    1.037087E-05, 'ao')
    mat_spring.add_nuclide('Ta181', 6.656060E-07, 'ao')
    mat_spring.add_element('Co',    4.087340E-06, 'ao')
    mat_spring.add_element('Fe',    2.976116E-03, 'ao')
    mat_spring.set_density('sum')
    materials.append(mat_spring)

    mat_dict = {}
    for k, v in list(locals().items()):
        if v in materials:
            mat_dict[k] = v

    return mat_dict


############
# Geometry #
############


def gen_geometry(mat_dict, config):
    """
    Generates the SPERT-3 reactor geometry.

    Parameters
    ----------

    mat_dict : dict
        A dictionary of OpenMC materials.

    config : ConfigParser
        A config parser of spert

    Returns
    -------
    openmc.Geometry
        An OpenMC.Geometry of the HolosGen reactor.
    """

    valid_mats = isinstance(mat_dict, dict) and all(isinstance(v, openmc.Material) for v in mat_dict.values())
    assert valid_mats, "Please provide a dictionary of OpenMC materials for mat_dict parameter."

    # Z-planes for fuel assembly
    s901 = openmc.ZPlane(z0=0.0, surface_id=901)
    s902 = openmc.ZPlane(z0=FA_height, surface_id=902)
    if config['core_dimensions'] == '2D':
        s901.boundary_type = 'reflective'
        s902.boundary_type = 'reflective'
    elif config['core_dimensions'] == '3D':
        s901.boundary_type = 'vacuum'
        s902.boundary_type = 'vacuum'

    ###########
    # pincell #
    ###########
    s11 = openmc.ZCylinder(r=pincell_fuel_radius, surface_id=11)  # fuel inner radius
    s12 = openmc.ZCylinder(r=pincell_fuel_radius + pincell_airgap_width, surface_id=12)  # clad inner radius
    s13 = openmc.ZCylinder(r=pincell_fuel_radius + pincell_airgap_width + pincell_clad_width,
                           surface_id=13)  # clad out rad
    s141 = openmc.XPlane(x0=-(pincell_pitch-flux_suppr_width)/2.0, surface_id=141)
    s142 = openmc.XPlane(x0=+(pincell_pitch-flux_suppr_width)/2.0, surface_id=142)
    s143 = openmc.YPlane(y0=-(pincell_pitch-flux_suppr_width)/2.0, surface_id=143)
    s144 = openmc.YPlane(y0=+(pincell_pitch-flux_suppr_width)/2.0, surface_id=144)
    s151 = openmc.XPlane(x0=-pincell_pitch/2.0, surface_id=151)
    s152 = openmc.XPlane(x0=+pincell_pitch/2.0, surface_id=152)
    s153 = openmc.YPlane(y0=-pincell_pitch/2.0, surface_id=153)
    s154 = openmc.YPlane(y0=+pincell_pitch/2.0, surface_id=154)
    if config['model_type'] == 'pincell':
        for surf in [s151, s152, s153, s154]:
            surf.boundary_type = 'reflective'

    # pincell WITHOUT flux suppressor:
    c110 = openmc.Cell(cell_id=110, fill=mat_dict["mat_fuel"], region=-s11)
    c120 = openmc.Cell(cell_id=120, fill=mat_dict["mat_helium"], region=+s11 & -s12)
    c130 = openmc.Cell(cell_id=130, fill=mat_dict["mat_clad"], region=+s12 & -s13)
    c140 = openmc.Cell(cell_id=140, fill=mat_dict["mat_mod"], region=+s13 & +s141 & -s142 & +s143 & -s144)
    c151 = openmc.Cell(cell_id=151, fill=mat_dict["mat_mod"])
    c151.region = (-s141 | +s142 | -s143 | +s144) & +s151 & -s152 & +s153 & -s154
    u11 = openmc.Universe(universe_id=11, cells=[c110, c120, c130, c140, c151])

    # pincell WITH flux suppressor:
    c111 = openmc.Cell(cell_id=111, fill=mat_dict["mat_fuel"], region=-s11)
    c121 = openmc.Cell(cell_id=121, fill=mat_dict["mat_helium"], region=+s11 & -s12)
    c131 = openmc.Cell(cell_id=131, fill=mat_dict["mat_clad"], region=+s12 & -s13)
    c141 = openmc.Cell(cell_id=141, fill=mat_dict["mat_mod"], region=+s13 & +s141 & -s142 & +s143 & -s144)
    c152 = openmc.Cell(cell_id=152, fill=mat_dict["mat_absorber"])
    c152.region = (-s141 | +s142 | -s143 | +s144) & +s151 & -s152 & +s153 & -s154
    u12 = openmc.Universe(universe_id=12, cells=[c111, c121, c131, c141, c152])

    # define container cell and universe of pincell for tallies
    c161 = openmc.Cell(cell_id=161, name="pincell only - WITHOUT flux suppressor")
    c161.region = +s151 & -s152 & +s153 & -s154 & +s901 & -s902
    c161.fill = u11
    u110 = openmc.Universe(universe_id=110, cells=[c161])  # universe of pincell WITHOUT flux suppressor
    c162 = openmc.Cell(cell_id=162, name="pincell only - WITH flux suppressor")
    c162.region = +s151 & -s152 & +s153 & -s154 & +s901 & -s902
    c162.fill = u12
    u120 = openmc.Universe(universe_id=120, cells=[c162])  # universe of pincell WITH flux suppressor

    if config['model_type'] == 'pincell':
        root_univ = u110
        geom = openmc.Geometry(root_univ)
        return geom

    ###########################
    # Fuel Assembly (FA) 5X5  #
    ###########################
    s211 = openmc.XPlane(x0=-FA5X5_box_in_sec/2.0, surface_id=211)  # FA5X5 box inner section
    s212 = openmc.XPlane(x0=+FA5X5_box_in_sec/2.0, surface_id=212)
    s213 = openmc.YPlane(y0=-FA5X5_box_in_sec/2.0, surface_id=213)
    s214 = openmc.YPlane(y0=+FA5X5_box_in_sec/2.0, surface_id=214)
    s221 = openmc.XPlane(x0=-FA5X5_box_out_sec/2.0, surface_id=221)  # FA5X5 box outer section
    s222 = openmc.XPlane(x0=+FA5X5_box_out_sec/2.0, surface_id=222)
    s223 = openmc.YPlane(y0=-FA5X5_box_out_sec/2.0, surface_id=223)
    s224 = openmc.YPlane(y0=+FA5X5_box_out_sec/2.0, surface_id=224)
    s231 = openmc.XPlane(x0=-FA5X5_total_sec/2.0, surface_id=231)  # FA outer section
    s232 = openmc.XPlane(x0=+FA5X5_total_sec/2.0, surface_id=232)
    s233 = openmc.YPlane(y0=-FA5X5_total_sec/2.0, surface_id=233)
    s234 = openmc.YPlane(y0=+FA5X5_total_sec/2.0, surface_id=234)
    if config['model_type'] in ['fuel_assembly',
                                'control_rod',
                                'transient_rod']:
        for surf in [s231, s232, s233, s234]:
            surf.boundary_type = 'reflective'

    l21 = openmc.RectLattice(name='FA5X5 lattice', lattice_id=21)
    l21.lower_left = [-FA5X5_box_in_sec/2.0]*2
    l21.pitch = (pincell_pitch, pincell_pitch)
    l21.universes = np.tile(u110, (5, 5))

    c20 = openmc.Cell(cell_id=20, fill=l21)  # fuel lattice
    c21 = openmc.Cell(cell_id=21, fill=mat_dict["mat_FA5X5box"])  # FA5X5 box
    c22 = openmc.Cell(cell_id=22, fill=mat_dict["mat_mod"])  # FA5X5 outer water strip
    c20.region = +s211 & -s212 & +s213 & -s214 & +s901 & -s902
    c21.region = +s221 & -s222 & +s223 & -s224 & (-s211 | +s212 | -s213 | +s214) & +s901 & -s902
    c22.region = +s231 & -s232 & +s233 & -s234 & (-s221 | +s222 | -s223 | +s224) & +s901 & -s902
    # TODO: ADD SPRING AND PLUG

    u2 = openmc.Universe(name='Fuel assembly', universe_id=2, cells=[c20, c21, c22])

    if config['model_type'] == 'fuel_assembly':
        root_univ = u2
        geom = openmc.Geometry(root_univ)
        return geom

    ####################
    # Control Rod (CR) #
    ####################
    s311 = openmc.XPlane(x0=-absorber_in_sec/2.0, surface_id=311)  # absorber inner section
    s312 = openmc.XPlane(x0=+absorber_in_sec/2.0, surface_id=312)
    s313 = openmc.YPlane(y0=-absorber_in_sec/2.0, surface_id=313)
    s314 = openmc.YPlane(y0=+absorber_in_sec/2.0, surface_id=314)
    s321 = openmc.XPlane(x0=-absorber_out_sec/2.0, surface_id=321)  # absorber outer section
    s322 = openmc.XPlane(x0=+absorber_out_sec/2.0, surface_id=322)
    s323 = openmc.YPlane(y0=-absorber_out_sec/2.0, surface_id=323)
    s324 = openmc.YPlane(y0=+absorber_out_sec/2.0, surface_id=324)
    s331 = openmc.XPlane(x0=-GT_in_sec/2.0, surface_id=331)  # guide tube (GT) inner section
    s332 = openmc.XPlane(x0=+GT_in_sec/2.0, surface_id=332)
    s333 = openmc.YPlane(y0=-GT_in_sec/2.0, surface_id=333)
    s334 = openmc.YPlane(y0=+GT_in_sec/2.0, surface_id=334)
    # NOTE: GT outer section = FA5X5 box outer section
    # NOTE: water outside GT = water outside FA5X5 box

    # Absorber Section (AS)
    c300 = openmc.Cell(cell_id=300, fill=mat_dict["mat_mod"])  # water inside absorber
    c300.region = +s311 & -s312 & +s313 & -s314 & +s901 & -s902
    c301 = openmc.Cell(cell_id=301, fill=mat_dict["mat_absorber"])  # absorber
    c301.region = +s321 & -s322 & +s323 & -s324 & (-s311 | +s312 | -s313 | +s314) & +s901 & -s902
    c302 = openmc.Cell(cell_id=302, fill=mat_dict["mat_mod"])  # water between absorber and guide tube
    c302.region = +s331 & -s332 & +s333 & -s334 & (-s321 | +s322 | -s323 | +s324) & +s901 & -s902
    c303 = openmc.Cell(cell_id=303, fill=mat_dict["mat_GT"])  # guide tube
    c303.region = +s221 & -s222 & +s223 & -s224 & (-s331 | +s332 | -s333 | +s334) & +s901 & -s902
    c304 = openmc.Cell(cell_id=304, fill=mat_dict["mat_mod"])  # FA5X5 outer water strip
    c304.region = +s231 & -s232 & +s233 & -s234 & (-s221 | +s222 | -s223 | +s224) & +s901 & -s902

    u31 = openmc.Universe(name='control rod - absorber in', universe_id=31)
    u31.add_cells([c300, c301, c302, c303, c304])

    # control rod - Control In (CI)
    if config['model_type'] == 'control_rod' and config['CR_config'] == 'CI':
        root_univ = u31
        geom = openmc.Geometry(root_univ)
        return geom

    # Fuel Follower (FF)
    s341 = openmc.XPlane(x0=-FF_box_in_sec/2.0, surface_id=341)  # fuel follower (FF) box inner section
    s342 = openmc.XPlane(x0=+FF_box_in_sec/2.0, surface_id=342)
    s343 = openmc.YPlane(y0=-FF_box_in_sec/2.0, surface_id=343)
    s344 = openmc.YPlane(y0=+FF_box_in_sec/2.0, surface_id=344)
    s351 = openmc.XPlane(x0=-FF_fuel_sec/2.0, surface_id=351)  # FF fuel inner section
    s352 = openmc.XPlane(x0=+FF_fuel_sec/2.0, surface_id=352)
    s353 = openmc.YPlane(y0=-FF_fuel_sec/2.0, surface_id=353)
    s354 = openmc.YPlane(y0=+FF_fuel_sec/2.0, surface_id=354)

    c311 = openmc.Cell(cell_id=311, fill=mat_dict["mat_mod"])  # water between 4X4 lattice and box
    c311.region = +s341 & -s342 & +s343 & -s344 & (-s351 | +s352 | -s353 | +s354) & +s901 & -s902
    c312 = openmc.Cell(cell_id=312, fill=mat_dict["mat_clad"])  # fuel box
    c312.region = +s321 & -s322 & +s323 & -s324 & (-s341 | +s342 | -s343 | +s344) & +s901 & -s902
    c313 = openmc.Cell(cell_id=313, fill=mat_dict["mat_mod"])  # water between box and guide tube
    c313.region = +s331 & -s332 & +s333 & -s334 & (-s321 | +s322 | -s323 | +s324) & +s901 & -s902
    c314 = openmc.Cell(cell_id=314, fill=mat_dict["mat_GT"])  # guide tube
    c314.region = +s221 & -s222 & +s223 & -s224 & (-s331 | +s332 | -s333 | +s334) & +s901 & -s902
    c315 = openmc.Cell(cell_id=315, fill=mat_dict["mat_mod"])  # FA5X5 outer water strip
    c315.region = +s231 & -s232 & +s233 & -s234 & (-s221 | +s222 | -s223 | +s224) & +s901 & -s902

    # FF lattice (FA4X4) WITHOUT flux suppressor
    l330 = openmc.RectLattice(lattice_id=330)
    l330.lower_left = [-(FF_fuel_sec + flux_suppr_width*2.0)/2.0]*2  # to account for the flux suprresor
    l330.pitch = (pincell_pitch, pincell_pitch)
    l330.universes = np.tile(u110, (4, 4))
    c3100 = openmc.Cell(cell_id=3100, fill=l330)
    c3100.region = +s351 & -s352 & +s353 & -s354 & +s901 & -s902
    u33 = openmc.Universe(name='control rod - absorber out', universe_id=33)
    u33.add_cells([c3100, c311, c312, c313, c314, c315])

    # control rod - Control Out (CO)
    if config['model_type'] == 'control_rod' and config['CR_config'] == 'CO':
        root_univ = u33
        geom = openmc.Geometry(root_univ)
        return geom

    # FF lattice (FA4X4) WITH flux suppressor
    l331 = openmc.RectLattice(lattice_id=331)
    l331.lower_left = [-(FF_fuel_sec + flux_suppr_width*2.0)/2.0]*2  # to account for the flux suprresor
    l331.pitch = (pincell_pitch, pincell_pitch)
    l331.universes = np.tile(u120, (4, 4))
    c3101 = openmc.Cell(cell_id=3101, fill=l331)
    c3101.region = +s351 & -s352 & +s353 & -s354 & +s901 & -s902
    u34 = openmc.Universe(name='control rod - supressor in', universe_id=34)
    u34.add_cells([c3101, c311, c312, c313, c314, c315])

    # control rod - Suppressor In (SI)
    if config['model_type'] == 'control_rod' and config['CR_config'] == 'SI':
        root_univ = u34
        geom = openmc.Geometry(root_univ)
        return geom

    ######################
    # Transient Rod (TR) #
    ######################
    s411 = openmc.XPlane(x0=orig_cor - FA4X4_lattice_pitch / 2.0, surface_id=411)  # FA4X4R lattice pitch
    s412 = openmc.XPlane(x0=orig_cor + FA4X4_lattice_pitch / 2.0, surface_id=412)
    s413 = openmc.YPlane(y0=orig_cor - FA4X4_lattice_pitch / 2.0, surface_id=413)
    s414 = openmc.YPlane(y0=orig_cor + FA4X4_lattice_pitch / 2.0, surface_id=414)

    s421 = openmc.XPlane(x0=orig_cor - FA4X4_box_in_sec / 2.0, surface_id=421)  # FA4X4 box inner section
    s422 = openmc.XPlane(x0=orig_cor + FA4X4_box_in_sec / 2.0, surface_id=422)
    s423 = openmc.YPlane(y0=orig_cor - FA4X4_box_in_sec / 2.0, surface_id=423)
    s424 = openmc.YPlane(y0=orig_cor + FA4X4_box_in_sec / 2.0, surface_id=424)

    s431 = openmc.XPlane(x0=orig_cor - FA4X4_box_out_sec / 2.0, surface_id=431)  # FA4X4 box outer section
    s432 = openmc.XPlane(x0=orig_cor + FA4X4_box_out_sec / 2.0, surface_id=432)
    s433 = openmc.YPlane(y0=orig_cor - FA4X4_box_out_sec / 2.0, surface_id=433)
    s434 = openmc.YPlane(y0=orig_cor + FA4X4_box_out_sec / 2.0, surface_id=434)

    s441 = openmc.XPlane(x0=orig_cor - FA4X4_GT_in_sec / 2.0, surface_id=441)  # FA4X4 GT inner section
    s442 = openmc.XPlane(x0=orig_cor + FA4X4_GT_in_sec / 2.0, surface_id=442)
    s443 = openmc.YPlane(y0=orig_cor - FA4X4_GT_in_sec / 2.0, surface_id=443)
    s444 = openmc.YPlane(y0=orig_cor + FA4X4_GT_in_sec / 2.0, surface_id=444)

    s451 = openmc.XPlane(x0=orig_cor - FA4X4_GT_out_sec / 2.0, surface_id=451)  # FA4X4 GT outer section
    s452 = openmc.XPlane(x0=orig_cor + FA4X4_GT_out_sec / 2.0, surface_id=452)
    s453 = openmc.YPlane(y0=orig_cor - FA4X4_GT_out_sec / 2.0, surface_id=453)
    s454 = openmc.YPlane(y0=orig_cor + FA4X4_GT_out_sec / 2.0, surface_id=454)

    s461 = openmc.XPlane(x0=-FA5X5_total_sec / 2.0 + TR_absorber_thick, surface_id=461)  # TR cruciform absorber
    s462 = openmc.XPlane(x0=-FA5X5_total_sec / 2.0 + TR_absorber_width, surface_id=462)
    s463 = openmc.YPlane(y0=-FA5X5_total_sec / 2.0 + TR_absorber_thick, surface_id=463)
    s464 = openmc.YPlane(y0=-FA5X5_total_sec / 2.0 + TR_absorber_width, surface_id=464)

    # TR-FA4X4 lattice
    l402 = openmc.RectLattice(name='Fuel assembly 4X4', lattice_id=402)
    l402.lower_left = [orig_cor-FA4X4_lattice_pitch/2.0]*2
    l402.pitch = (pincell_pitch, pincell_pitch)
    l402.universes = np.tile(u110, (4, 4))

    # TR cells and universe
    c40 = openmc.Cell(cell_id=40, fill=l402)  # FA4X4
    c40.region = +s411 & -s412 & +s413 & -s414 & +s901 & -s902
    c41 = openmc.Cell(cell_id=41, fill=mat_dict["mat_mod"])  # inner water strip
    c41.region = +s421 & -s422 & +s423 & -s424 & (-s411 | +s412 | -s413 | +s414) & +s901 & -s902
    c42 = openmc.Cell(cell_id=42, fill=mat_dict["mat_clad"])  # FA4X4 box
    c42.region = +s431 & -s432 & +s433 & -s434 & (-s421 | +s422 | -s423 | +s424) & +s901 & -s902
    c43 = openmc.Cell(cell_id=43, fill=mat_dict["mat_mod"])  # water between box and GT
    c43.region = +s441 & -s442 & +s443 & -s444 & (-s431 | +s432 | -s433 | +s434) & +s901 & -s902
    c441 = openmc.Cell(cell_id=441, fill=mat_dict["mat_GT"])  # FA4X4 GT part1
    c441.region = +s231 & +s233 & -s452 & -s454 & (+s442 | +s444) & +s901 & -s902
    c442 = openmc.Cell(cell_id=442, fill=mat_dict["mat_GT"])  # FA4X4 GT part2
    c442.region = +s451 & +s453 & -s444 & -s442 & (-s441 | -s443) & +s901 & -s902
    c45 = openmc.Cell(cell_id=45, fill=mat_dict["mat_mod"])  # water strip outside GT
    c45.region = +s231 & -s232 & +s233 & -s234 & (+s452 | +s454) & +s901 & -s902
    c46 = openmc.Cell(cell_id=46)  # TR cruciform
    c46.region = +s231 & -s462 & +s233 & -s464 & (-s463 | -s461) & +s901 & -s902
    if config['TR_config'] == 'TI':  # transient rod - absorber IN
        c46.fill = mat_dict["mat_absorber"]
    elif config['TR_config'] == 'TO':  # transient rod - absorber OUT
        c46.fill = mat_dict["mat_filler"]

    c471 = openmc.Cell(cell_id=471, fill=mat_dict["mat_mod"])  # water in cruciform GT part 1
    c471.region = +s461 & -s442 & +s463 & -s444 & (-s453 | -s451) & +s901 & -s902
    c472 = openmc.Cell(cell_id=472, fill=mat_dict["mat_mod"])  # water in cruciform GT part 2
    c472.region = +s231 & -s461 & +s464 & -s444 & +s901 & -s902
    c473 = openmc.Cell(cell_id=473, fill=mat_dict["mat_mod"])  # water in cruciform GT part 3
    c473.region = +s233 & -s463 & +s462 & -s442 & +s901 & -s902

    u4 = openmc.Universe(name='transient rod', universe_id=4)
    u4.add_cells([c40, c41, c42, c43, c441, c442, c45, c46, c471, c472, c473])
    c481 = openmc.Cell(cell_id=481, fill=u4)
    c481.region = +s231 & -s232 & +s233 & -s234 & +s901 & -s902
    c482 = openmc.Cell(cell_id=482, fill=u4)
    c482.region = +s231 & -s232 & +s233 & -s234 & +s901 & -s902
    c483 = openmc.Cell(cell_id=483, fill=u4)
    c483.region = +s231 & -s232 & +s233 & -s234 & +s901 & -s902
    c484 = openmc.Cell(cell_id=484, fill=u4)
    c484.region = +s231 & -s232 & +s233 & -s234 & +s901 & -s902
    c481.rotation = [0.0, 0.0, 0.0]
    c482.rotation = [0.0, 0.0, 90.0]
    c483.rotation = [0.0, 0.0, 180.0]
    c484.rotation = [0.0, 0.0, 270.0]
    u41 = openmc.Universe(name='transient rod NE', universe_id=41, cells=([c481]))
    u42 = openmc.Universe(name='transient rod NW', universe_id=42, cells=([c482]))
    u43 = openmc.Universe(name='transient rod SW', universe_id=43, cells=([c483]))
    u44 = openmc.Universe(name='transient rod SE', universe_id=44, cells=([c484]))

    if config["model_type"] == 'transient_rod':
        root_univ = u41
        geom = openmc.Geometry(root_univ)
        return geom

    #######################
    # Filler "assemblies" #
    #######################
    # normal filler
    s811 = openmc.XPlane(x0=-filler_box_in_sec/2.0, surface_id=811)  # filler box inner section
    s812 = openmc.XPlane(x0=+filler_box_in_sec/2.0, surface_id=812)
    s813 = openmc.YPlane(y0=-filler_box_in_sec/2.0, surface_id=813)
    s814 = openmc.YPlane(y0=+filler_box_in_sec/2.0, surface_id=814)
    s821 = openmc.XPlane(x0=-filler_box_out_sec/2.0, surface_id=821)  # filler box outer section
    s822 = openmc.XPlane(x0=+filler_box_out_sec/2.0, surface_id=822)
    s823 = openmc.YPlane(y0=-filler_box_out_sec/2.0, surface_id=823)
    s824 = openmc.YPlane(y0=+filler_box_out_sec/2.0, surface_id=824)
    c80 = openmc.Cell(cell_id=80, fill=mat_dict["mat_mod"])  # water inside filler
    c81 = openmc.Cell(cell_id=81, fill=mat_dict["mat_filler"])  # filler box
    c82 = openmc.Cell(cell_id=82, fill=mat_dict["mat_mod"])  # water outside filler
    c80.region = +s811 & -s812 & +s813 & -s814 & +s901 & -s902
    c81.region = +s821 & -s822 & +s823 & -s824 & (-s811 | +s812 | -s813 | +s814) & +s901 & -s902
    c82.region = +s231 & -s232 & +s233 & -s234 & (-s821 | +s822 | -s823 | +s824) & +s901 & -s902
    u8 = openmc.Universe(name='filler assembly', universe_id=8, cells=[c80, c81, c82])

    # filler with UPPER side missing
    c804 = openmc.Cell(cell_id=804, fill=mat_dict["mat_mod"])  # water inside filler
    c814 = openmc.Cell(cell_id=814, fill=mat_dict["mat_filler"])  # filler box
    c824 = openmc.Cell(cell_id=824, fill=mat_dict["mat_mod"])  # water outside filler
    c804.region = +s811 & -s812 & +s813 & +s901 & -s902
    c814.region = +s821 & -s822 & +s823 & (-s811 | +s812 | -s813) & +s901 & -s902
    c824.region = +s231 & -s232 & +s233 & (-s821 | +s822 | -s823) & +s901 & -s902
    u84 = openmc.Universe(universe_id=84, cells=[c804, c814, c824])

    # filler "assembly" - with LOWER side missing
    c833 = openmc.Cell(cell_id=833, fill=u84)
    c833.rotation = [0.0, 0.0, 180.0]
    u83 = openmc.Universe(universe_id=83, cells=[c833])

    # filler "assembly" - with LEFT side missing
    c831 = openmc.Cell(cell_id=831, fill=u84)
    c831.rotation = [0.0, 0.0, 90.0]
    u81 = openmc.Universe(universe_id=81, cells=[c831])

    # filler "assembly" - with RIGHT side missing
    c832 = openmc.Cell(cell_id=832, fill=u84)
    c832.rotation = [0.0, 0.0, 270.0]
    u82 = openmc.Universe(universe_id=82, cells=[c832])

    # small filler (NE corner)
    sfs = skirt_in_rad/np.sqrt(2) - 3.5*FA5X5_total_sec - filler_box_width  # small filler section (SFS)
    s8125 = openmc.XPlane(x0=sfs, surface_id=8125)
    s8145 = openmc.YPlane(y0=sfs, surface_id=8145)
    s8225 = openmc.XPlane(x0=sfs+filler_box_width, surface_id=8225)
    s8245 = openmc.YPlane(y0=sfs+filler_box_width, surface_id=8245)
    s8126 = openmc.XPlane(x0=sfs+filler_box_width+2*FA_out_water_gap, surface_id=8126)
    s8146 = openmc.YPlane(y0=sfs+filler_box_width+2*FA_out_water_gap, surface_id=8146)
    s8226 = openmc.XPlane(x0=sfs+filler_box_width+2*FA_out_water_gap+filler_box_width, surface_id=8226)
    s8246 = openmc.YPlane(y0=sfs+filler_box_width+2*FA_out_water_gap+filler_box_width, surface_id=8246)
    c805 = openmc.Cell(cell_id=805, fill=mat_dict["mat_mod"])  # water inside filler
    c805.region = +s811 & -s8125 & +s813 & -s8145 & +s901 & -s902
    c815 = openmc.Cell(cell_id=815, fill=mat_dict["mat_filler"])  # filler box
    c815.region = +s821 & -s8225 & +s823 & -s8245 & (-s811 | +s8125 | -s813 | +s8145) & +s901 & -s902
    c8151 = openmc.Cell(cell_id=8151, fill=mat_dict["mat_filler"])  # filler box
    c8151.region = +s821 & +s8146 & (-s811 | -s8246) & +s901 & -s902
    c8152 = openmc.Cell(cell_id=8152, fill=mat_dict["mat_filler"])  # filler box
    c8152.region = +s823 & +s8126 & (-s813 | -s8226) & +s901 & -s902
    c8051 = openmc.Cell(cell_id=8051, fill=mat_dict["mat_mod"])
    c8051.region = +s231 & +s233 & (-s821 | -s823) & +s901 & -s902
    c8052 = openmc.Cell(cell_id=8052, fill=mat_dict["mat_mod"])
    c8052.region = -s8146 & -s8126 & (+s8225 | +s8245) & +s901 & -s902
    c8053 = openmc.Cell(cell_id=8053, fill=mat_dict["mat_mod"])
    c8053.region = +s811 & +s813 & -s232 & -s234 & (+s8226 | +s8246) & +s901 & -s902
    u91 = openmc.Universe(universe_id=91, cells=[c805, c815, c8151, c8152, c8051, c8052, c8053])

    # small filler (NW corner)
    c8002 = openmc.Cell(cell_id=8002, fill=u91)
    c8002.rotation = [0.0, 0.0, 90.0]
    u92 = openmc.Universe(universe_id=92, cells=[c8002])

    # small filler (SW corner)
    c8003 = openmc.Cell(cell_id=8003, fill=u91)
    c8003.rotation = [0.0, 0.0, 180.0]
    u93 = openmc.Universe(universe_id=93, cells=[c8003])

    # small filler (SE corner)
    c8004 = openmc.Cell(cell_id=8004, fill=u91)
    c8004.rotation = [0.0, 0.0, 270.0]
    u94 = openmc.Universe(universe_id=94, cells=[c8004])

    ####################################
    # Full Core and Quarter Core (NEq) #
    ####################################
    if config["CR_config"] == 'CI':  # control rod - absorber IN
        u3 = u31
    if config["CR_config"] == 'CO':  # control rod - absorber OUT (fuel follower in)
        u3 = u33
    if config["CR_config"] == 'SI':  # control rod - flux supressor IN (inside fuel follower)
        u3 = u34

    # define four quarter-core lattices
    NEq = np.array([[u8,  u83, u8,  u8,  u8,  u8],
                    [u8,  u84, u8,  u83, u8,  u8],
                    [u2,  u2,  u2,  u91, u81, u8],
                    [u3,  u2,  u2,  u2,  u8,  u8],
                    [u2,  u3,  u2,  u2,  u82, u81],
                    [u41, u2,  u2,  u2,  u8,  u8]])

    NWq = np.array([[u8,  u8,  u8,  u8,  u83, u8],
                    [u8,  u8,  u83, u8,  u84, u8],
                    [u8,  u82, u92, u2,  u2,  u2],
                    [u8,  u8,  u2,  u2,  u2,  u3],
                    [u82, u81, u2,  u2,  u3,  u2],
                    [u8,  u8,  u2,  u2,  u2,  u42]])

    SWq = np.array([[u8,  u8,  u2,  u2,  u2,  u43],
                    [u82, u81, u2,  u2,  u3,  u2],
                    [u8,  u8,  u2,  u2,  u2,  u3],
                    [u8,  u82, u93, u2,  u2,  u2],
                    [u8,  u8,  u84, u8,  u83, u8],
                    [u8,  u8,  u8,  u8,  u84, u8]])

    SEq = np.array([[u44, u2,  u2,  u2,  u8,  u8],
                    [u2,  u3,  u2,  u2,  u82, u81],
                    [u3,  u2,  u2,  u2,  u8,  u8],
                    [u2,  u2,  u2,  u94, u81, u8],
                    [u8,  u83, u8,  u84, u8,  u8],
                    [u8,  u84, u8,  u8,  u8,  u8]])

    Nh = np.concatenate((NWq, NEq), axis=1)  # north half
    Sh = np.concatenate((SWq, SEq), axis=1)  # sourh half
    full_core_lattice = np.concatenate((Nh, Sh))

    # vessel layers surfaces
    s501 = openmc.ZCylinder(x0=0.0, y0=0.0, r=skirt_in_rad, surface_id=501)
    s502 = openmc.ZCylinder(x0=0.0, y0=0.0, r=skirt_out_rad, surface_id=502)
    s503 = openmc.ZCylinder(x0=0.0, y0=0.0, r=SH1_in_rad, surface_id=503)
    s504 = openmc.ZCylinder(x0=0.0, y0=0.0, r=SH1_out_rad, surface_id=504)
    s505 = openmc.ZCylinder(x0=0.0, y0=0.0, r=SH2_in_rad, surface_id=505)
    s506 = openmc.ZCylinder(x0=0.0, y0=0.0, r=SH2_out_rad, surface_id=506)
    s507 = openmc.ZCylinder(x0=0.0, y0=0.0, r=SH3_in_rad, surface_id=507)
    s508 = openmc.ZCylinder(x0=0.0, y0=0.0, r=SH3_out_rad, surface_id=508)
    s509 = openmc.ZCylinder(x0=0.0, y0=0.0, r=SH4_in_rad, surface_id=509)
    s510 = openmc.ZCylinder(x0=0.0, y0=0.0, r=SH4_out_rad, surface_id=510)
    s511 = openmc.ZCylinder(x0=0.0, y0=0.0, r=vessel_in_rad, surface_id=511)
    s512 = openmc.ZCylinder(x0=0.0, y0=0.0, r=vessel_out_rad, surface_id=512)
    s513 = openmc.ZCylinder(x0=0.0, y0=0.0, r=bioShield_out_rad, surface_id=513)
    s513.boundary_type = 'vacuum'

    # core lattice + vessel layers
    c502 = openmc.Cell(cell_id=502, fill=mat_dict["mat_shield"], region=+s501 & -s502 & +s901 & -s902)  # skirt shield
    c503 = openmc.Cell(cell_id=503, fill=mat_dict["mat_mod"], region=+s502 & -s503 & +s901 & -s902)  # water between skirt and SH1
    c504 = openmc.Cell(cell_id=504, fill=mat_dict["mat_shield"], region=+s503 & -s504 & +s901 & -s902)  # shield SH1
    c505 = openmc.Cell(cell_id=505, fill=mat_dict["mat_mod"], region=+s504 & -s505 & +s901 & -s902)  # water between SH1 and SH2
    c506 = openmc.Cell(cell_id=506, fill=mat_dict["mat_shield"], region=+s505 & -s506 & +s901 & -s902)  # shield SH2
    c507 = openmc.Cell(cell_id=507, fill=mat_dict["mat_mod"], region=+s506 & -s507 & +s901 & -s902)  # water between SH2 and SH3
    c508 = openmc.Cell(cell_id=508, fill=mat_dict["mat_shield"], region=+s507 & -s508 & +s901 & -s902)  # shield SH3
    c509 = openmc.Cell(cell_id=509, fill=mat_dict["mat_mod"], region=+s508 & -s509 & +s901 & -s902)  # water between SH3 and SH4
    c510 = openmc.Cell(cell_id=510, fill=mat_dict["mat_shield"], region=+s509 & -s510 & +s901 & -s902)  # shield SH4
    c511 = openmc.Cell(cell_id=511, fill=mat_dict["mat_mod"], region=+s510 & -s511 & +s901 & -s902)  # water between SH4 and vessel
    c512 = openmc.Cell(cell_id=512, fill=mat_dict["mat_shield"], region=+s511 & -s512 & +s901 & -s902)  # vessel
    c513 = openmc.Cell(cell_id=513, fill=mat_dict["mat_bioShield"], region=+s512 & -s513 & +s901 & -s902)  # biological shielding

    # full core lattice
    l5 = openmc.RectLattice(lattice_id=5)
    l5.pitch = (FA5X5_total_sec, FA5X5_total_sec)
    l5.lower_left = [-FA5X5_total_sec*6.0]*2
    l5.universes = full_core_lattice
    c5011 = openmc.Cell(cell_id=5011, fill=l5, region=-s501 & +s901 & -s902)  # inside skirt (FULL CORE)
    u51 = openmc.Universe(universe_id=51)
    u51.add_cells([c5011, c502, c503, c504, c505, c506, c507, c508, c509, c510, c511, c512, c513])

    if config["model_type"] == 'full_core':
        root_univ = u51
        geom = openmc.Geometry(root_univ)
        return geom

    # quarter-core (NEq) lattice
    l6 = openmc.RectLattice(lattice_id=6)
    l6.pitch = (FA5X5_total_sec, FA5X5_total_sec)
    l6.lower_left = [0.0, 0.0]
    l6.universes = NEq
    c5012 = openmc.Cell(cell_id=5012, fill=l6, region=-s501 & +s901 & -s902)  # inside skirt (QUARTER CORE)
    u52 = openmc.Universe(universe_id=52)
    u52.add_cells([c5012, c502, c503, c504, c505, c506, c507, c508, c509, c510, c511, c512, c513])

    # X=0 and Y=0 planes for quarter-core calculations (pi/2 periodic)
    s71 = openmc.XPlane(x0=0.0, surface_id=71, boundary_type='periodic')
    s72 = openmc.YPlane(y0=0.0, surface_id=72, boundary_type='periodic')
    s71.periodic_surface = s72
    c522 = openmc.Cell(cell_id=522, fill=u52)
    c522.region = -s513 & +s71 & +s72 & +s901 & -s902
    u522 = openmc.Universe(universe_id=522)
    u522.add_cells([c522])

    if config["model_type"] == 'quarter_core':
        root_univ = u522
        geom = openmc.Geometry(root_univ)
        return geom


def gen_plots(mats):
    """
    Generates SPERT-3 Reactor materials.

    Returns
    -------
    openmc.Plots
        The set of plots to generate when running OpenMC.
    """
    # set material colors
    color_mapping = {'mat_fuel': (255, 255, 0),
                     'mat_mod': (0, 0, 255),
                     'mat_filler': (0, 100, 0),
                     'mat_shield': (210, 105, 30),
                     'mat_clad': (255, 0, 0),
                     'mat_absorber': (0, 0, 0),
                     'mat_bioShield': (165, 42, 42),
                     'mat_GT': (50, 50, 50),
                     'mat_FA5X5box': (210, 210, 210),
                     'mat_helium': (250, 200, 200),
                     'mat_spring': (0, 0, 100)}

    mat_colors = {}
    for k, v in color_mapping.items():
        try:
            mat_colors[mats[k]] = v
        except:
            pass

    plots = openmc.Plots()

    wide_resolution = (3000, 3000)
    near_resolution = (2000, 2000)

    # for div in axial_divs:
    for div in [FA_height/2.0]:

        # offset from z plane just a bit
        z = div + 0.1

        # wide slice through lattice
        plot = openmc.Plot()
        plot.filename = "wide_cell_z={}".format(div)
        plot.basis = 'xy'
        plot.color_by = 'cell'
        plot.origin = (0., 0., z)
        plot.width = (bioShield_out_rad*2.0*1.05, bioShield_out_rad*2.0*1.05)
        plot.pixels = wide_resolution
        plots.append(plot)

        # wide slice through lattice (by material)
        plot = openmc.Plot()
        plot.filename = "wide_mat_z={}".format(div)
        plot.basis = 'xy'
        plot.color_by = 'material'
        plot.colors = mat_colors
        plot.origin = (0., 0., z)
        plot.width = (bioShield_out_rad*2.0*1.05, bioShield_out_rad*2.0*1.05)
        plot.pixels = wide_resolution
        plots.append(plot)

        # zoomed image of central pin
        plot = openmc.Plot()
        plot.filename = "center_cell_z={}".format(div)
        plot.basis = 'xy'
        plot.color_by = 'cell'
        plot.origin = (0., 0., z)
        plot.width = (FA5X5_total_sec*1.5, FA5X5_total_sec*1.5)
        plot.pixels = near_resolution
        plots.append(plot)

        # zoomed image of central pin
        plot = openmc.Plot()
        plot.filename = "center_mat_z={}".format(div)
        plot.basis = 'xy'
        plot.color_by = 'material'
        plot.colors = mat_colors
        plot.origin = (0., 0., z)
        plot.width = (FA5X5_total_sec*1.5, FA5X5_total_sec*1.5)
        plot.pixels = near_resolution
        plots.append(plot)

    xs = [0.0]

    for x in xs:
        # wide axial slice
        plot = openmc.Plot()
        plot.filename = "yz_cell_x={}".format(x)
        plot.basis = 'yz'
        plot.color_by = 'cell'
        plot.origin = (x, 0.0, FA_height/2.0)
        plot.width = (bioShield_out_rad*2.0, FA_height)
        plot.pixels = (1000, 800)
        plots.append(plot)

        # wide axial slice by material
        plot = openmc.Plot()
        plot.filename = "yz_mat_x={}".format(x)
        plot.basis = 'yz'
        plot.color_by = 'material'
        plot.colors = mat_colors
        plot.origin = (x, 0.0, FA_height/2.0)
        plot.width = (bioShield_out_rad*2.0, FA_height)
        plot.pixels = (1000, 800)
        plots.append(plot)

    return plots


############
# Settings #
############


def gen_settings(config):
    """
    Creates a settings object

    Returns
    -------
    openmc.Settings
        The settings to use in the OpenMC run.
    """

    settings = openmc.Settings()
    settings.run_mode = 'eigenvalue'

    source = openmc.Source()
    ll = [-pincell_fuel_radius/2.0, -pincell_fuel_radius/2.0, -FA_height/2.0+1.0]
    ur = [pincell_fuel_radius/2.0, pincell_fuel_radius/2.0, FA_height/2.0-1.0]
    source.space = openmc.stats.Box(ll, ur)
    source.strength = 1.0
    settings.source = source
    settings.output = {'summary': False}
    settings.batches = config.getint('n_batches')
    settings.inactive = config.getint('n_inactive')
    settings.particles = config.getint('n_particles')
    settings.temperature = {'method': 'interpolation'}

    return settings


############
# Tallies  #
############


def gen_tallies(config):
    """
    Creates a tallies object 

    Returns
    -------
    openmc.Tallies
        The tallies to use in the OpenMC run.
    """
    #############################
    # tally scores and nuclides #
    #############################
#    tally_scores = [
#        "absorption",
#        "absorption",
#        "absorption",
#        "fission",
#        "fission",
#        "flux",
#        "nu-fission",
#        "scatter",
#        "scatter",
#        "scatter"
#    ]
#    tally_nuclides = [
#        "All",
#        "U235",
#        "U238",
#        "U235",
#        "U238",
#        "All",
#        "All",
#        "U235",
#        "U238",
#        "H1"
#    ]

    tally_scores = [
        "fission",
    ]
    tally_nuclides = [
        "U235",
    ]

    #################
    # tally filters #
    #################

    # ENERGY filter
    energy_groups = np.flip(np.array(np.loadtxt(energy_structure_path)))*1e6
    # energy_groups = np.array([0.0, 0.4, 9e3, 10e6])
    energy_filter = openmc.EnergyFilter(energy_groups)

    # CELL filter for homogenized pincell
    if config['model_type'] in ['pincell', 'fuel_assembly', 'transient_rod']:
        cell_filter_1 = openmc.DistribcellFilter([161])
        cell_filters_all = [cell_filter_1]
    elif config['model_type'] == 'control_rod':
        if config['CR_config'] == 'CO':
            cell_filter_1 = openmc.DistribcellFilter([161])
        elif config['CR_config'] == 'SI':
            cell_filter_1 = openmc.DistribcellFilter([162])
        cell_filters_all = [cell_filter_1]
    elif config['model_type'] in ['full_core', 'quarter_core']:
        cell_filter_1 = openmc.DistribcellFilter([161])  # WITHOUT flux supressor
        cell_filters_all = [cell_filter_1]
        if config['CR_config'] == 'SI':
            cell_filter_2 = openmc.DistribcellFilter([162])  # WITH flux supressor
            cell_filters_all.append(cell_filter_2)

    # generate tallies
    tallies = openmc.Tallies()
    num_scores = len(tally_scores)
    # num_scores = 10
    for i in range(num_scores):
        for j in range(len(cell_filters_all)):
            single_tally = openmc.Tally()
            single_tally.name = tally_scores[i]+'_'+tally_nuclides[i]
            if j == 1:  # pincells with flux suppressors in full core / quarter core - to ignore title in tallies
                single_tally.name = single_tally.name+'_2'
            single_tally.filters.append(cell_filters_all[j])
#            single_tally.filters.append(energy_filter)
            single_tally.scores.append(tally_scores[i])
            if tally_nuclides[i] != "All":
                single_tally.nuclides = [tally_nuclides[i]]
            tallies.append(single_tally)

    # # MESH filter
    # mesh = openmc.RegularMesh()
    # mesh.dimension = [40, 40, 1]
    # mesh.lower_left = [-4.0*FA5X5_total_sec, -4.0*FA5X5_total_sec, 0.0]
    # mesh.upper_right = [4.0*FA5X5_total_sec, 4.0*FA5X5_total_sec, core_height]
    # mesh_filter = openmc.MeshFilter(mesh)

    # ENERGY and MESH tallies
    # for tally_filter in [energy_filter, mesh_filter]:
    #     for i in range(num_scores):
    #         single_tally = openmc.Tally()
    #         single_tally.name = tally_filter.short_name+'_'+tally_scores[i]+'_'+tally_nuclides[i]
    #         single_tally.filters.append(tally_filter)
    #         single_tally.scores.append(tally_scores[i])
    #         if tally_nuclides[i] is not "All":
    #             single_tally.nuclides = [tally_nuclides[i]]
    #         tallies.append(single_tally)

    return tallies



