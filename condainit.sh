#!/usr/bin/env sh

# This script is used to initialize the conda environment or make a new one if it doesn't exist

conda activate nidaq-mqtt || conda create -n nidaq-mqtt -f environment.yml
