import os
import sys
import json
import argparse
import datetime
from functools import wraps
import scrypt
from flask import Flask, request, session, url_for, redirect, render_template
from dunetoolkit import search_by_id, convert_date_to_str
from frontend_helpers import _get_user, do_q_append, parse_update, perform_search, perform_insert, perform_update
from pymongo import MongoClient

app = Flask(__name__)

config_name = os.getenv('DUNE_API_CONFIG_NAME')
if config_name is None:
    config_name = 'app_config.txt'
config_dict = None

with open(config_name, 'r') as config:
    config_dict = json.load(config)
app.config['SECRET_KEY'] = config_dict['secret_key']
salt = config_dict['salt']
database_name = config_dict['database']
db_obj = MongoClient('localhost', 27017)[database_name]

app.permanent_session_lifetime = datetime.timedelta(hours=24)
USER_MODES = ['DUNEreader', 'DUNEwriter']


'''
 define custom decorator
 used: https://blog.tecladocode.com/learn-python-defining-user-access-roles-in-flask/
'''
def requires_permissions(permissions_levels):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_mode = session.get('user_mode')
            if user_mode is None:
                return redirect(url_for('login'))

            for permissions_level in permissions_levels:
                if user_mode == permissions_level:
                    return f(*args, **kwargs)
            return redirect(url_for('restricted_page'))
        return decorated_function
    return decorator

@app.route('/', methods=['GET', 'POST'])
@requires_permissions(['DUNEreader', 'DUNEwriter', 'Admin'])
def reference_endpoint():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
@requires_permissions(['Admin'])
def register():
    from frontend_helpers import _add_user
    if request.method == 'POST':
        user = request.form.get('user')
        user_obj = _get_user(user, database_name)
        if user_obj is not None:
            return render_template('register.html', msg='Your email already exists in the database.')

        password = request.form.get('password')
        encrypted_pw = scrypt.hash(password, salt, N=16) #password, salt, N=(num_iterations), r=(block_size), p=(num_threads), bufflen=(num_output_bytes)

        insert_resp = _add_user(user, encrypted_pw, database_name)
        return redirect(url_for('login'))

    else:
        return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('user')
        plaintext_password = request.form.get('password')

        user_obj = _get_user(user, database_name)
        if user_obj is None:
            return render_template('login.html', msg='User was not found in the database')
        else:
            user_db_pw_hash = user_obj['password_hashed']
            is_correct_pw = (scrypt.hash(plaintext_password, salt, N=16) == user_db_pw_hash)

            if is_correct_pw:
                session['permanent'] = True
                session['user_mode'] = user_obj['user_mode']
                return redirect(url_for('reference_endpoint'))
            else:
                return render_template('login.html', msg="incorrect password")
    else:
        return render_template('login.html')

@app.route('/logout', methods=['GET'])
@requires_permissions(['DUNEreader', 'DUNEwriter', 'Admin'])
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/restricted_page')
def restricted_page():
    return render_template('restricted_page.html')

@app.route('/search', methods=['GET','POST'])
@requires_permissions(['DUNEreader', 'DUNEwriter', 'Admin'])
def search_endpoint():
    final_q_lines_list = []
    append_mode = ''
    results = []
    results_str = []

    if request.form.get("append_button") == "do_and":
        q_dict, q_str, num_q_lines, error_msg = do_q_append(request.form)
        append_mode = "AND"

    elif request.form.get("append_button") == "do_or":
        q_dict, q_str, num_q_lines, error_msg = do_q_append(request.form)
        append_mode = "OR"
 
    elif request.method == "POST":
        final_q, final_q_str, num_q_lines, error_msg = do_q_append(request.form)

        results, error_msg = perform_search(final_q, db_obj)
        
        final_q_lines_list = []
        if final_q_str != '':
            final_q_lines_list = final_q_str.split('\n')
        
        results_str = [ str(r) for r in results ]
        q_dict = {}
        q_str = ''
        num_q_lines = 0

    else:
        q_dict = {}
        q_str = ''
        num_q_lines = 0
        error_msg = ''

    return render_template('search.html', existing_query=q_str, append_mode=append_mode, error_msg=error_msg, num_q_lines=num_q_lines, final_q=final_q_lines_list, results_str=results_str, results_dict=results)

@app.route('/insert', methods=['GET','POST'])
@requires_permissions(['DUNEwriter', 'Admin'])
def insert_endpoint():
    if request.method == "POST":
        new_doc_id, error_msg = perform_insert(request.form, db_obj)
        new_doc_msg = 'new doc id: '+str(new_doc_id)
        if new_doc_id is None:
            new_doc_msg = "ERROR: record not inserted because "+error_msg
    else:
        new_doc_msg = ""
    return render_template('insert.html', new_doc_msg=new_doc_msg)

@app.route('/update', methods=['GET','POST'])
@requires_permissions(['DUNEwriter', 'Admin'])
def update_endpoint():
    if request.method == "GET":
        return render_template('update.html', doc_data=False, message="")

    elif request.form.get("submit_button") == "find_doc":
        doc_id = request.form.get('doc_id', '')
        doc = search_by_id(doc_id, db_obj)

        if doc is None:
            return render_template('update.html', doc_data=False, message="No document was found with the ID you provided.")
        
        for i in range(len(doc['measurement']['results'])):
            num_vals = len(doc['measurement']['results'][i]['value'])
            if num_vals == 0:
                doc['measurement']['results'][i]['value'] = []
            if num_vals < 2:
                doc['measurement']['results'][i]['value'].append('')
            if num_vals < 3:
                doc['measurement']['results'][i]['value'].append('')

        return render_template('update.html', doc_data=True, doc_id=doc['_id'], \
                grouping=doc['grouping'], \
                sample_name=doc['sample']['name'], \
                sample_description=doc['sample']['description'], \
                sample_source=doc['sample']['source'], \
                sample_id=doc['sample']['id'], \
                sample_owner_name=doc['sample']['owner']['name'], \
                sample_owner_contact=doc['sample']['owner']['contact'], \
                data_reference=doc['data_source']['reference'], \
                data_input_name=doc['data_source']['input']['name'], \
                data_input_contact=doc['data_source']['input']['contact'], \
                data_input_date=' '.join([convert_date_to_str(date_ele) for date_ele in doc['data_source']['input']['date']]), \
                data_input_notes=doc['data_source']['input']['notes'], \
                measurement_practitioner_name=doc['measurement']['practitioner']['name'], \
                measurement_practitioner_contact=doc['measurement']['practitioner']['contact'], \
                measurement_technique=doc['measurement']['technique'], \
                measurement_institution=doc['measurement']['institution'], \
                measurement_date=' '.join([convert_date_to_str(date_ele) for date_ele in doc['measurement']['date']]), \
                measurement_description=doc['measurement']['description'], \
                measurement_requestor_name=doc['measurement']['requestor']['name'], \
                measurement_requestor_contact=doc['measurement']['requestor']['contact'], \
                measurement_results=doc['measurement']['results']
            ) 

    elif request.form.get("submit_button") == "update_doc":
        doc_id, remove_doc, update_pairs, meas_remove_indices, meas_add_eles = parse_update(request.form)
        new_doc_id, error_msg = perform_update(doc_id, remove_doc, update_pairs, meas_remove_indices, meas_add_eles, db_obj)
        if new_doc_id != None:
            message = "update success. New doc version ID: "+str(new_doc_id)
        else:
            message = 'Error: '+error_msg
        return render_template('update.html', doc_data=False, message=message)
    return None

# asasys
# assays_old_versions


