#!/usr/bin/env python3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy.optimize import curve_fit
from statsmodels.regression.rolling import RollingOLS
import sys
from matplotlib import cm
from io import BytesIO
imgdata = BytesIO()

ExcelWriter=pd.ExcelWriter("thermofit-gradient.xlsx",engine='xlsxwriter')
plt.interactive(False) #Show plots until closed

#Fill in your values
ProductAbsorbing=True
EnzymeConcentration=2.5e-9 
ExtCoeff=1.78e4
Kmguess=1e-3 #initial guess
Vmaxguess=50 #initial guess
temperaturebins=12
#To be used for when the product is the chromogenic unit
topconcentration=2e-3
dilution=2
positions=6

lowtempcutoff=270
hightempcutoff=373

#Should probably not be changed
R=8.314
T=298.15
h=6.626e-34
kb=1.38e-23

Parameters=pd.Series(("EnzConc","ExtCoeff","Kmguess","Vmaxguess","temperaturebins","topsubstrateconc","dilutionfactor","lowtempcutoff","hightempcutoff","R","T","h","kb"))
Values=pd.Series((EnzymeConcentration,ExtCoeff,Kmguess,Vmaxguess,temperaturebins,topconcentration,dilution,lowtempcutoff,hightempcutoff,R,T,h,kb))
frame={"Parameters":Parameters,"Values":Values}
thermofitparameters=pd.DataFrame(frame)
thermofitparameters.to_excel(ExcelWriter,sheet_name="Parameters")


startingconcentrations= [topconcentration/dilution**x for x in range(0,positions)]

def MichaelisMenten(x,Km,Vmax):
    return (Vmax*x)/(Km+x)
def fitMichaelisMenten(dataframesection):
    popt,pcov = curve_fit(MichaelisMenten,dataframesection[1]["Concentration"],dataframesection[1]["Time_regression"],p0=[Kmguess,Vmaxguess]) #standard linear regression
    return (popt,pcov) #ignore covariances for now
def inversetemp(temperature):
    return 1.0/temperature
def logKcat(Kcat):
    return np.log(Kcat)

def processcsv(datafile): 
    df=pd.read_csv(datafile,sep=",",header=None,names=("Cuvette","Time","Temperature","Absorbance")) #Assumes a csv-file following the named columns
    df.to_excel(ExcelWriter,sheet_name="Raw data %s" % datafile.rpartition("/")[2])
    df["Time"]=df["Time"]*60 #calculate time in seconds instead of minutes (as the software supplies)
    df["Temperature"]=df["Temperature"]+273.15 #calculate temperature in Kelvin instead of degrees Celsius
    if ProductAbsorbing:
        df["StartingConcentration"]=[startingconcentrations[x-1 ] for x in df["Cuvette"]]
        df["Concentration"] = df["StartingConcentration"] - df["Absorbance"]/ExtCoeff #calculate concentration depending on start concentration and depletion of substrate
    else:
        df["Concentration"]= df["Absorbance"]/ExtCoeff #calculate concentration directly from absorbance
    df.sort_index(ascending=False,inplace=True) #The rolling regression leaves NaN for the first window, I would prefer to have the low temperature points available and reverse the dataframe for this reason
    cuvettes=df.groupby("Cuvette")
    regression=pd.DataFrame() #Build up a dataframe cuvette by cuvette
    for cuvette in cuvettes:
        cuvettedf=cuvette[1]
        Velocity=sm.add_constant(cuvettedf["Time"])
        Concentration=cuvettedf["Concentration"]
        movingregression=RollingOLS(Concentration,Velocity,window=4).fit(params_only=True)
        regression=pd.concat([regression,movingregression.params])
    dfwregression=df.join(regression,rsuffix="_regression")
    df.sort_index(ascending=True,inplace=True) #Repeat rolling regression other direction, double the number of points
    cuvettes=df.groupby("Cuvette")
    regression=pd.DataFrame() #Build up a dataframe cuvette by cuvette
    for cuvette in cuvettes:
        cuvettedf=cuvette[1]
        Velocity=sm.add_constant(cuvettedf["Time"])
        Concentration=cuvettedf["Concentration"]
        movingregression=RollingOLS(Concentration,Velocity,window=4).fit(params_only=True)
        regression=pd.concat([regression,movingregression.params])

    dfwregression=df.join(regression,rsuffix="_regression")
    dfwregression.dropna(inplace=True) #Remove the NaN rows
    dfwregression["Time_regression"]=np.abs(dfwregression["Time_regression"]) #Whether absorbance is increasing or decreasing, velocities should always be positive.
    return dfwregression

