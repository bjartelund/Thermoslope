#!/usr/bin/env python3
import pandas as pd
import sys
datafile1 = sys.argv[1]
datafile2 = sys.argv[2]
df1 = pd.read_csv(datafile1)
df2 = pd.read_csv(datafile2)
df1.iloc[:, -1] = (df1.iloc[:, -1]+df2.iloc[:, -1])/2
df1.to_csv("averaged.csv", index=False)
