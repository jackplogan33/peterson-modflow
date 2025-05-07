# Multi-solute Flow and Transport Model using MODFLOW 6 with PEST++ Calibration


## Project Summary

This repository is a framework that models groundwater flow and transport in Colorado Springs, CO using MODFLOW 6. This project also completes an automatic calibration of transport parameters using an interaterive ensemble smoother (IES) through PEST++.

The goal of this project was to determine the path of PFAS transport from an AFFF training site on Peterson Space Force base in Colorado Springs to a set of pumping wells in Fountain, CO. The model starts on July 1, 1970 and finishes on January 1, 2020. Through this time period, we have observations at 30 wells from a single sampling events in May, 2018. Each well has a measurement of PFOS, PFOA and PFHxS.

## Disclaimer

We believe it is most helpful to start by reading the flopy and MODFLOW 6 documentation before beginning with this repository. This is far from a comprehensive overview of the capabilities of MODFLOW 6. This software is extrememly powerful, and this workflow aims to walk through a simulation with one flow and three transport models (one for each solute). 

## How to Use this Repository

This repository has three main directories: `notebooks/`, `model/`, and `pest-template`. The notebooks folder contains all of the necessary scripts to generate, run, visualize, and calibrate the model. The notebooks each have a specific purpose:
- `01-flow-model.ipynb`: This notebook initializes a MODFLOW 6 Simulation and creates a flow model using flopy.
- `02-transport-model.ipynb`: This notebook creates three solute transport models, one for PFOS, PFOA and PFHxS.
- `03-model-visualization.ipynb`: This notebook takes you through various different visualizations of model outputs. It includes geospatial plots, observed vs simulated plots, and breakthrough curves at wells. 
- `04-pest-setup.ipynb`: This notebook walks through the process of creating the PEST++ input files.
- `05-calibration-statistics.ipynb`: This notebook visualizes the IES outputs.

An environment file with all the required files has been included. To download the required packages, run the following line in the terminal:
```
conda env create --name PFAS --file=environment.yml
```