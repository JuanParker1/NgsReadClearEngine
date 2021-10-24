#!/usr/bin/env python3


import sys
import site

site.addsitedir('/var/www/cgi-bin/fltr_backend/venv/lib/python3.6/site-packages')
site.addsitedir('/var/www/cgi-bin/fltr_backend/venv/lib/python3.6/site-packages/flask')
sys.path.insert(0, '/var/www/cgi-bin/fltr_backend')

from app import app as application
