#!/usr/bin/env python3
__author__ = "Bjarte Aarmo Lund,Jørgen Aarmo Lund"
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy.optimize import curve_fit

def MichaelisMenten(x,Km,Vmax):
    return (Vmax*x)/(Km+x)

Kmguess=1e-3 #initial guess
Vmaxguess=1 #initial guess

positions=6
readings=14
skipstart=1
df=pd.read_csv("exampledata/191128-pLipA-PNPB-288-1.csv",sep=",")
columns=df.columns
velocityvsconcentration= pd.DataFrame(columns=["Concentration","Velocity","StdErr"])
for position in range(0,positions*2,2):
    absorbancevstime=df[[columns[position],columns[position+1]]][skipstart:readings]
    avt=absorbancevstime.astype(float)
    Y=avt[columns[position+1]]
    X=avt[columns[position]]
    X=sm.add_constant(X)
    linearmodel=sm.OLS(Y,X).fit()
    velocityvsconcentration.loc[position]= [float(columns[position][columns[position].find("-")+2:]),linearmodel.params[1],linearmodel.bse[1]]
velocityvsconcentration.plot(x="Concentration",y="Velocity")
popt,pcov = curve_fit(MichaelisMenten,velocityvsconcentration["Concentration"],velocityvsconcentration["Velocity"],p0=[Kmguess,Vmaxguess])
print(popt)
plt.plot(velocityvsconcentration["Concentration"],MichaelisMenten(velocityvsconcentration["Concentration"],*popt))

plt.show()


