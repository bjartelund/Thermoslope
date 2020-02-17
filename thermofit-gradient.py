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


ExtCoeff=2630
topconcentration=5e-4
dilution=2
guessA=1e6
R=8.314
T=298.15
guessckm=1
guessmkm=0.01
guessEa=30000
def tempdependentMichaelisMenten(x,A,Ea,ckm,mkm):
    return A*np.exp(-Ea/R*x[1])*(x[0]/((ckm+mkm*x[1])+x[0]))

for datafile in sys.argv[1:]:
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
        movingregression=RollingOLS(Concentration,Velocity,window=7).fit(params_only=True)
#        fig = movingregression.plot_recursive_coefficient()
        regression=pd.concat([regression,movingregression.params])
    #fig.show()

    dfwregression=df.join(regression,rsuffix="_regression")
    dfwregression.dropna(inplace=True)
    print(dfwregression)
#    plt.plot(dfwregression.Temperature,dfwregression.Time_regression)
 #   plt.show()
    popt,pcov = curve_fit(tempdependentMichaelisMenten,
            (dfwregression["Concentration"],dfwregression["Temperature"]),
            dfwregression["Time_regression"],
            p0=[guessA,guessEa,guessckm,guessmkm])
    print(popt)
    fig=plt.figure()
    ag=Axes3D(fig)
    ag.plot_trisurf(dfwregression.Concentration,dfwregression.Temperature,dfwregression.Time_regression,cmap=cm.jet)
    #plt.scatter(dfwregression["Temperature"],tempdependentMichaelisMenten((dfwregression["Concentration"],dfwregression["Temperature"]),*popt))
    plt.show()
