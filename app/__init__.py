from flask import Flask, flash, request, redirect, url_for, render_template, Response, jsonify, send_file
from werkzeug.utils import secure_filename
from Job_Manager_API import Job_Manager_API
from SharedConsts import UI_CONSTS, CUSTOM_DB_NAME, State
from KrakenHandlers.KrakenConsts import KRAKEN_DB_NAMES
from utils import logger
import os
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
app.config['PASSPHRASE_KILL'] = '?GL~bXZy7(xr)n@uJX5T4Tw6n/\s6'
app.config['PASSPHRASE_CLEAN'] = '4?eB!ay9Ah#rqqU$f+K!tQvLtFU2sf-D'

app.config['UPLOAD_FOLDERS_ROOT_PATH'] = UPLOAD_FOLDERS_ROOT_PATH # path to folder
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000 * 1000 # MAX file size to upload
process_id2update = []

def update_html(process_id, state):
    logger.info(f'process_id = {process_id} state = {state}')
    if process_id:
        process_id2update.append(process_id)


@app.route("/process_page_update/<process_id>")
def update_process_page(process_id):
    if process_id in process_id2update:
        process_id2update.remove(process_id)
        return UI_CONSTS.TEXT_TO_RELOAD_HTML
    return ""


manager = Job_Manager_API(MAX_NUMBER_PROCESS, UPLOAD_FOLDERS_ROOT_PATH, USER_FILE_NAME, update_html)


def allowed_file(filename):
    logger.debug(f'filename = {filename}')
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in UI_CONSTS.ALLOWED_EXTENSIONS

@app.route('/process_state/<process_id>')
def process_state(process_id):
    job_state_kraken = manager.get_kraken_job_state(process_id)
    job_state_download = manager.get_download_job_state(process_id)
    if job_state_kraken == None and job_state_download == None:
        return redirect(url_for('error', error_type=UI_CONSTS.UI_Errors.UNKNOWN_PROCESS_ID.name))
    if job_state_kraken == State.Crashed or job_state_download == State.Crashed:
        return redirect(url_for('error', error_type=UI_CONSTS.UI_Errors.JOB_CRASHED.name))
    if job_state_kraken != State.Finished:
        kwargs = {
            "process_id": process_id,
            "text": UI_CONSTS.states_text_dict[job_state_kraken] if job_state_kraken != None else UI_CONSTS.states_text_dict[job_state_download],
            "gif": UI_CONSTS.states_gifs_dict[job_state_kraken] if job_state_kraken != None else UI_CONSTS.states_gifs_dict[job_state_download],
            "message_to_user": UI_CONSTS.PROCESS_INFO_KR,
            "update_text": UI_CONSTS.TEXT_TO_RELOAD_HTML,
            "update_interval_sec": UI_CONSTS.FETCH_UPDATE_INTERVAL_HTML_SEC
        }
        return render_template('process_running.html', **kwargs)
    else:
        return redirect(url_for('results', process_id=process_id))

@app.route('/download_file/<process_id>', methods=['GET', 'POST'])
def download_file(process_id):
    file2send = manager.export_file(process_id)
    if file2send == None:
        logger.warning(f'failed to export file exporting, process_id = {process_id}, file2send = {file2send}')
        return redirect(url_for('error', error_type=UI_CONSTS.UI_Errors.EXPORT_FILE_UNAVAILABLE.name))
    if request.method == 'POST':
        logger.info(f'exporting, process_id = {process_id}, file2send = {file2send}')
        return send_file(file2send, mimetype='application/octet-stream')
    return render_template('export_file.html')

