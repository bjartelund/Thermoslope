#!/usr/bin/env python3
import numpy as np
import sys
R=8.314
T=298.15
h=6.626e-34
kb=1.38e-23

if not len(sys.argv) > 1:
    print("Arguments taken A Ea/R")
else:
    A=float(sys.argv[1])
    EadivR=float(sys.argv[2])
    Ea=EadivR*R
    lnkcat=(-Ea/R)*(1/T)+A

    dH=Ea-R*T
    dH=dH/4181
    print("dH:%e" %dH)
    dG=R*T*(np.log(kb/h) +np.log(T)-lnkcat)
    dG=dG/4181
    print("dG:%e" %dG)
    dS=(dH-dG)
    dS=dS/4.18
    print("TdS:%e" %dS)
