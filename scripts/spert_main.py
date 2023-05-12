from argparse import ArgumentParser
from configparser import ConfigParser
from pathlib import Path
import os

import openmc

import spert_model as spert
import spert_tallies_parse


def main(config_file='spert_config.ini'):
    
    ap = ArgumentParser(description="A configurable script for generating the SPERT-3 model")
    ap.add_argument("-mt", "--model_type", type=str, default="full_core",
                    help="Model type options: full_core, quarter_core, pincell, fuel_assembly, control_rod, transient_rod")
    ap.add_argument("-p", "--plot", default=False, action="store_true",
                    help="If present, plot the model after generation.")
    ap.add_argument("-r", "--run", default=False, action="store_true",
                    help="If present, run OpenMC after generating the model")
    args = ap.parse_args()
 
    # import configuration
    config = ConfigParser()
    # assume config file is in current location with script
    if os.path.exists(config_file):
        config.read(config_file)
    # try location with script if not
    else:
        config.read(Path(__file__).parent / config_file)
    config = config['SPERT_config']
    config['model_type'] = args.model_type

    # Some output for reference
    print("Model type: {}".format(config['model_type']))
    print("Core dimensions: {}".format(config['core_dimensions']))
    print("TR_config: {}".format(config['TR_config']))
    print("CR_config: {}".format(config['CR_config']))
    print("Core condition: {}".format(config['core_condition']))
    print("XS library: {}".format(config['xs_lib']))
    print("Using SAB: {}".format(config['use_sab']))
    print("Tallies generate: {}".format(config['tallies_generate']))
    print("Tallies parsing: {}".format(config['tallies_parse']))

    # create materials dictionary
    mats = spert.gen_materials(config)

    # create geometry
    geom = spert.gen_geometry(mats, config)
    geom.export_to_xml()

    # get all materials used in problem
    materials_out = geom.get_all_materials()
    materials_out_exp = spert.openmc.Materials(materials_out.values())
    materials_out_exp.cross_sections = config['xs_lib']
    materials_out_exp.export_to_xml()

    # update mats dictionary
    mats_new = {}
    for mat in materials_out.values():
        for k, v in mats.items():
            if v == mat:
                mats_new[k] = mat
    mats = mats_new

    # plots
    plots = spert.gen_plots(mats)
    plots.export_to_xml()

    # settings
    settings = spert.gen_settings(config)
    settings.export_to_xml()

    # tallies
    if config.getboolean('tallies_generate'):
        tallies = spert.gen_tallies(config)
        tallies.export_to_xml()

    if args.plot:
        spert.openmc.plot_geometry()

    if args.run:
	    spert.openmc.run()

    if config.getboolean('tallies_parse'):
        spert_tallies_parse.main()

if __name__ == '__main__':
    main()



