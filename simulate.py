from scipy.integrate import quad_vec, quad
import matplotlib.pyplot as plt
import numpy as np
import math

enzymeconc=1e-9
km=2e-4
R=8.314
starttemperature=274
Ea=60000
A=1e11
gradient=1/15 #how many degrees per second the temperature is increased
extinctioncoefficient=1.78e4
duration=300 #How long should the simulated experiment last, gives the upper bond for temperature
substratemaxconc=5e-3
numberofcuvettes=6
figure=False

def kcat(A,Ea,temperature): #The Arrhenius equation
    exponent=( Ea) / (R*temperature)
    return A*math.exp(-exponent)

def MM(time,conc): #The Michaelis Menten equation with kcat as the temperature-dependent term
    temperature=starttemperature+gradient*time #temperature is calculated based on the slope/gradient and the elapsed time since start
    v=(kcat(A,Ea,temperature)*enzymeconc*conc)/(km+conc)
    return v*extinctioncoefficient #The exctinction coefficient is obviously not really relevant for the simulation, but should allow for test-sets to be on the same order of magnitude as real experimental sets.
def intMM(*args): #The integration function takes a list of arguments, the first being concentration in Molar, and the second the time elapsed in seconds
    conc=args[0][0]
    time=args[0][1]
    return quad(MM,0,time,args=(conc,))[0]


#Build up a 2D array of concentrations and time
concentrations=np.array([substratemaxconc/2**x for x in range(0,numberofcuvettes)]) #generates a list of substrate concentrations with 1:1 dilutions
timerange=np.arange(0,duration) # individual datapoints, analogous to reads in experiment
kineticarray= np.concatenate([np.column_stack((np.full(len(timerange),conc),timerange)) for conc in concentrations])
#Calculate velocities for each concentration/time combination by integrating the michaelismenten equation
resultater=np.hstack((kineticarray,np.row_stack(np.apply_along_axis(intMM,1,kineticarray))))

#To visualize the output generate a 3D scatter plot, but slow process so only if requested
X=resultater[:,0] # the concentration
Y=resultater[:,1] #time in seconds
noise = np.random.normal(1, 0.01, Y.shape) #1 centered with .01 std dev
Z=resultater[:,2] #*noise #the calculated velocity with some noise multiplied in

if figure:
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(X,Y,Z)
    fig.savefig("simulatedoutput.png")

temperatures=-273.15+starttemperature+gradient*Y #The thermoslope software expects temperatures in degree Celsius from its input
timeinmin=Y/60 #the time is expected to be reported in minutes
cuvette=np.array([concentrations.tolist().index(x)+1 for x in X]) #the cuvettes is to referred to by their number (1-6) (in contrast to python numbering (0-5)
simulatedoutput=np.stack([cuvette,timeinmin,temperatures,Z],axis=1)
np.savetxt("simulatedoutput.csv", simulatedoutput, delimiter=",",fmt=("%d","%3f","%3f","%3f")) #Export the generated array as csv. if higher precission is needed it is possible to extend the floats i.e. %3f to %5f 
