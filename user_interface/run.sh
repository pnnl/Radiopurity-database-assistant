#!/bin/bash

export DUNE_API_CONFIG_NAME="app_config.json"  
gunicorn --workers 4 --bind 0.0.0.0:5000 wsgi
