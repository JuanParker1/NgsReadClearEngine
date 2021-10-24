from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
from Job_Manager_API import Job_Manager_API
import os

UPLOAD_FOLDERS_ROOT_PATH = '/data/www/cgi-bin/fltr_backend/data/'
USER_FILE_NAME = 'reads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
MAX_NUMBER_PROCESS = 3


app = Flask(__name__)
app.config['UPLOAD_FOLDERS_ROOT_PATH'] = UPLOAD_FOLDERS_ROOT_PATH # path to folder
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000 # MAX file size to upload
manager = Job_Manager_API(MAX_NUMBER_PROCESS, UPLOAD_FOLDERS_ROOT_PATH)

#@app.route("/")
#def hello():
#    return "Hello world!"

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/process_state/<process_id>')
def process_state(process_id):
    manager.add_process(process_id)
    return render_template('file_download.html', process_id=process_id)

@app.route('/admin/running_process')
def running_processes():
    return render_template('runnning_processes.html', processes_ids=manager.get_running_process())

@app.route('/admin/waiting_processes')
def waiting_processes():
    return render_template('waiting_processes.html', processes_ids=manager.get_waiting_process())

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            new_process_id = manager.get_new_process_id()
            folder2save_file = os.path.join(app.config['UPLOAD_FOLDERS_ROOT_PATH'], new_process_id)
            os.mkdir(folder2save_file)
            # TODO change file name
            file.save(os.path.join(folder2save_file, filename))
            return redirect(url_for('process_state', process_id=new_process_id))
    return render_template('home.html')