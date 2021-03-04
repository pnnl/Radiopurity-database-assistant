"""
.. module:: radiopurity_api
   :synopsis: The access point for the user interface or API users to access the radiopurity functionality.

.. moduleauthor:: Elise Saxon
"""

import os
import sys
import json
import argparse
import datetime
from functools import wraps
import scrypt
from flask import Flask, request, session, url_for, redirect, render_template
from dunetoolkit import search_by_id, convert_date_to_str
from frontend_helpers import _add_user, _get_user, do_q_append, parse_update, perform_search, perform_insert, perform_update
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
db_obj = MongoClient(config_dict['mongodb_host'], config_dict['mongodb_port'])[config_dict['database']]

app.permanent_session_lifetime = datetime.timedelta(hours=24)
USER_MODES = ['DUNEwriter']


def requires_permissions(permissions_levels):
    """This defines a custom decorator for other endpoints which specifies which users can access a given endpoint. This decorator checks if the user that is currently logged in has permissions in the group of permissions_levels that are permitted to access the given endpoint. If permission is granted, the user is taken to the requested endpoint. Otherise, they are taken to the "login" page if the user mode was None, or to the "restricted" page if their user mode does not have access.

    args:
        * permissions_levels (list of str): The user modes (user names) that are allowed to access this endpoint
    """
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
def reference_endpoint():
    return render_template('simple_search.html')
    """This is the landing page for the API if no endpoint is specified. It redirects to the search endpoint.
    """

@app.route('/register', methods=['GET', 'POST'])
@requires_permissions(['Admin'])
def register():
    """This is the endpoint to add a new user to the database. Only administrators of the API can access it. At this point, it should only be used for development purposes, since the only users necessary for the API are DUNEreader, DUNEwriter, and Admin.

    GET request:
        Render the request page.
    POST request:
        Perform user creation by adding the new username and password to the database.
        form data:
            * user (str): username to insert into the database
            * password (str): plaintext password to encrypt and insert into the database
    """
    if request.method == 'POST':
        user = request.form.get('user')
        user_obj = _get_user(user, db_obj)
        if user_obj is not None:
            return render_template('register.html', msg='Your email already exists in the database.')

        password = request.form.get('password')
        encrypted_pw = scrypt.hash(password, salt, N=16) #password, salt, N=(num_iterations), r=(block_size), p=(num_threads), bufflen=(num_output_bytes)

        insert_resp = _add_user(user, encrypted_pw, db_obj)
        return redirect(url_for('login'))

    else:
        return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """This endpoint is used to initiate a session with a given set of permissions. The user provides a username and password, which are compared against entries in the database to try and find a match. If a match is found, a session is created for that user and they are redirected to the main landing endpoint, which is the search endpoint.

    GET request:
        Render the login page.
    POST request:
        Attempt to initiate a session for the user by checking that their username and password correspond to a user in the database.
        form data:
            * user (str): username to check against the database.
            * password (str): corresponding plaintext password to encrypt and check.
    """
    if request.method == 'POST':
        user = request.form.get('user')
        plaintext_password = request.form.get('password')

        user_obj = _get_user(user, db_obj)
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
@requires_permissions(['DUNEwriter', 'Admin'])
def logout():
    """When the user hits this endpoint, their session is deleted, essentially logging them out.

    GET request:
        Render the login page.
    """
    session.clear()
    return redirect(url_for('login'))

@app.route('/about', methods=['GET'])
def about_endpoint():
    return render_template('about.html')

@app.route('/restricted_page')
def restricted_page():
    """This endpoint is where users are redirected to when they try to access an endpoint they do not have access to with the account they are currently logged in as.
    """
    return render_template('restricted_page.html')

@app.route('/simple_search', methods=['GET','POST'])
def simplesearch_endpoint():
    if request.method == 'POST':
        field = "all"
        comparison = "contains"
        q_dict, q_str, _, error_msg = do_q_append(request.form)

        results, error_msg = perform_search(q_dict, db_obj)
        results_str = [ str(r) for r in results ]

    else:
        error_msg = ''
        results_str = ''
        results = []

    return render_template('simple_search.html', error_msg=error_msg, results_str=results_str, results_dict=results)

@app.route('/search', methods=['GET','POST'])
def search_endpoint():
    """Intakes query term elements, assembles them into a valid query term, and appends the new query term to an existing query, if possible. If the option to perform the search is selected, this endpoint calls the back-end's search function with the newly assembled query and returns the resulting documents from the database.

    GET request:
        Render the search page with no results or existing query.
    POST request:
        Render the search page with specific information depending on the form elements present:
        form data:
            * append_button (str): if the value for this field is "do_and" or "do_or", the rest of the form data is parsed into the elements of a new query term and added to whatever query terms already exist. If the value is "do_and", the query term is added to the existing query with an "and" operation. If the value is "do_or", it is added with an "or" operation.
            * existing_query (str): the human-readable version of whatever existing query is already present and is currently being added to.
            * query_field (str): the field that is being queried against.
            * comparison_operator (str): the type of comparison being made in the query term.
            * query_value (str): the value to compare.
            * include_synonyms (str): if "true", the query searches not only for the specified value, but also for all synonyms of the value, if the value is present in the synonyms list.
            * append_mode (str): whether to add the new query term to the existing query with an "and" or "or"  operation.
    """
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

    print('Q STR:',q_str)
    print('APPEND MODE:',append_mode)
    return render_template('search.html', existing_query=q_str, append_mode=append_mode, error_msg=error_msg, num_q_lines=num_q_lines, final_q=final_q_lines_list, results_str=results_str, results_dict=results)

