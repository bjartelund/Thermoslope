#!/usr/bin/env python3
__author__ = "Bjarte Aarmo Lund"
def MichaelisMenten(x,Km,Vmax):
    return (Vmax*x)/(Km+x)

Vmax=1
Km=1
x=4.5
print(MichaelisMenten(x,Km,Vmax))
