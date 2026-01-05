# WRF-complex-terrain-convective-storms-Yunnan

This repository contains data, scripts, and configuration files associated with the study on **WRF simulations of strong convective storms over complex terrain in Yunnan, China**.  
The repository is intended to support transparency, reproducibility, and reuse of the modelling and analysis workflow presented in the paper.

---

## Repository Structure

### 📁 Figures
This folder contains:
- Figures used in the manuscript
- Scripts for post-processing, analysis, and figure generation (e.g. plotting scripts)

These scripts reproduce the main figures presented in the paper based on the WRF simulation outputs.

---

### 📁 Gis_data
This folder includes geospatial datasets used in the study:
- Digital Elevation Model (DEM)
- Shapefiles (e.g. administrative boundaries, study region outlines)

All GIS data are used for domain setup, terrain analysis, and visualization.

---

### 📁 WRF_simulation
This folder contains materials related to the WRF model configuration and outputs:
- Two WRF namelist files (`namelist.input`, `namelist.wps`)
- Selected WRF simulation outputs, including:
  - Accumulated precipitation variables (`RAINC`, `RAINNC`)
  - Simulated radar reflectivity (`REFL_10CM`)

These outputs are used for analyzing precipitation characteristics and convective storm structure over complex terrain.

---

## Notes

- Large raw WRF output files are not fully hosted on GitHub due to size limitations.
- The repository is provided for academic and research purposes.

---

## Contact

For questions related to the model setup, data processing, or analysis, please contact the authors of the study.
Cong Jiang (IGB), cong.jiang@igb-berlin.de; Xin Yin, xin.yin@bnu.edu.cn
