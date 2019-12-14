#!/usr/bin/env python3
__author__ = "Bjarte Aarmo Lund,Jørgen Aarmo Lund"
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm


positions=6
readings=14
skipstart=1
df=pd.read_csv("exampledata/191128-pLipA-PNPB-288-1.csv",sep=",")
columns=df.columns
for position in range(0,positions*2,2):
    absorbancevstime=df[[columns[position],columns[position+1]]][skipstart:readings]
    avt=absorbancevstime.astype(float)
    avt.plot(x=columns[position],y=columns[position+1])
plt.show()