@app.route('/post_process_state/<process_id>')
def post_process_state(process_id):
    job_state = manager.get_postprocess_job_state(process_id)
    if job_state == None:
        return redirect(url_for('error', error_type=UI_CONSTS.UI_Errors.UNKNOWN_PROCESS_ID.name))
    if job_state == State.Crashed:
        return redirect(url_for('error', error_type=UI_CONSTS.UI_Errors.JOB_CRASHED.name))
    if job_state != State.Finished:
        kwargs = {
            "process_id": process_id,
            "text": UI_CONSTS.states_text_dict[job_state],
            "message_to_user": UI_CONSTS.PROCESS_INFO_PP,
            "gif": UI_CONSTS.states_gifs_dict[job_state],
            "update_text": UI_CONSTS.TEXT_TO_RELOAD_HTML,
            "update_interval_sec": UI_CONSTS.FETCH_UPDATE_INTERVAL_HTML_SEC
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
            logger.error(f'{e}')
            #TODO what about the df??
            return redirect(url_for('error', error_type=UI_CONSTS.UI_Errors.INVALID_EXPORT_PARAMS.name))
        logger.info(f'exporting, process_id = {process_id}, k_threshold = {k_threshold}, species_list = {species_list}')
        man_results = manager.add_postprocess(process_id, species_list, k_threshold)
        if man_results == None:
            #TODO what about the df??
            return redirect(url_for('error', error_type=UI_CONSTS.UI_Errors.POSTPROCESS_CRASH.name))
        logger.info(f'process_id = {process_id}, post_process added')
        return redirect(url_for('post_process_state', process_id=process_id))
    # results
    df, summary_json = manager.get_UI_matrix(process_id)
    if df is None:
        logger.error(f'process_id = {process_id}, df = {df}')
        return render_template('file_download.html', process_id=process_id, text=UI_CONSTS.states_text_dict[State.Crashed], gif=UI_CONSTS.states_gifs_dict[State.Crashed], summary_stats=summary_json)
    logger.info(f'process_id = {process_id}, df = {df}')
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
        logger.info(f'request.files = {request.files}')
        if 'file' not in request.files:
            return redirect(url_for('error', error_type=UI_CONSTS.UI_Errors.INVALID_FILE.name))
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        logger.info(f'request.form = {request.form}')
        if file.filename == '':
            return redirect(url_for('error', error_type=UI_CONSTS.UI_Errors.INVALID_FILE.name))
        if file and allowed_file(file.filename):
            email_address, db_type, species_list = manager.parse_form_inputs(request.form)
            if email_address == None:
                logger.warning(f'email_address not available')
                return redirect(url_for('error', error_type=UI_CONSTS.UI_Errors.INVALID_MAIL.name))
            if db_type == CUSTOM_DB_NAME:
                if not manager.valid_species_list(species_list):
                    return redirect(url_for('error', error_type=UI_CONSTS.UI_Errors.INVALID_SPECIES_LIST.name))
            logger.info(f'file uploaded = {file}, email_address = {email_address}')
            filename = secure_filename(file.filename)
            new_process_id = manager.get_new_process_id()
            folder2save_file = os.path.join(app.config['UPLOAD_FOLDERS_ROOT_PATH'], new_process_id)
            os.mkdir(folder2save_file)
            if not filename.endswith('gz'): #zipped file
                file.save(os.path.join(folder2save_file, USER_FILE_NAME))
            else:
                file.save(os.path.join(folder2save_file, USER_FILE_NAME + '.gz'))
            logger.info(f'file saved = {file}')
            man_results = manager.add_kraken_process(new_process_id, email_address, db_type, species_list)
            if not man_results:
                logger.warning(f'job_manager_api can\'t add process')
                return redirect(url_for('error', error_type=UI_CONSTS.UI_Errors.INVALID_FILE.name))
            logger.info(f'process added man_results = {man_results}, redirecting url')
            return redirect(url_for('process_state', process_id=new_process_id))
        else:
            logger.info(f'file extention not allowed')
            return redirect(url_for('error', error_type=UI_CONSTS.UI_Errors.INVALID_FILE.name))
    return render_template('home.html', 
            databases=KRAKEN_DB_NAMES, 
            max_custom=UI_CONSTS.KRAKEN_MAX_CUSTOM_SPECIES, 
            species_prefix=UI_CONSTS.SPECIES_FORM_PREFIX,
            extensions=",".join(UI_CONSTS.ALLOWED_EXTENSIONS))

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('error', error_type=UI_CONSTS.UI_Errors.PAGE_NOT_FOUND.name))


@app.route("/about")
def about():
    return render_template('about.html')



@app.route("/debug/killswitch", methods=['GET', 'POST'])
def killswitch():
    if request.method == 'POST':
        passphrase = request.form.get("passphrase")
        if passphrase == app.config['PASSPHRASE_KILL']:
            # should check which process group we are in.
            import signal, os
            os.kill(os.getpid(), signal.SIGINT)
        if passphrase == app.config['PASSPHRASE_CLEAN']:
            manager.clean_internal_state()
    return render_template('debug.html')





