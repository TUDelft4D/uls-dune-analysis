# UAV-LIDAR morphological dynamics analysis
This repository provides the code for framework to analyse a time series of UAV-LIDAR derived DEMs and RGB imagery of the Zandmotor, available at doi:10.5281/zenodo.18849734, underlying the publication [add DOI].

The repository is organized in two folders. One for the analysis and one for visualization.
- 01_analysis
- 02_visualization

'01_analysis' consists of four subfolders, referring to the four parts of the framework:
- 01_analysis/01_quantifying_volumetric_changes -- Methods Section 3.1 : Quantifying volumetric changes (DEMs of Difference)
- 01_analysis/02_clustering_elevation_change_patterns -- Methods Section 3.2 : Clustering of elevation change patterns (K-means)
- 01_analysis/03_extraction_of_dune_morphology -- Methods Section 3.3 : Extraction of dune morphology (ridgeline detection)
- 01_analysis/04_vegetation_detection -- Methods Section 3.4 : Vegetation detection

'02_visualization' contains the scripts to visualize the (derived) data conforming the figures in the Manuscript.

To use the code the necessary Python libraries have to be installed in your local environment, and the data has to be downloaded separately at: [https://doi.org/10.5281/zenodo.18849734](https://doi.org/10.5281/zenodo.18849734], relative paths to the data have to be changed at the specified locations in the scripts.


For any questions please correspond to Daan Hulskemper (d.c.hulskemper@tudelft.nl) or Romy Hulskamp (r.l.hulskamp@tudelft.nl)



