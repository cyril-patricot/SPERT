from argparse import ArgumentParser
from configparser import ConfigParser
from pathlib import Path
import os

import openmc

import spert
import parse_tallies


def main(config_file='spert_config.ini'):

    # import configuration
    config = ConfigParser()

    # assume config file is in current location with script
    if os.path.exists(config_file):
        config.read(config_file)
    # try location with script if not
    else:
        config.read(Path(__file__).parent / config_file)

    # # assume config file is in location with script
    # try:
    #     config.read(Path(__file__).parent / config_file)
    # except IOError:
    # # try current location if not
    #     config.read(config_file)

    ap = ArgumentParser(description="A configurable script for generating the SPERT-3 model")

    ap.add_argument("-c", "--config", type=str, default="FULL_CORE",
                    help="Core configuration. Should be one of " + str(config.sections()))

    ap.add_argument("-p", "--plot", default=False, action="store_true",
                    help="If present, plot the model after generation.")

    ap.add_argument("-r", "--run", default=False, action="store_true",
                    help="If present, run OpenMC after generating the model")

    args = ap.parse_args()

    custom_config = config[args.config]

    config = config['FULL_CORE']

    # update any custome values over the default configuration values
    for key, val in custom_config.items():
        config[key] = val

    # Some output for reference
    print("Configuration: {}".format(args.config))
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
        parse_tallies.main()

if __name__ == '__main__':
    main()