@app.route('/insert', methods=['GET','POST'])
@requires_permissions(['DUNEwriter', 'Admin'])
def insert_endpoint():
    """Assembles all specified fields and values into a valid database object and inserts it into the database.

    GET request:
        Renders the blank insert page.
    POST request:
        Parses the fields and values specified in the form into a JSON document, inserts the document into the database, and renders a new blank insert page with a message providing the new database ID of the document that was just added to the database.
        form data:
            * grouping (str): experiment name
            * sample.name (str): concise sample description
            * sample.description (str): more detailed sample description
            * sample.source (str): where the sample came from
            * sample.id (str): sample identification number
            * sample.owner.name (str): who owns the sample
            * sample.owner.contact (str): email of the person who owns the sample
            * data_source.reference (str): where the data came from
            * data_source.input.notes (str): input simplifications, assumptions, etc.
            * data_source.input.name (str): who performed the data input
            * data_source.input.contact (str): email of the person who performed the data input
            * measurement.technique (str): technique name
            * measurement.institution (str): name of the institution where the measurement was performed
            * measurement.description (str): detailed description
            * measurement.date (str): date when measurement was performed
            * measurement.results.isotopeX (str): the value of the isotope for the measurement X where X is any positive integer.
            * measurement.results.typeX (str): the type of the measurement X ("measurement", "range", or "limit") where X is any positive integer.
            * measurement.results.unitX (str): the units of the measurement X values where X is any positive integer.
            * measurement.results.valueAX (str): the first value of the measurement X where X is any positive integer. If measurement.results.typeX is "measurement", this value is the central value. If measurement.results.typeX is "range", this value is the lower limit. If measurement.results.typeX is "limit", this value is the upper limit.
            * measurement.results.valueBX (str): the second value of the measurement X where X is any positive integer. If measurement.results.typeX is "measurement", this value is the symmetric error. If measurement.results.typeX is "range", this value is the upper limit. If measurement.results.typeX is "limit", this value is the confidence level.
            * measurement.results.valueCX (str): the third value of the measurement X where X is any positive integer. If measurement.results.typeX is "measurement", this value is the asymmetric error. If measurement.results.typeX is "range", this value is the confidence level. If measurement.results.typeX is "limit", this value should not be present.
            * measurement.requestor.name (str): who coordinated the measurement
            * measurement.requestor.contact (str): email of the person who coordinated the measurement
            * measurement.practitioner.name (str): who performed the measurement
            * measurement.practitioner.contact (str): email of the person who performed the measurement
    """
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
    """Finds the document with the given ID in the database and updates its fields and values with the fields and values that the user supplies in the form data.

    GET request:
        Renders the page for a user to specify a document ID to search for.
    POST request:
        If the "submit_button" form data value is "find_doc", extract the "doc_id" value, search for it in the database, and return the update page with the found document's fields and values. If the "submit_button" value is "update_doc", extract all the new user-specified fields and values and update the document in the database with them.
        form data:
            * submit_button (str): one of "find_doc" or "update_doc", this field dictates what operation to perform on the back-end
            * doc_id (str): this should only be present if the "find_doc" option is specified
            * grouping (str): the updated value for experiment name
            * sample.name (str): the updated value for concise sample description
            * sample.description (str): the updated value for more detailed sample description
            * sample.source (str): the updated value for where the sample came from
            * sample.id (str): the updated value for sample identification number
            * sample.owner.name (str): the updated value for who owns the sample
            * sample.owner.contact (str): the updated value for email of the person who owns the sample
            * data_source.reference (str): the updated value for where the data came from
            * data_source.input.notes (str): the updated value for input simplifications, assumptions, etc.
            * data_source.input.name (str): the updated value for who performed the data input
            * data_source.input.contact (str): the updated value for email of the person who performed the data input
            * measurement.technique (str): the updated value for technique name
            * measurement.institution (str): the updated value for name of the institution where the measurement was performed
            * measurement.description (str): the updated value for detailed description
            * measurement.date (str): the updated value for date when measurement was performed
            * measurement.results.isotopeX (str): the updated value for the value of the isotope for the measurement X where X is any positive integer.
            * measurement.results.typeX (str): the updated value for the type of the measurement X ("measurement", "range", or "limit") where X is any positive integer.
            * measurement.results.unitX (str): the updated value for the units of the measurement X values where X is any positive integer.
            * measurement.results.valueAX (str): the updated value for the first value of the measurement X where X is any positive integer. If measurement.results.typeX is "measurement", this value is the central value. If measurement.results.typeX is "range", this value is the lower limit. If measurement.results.typeX is "limit", this value is the upper limit.
            * measurement.results.valueBX (str): the updated value for the second value of the measurement X where X is any positive integer. If measurement.results.typeX is "measurement", this value is the symmetric error. If measurement.results.typeX is "range", this value is the upper limit. If measurement.results.typeX is "limit", this value is the confidence level.
            * measurement.results.valueCX (str): the updated value for the third value of the measurement X where X is any positive integer. If measurement.results.typeX is "measurement", this value is the asymmetric error. If measurement.results.typeX is "range", this value is the confidence level. If measurement.results.typeX is "limit", this value should not be present.
            * measurement.requestor.name (str): the updated value for who coordinated the measurement
            * measurement.requestor.contact (str): the updated value for email of the person who coordinated the measurement
            * measurement.practitioner.name (str): the updated value for who performed the measurement
            * measurement.practitioner.contact (str): the updated value for email of the person who performed the measurement
            * current.measurement.results.isotopeX (str): the document's original value of the isotope for the measurement X where X is any positive integer.
            * current.measurement.results.typeX (str): the document's original type of the measurement X ("measurement", "range", or "limit") where X is any positive integer.
            * current.measurement.results.unitX (str): the document's original units of the measurement X values where X is any positive integer.
            * current.measurement.results.valueAX (str): the document's original first value of the measurement X where X is any positive integer.
            * current.measurement.results.valueBX (str): the document's original second value of the measurement X where X is any positive integer.
            * current.measurement.results.valueCX (str): the document's original third value of the measurement X where X is any positive integer.
            * new.measurement.results.isotopeX (str): the value of the isotope for the measurement X where X is any positive integer, and where this value is being added for a measurement result that is not part of the original document
            * new.measurement.results.typeX (str): the type of the measurement X ("measurement", "range", or "limit") where X is any positive integer, and where this value is being added for a measurement result that is not part of the original document
            * new.measurement.results.unitX (str): the units of the measurement X values where X is any positive integer, and where this value is being added for a measurement result that is not part of the original document
            * new.measurement.results.valueAX (str): the first value of the measurement X where X is any positive integer, and where this value is being added for a measurement result that is not part of the original document
            * new.measurement.results.valueBX (str): the second value of the measurement X where X is any positive integer, and where this value is being added for a measurement result that is not part of the original document
            * new.measurement.results.valueCX (str): the third value of the measurement X where X is any positive integer, and where this value is being added for a measurement result that is not part of the original document
            * remove.grouping (str): if present and not an empty string, remove the current value for the grouping field
            * remove.sample.name (str): if present and not an empty string, remove the current value for the sample.name field
            * remove.sample.description (str): if present and not an empty string, remove the current value for the sample.description field
            * remove.sample.source (str): if present and not an empty string, remove the current value for the sample.source field
            * remove.sample.id (str): if present and not an empty string, remove the current value for the sample.id field
            * remove.sample.owner.name (str): if present and not an empty string, remove the current value for the sample.owner.name field
            * remove.sample.owner.contact (str): if present and not an empty string, remove the current value for the sample.owner.contact field
            * remove.data_source.reference (str): if present and not an empty string, remove the current value for the data_source.reference field
            * remove.data_source.input.notes (str): if present and not an empty string, remove the current value for the data_source.input.notes field
            * remove.data_source.input.name (str): if present and not an empty string, remove the current value for the data_source.input.name field
            * remove.data_source.input.contact (str): if present and not an empty string, remove the current value for the data_source.input.contact field
            * remove.measurement.technique (str): if present and not an empty string, remove the current value for the measurement.technique field
            * remove.measurement.institution (str): if present and not an empty string, remove the current value for the measurement.institution field
            * remove.measurement.description (str): if present and not an empty string, remove the current value for the measurement.description field
            * remove.measurement.date (str): if present and not an empty string, remove the current value for the measurement.date field
            * remove.measurement.resultsX (str): if present and not an empty string, remove the entire measurement result at position X in the documents measurement results list where X is a postive integer
            * remove.measurement.results.isotopeX (str): if present and not an empty string, remove the current value for the measurement.results.isotopeX field
            * remove.measurement.results.typeX (str): if present and not an empty string, remove the current value for the measurement.results.typeX field
            * remove.measurement.results.unitX (str): if present and not an empty string, remove the current value for the measurement.results.unitX field
            * remove.measurement.results.valueAX (str): if present and not an empty string, remove the current value for the measurement.results.valueAX field
            * remove.measurement.results.valueBX (str): if present and not an empty string, remove the current value for the measurement.results.valueBX field
            * remove.measurement.results.valueCX (str): if present and not an empty string, remove the current value for the measurement.results.valueCX field
            * remove.measurement.requestor.name (str): if present and not an empty string, remove the current value for the measurement.requestor.name field
            * remove.measurement.requestor.contact (str): if present and not an empty string, remove the current value for the measurement.requestor.contact field
            * remove.measurement.practitioner.name (str): if present and not an empty string, remove the current value for the measurement.practitioner.name field
            * remove.measurement.practitioner.contact (str): if present and not an empty string, remove the current value for the measurement.practitioner.contact field
    """
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



