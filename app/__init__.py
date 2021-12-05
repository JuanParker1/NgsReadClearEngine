from flask import Flask, flash, request, redirect, url_for, render_template, Response, jsonify, send_file
from werkzeug.utils import secure_filename
from Job_Manager_API import Job_Manager_API
from SharedConsts import UI_CONSTS
from utils import State, logger
import os
import warnings
import time


#TODO think about it
warnings.filterwarnings("ignore")

UPLOAD_FOLDERS_ROOT_PATH = '/bioseq/data/results/genome_fltr/'
USER_FILE_NAME = 'reads.fasta'
ALLOWED_EXTENSIONS = {'fasta', 'fastqc', 'png', 'jpg', 'jpeg', 'gif', 'pdf'}
MAX_NUMBER_PROCESS = 3
TIME_OF_STREAMING_UPDATE_REQUEST_BEFORE_DELETING_IT_SEC = 1200


app = Flask(__name__)
app.config['SECRET_KEY'] = '168b36af-0822-4393-92c2-3e8592a48d2c'
app.config['UPLOAD_FOLDERS_ROOT_PATH'] = UPLOAD_FOLDERS_ROOT_PATH # path to folder
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000 # MAX file size to upload
process_id2update = []

def update_html(process_id, state):
    logger.info(f'process_id = {process_id} state = {state}')
    if process_id:
        process_id2update.append(process_id)

@app.route('/remove_update/<process_id>')
def remove_update(process_id):
    logger.info(f'process_id = {process_id}')
    if process_id in process_id2update:
        logger.info(f'removing {process_id} from process_id2update')
        process_id2update.remove(process_id)
    return jsonify('data')

@app.route('/stream/')
def stream():
    # function to stream data to client
    requests_time_dict = {}
    TIME_BETWEEN_BROADCASTING_EVENTS = 0.1
    
    def eventStream():
        while True:
            if len(process_id2update):
                for process_id in process_id2update:
                    yield 'data: {}\n\n'.format(process_id)
                    time.sleep(TIME_BETWEEN_BROADCASTING_EVENTS)
                    time_broadcasting_process_event = requests_time_dict.get(process_id, 0)
                    time_broadcasting_process_event += TIME_BETWEEN_BROADCASTING_EVENTS
                    requests_time_dict[process_id] = time_broadcasting_process_event

                max_broadcasting_event = max(requests_time_dict, key=requests_time_dict.get)
                if requests_time_dict[max_broadcasting_event] >= TIME_OF_STREAMING_UPDATE_REQUEST_BEFORE_DELETING_IT_SEC:
                    logger.info(f'removing max_broadcasting_event = {process_id} as it reached the max amount of time broadcasting')
                    requests_time_dict.pop(max_broadcasting_event)
            else:
                requests_time_dict.clear()
                time.sleep(1)
    return Response(eventStream(), mimetype="text/event-stream")

manager = Job_Manager_API(MAX_NUMBER_PROCESS, UPLOAD_FOLDERS_ROOT_PATH, USER_FILE_NAME, update_html)


def allowed_file(filename):
    logger.debug(f'filename = {filename}')
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/process_state/<process_id>')
def process_state(process_id):
    job_state = manager.get_job_state(process_id)
    if job_state != State.Finished:
        return render_template('file_download.html', process_id=process_id, state=job_state, gif=UI_CONSTS.states_gifs_dict[job_state])
    else:
        return redirect(url_for('results', process_id=process_id))

@app.route('/admin/running')
def running_processes():
    return render_template('runnning_processes.html', processes_ids=manager.get_running_process())

@app.route('/admin/waiting')
def waiting_processes():
    return render_template('waiting_processes.html', processes_ids=manager.get_waiting_process())
    
@app.route('/results/<process_id>')
def results(process_id):
    df = manager.get_UI_matrix(process_id)
    if isinstance(df, str):
        logger.error(f'process_id = {process_id}, df = {df}')
        return render_template('file_download.html', process_id=process_id, state=State.Crashed, gif=UI_CONSTS.states_gifs_dict[State.Crashed])
    logger.info(f'process_id = {process_id}, df_path = {df}')
    return render_template('results.html', data=df.to_json())

@app.route('/export/<process_id>', methods=['POST'])
def export(process_id):
    request_json = request.json
    #TODO extract k_threshold and species_list
    species_list, k_threshold = None, None
    file2send = manager.export_file(process_id, species_list, k_threshold)
    return send_file(file2send)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            logger.info(f'file uploaded = {file}')
            filename = secure_filename(file.filename)
            new_process_id = manager.get_new_process_id()
            folder2save_file = os.path.join(app.config['UPLOAD_FOLDERS_ROOT_PATH'], new_process_id)
            os.mkdir(folder2save_file)
            file.save(os.path.join(folder2save_file, USER_FILE_NAME))
            logger.info(f'file saved = {file}')
            man_results = manager.add_process(new_process_id)
            logger.info(f'process added man_results = {man_results}, redirecting url')
            return redirect(url_for('process_state', process_id=new_process_id))
        else:
            logger.info(f'file extention not allowed')
    return render_template('home.html')