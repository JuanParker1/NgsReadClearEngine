from flask import Flask, flash, request, redirect, url_for, render_template, Response, jsonify, send_file
from werkzeug.utils import secure_filename
from SharedConsts import UI_CONSTS
from KrakenHandlers.KrakenConsts import KRAKEN_DB_NAMES, KRAKEN_MAX_CUSTOM_SPECIES
from utils import State
import pandas as pd
import os
import json
import warnings
import time


#TODO think about it
warnings.filterwarnings("ignore")

UPLOAD_FOLDERS_ROOT_PATH = '/bioseq/data/results/genome_fltr/'
USER_FILE_NAME = 'reads.fasta'
MAX_NUMBER_PROCESS = 3
TIME_OF_STREAMING_UPDATE_REQUEST_BEFORE_DELETING_IT_SEC = 1200


app = Flask(__name__)
app.config['SECRET_KEY'] = '168b36af-0822-4393-92c2-3e8592a48d2c'
app.config['UPLOAD_FOLDERS_ROOT_PATH'] = UPLOAD_FOLDERS_ROOT_PATH # path to folder
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000 * 1000 # MAX file size to upload
process_id2update = []

def update_html(process_id, state):
    if process_id:
        process_id2update.append(process_id)

@app.route('/remove_update/<process_id>')
def remove_update(process_id):
    if process_id in process_id2update:
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
                    requests_time_dict.pop(max_broadcasting_event)
            else:
                requests_time_dict.clear()
                time.sleep(1)
    return Response(eventStream(), mimetype="text/event-stream")



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in UI_CONSTS.ALLOWED_EXTENSIONS

@app.route('/process_state/<process_id>')
def process_state(process_id):
    job_state = 0
    if job_state == None:
        return redirect(url_for('error', error_type=UI_CONSTS.UI_Errors.UNKNOWN_PROCESS_ID.name))
    if job_state != State.Finished:
        kwargs = {
            "process_id": process_id,
            "text": UI_CONSTS.states_text_dict[State.Running],
            "message_to_user": UI_CONSTS.PROCESS_INFO_KR,
            "gif": UI_CONSTS.states_gifs_dict[State.Running],
        }
        return render_template('process_running.html', **kwargs)
    else:
        return redirect(url_for('results', process_id=process_id))

@app.route('/download_file/<process_id>', methods=['GET', 'POST'])
def download_file(process_id):
    if request.method == 'POST':
        file2send = None#manager.export_file(process_id)
        if file2send == None:
            return redirect(url_for('error', error_type=UI_CONSTS.UI_Errors.EXPORT_FILE_UNAVAILABLE.name))
        return send_file(file2send, mimetype='application/octet-stream')
    return render_template('export_file.html')

@app.route('/post_process_state/<process_id>')
def post_process_state(process_id):
    job_state = 0
    if job_state == None:
        return redirect(url_for('error', error_type=UI_CONSTS.UI_Errors.UNKNOWN_PROCESS_ID.name))
    if job_state != State.Finished:
        kwargs = {
            "process_id": process_id,
            "text": UI_CONSTS.states_text_dict[job_state],
            "message_to_user": UI_CONSTS.PROCESS_INFO_PP,
            "gif": UI_CONSTS.states_gifs_dict[job_state],
        }
        return render_template('process_running.html', **kwargs)
    else:
        return redirect(url_for('download_file', process_id=process_id))

@app.route('/results/<process_id>', methods=['GET', 'POST'])
def results(process_id):
    # export
    if request.method == 'POST':
        data = request.form
        try:
            species_list, k_threshold = data['species_list'].split(','), float(data['k_mer_threshold'])
        except Exception as e:
            #TODO what about the df??
            return redirect(url_for('error', error_type=UI_CONSTS.UI_Errors.INVALID_EXPORT_PARAMS.name))
        return redirect(url_for('post_process_state', process_id=process_id))
    # results
    df, summary_json = pd.read_csv("file:///home/elyawy/Development/Msc/projects/temp/CounterMatrixForUI.csv"), json.load(open("/home/elyawy/Development/Msc/projects/temp/summary_stat_UI.json"))
    if df is None:
        return render_template('file_download.html', process_id=process_id, text=UI_CONSTS.states_text_dict[State.Crashed], gif=UI_CONSTS.states_gifs_dict[State.Crashed], summary_stats=summary_json)
    return render_template('results.html', data=df.to_json(), summary_stats=summary_json)


@app.route('/error/<error_type>')
def error(error_type):
    # checking if error_type exists in error enum
    try:
        return render_template('error_page.html', error_text=UI_CONSTS.UI_Errors[error_type].value)
    except:
        return render_template('error_page.html', error_text=f'Unknown error, \"{error_type}\" is not a valid error code')

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        print(request.form)
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            return redirect(url_for('error', error_type=UI_CONSTS.UI_Errors.INVALID_FILE.name))
        if file and allowed_file(file.filename):
            email_address = request.form.get('email', None)
            if email_address == None:
                return redirect(url_for('error', error_type=UI_CONSTS.UI_Errors.INVALID_MAIL.name))
            filename = secure_filename(file.filename)
            new_process_id = "1"
            return redirect(url_for('process_state', process_id=new_process_id))
        else:
            return redirect(url_for('error', error_type=UI_CONSTS.UI_Errors.INVALID_FILE.name))
    return render_template('home.html', databases=KRAKEN_DB_NAMES, max_custom=KRAKEN_MAX_CUSTOM_SPECIES)

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('error', error_type=UI_CONSTS.UI_Errors.PAGE_NOT_FOUND.name))


@app.route("/about")
def about():
    return render_template('about.html')