#!/usr/bin/env python3
import os
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import sys
from statsmodels.regression.rolling import RollingOLS
from scipy.optimize import curve_fit
import statsmodels.api as sm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.style as mplstyle
mpl.use('agg')
plt.ioff()
mpl.rcParams['path.simplify'] = True
mpl.rcParams['path.simplify_threshold'] = 1.0
mpl.rcParams['savefig.dpi'] = 50

mplstyle.use('fast')

np.seterr(all='raise')


def MichaelisMenten(x, Km, Vmax):
    return (Vmax*x)/(Km+x)


def inversetemp(temperature):
    return 1.0/temperature


def logKcat(Kcat):
    return np.log(Kcat)


class ThermoSlope:
    def __init__(self, datafiles, **kwargs):
        self.datafiles = datafiles
        # assumes that all files are from the same directory
        self.path = os.path.dirname(datafiles[0])
        self.ProductAbsorbing = kwargs["ProductAbsorbing"] if "ProductAbsorbing" in kwargs else True
        self.EnzymeConcentration = float(
            kwargs["EnzymeConcentration"]) if "EnzymeConcentration" in kwargs else 2.5e-9
        self.ExtCoeff = float(
            kwargs["ExtCoeff"]) if "ExtCoeff" in kwargs else 1.78e4
        self.Kmguess = float(
            kwargs["Kmguess"]) if "Kmguess" in kwargs else 1e-5
        self.Vmaxguess = float(
            kwargs["Vmaxguess"]) if "Vmaxguess" in kwargs else 50
        self.temperaturebins = int(
            kwargs["temperaturebins"]) if "temperaturebins" in kwargs else 12
        self.topconcentration = float(
            kwargs["topconcentration"]) if "topconcentration" in kwargs else 2e-3
        self.dilution = int(kwargs["dilution"]) if "dilution" in kwargs else 2
        self.positions = int(kwargs["positions"]
                             ) if "positions" in kwargs else 6
        self.lowtempcutoff = float(
            kwargs["lowtempcutoff"]) if "lowtempcutoff" in kwargs else 270
        self.hightempcutoff = float(
            kwargs["hightempcutoff"]) if "hightempcutoff" in kwargs else 373

    def fitMichaelisMenten(self, dataframesection):
        Concvstime=dataframesection[1]
        popt, pcov = curve_fit(MichaelisMenten, Concvstime["Concentration"], Concvstime["Time_regression"], p0=[
                               self.Kmguess, self.Vmaxguess])  # standard linear regression
        return (popt, pcov)  # ignore covariances for now

    def processcsv(self, datafile):
        df = pd.read_csv(datafile, sep=",", header=None, names=(
            "Cuvette", "Time", "Temperature", "Absorbance"))  # Assumes a csv-file following the named columns
        # calculate time in seconds instead of minutes (as the software supplies)
        df["Time"] = df["Time"]*60
        # calculate temperature in Kelvin instead of degrees Celsius
        df["Temperature"] = df["Temperature"]+273.15
        if self.ProductAbsorbing:
            df["StartingConcentration"] = [self.startingconcentrations[x-1]
                                           for x in df["Cuvette"]]
            # calculate concentration depending on start concentration and depletion of substrate
            df["Concentration"] = df["StartingConcentration"] - \
                df["Absorbance"]/self.ExtCoeff
        else:
            # calculate concentration directly from absorbance
            df["Concentration"] = df["Absorbance"]/self.ExtCoeff
        # The rolling regression leaves NaN for the first window, 
        #I would prefer to have the low temperature points available 
        #and reverse the dataframe for this reason
        df.sort_index(ascending=False, inplace=True)
        cuvettes = df.groupby("Cuvette")
        regression = pd.DataFrame()  # Build up a dataframe cuvette by cuvette
        for cuvette in cuvettes:
            cuvettedf = cuvette[1]
            Velocity = sm.add_constant(cuvettedf["Time"])
            Concentration = cuvettedf["Concentration"]
            movingregression = RollingOLS(
                Concentration, Velocity, window=4).fit(params_only=True)
            regression = pd.concat([regression, movingregression.params])
        dfwregression = df.join(regression, rsuffix="_regression")
        # Repeat rolling regression other direction, double the number of points
        df.sort_index(ascending=True, inplace=True)
        cuvettes = df.groupby("Cuvette")
        regression = pd.DataFrame()  # Build up a dataframe cuvette by cuvette
        for cuvette in cuvettes:
            cuvettedf = cuvette[1]
            Velocity = sm.add_constant(cuvettedf["Time"])
            Concentration = cuvettedf["Concentration"]
            movingregression = RollingOLS(
                Concentration, Velocity, window=4).fit(params_only=True)
            regression = pd.concat([regression, movingregression.params])

        dfwregression = df.join(regression, rsuffix="_regression")
        dfwregression.dropna(inplace=True)  # Remove the NaN rows
        # Whether absorbance is increasing or decreasing, velocities should always be positive.
        dfwregression["Time_regression"] = np.abs(
            dfwregression["Time_regression"])
        return dfwregression

    def process(self):
        plt.interactive(False)  # Show plots until closed
        # Should probably not be changed
        R = 8.314
        T = 298.15
        h = 6.626e-34
        kb = 1.38e-23

        self.startingconcentrations = [
            self.topconcentration/self.dilution**x for x in range(0, self.positions)]

        # Collect all processed datasets in a single dataframe
        mergeddataframes = pd.concat(
            [self.processcsv(datafile) for datafile in self.datafiles])
        # Show excerpt of data with velocities
        # 3D plot of raw data
        fig, ax = plt.subplots()
        ag = Axes3D(fig)
        ag.plot_trisurf(mergeddataframes.Concentration, mergeddataframes.Temperature,
                        mergeddataframes.Time_regression, cmap=cm.jet)
        fig.savefig(os.path.join(
            self.path, "thermoslope-3D.png"), format="png")
        plt.clf()

        # Bin observations by temperature
        temperatures = pd.cut(
            mergeddataframes.Temperature, self.temperaturebins)
        temperaturesets = mergeddataframes.groupby(temperatures)

        # Fit individual bins by classical Michaelis Menten by non-linear regression
        temperaturesetslist = []

        self.figurefilenames = []
      

        fig = plt.figure()
        for temperature in temperaturesets:
            temperaturemean = temperature[1]["Temperature"].mean()
            if self.lowtempcutoff < temperaturemean < self.hightempcutoff:
                plt.title(temperature[1]["Temperature"].mean())
                plt.plot(temperature[1].Concentration, temperature[1].Time_regression,
                         linestyle="None", markersize=10, color="r", marker=11)
                regression, covariance = self.fitMichaelisMenten(temperature)
                Vmax = regression[1]
                kcat = Vmax/self.EnzymeConcentration
                perr = np.sqrt(np.diag(covariance))
                kcaterror = perr[1]/self.EnzymeConcentration
                plt.plot(temperature[1].Concentration, MichaelisMenten(
                    temperature[1].Concentration, regression[0], regression[1]), linestyle="None", marker=9)
                temperaturesetslist.append(
                    [temperaturemean, Vmax, kcat, kcaterror])
                figurefilename = os.path.join(
                    self.path, str(temperaturemean)+"-MM.png")
                fig.savefig(figurefilename, format="png")
                self.figurefilenames.append(figurefilename)
                plt.clf()

        # Construct Arrhenius-plot
        kcatsvstemp = pd.DataFrame(temperaturesetslist, columns=[
                                   "Temperature", "Vmax", "Kcat", "Kcaterror"])

        kcatsvstemp["1/T"] = inversetemp(kcatsvstemp["Temperature"])
        kcatsvstemp["ln(Kcat)"] = np.log(kcatsvstemp["Kcat"])
        kcatsvstemp["ln(Kcaterror)"] = np.log(kcatsvstemp["Kcaterror"])
        self.kcatsvstemp = kcatsvstemp  # To be used in the report
        # Fit ln(kcat) against inverse Temp, weighing the parameters by the stddev of the estimated Kd
        # try:
        Arrheniusmodel = sm.WLS(kcatsvstemp["ln(Kcat)"].values, sm.add_constant(
            kcatsvstemp["1/T"].values), weights=kcatsvstemp["ln(Kcaterror)"].values**2).fit()
        # except:
        # Arrheniusmodel=sm.OLS(kcatsvstemp["ln(Kcat)"],sm.add_constant(kcatsvstemp["1/T"])).fit()
        plt.title("Arrhenius")
        plt.plot(kcatsvstemp["1/T"], kcatsvstemp["ln(Kcat)"],
                 linestyle="None", marker=11)
        fig.savefig(os.path.join(self.path, "arrhenius.png"), format="png")
        plt.close()
        # Fit Arrhenius-equation
        Ea = -Arrheniusmodel.params[1]*R
        lnkcat = (-Ea/R)*(1/T)+Arrheniusmodel.params[0]
        # Calculate thermodynamic properties
        dH = Ea-R*T
        dG = R*T*(np.log(kb/h) + np.log(T)-lnkcat)
        TdS = (dH-dG)
        dS = TdS/T
        Parameters = pd.Series(
            ("dG", "dH", "dS", "TdS", "Ea", "ln(kcat) 298K"))
        Values = pd.Series((dG, dH, dS, TdS, Ea, lnkcat))
        frame = {"Parameters": Parameters, "Values": Values}
        arrheniusparameters = pd.DataFrame(frame)
        arrheniusparameters["Values(kcal/mol)"] = arrheniusparameters.Values/4181
        self.arrheniusparameters = arrheniusparameters


if __name__ == '__main__':
    analysis = ThermoSlope(sys.argv[1:])
    analysis.process()
    #print(analysis.arrheniusparameters)