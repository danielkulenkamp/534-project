# CSE 534 Project

This repository contains all of the code that I used in my 534 project. It also contains code from my honors thesis and Matt's thesis (since I forked from his repo). 

The following files are of interest for my 534 project:
- la.tsv --> the locating array I used
- fd.tsv --> the factor data file (not reading in from it yet)
- fabfile.py --> look at lines 1451 to the end, this file is used by the fabric library to make remote calls on all of the nodes. It simplifies running experiments. It contains lots of code used for setting up REACT and experiments, including all of the experiments Matt ran, the ones I ran for my thesis, and the ones I ran for my 534 project. All of the 534 stuff is at the end of the file. 

That should be most of the code I used. The REACT code is in testbed/_react.py if you wanted to look at that. 

Let me know if there's anything else you need! :) 