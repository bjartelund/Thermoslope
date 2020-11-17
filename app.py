import os
import uuid
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
ALLOWED_EXTENSIONS = {'txt', 'csv', 'tsv', 'dat'}

app = Flask(__name__,template_folder="static")
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
        returnvalue=""
        fileuploaduuid=uuid.uuid1().hex #random directory name for each seassion, should not collide
        os.mkdir(os.path.join("user-contrib/",fileuploaduuid))
        for file in request.files.getlist('file'):
        # if user does not select file, browser also
        # submit an empty part without filename
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                
                filename=uuid.uuid1().hex #random filename as well
                file.save(os.path.join("user-contrib/", fileuploaduuid,filename))
                returnvalue += filename
        return returnvalue
    else:
        return render_template('submit.html')

@app.route("/analyze", methods=["GET"])
def analyze():
    analysisuuid=request.args.get('uuid','')
    if analysisuuid == '':
        flash("No uuid")
        return render_template("submit.html")
    else:
        return analysisuuid
