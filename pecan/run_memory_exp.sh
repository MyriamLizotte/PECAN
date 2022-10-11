#!/bin/bash

# run this script from the PECAN/pecan directory
# load modules
# module load python/3.9

# activate env
# source $HOME/env_pecan/bin/activate # on linux
#source ../env_tda/Scripts/activate

# run diffusion condensation on multiple datasets with multiple parameters

#datasets_list=("petals" "double_annulus")
datasets_list=("blobs" "moons" "nested_circles" "barbell")
memory_value_list=(1.00 0.99 0.95 0.90 0.85 0.80 0.50)

for dataset in ${datasets_list[@]}; do
    for memory_value in ${memory_value_list[@]}; do

        output_name="${dataset}_memory${memory_value}.npz"
        
        python condensation.py -n 256 -d $dataset -o $output_name -a $memory_value
    done
done