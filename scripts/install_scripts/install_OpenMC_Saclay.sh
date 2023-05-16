#!/usr/bin/env bash

if [ "$#" -ne 2 ]; then
 echo "invalid number of arguments. You must specify the names of the installation directory and of cross-section library."
 exit
fi

module load gcc/11.2.0 openmpi/gcc_11.2.0/4.1.4 hdf5/gcc_11.2.0_openmpi_4.1.4/1.12.1 cmake/gcc_11.2.0/3.21.1 python/3.11.2

install_path=$(realpath $1)
cross_section_path=$(realpath $2)
python -m venv ${install_path}
. ${install_path}/bin/activate
pip install --upgrade pip

pip install venv-modulefile==0.0.22

venvmod-initialize ${install_path}
venvmod-cmd-module-load ${install_path} gcc/11.2.0 openmpi/gcc_11.2.0/4.1.4 hdf5/gcc_11.2.0_openmpi_4.1.4/1.12.1 cmake/gcc_11.2.0/3.21.1 python/3.11.2
venvmod-cmd-setenv ${install_path} OPENMC_CROSS_SECTIONS ${cross_section_path}/jeff-3.3-hdf5/cross_sections.xml

deactivate
module purge
. ${install_path}/bin/activate

mkdir -p ${install_path}/tmp
git clone --recurse-submodules -b v0.13.3 https://github.com/openmc-dev/openmc.git ${install_path}/tmp/openmc
mkdir -p ${install_path}/tmp/openmc/build
(cd ${install_path}/tmp/openmc/build && cmake -DCMAKE_INSTALL_PREFIX=${install_path} -DOPENMC_USE_MPI=on ..)
(cd ${install_path}/tmp/openmc/build && make install -j20)

(cd ${install_path}/tmp/openmc && pip install .)

rm -rf ${install_path}/tmp


