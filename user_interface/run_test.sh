#!/bin/bash

export DUNE_API_CONFIG_NAME="app_config_test.json"
gunicorn --workers 4 --bind 127.0.0.1:5000 wsgi