mergeddataframes=pd.concat([processcsv(datafile) for datafile in sys.argv[1:]]) #Collect all processed datasets in a single dataframe
#Show excerpt of data with velocities
mergeddataframes.to_excel(ExcelWriter,sheet_name="Processed data")
#3D plot of raw data
fig=plt.figure()
fig, ax = plt.subplots()
ag=Axes3D(fig)
ag.plot_trisurf(mergeddataframes.Concentration,mergeddataframes.Temperature,mergeddataframes.Time_regression,cmap=cm.jet)
fig.savefig(imgdata, format="png")
imgdata.seek(0)
workbook=ExcelWriter.book
worksheet = workbook.add_worksheet()
worksheet.insert_image("F20","3D.png",{'image_data': imgdata})


temperatures=pd.cut(mergeddataframes.Temperature,temperaturebins) #Bin observations by temperature
temperaturesets=mergeddataframes.groupby(temperatures)

#Fit individual bins by classical Michaelis Menten by non-linear regression
temperaturesetslist=[]

worksheet = workbook.add_worksheet()
i=1
for temperature in temperaturesets:
    temperaturemean=temperature[1]["Temperature"].mean()
    imgdata = BytesIO()
    if lowtempcutoff<temperaturemean<hightempcutoff:
        fig=plt.figure()
        plt.title(temperature[1]["Temperature"].mean())
        plt.plot(temperature[1].Concentration,temperature[1].Time_regression,linestyle="None",markersize=10,color="r",marker=11)
        regression,covariance=fitMichaelisMenten(temperature)
        Vmax=regression[1]
        kcat=Vmax/EnzymeConcentration
        perr = np.sqrt(np.diag(covariance))
        kcaterror=perr[1]/EnzymeConcentration
        plt.plot(temperature[1].Concentration,MichaelisMenten(temperature[1].Concentration,regression[0],regression[1]),linestyle="None",marker=9)
        temperaturesetslist.append([temperaturemean,Vmax,kcat,kcaterror])
        fig.savefig(imgdata, format="png")
        imgdata.seek(0)
        worksheet.insert_image("A"+str(i),str(temperaturemean)+"MM.png",{'image_data': imgdata})
        i=i+25
#Construct Arrhenius-plot
kcatsvstemp=pd.DataFrame(temperaturesetslist,columns=["Temperature","Vmax","Kcat","Kcaterror"])

kcatsvstemp["1/T"]=inversetemp(kcatsvstemp["Temperature"])
kcatsvstemp["ln(Kcat)"]=np.log(kcatsvstemp["Kcat"])
kcatsvstemp["ln(Kcaterror)"]=np.log(kcatsvstemp["Kcaterror"])
#Fit ln(kcat) against inverse Temp, weighing the parameters by the stddev of the estimated Kd
Arrheniusmodel=sm.WLS(kcatsvstemp["ln(Kcat)"].values,sm.add_constant(kcatsvstemp["1/T"].values),weights=kcatsvstemp["ln(Kcaterror)"].values).fit()
print(Arrheniusmodel.summary())
imgdata = BytesIO()
fig=plt.figure()
plt.title("Arrhenius")
plt.plot(kcatsvstemp["1/T"],kcatsvstemp["ln(Kcat)"],linestyle="None",marker=11)
plt.plot(kcatsvstemp["1/T"],Arrheniusmodel.params[0]+Arrheniusmodel.params[1]*np.array(kcatsvstemp["1/T"]))
fig, ax =plt.subplots(figsize=(12,4))        
fig.savefig(imgdata, format="png")
imgdata.seek(0)
kcatsvstemp.to_excel(ExcelWriter,sheet_name="Kcat vs temp")
worksheet = workbook.add_worksheet()
worksheet.insert_image("A1","Arrhenius.png",{'image_data': imgdata})
#Fit Arrhenius-equation
Ea=-Arrheniusmodel.params[1]*R
lnkcat=(-Ea/R)*(1/T)+Arrheniusmodel.params[0]
#Calculate thermodynamic properties
dH=Ea-R*T
dG=R*T*(np.log(kb/h) +np.log(T)-lnkcat)
dS=(dH-dG)/T
Parameters=pd.Series(("dG","dH","dS","Ea","ln(kcat) 298K"))
Values=pd.Series((dG,dH,dS,Ea,lnkcat))
frame={"Parameters":Parameters,"Values":Values}
arrheniusparameters=pd.DataFrame(frame)
arrheniusparameters["ValuesKcat"]=arrheniusparameters.Values/4181
arrheniusparameters.to_excel(ExcelWriter,sheet_name="Fitted parameters")

commandline=pd.DataFrame(sys.argv,columns=("argument",))
commandline.to_excel(ExcelWriter,sheet_name="Arguments")



ExcelWriter.close()
