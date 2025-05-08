# Multi-solute Flow and Transport Model using MODFLOW 6 with PEST++ Calibration

## Project Summary

This repository is a framework that models groundwater flow and transport in Colorado Springs, CO using MODFLOW 6. This project also completes an automatic calibration of transport parameters using an iterative ensemble smoother (IES) through PEST++.

The goal of this project was to determine the path of PFAS transport from an AFFF training site on Peterson Space Force base in Colorado Springs to a set of pumping wells in Fountain, CO. The model starts on July 1, 1970, and finishes on January 1, 2020. Through this time period, we have concentration observations at 30 wells from a single sampling event in May 2018. Each well has a measurement of PFOS, PFOA and PFHxS.

## Disclaimers

We believe it is most helpful to start by reading the flopy and MODFLOW 6 documentation before beginning with this repository. This is far from a comprehensive overview of the capabilities of MODFLOW 6. This software is extremely powerful, and this workflow aims to walk through a simulation with one flow and three transport models (one for each solute). 

We also believe the PEST++ documentation is incredibly important to read, as there are nearly infinite combinations of parameters you can choose. Depending on your model size and calibration needs, you should consider calibrating on a high performance computer (HPC).

## How to Use this Repository

Click [here]() for a video walking through the repository.

This repository has four main directories: `notebooks/`, `model/`, `pest-template/`, and `bin/`. 

* The notebooks folder contains all of the necessary scripts to generate, run, visualize, and calibrate the model. The notebooks each have a specific purpose:
    - `01-flow-model.ipynb`: This notebook initializes a MODFLOW 6 Simulation and creates a flow model using flopy.
    - `02-transport-model.ipynb`: This notebook creates three solute transport models, one for PFOS, PFOA and PFHxS.
    - `03-model-visualization.ipynb`: This notebook takes you through various different visualizations of model outputs. It includes geospatial plots, observed vs simulated plots, and breakthrough curves at wells. 
    - `04-pest-setup.ipynb`: This notebook walks through the process of creating the PEST++ input files.
    - `05-calibration-statistics.ipynb`: This notebook visualizes the IES outputs.

* The model folder contains three subdirectories: `data/`, `inputs/`, and `outputs/`. The data folder contains all of the necessary external DAT files and any CSV files. They are organized into domain, flow, transport, and pest catergories. The inputs folder is where notebooks 01 and 02 print the input folders. This is where the MODFLOW 6 simulation lives. It will print all output files to the outputs folder.

* The pest-template folder is were we will construct the PEST++ calibration model. In notebook 04 we will copy the entire `model/` folder and the `forward_run.py` script there.

* The `bin/` folder contains all of the MODFLOW 6 and PEST++ executable files. These are referened using relative paths from wherever they are called.

You can clone this repository using either of the following commands:
```git clone git@github.com:jackplogan33/peterson-modflow.git```
```git clone https://github.com/jackplogan33/peterson-modflow.git```

An environment file with all the required packages has been included. To download these packages, run the following line in the terminal:
```
conda env create --name PFAS --file=environment.yml
```

After completing these steps, you are all set to follow this MODFLOW 6 and PEST++ tutorial!