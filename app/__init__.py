from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
from Job_Manager_API import Job_Manager_API
import os
import warnings


#TODO think about it
warnings.filterwarnings("ignore")

UPLOAD_FOLDERS_ROOT_PATH = '/bioseq/data/results/genome_fltr/'
USER_FILE_NAME = 'reads.fasta'
ALLOWED_EXTENSIONS = {'fasta', 'fastqc', 'png', 'jpg', 'jpeg', 'gif', 'pdf'}
MAX_NUMBER_PROCESS = 3


app = Flask(__name__)
app.config['SECRET_KEY'] = '168b36af-0822-4393-92c2-3e8592a48d2c'
app.config['UPLOAD_FOLDERS_ROOT_PATH'] = UPLOAD_FOLDERS_ROOT_PATH # path to folder
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000 # MAX file size to upload
manager = Job_Manager_API(MAX_NUMBER_PROCESS, UPLOAD_FOLDERS_ROOT_PATH, USER_FILE_NAME)

#@app.route("/")
#def hello():
#    return "Hello world!"

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/process_state/<process_id>')
def process_state(process_id):
    man_results = manager.add_process(process_id)
    if man_results:
        message = 'File uploaded successfully!'
    else:
        message = 'Verify file is of type fasta or fastqc'
    #print('__init__', 'process_state()', f'process_id = {process_id} message = {message}')
    job_state = manager.get_job_state(process_id)
    #print('__init__', 'process_state()', f'process_id = {process_id} message = {message} job_state = {job_state}')
    return render_template('file_download.html', process_id=process_id, message=message, state=job_state)

@app.route('/admin/running')
def running_processes():
    return render_template('runnning_processes.html', processes_ids=manager.get_running_process())

@app.route('/admin/waiting')
def waiting_processes():
    return render_template('waiting_processes.html', processes_ids=manager.get_waiting_process())

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        #print('__init__', 'upload_file()', f'request.files = {request.files}')
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
            file.save(os.path.join(folder2save_file, USER_FILE_NAME))
            return redirect(url_for('process_state', process_id=new_process_id))
        else:
            # TODO handle not allowed file extention
            print('__init__', 'upload_file()', 'file extention not allowed')
    return render_template('home.html')