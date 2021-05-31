#!/usr/bin/env python3
__author__ = "Bjarte Aarmo Lund"
import os
from io import BytesIO,StringIO

import json
import uuid
from flask import Flask, flash, request, redirect, url_for, render_template, send_from_directory, send_file
from nbformat import v4 as nbf
import nbformat
import thermoslope
ALLOWED_EXTENSIONS = {'txt', 'csv', 'tsv', 'dat'}

app = Flask(__name__, template_folder="static")
app.secret_key = uuid.uuid4().bytes

try:
    os.mkdir("user-contrib")
except FileExistsError:
    pass


@app.route('/')
def about():
    return render_template("about.html")


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        # random directory name for each seassion, should not collide
        fileuploaduuid = uuid.uuid4().hex
        fileuploaddir = os.path.join("user-contrib/", fileuploaduuid)
        os.mkdir(fileuploaddir)
        settingsfile = os.path.join(fileuploaddir, "settings.json")
        with open(settingsfile, "w") as f:
            json.dump(request.form, f)

        for analysisfile in request.files.getlist('file'):
            # if user does not select file, browser also
            # submit an empty part without filename
            if analysisfile and allowed_file(analysisfile.filename):

                filename = uuid.uuid4().hex  # random filename as well
                fullfilename = os.path.join(
                    "user-contrib/", fileuploaduuid, filename)
                analysisfile.save(fullfilename)
            else:
                flash('No selected file or filetype not allowed')
                return redirect(request.url)

        return redirect(url_for("analyze", uuid=fileuploaduuid))

    else:
        return render_template('submit.html')


@app.route("/analyze", methods=["GET"])
def analyze():
    analysisuuid = request.args.get('uuid', '')
    if analysisuuid == '':
        flash("No uuid")
        return redirect(url_for("upload_file"))
    else:
        uploaddir = os.path.join("user-contrib/", analysisuuid)
        if os.path.exists(uploaddir):
            datafiles = [x for x in os.listdir(
                uploaddir) if "png" not in x and "json" not in x]
            fullpathdatafiles = [os.path.join(
                "user-contrib", analysisuuid, datafile) for datafile in datafiles]
            settings = json.load(open(os.path.join(uploaddir,"settings.json")))
            analysis = thermoslope.ThermoSlope(fullpathdatafiles, **settings)
            analysis.process()
            return render_template("analyze.html", uuid=analysisuuid, results=analysis)
        else:
            flash("Not found")
            return analysisuuid

@app.route("/exportipynb", methods=["GET"])
def exportipynb():
    nb =nbf.new_notebook()
    nbcells= []
    analysisuuid = request.args.get('uuid', '')
    if analysisuuid == '':
        flash("No uuid")
        return redirect(url_for("upload_file"))
    else:
        nb =nbf.new_notebook()
        nbcells= []
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
            nbcells.append(nbf.new_code_cell("modulesource=requests.get('https://raw.githubusercontent.com/bjartelund/Thermoslope/master/thermoslope.py').content"))
            nbcells.append(nbf.new_code_cell("value=compile(modulesource,'thermoslope','exec')"))
            nbcells.append(nbf.new_code_cell("module = imp.new_module('thermoslope')"))
            nbcells.append(nbf.new_code_cell("exec (value, module.__dict__)"))
            nbcells.append(nbf.new_code_cell("thermoslope=module"))
            
            nbcells.append(nbf.new_code_cell("from tempfile import NamedTemporaryFile"))
            nbcells.append(nbf.new_code_cell("datafiles = []"))
            for datafile in fullpathdatafiles:
                with open(datafile) as reader:
                    nbcells.append(nbf.new_code_cell("f = NamedTemporaryFile(mode='w+', delete=False)"))

                    nbcells.append(nbf.new_code_cell('f.write("""%s""")' % reader.read()))
                    nbcells.append(nbf.new_code_cell("f.close()"))
                    nbcells.append(nbf.new_code_cell("datafiles.append(f.name)"))
            nbcells.append(nbf.new_code_cell("analysisuuid='%s'" % analysisuuid))
            nbcells.append(nbf.new_code_cell("settings = %s" % settings))

            nbcells.append(nbf.new_code_cell("analysis = thermoslope.ThermoSlope(datafiles, **settings)"))
            
            nbcells.append(nbf.new_code_cell("analysis.process()"))
            nbcells.append(nbf.new_code_cell("[os.unlink(tmpfile) for tmpfile in datafiles]"))
            nb["cells"]=nbcells
            virtualfile = StringIO()
            nbformat.write(nb, virtualfile)
            virtualfile.seek(0)
            virtualfilebytes=BytesIO(virtualfile.read().encode("utf-8"))
            return send_file(virtualfilebytes,as_attachment=True,attachment_filename='thermoslope-analysis.ipynb',mimetype='application/x-ipynb+json')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


