# PIO
Principal Interacting Orbital

Requirement
---
- Gaussian 09/16
- NBO 6.0
- Python 3.6
- Numpy 1.13.1

The combination here has been well-tested. Other versions are not guaranteed to work but are welcomed to test.

Tutorial
---
1. Run quantum chemistry calculation
    
    Optmize the structure and calculate the electronic structure using standard quantum chemistry softwares. Gaussian09 is used for following demonstration.
    
    **Input**
    - *FILENAME.gjf*
    
    **Output**
    - *FILENAME.log*
        ordinary Gaussian output file
    - *FILENAME.FChk*
        FormCheck file is required for the current version of PIO analysis, for the purpose of visualizing orbital using GaussView. It can be generated via keyword *formcheck* specified in gjf file, or via running external formchk utility
    - *FILENAME.47*
        A FILENAME.47 file can be generated in Gaussian calculations via keyword *pop=nboread* and nbo keyword *$NBO archive $end* specified in gjf file. As the built-in NBO package in Gaussian 09 is NBO3.0, which is a quite old version of NBO package, an external NBO analysis with more recent version is suggested. 

2. Run an NBO analysis

    Run a NBO analysis on the system of interest. The test result is done by an external NBO package. Usage of NBO 3.0 (which is built-in in Gaussian 09) is not recommended but is allowed as long as proper NBO keywords are specified in the gaussian input file (in this case no .nbo file will be generated but a .49 file will still be generated for this PIO code to read).
    
    **Input**
    - *FILENAME.47*
        NBO input file, can be generated via running an internal NBO analysis in Gaussian
    
    The following NBO keywords should be specified in the NBO analysis:
    
        $NBO AONAO=W49 FNAO=W49 DMNAO=W49 SKIPBO $END
   
    **Running the NBO analysis**         
    Run the NBO analysis using the following command (replace FILENAME with your own file name, and note .47 should not be included):
    
        gennbo FILENAME
    
    **Output**
    - *FILENAME.nbo*
        ordinary NBO output file (if run by an external NBO package)
    - *FILENAME.49*
        extra output required for PIO analysis, containing NAO coefficients, density matrix in NAO basis, and Fock matrix in NAO basis if available; only appear if the above mentioned NBO keywords have been specified properly

3. Run PIO analysis

    We now run PIO analysis with the following command. Note that FILENAME.49 must exist with the same name as FILENAME.FChk.
    
    **Command:**
    
        python PIO.py FILENAME.FChk
    
    The program will then request for a fragmentation as input to specify two groups of atoms
    
    **Input:**
    
        1,2,3,4 5-8
    
    Two groups of atom IDs should be input here separated by a space. Numbers in each group are separated by a comma. Hyphen is supported for sequential numbers. Atom numbering starts from 1. Complete fragmentation is always recommended (i.e. the specified two groups cover all the atoms present in the system). Incomplete fragmentation will lead to absence of mathematical elegance but is still meaningful if you really want to do it.

    **Output**
     *FILENAME_pio.txt*
        PIO log file, containing basic information of the PIOs of the system subject to the input fragmentation
    - *FILENAME_pio.FChk*
        Gaussian FormCheck file containing PIOs labeled as in the txt file, could be visualized by GaussView and other compatable orbital visualization softwares
    - *FILENAME_pimo.FChk*
        A similar Gaussian FormCheck file containing PIMOs whose ordering is same as that of PIOs
    - *FILENAME_pio.raw*
        numpy-formatted raw data file for debugging or advanced user

Related publication
---
DOI:10.1002/chem.201801220

TODO
---
- [x] Upgrade the code to make it compatable with spin-polarized systems (coming soon)
- [x] Transplant to python 3

Disclaimer
---
Copyright (c) 2018 jxzhangcc and fksheong

All rights reserved.

Redistribution and use in source and binary forms are permitted provided that the above copyright notice and this paragraph are duplicated in all such forms and that any documentation, advertising materials, and other materials related to such distribution and use acknowledge that the software was developed by the author. The name of the authors may not be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED ``AS IS'' AND WITHOUT ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
