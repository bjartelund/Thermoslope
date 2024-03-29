#!/usr/bin/env python3
__author__ = "Bjarte Aarmo Lund"
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy.optimize import curve_fit
import sys
import matplotlib.backends.backend_pdf


def MichaelisMenten(x, Km, Vmax):
    return (Vmax*x)/(Km+x)


Kmguess = 1e-3  # initial guess
Vmaxguess = 1  # initial guess
E0 = 1e-8  # Molar enzyme concentration
ExtCoeff = 2920
positions = 6
readings = 14
skipstart = 1

kcatvstemperature = pd.DataFrame(columns=["Temperature", "Kcat"])
ExcelWriter = pd.ExcelWriter("michaelismenten.xlsx")
pdf = matplotlib.backends.backend_pdf.PdfPages("michaelismenten-output.pdf")

for datafile in sys.argv[1:]:
    print(datafile)
    df = pd.read_csv(datafile, sep=",")
    columns = df.columns
    velocityvsconcentration = pd.DataFrame(
        columns=["Concentration", "Velocity", "StdErr"])
    for position in range(0, positions*2, 2):
        absorbancevstime = df[[columns[position],
                               columns[position+1]]][skipstart:readings]
        avt = absorbancevstime
        Y = pd.to_numeric(avt[columns[position+1]],
                          errors="coerce")[pd.notnull]
        X = pd.to_numeric(avt[columns[position]], errors="coerce")[pd.notnull]
        X = sm.add_constant(X)
        linearmodel = sm.OLS(Y, X).fit()
        velocityvsconcentration.loc[position] = [float(columns[position][columns[position].find(
            "-")+2:]), linearmodel.params[1], linearmodel.bse[1]]
    popt, pcov = curve_fit(
        MichaelisMenten, velocityvsconcentration["Concentration"], velocityvsconcentration["Velocity"], p0=[Kmguess, Vmaxguess])
    # 60 seconds in a minute, readings given per minute. seconds is SI
    kcat = (popt[1]/(60*ExtCoeff))/E0
    print(kcat)
    fig = plt.figure()
    plt.plot(velocityvsconcentration["Concentration"], MichaelisMenten(
        velocityvsconcentration["Concentration"], *popt))
    pdf.savefig(fig)

    temperatures = df[df[columns[0]].str.startswith(
        "Hold Temperature Changed")]
    newtemp = temperatures[columns[2]].iloc[-1]
    # temperatures given in Celsius
    tempinkelvin = float(newtemp[newtemp.find("New:")+4:])+273.15

plt.show()
pdf.close()
