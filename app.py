import os
import json
import uuid
from flask import Flask, flash, request, redirect, url_for, render_template, send_from_directory
import thermoslope
ALLOWED_EXTENSIONS = {'txt', 'csv', 'tsv', 'dat'}

app = Flask(__name__, template_folder="static")
app.secret_key = uuid.uuid4().bytes

try:
    os.mkdir("user-contrib")
except FileExistsError:
    pass


@app.route('/')
def hello():
    return 'Hello, World!'


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
            analysis = thermoslope.ThermoSlope(fullpathdatafiles)
            analysis.process()
            return render_template("analyze.html", uuid=analysisuuid, results=analysis)
        return analysisuuid


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/user-contrib/<path:filepath>')
def data(filepath):
    return send_from_directory('user-contrib', filepath)
