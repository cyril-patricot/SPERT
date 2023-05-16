from argparse import ArgumentParser
from configparser import ConfigParser
from pathlib import Path
import os
import spert_model as spert
import spert_tallies_parse
import openmc


def main(config_file='spert_config.ini', plot=False, run=False, model_type="full_core"):
    # import configuration
    config = ConfigParser()
    # assume config file is in current location with script
    if os.path.exists(config_file):
        config.read(config_file)
    # try location with script if not
    else:
        config.read(Path(__file__).parent / config_file)
    config = config['SPERT_config']
    config['model_type'] = model_type

    # Print config to screen
    print("Core configuration:")
    print("Model type: {}".format(config['model_type']))
    print("Core dimensions: {}".format(config['core_dimensions']))
    print("TR_config: {}".format(config['TR_config']))
    print("CR_config: {}".format(config['CR_config']))
    print("Fuel temperature: {} F".format(config['fuel_temp']))
    print("Water temperature: {} F".format(config['water_temp']))
    print("Water pressure: {} psig".format(config['water_pressure']))    
    print("Core temperature: {} F".format(config['core_temp']))
    print("Using SAB: {}".format(config['use_sab']))
    print("Tallies generate: {}".format(config['tallies_generate']))
    print("Tallies parsing: {}".format(config['tallies_parse']))

    # Generate materials dictionary
    mats = spert.gen_materials(config)

    # Generate geometry
    geom = spert.gen_geometry(mats, config)
    geom.export_to_xml()

    # Get all materials used in problem
    materials_out = geom.get_all_materials()
    materials_out_exp = openmc.Materials(materials_out.values())
    #materials_out_exp.cross_sections = config['xs_lib']
    materials_out_exp.export_to_xml()

    # Update mats dictionary
    mats_new = {}
    for mat in materials_out.values():
        for k, v in mats.items():
            if v == mat:
                mats_new[k] = mat
    mats = mats_new

    # Generate plots

    # Generate settings
    settings = spert.gen_settings(config)
    settings.export_to_xml()

    # Generate tallies
    if config.getboolean('tallies_generate'):
        tallies = spert.gen_tallies(config)
        tallies.export_to_xml()

    # Generate plots
    if plot:
        plots = spert.gen_plots(mats)
        plots.export_to_xml()
        openmc.plot_geometry()

    # Run Monte-Carlo simulation
    if run:
        openmc.run()

    # Parse tallies
    if config.getboolean('tallies_parse'):
        spert_tallies_parse.main()

if __name__ == '__main__':
    ap = ArgumentParser(description="A configurable script for generating the SPERT-3 model")
    ap.add_argument("-p", "--plot", default=False, action="store_true",
                    help="If present, plot the model after generation.")
    ap.add_argument("-r", "--run", default=False, action="store_true",
                    help="If present, run OpenMC after generating the model")
    ap.add_argument("-mt", "--model_type", type=str, default="full_core",
                    help="Model type options: full_core, quarter_core, pincell, fuel_assembly, control_rod, transient_rod")
    args = vars(ap.parse_args())

    main(**args)
