from enum import Enum
from datetime import datetime
import logging
import os


logging_file_name = os.path.join('/data/www/flask/fltr_backend/logs/', datetime.now().strftime('%Y_%m_%d.log'))
logging.basicConfig(filename = logging_file_name, level=logging.WARNING, format='%(asctime)s[%(levelname)s][%(filename)s][%(funcName)s]: %(message)s')
logger = logging.getLogger('main')
LOGGER_LEVEL_JOB_MANAGE_THREAD_SAFE = logging.DEBUG
LOGGER_LEVEL_JOB_MANAGE_API = logging.DEBUG


class State(Enum):
    Running = 1
    Finished = 2
    Crashed = 3
    Waiting = 4
    Init = 5


def send_email(smtp_server, sender, receiver, subject='', content=''):
    from email.mime.text import MIMEText
    from smtplib import SMTP
    msg = MIMEText(content)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver
    s = SMTP(smtp_server)
    s.send_message(msg)
    s.quit()
