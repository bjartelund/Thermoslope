#!/usr/bin/env python3
import thermoslope
import os
import json
from nbformat import v4 as nbf
import nbformat

nb =nbf.new_notebook()
nbcells= []
def analyze(analysisuuid):
    if analysisuuid:
        nbcells.append(nbf.new_markdown_cell(analysisuuid))
        uploaddir = os.path.join("user-contrib/", analysisuuid)
        if os.path.exists(uploaddir):
            datafiles = [x for x in os.listdir(
                uploaddir) if "png" not in x and "json" not in x]
            fullpathdatafiles = [os.path.join(
                "user-contrib", analysisuuid, datafile) for datafile in datafiles]
            settings = json.load(open(os.path.join(uploaddir,"settings.json")))
            nbcells.append(nbf.new_code_cell("import requests"))
            nbcells.append(nbf.new_code_cell("import imp"))
            nbcells.append(nbf.new_code_cell("import os"))
            nbcells.append(nbf.new_code_cell("modulesource=requests.get('https://raw.githubusercontent.com/bjartelund/Thermoslope/ab70e0747e80d3483263988b203f5056496ccb5e/thermoslope.py').content"))
            nbcells.append(nbf.new_code_cell("value=compile(modulesource,'thermoslope','exec')"))
            nbcells.append(nbf.new_code_cell("module = imp.new_module('thermoslope')"))
            nbcells.append(nbf.new_code_cell("exec (value, module.__dict__)"))
            nbcells.append(nbf.new_code_cell("thermoslope=module"))
            
            nbcells.append(nbf.new_code_cell("import json"))
            nbcells.append(nbf.new_code_cell("analysisuuid='%s'" % analysisuuid))
            nbcells.append(nbf.new_code_cell("uploaddir = os.path.join('user-contrib/', analysisuuid)"))
            nbcells.append(nbf.new_code_cell("settings = json.load(open(os.path.join(uploaddir,'settings.json')))"))

            nbcells.append(nbf.new_code_cell("datafiles = [x for x in os.listdir(uploaddir) if 'png' not in x and 'json' not in x]"))
            nbcells.append(nbf.new_code_cell("fullpathdatafiles = [os.path.join('user-contrib', analysisuuid, datafile) for datafile in datafiles]"))
            nbcells.append(nbf.new_code_cell("analysis = thermoslope.ThermoSlope(fullpathdatafiles, **settings)"))
            #nbcells.append(nbf.new_code_cell("""\
            #        %pylab inline
            #        print(**settings);"""))
            
            nbcells.append(nbf.new_code_cell("analysis.process()"))
            analysis = thermoslope.ThermoSlope(fullpathdatafiles, **settings)
            analysis.process()
            return analysis
result=analyze("a0ef33f01b1247a9a73603b2314df3c6")
print(result)
print(dir(result))
nb["cells"]=nbcells
nbformat.write(nb, 'test.ipynb')

