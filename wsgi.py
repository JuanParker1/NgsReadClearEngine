#!/usr/bin/env python3

import sys
import site

site.addsitedir('/data/www/flask/fltr_backend/venv/lib/python3.6/site-packages')
site.addsitedir('/data/www/flask/fltr_backend/venv/lib/python3.6/site-packages/flask')
sys.path.insert(0, '/data/www/flask/fltr_backend')


from app import app as application
