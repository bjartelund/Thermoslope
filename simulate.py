from scipy.integrate import quad_vec, quad
import matplotlib.pyplot as plt
import numpy as np
enzymeconc=1e-9
km=2e-4
vmax=20e-5
R=8.314
starttemperature=270
temperature=298
Ea=60000
import math
#A=np.exp(19.3)
A=1e11
gradient=1/15
extinctioncoefficient=1.78e4


def kcat(A,Ea,temperature):
    exponent=( Ea) / (R*temperature)
    return A*math.exp(-exponent)

def MM(time,conc):
    temperature=starttemperature+gradient*time
    v=(kcat(A,Ea,temperature)*enzymeconc*conc)/(km+conc)
    return v*extinctioncoefficient
    #return v*timespace
def intMM(*args):
    time=args[0][1]
    conc=args[0][0]
    return quad(MM,0,time,args=(conc,))[0]
vintMM=np.frompyfunc(intMM,2,1)
f = lambda x: x*((vmax*conc)/(km+conc))
print(kcat(A,Ea,temperature))

ys=[]
concentrations=np.array([20e-4/2**x for x in range(0,6)])
print(concentrations)
timerange=np.arange(0,300)
#kineticarray=np.column_stack((concentrations,timerange))
kineticarray= np.concatenate([np.column_stack((np.full(len(timerange),conc),timerange)) for conc in concentrations])

resultater=np.hstack((kineticarray,np.row_stack(np.apply_along_axis(intMM,1,kineticarray))))

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
X=resultater[:,0]
Y=resultater[:,1]
Z=resultater[:,2]
ax.scatter(resultater[:,0],resultater[:,1],resultater[:,2])
#from matplotlib import cm

#surf = ax.plot_surface(X, Y, Z, cmap=cm.coolwarm,
#                       linewidth=0, antialiased=False)
plt.show()

temperatures=-273.15+starttemperature+gradient*Y
timeinmin=Y/60
timeinmin
cuvette=np.array([concentrations.tolist().index(x)+1 for x in X])
simulatedoutput=np.stack([cuvette,timeinmin,temperatures,Z],axis=1)
print(simulatedoutput.shape)
np.savetxt("simulatedoutput.csv", simulatedoutput, delimiter=",",fmt=("%d","%3f","%3f","%3f"))

