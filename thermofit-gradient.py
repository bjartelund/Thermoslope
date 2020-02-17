#!/usr/bin/env python3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy.optimize import curve_fit
from statsmodels.regression.rolling import RollingOLS
import sys
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm

plt.interactive(False)

EnzymeConcentration=1e-8
ExtCoeff=2630
topconcentration=5e-4
dilution=2
guessA=1
R=8.314
T=298.15
guessmkm=1e-4
guessEa=30000

Kmguess=1e-4 #initial guess
Vmaxguess=50 #initial guess
def tempdependentMichaelisMenten(x,A,Ea,mkm):
    return A*np.exp(-Ea/(R*x[1]))*(x[0]/((mkm*x[1])+x[0]))

def MichaelisMenten(x,Km,Vmax):
    return (Vmax*x)/(Km+x)
def fitMichaelisMenten(dataframesection):
    popt,pcov = curve_fit(MichaelisMenten,dataframesection[1]["Concentration"],dataframesection[1]["Time_regression"],p0=[Kmguess,Vmaxguess])
    return popt
def inversetemp(temperature):
    return 1.0/temperature
def logKcat(Kcat):
    return np.log(Kcat)

#def tempdependentMichaelisMenten(x

def processcsv(datafile):
    print(datafile)
    df=pd.read_csv(datafile,sep=",",header=None,names=("Cuvette","Time","Temperature","Absorbance"))
    df["Time"]=df["Time"]*60 #calculate time in seconds instead of minutes
    df["Temperature"]=df["Temperature"]+273.15 #calculate temperature in Kelvin instead of degrees Celsius
    df["Concentration"]=df["Absorbance"]/ExtCoeff #calculate time in seconds instead of minutes
    df.sort_index(ascending=False,inplace=True)
    cuvettes=df.groupby("Cuvette")
    regression=pd.DataFrame()
    for cuvette in cuvettes:
        cuvettedf=cuvette[1]
        Velocity=sm.add_constant(cuvettedf["Time"])
        Concentration=cuvettedf["Concentration"]
        movingregression=RollingOLS(Concentration,Velocity,window=4).fit(params_only=True)
#        fig = movingregression.plot_recursive_coefficient()
        regression=pd.concat([regression,movingregression.params])
    #fig.show()

    dfwregression=df.join(regression,rsuffix="_regression")
    dfwregression.dropna(inplace=True)
    dfwregression["Time_regression"]=np.abs(dfwregression["Time_regression"])
#    plt.plot(dfwregression.Temperature,dfwregression.Time_regression)
 #   plt.show()
    #plt.scatter(dfwregression["Temperature"],tempdependentMichaelisMenten((dfwregression["Concentration"],dfwregression["Temperature"]),*popt))
    return dfwregression

dataframes=[processcsv(datafile) for datafile in sys.argv[1:]]
mergeddataframes=pd.concat(dataframes)
temperatures=pd.cut(mergeddataframes.Temperature,12)
temperaturesets=mergeddataframes.groupby(temperatures)

kcatsvstemp=pd.DataFrame(([(temperature[1]["Temperature"].mean(),fitMichaelisMenten(temperature)[1]/EnzymeConcentration) for temperature in temperaturesets]),columns=("Temperature","Kcat"))
kcatsvstemp["1/T"]=inversetemp(kcatsvstemp["Temperature"])
kcatsvstemp["ln(Kcat)"]=logKcat(kcatsvstemp["Kcat"])
kcatsvstemp.plot("ln(Kcat)","Temperature")
plt.show()
print(kcatsvstemp)
Arrheniusmodel=sm.OLS(kcatsvstemp["ln(Kcat)"],sm.add_constant(kcatsvstemp["Temperature"])).fit()
print(Arrheniusmodel.params[1])
    #temperature[1].plot("Concentration","Time_regression",linestyle="None",markersize=10,color="r",marker=11)
