#!/usr/bin/env python3
__author__ = "Bjarte Aarmo Lund"
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy.optimize import curve_fit
import sys
import matplotlib.backends.backend_pdf
import matplotlib as mpl
mpl.use('agg')


def MichaelisMenten(x, Km, Vmax):
    return (Vmax*x)/(Km+x)


Kmguess = 1e-3  # initial guess
Vmaxguess = 1  # initial guess
E0 = 1e-9  # Molar enzyme concentration
ExtCoeff = 1.78e4
positions = 6
readings = 5
skipstart = 1

kcatvstemperature = pd.DataFrame(columns=["Temperature", "Kcat","Kcaterror","Km","Kmerror"])
ExcelWriter = pd.ExcelWriter("thermofit.xlsx")
pdf = matplotlib.backends.backend_pdf.PdfPages("thermofit-output.pdf")

joinedvelocityvsconcentrations = pd.DataFrame(columns=["Concentration", "Velocity", "StdErr","Temperature"])
for datafile in sys.argv[1:]:
    velocityvsconcentrations = pd.DataFrame(columns=["Concentration", "Velocity", "StdErr","Temperature"])
    df = pd.read_csv(datafile, sep=",")
    columns = df.columns
    temperatures = df[df[columns[0]].str.startswith(
        "Hold Temperature Changed")]
    newtemp = temperatures[columns[2]].iloc[-1]
    # temperatures given in Celsius
    tempinkelvin = float(newtemp[newtemp.find("New:")+4:])+273.15
    for position in range(0, positions*2, 2):
        absorbancevstime = df[[columns[position],
                               columns[position+1]]][skipstart:readings]
        avt = absorbancevstime
        Y = pd.to_numeric(avt[columns[position+1]],
                          errors="coerce")[pd.notnull]
        X = pd.to_numeric(avt[columns[position]], errors="coerce")[pd.notnull]
        X = sm.add_constant(X)
        linearmodel = sm.OLS(Y, X).fit()
        velocityvsconcentrations.loc[position] = [float(columns[position][columns[position].find(
            "-")+2:]), linearmodel.params[1], linearmodel.bse[1],tempinkelvin]
    joinedvelocityvsconcentrations=joinedvelocityvsconcentrations.append(velocityvsconcentrations)

for temperature in joinedvelocityvsconcentrations["Temperature"].unique():
        velocityvsconcentration=joinedvelocityvsconcentrations[joinedvelocityvsconcentrations["Temperature"] == temperature]
        popt, pcov = curve_fit(MichaelisMenten, velocityvsconcentration["Concentration"], velocityvsconcentration["Velocity"], p0=[Kmguess, Vmaxguess])
    # 60 seconds in a minute, readings given per minute. seconds is SI
        kcat = (popt[1]/(60*ExtCoeff))/E0
        perr = np.sqrt(np.diag(pcov))
        kcaterror = (perr[1]/(60*ExtCoeff))/E0
        km= popt[0]
        kmerror= perr[0]
        kcatvstemperature=kcatvstemperature.append({"Temperature":temperature,"Kcat": kcat,"Kcaterror":kcaterror,"Km":km,"Kmerror":kmerror},ignore_index=True)

# Arrhenius


def inversetemp(temperature):
    return 1.0/temperature


def logKcat(Kcat):
    return np.log(Kcat)


kcatvstemperature["Inverse Temperature"] = kcatvstemperature["Temperature"].apply(
    inversetemp)
X = kcatvstemperature["Inverse Temperature"]
kcatvstemperature["ln(Kcat)"] = kcatvstemperature["Kcat"].apply(logKcat)
Y = kcatvstemperature["ln(Kcat)"]
fig = plt.figure()
kcatvstemperature.plot.scatter(x="Inverse Temperature", y="ln(Kcat)")
pdf.savefig(fig)

kcatvstemperature.to_csv(path_or_buf="kcatvstemperature.csv", index=False)
kcatvstemperature.to_excel(excel_writer="kcatvstemperature.xlsx", index=False)
X = sm.add_constant(X)
Arrheniusmodel = sm.OLS(Y, X).fit()
print(kcatvstemperature)
print(Arrheniusmodel.params[1])
print(Arrheniusmodel.params[0])
pdf.close()
