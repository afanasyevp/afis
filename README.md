# Aberration-free image shift (AFIS) compensation for the EPU data

Here two scripts and instructions for their use can be found:

**optics_split.py** finds optics group for each movie in your dataset

**optics_add.py** assigns optics group to each micrograph or particle from your dataset

### Splitting micrographs into optics groups
You are welcome to use the script below. Here is a step-by-step instruction:

1. Install anaconda (https://www.anaconda.com/) with python3.6 or later or check if you have it installed.

2. Copy optics_split.py and optics_add.py

3. Replace the first line in the scripts with your path to Anaconda's python.

4. Save the scripts and copy them to your relion project folder.

5. In the relion project folder create a folder where you will keep the symbolic links to your raw data.
```
mkdir movies
cd movies
```
6. Find the raw data from the microscope to import:
```
find [path to your data] -name "*fractions.tiff"
```
7. Create symbolic links to your micrograph-movie files (use wildcards):
```
find [path to your movie-data] -name "*fractions.tiff" | xargs -I {} ln -s {} .

Example:
find /mnt/scopem-emdata/krios2/cryohub/my_dataset/ -name "*fractions.tiff" | xargs -I {} ln -s {} . 
```
8. Find the EPU data (.xml files, which are kept in the separate folder when you collect your data!) from the microscope to import (use wildcards):
```
find  [path to your epu-data] -name "FoilHole_????????_Data_????????_????????_????????_??????.xml" | xargs -I {} ln -s {} .  
```
9. Run optics_split.py to see the options.

10. Run optics_split.py with your data colection parameters.
```
Example for 9 holes/stage shift:
optics_split.py --i ./movies --o movies_with_optics.star --f tiff --clusters 9 --pix 1.09
```
11. Run optics_add.py using the output from optics_split.py and your particles.star file (please note that the particles.star file should be before all the CtfRefinement procedures) 
```
optics_add.py --mov movies_with_optics.star --part particles.star --o particles_with_optics.star
```
