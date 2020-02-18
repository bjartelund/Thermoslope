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
import matplotlib.backends.backend_pdf

pdf = matplotlib.backends.backend_pdf.PdfPages("thermofit-gradient-output.pdf")

plt.interactive(False) #Show plots until closed

#Fill in your values
EnzymeConcentration=1e-8 
ExtCoeff=2630
Kmguess=1e-4 #initial guess
Vmaxguess=50 #initial guess
temperaturebins=12
#To be used for when the product is the chromogenic unit
topconcentration=5e-4
dilution=2


#Should probably not be changed
R=8.314
T=298.15
h=6.626e-34
kb=1.38e-23


def MichaelisMenten(x,Km,Vmax):
    return (Vmax*x)/(Km+x)
def fitMichaelisMenten(dataframesection):
    popt,pcov = curve_fit(MichaelisMenten,dataframesection[1]["Concentration"],dataframesection[1]["Time_regression"],p0=[Kmguess,Vmaxguess]) #standard linear regression
    return popt #ignore covariances for now
def inversetemp(temperature):
    return 1.0/temperature
def logKcat(Kcat):
    return np.log(Kcat)

def processcsv(datafile): 
    df=pd.read_csv(datafile,sep=",",header=None,names=("Cuvette","Time","Temperature","Absorbance")) #Assumes a csv-file following the named columns
    df["Time"]=df["Time"]*60 #calculate time in seconds instead of minutes (as the software supplies)
    df["Temperature"]=df["Temperature"]+273.15 #calculate temperature in Kelvin instead of degrees Celsius
    df["Concentration"]=df["Absorbance"]/ExtCoeff #calculate time in seconds instead of minutes
    df.sort_index(ascending=False,inplace=True) #The rolling regression leaves NaN for the first window, I would prefer to have the low temperature points available and reverse the dataframe for this reason
    cuvettes=df.groupby("Cuvette")
    regression=pd.DataFrame() #Build up a dataframe cuvette by cuvette
    for cuvette in cuvettes:
        cuvettedf=cuvette[1]
        Velocity=sm.add_constant(cuvettedf["Time"])
        Concentration=cuvettedf["Concentration"]
        movingregression=RollingOLS(Concentration,Velocity,window=4).fit(params_only=True)
#        fig = movingregression.plot_recursive_coefficient()
        regression=pd.concat([regression,movingregression.params])
    #fig.show()

    dfwregression=df.join(regression,rsuffix="_regression")
    dfwregression.dropna(inplace=True) #Remove the NaN rows
    dfwregression["Time_regression"]=np.abs(dfwregression["Time_regression"]) #Whether absorbance is increasing or decreasing, velocities should always be positive.
#    plt.plot(dfwregression.Temperature,dfwregression.Time_regression)
 #   plt.show()
    #plt.scatter(dfwregression["Temperature"],tempdependentMichaelisMenten((dfwregression["Concentration"],dfwregression["Temperature"]),*popt))
    return dfwregression

mergeddataframes=pd.concat([processcsv(datafile) for datafile in sys.argv[1:]]) #Collect all processed datasets in a single dataframe
#3D plot of raw data
fig=plt.figure()
ag=Axes3D(fig)
ag.plot_trisurf(mergeddataframes.Concentration,mergeddataframes.Temperature,mergeddataframes.Time_regression,cmap=cm.jet)
pdf.savefig(fig)

#Show excerpt of data with velocities
fig, ax =plt.subplots(figsize=(12,4))
ax.axis('tight')
ax.axis('off')
the_table = ax.table(cellText=mergeddataframes.values[:10],colLabels=mergeddataframes.columns,loc='center')
pdf.savefig(fig, bbox_inches='tight')

temperatures=pd.cut(mergeddataframes.Temperature,temperaturebins) #Bin observations by temperature
temperaturesets=mergeddataframes.groupby(temperatures)

#Fit individual bins by classical Michaelis Menten by non-linear regression
kcatsvstemp=pd.DataFrame(([(temperature[1]["Temperature"].mean(),fitMichaelisMenten(temperature)[1]/EnzymeConcentration) for temperature in temperaturesets]),columns=("Temperature","Kcat"))
for temperature in temperaturesets:
    fig=plt.figure()
    plt.title(temperature[1]["Temperature"].mean())
    plt.plot(temperature[1].Concentration,temperature[1].Time_regression,linestyle="None",markersize=10,color="r",marker=11)
    regression=fitMichaelisMenten(temperature)
    plt.plot(temperature[1].Concentration,MichaelisMenten(temperature[1].Concentration,regression[0],regression[1]),linestyle="None",marker=9)
    pdf.savefig(fig)
#Construct Arrhenius-plot
kcatsvstemp["1/T"]=inversetemp(kcatsvstemp["Temperature"])
kcatsvstemp["ln(Kcat)"]=logKcat(kcatsvstemp["Kcat"])
Arrheniusmodel=sm.OLS(kcatsvstemp["ln(Kcat)"],sm.add_constant(kcatsvstemp["1/T"])).fit()
fig=plt.figure()
plt.title("Arrhenius")
plt.plot(kcatsvstemp["1/T"],kcatsvstemp["ln(Kcat)"],linestyle="None",marker=11)
plt.plot(kcatsvstemp["1/T"],Arrheniusmodel.params[0]+Arrheniusmodel.params[1]*np.array(kcatsvstemp["1/T"]))
pdf.savefig(fig)
fig, ax =plt.subplots(figsize=(12,4))
ax.axis('tight')
ax.axis('off')
the_table = ax.table(cellText=kcatsvstemp.values[:10],colLabels=kcatsvstemp.columns,loc='center')
pdf.savefig(fig, bbox_inches='tight')
#Fit Arrhenius-equation
Ea=-Arrheniusmodel.params[1]*R
lnkcat=(-Ea/R)*(1/T)+Arrheniusmodel.params[0]
#Calculate thermodynamic properties
dH=Ea-R*T
dG=R*T*(np.log(kb/h) +np.log(T)-lnkcat)
dG=R*T*(np.log(kb/h) +np.log(T)-lnkcat)
dS=(dH-dG)/T
Parameters=pd.Series(("dG","dH","dS","Ea","ln(kcat) 298K"))
Values=pd.Series((dG,dH,dS,Ea,lnkcat))
frame={"Parameters":Parameters,"Values":Values}
arrheniusparameters=pd.DataFrame(frame)

fig, ax =plt.subplots(figsize=(12,4))
ax.axis('tight')
ax.axis('off')
the_table = ax.table(cellText=arrheniusparameters.values,colLabels=arrheniusparameters.columns,loc='center')
pdf.savefig(fig, bbox_inches='tight')
pdf.close()
