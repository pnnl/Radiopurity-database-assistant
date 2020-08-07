import sys
import argparse
import datetime
from functools import wraps
from flask_bcrypt import Bcrypt
from flask import Flask, request, session, url_for, redirect, render_template
from python_mongo_toolkit import set_ui_db, search_by_id, convert_date_to_str
from frontend_helpers import do_q_append, parse_existing_q, perform_search, perform_insert, parse_update, perform_update
from frontend_helpers import _find_user, _add_user

app = Flask(__name__)
app.config['SECRET_KEY'] = open('app_config.txt', 'r').readline().strip()
app.permanent_session_lifetime = datetime.timedelta(hours=24)
bcrypt = Bcrypt(app)

'''
 define custom decorator
 used: https://blog.tecladocode.com/learn-python-defining-user-access-roles-in-flask/
'''
def requires_permissions(permissions_level):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            email = session.get('email')
            if email is None:
                return redirect(url_for('login'))

            user_obj = _find_user(email)
            if not user_obj[permissions_level]:
                return redirect(url_for('restricted_page'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/', methods=['GET', 'POST'])
@requires_permissions('permissions_read')
def reference_endpoint():
    ui_url_parts = request.host.split(':')
    ui_ip = ui_url_parts[0]
    ui_port = ui_url_parts[1]
    return render_template('index.html', db_name=database_type, ip=ui_ip, port=ui_port)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        user_obj = _find_user(email)
        if user_obj is not None:
            return render_template('register.html', msg='Your email already exists in the database.')

        password = request.form.get('password')
        encrypted_pw = bcrypt.generate_password_hash(password, 12)
        first_name = request.form.get('firstname')
        last_name = request.form.get('lastname')

        insert_resp = _add_user(email, encrypted_pw, first_name, last_name)
        return redirect(url_for('login'))

    else:
        return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        plaintext_password = request.form.get('password')

        user_obj = _find_user(email)
        if user_obj is None:
            return render_template('login.html', msg='User was not found in the database')
        else:
            user_db_pw_hash = user_obj['password_hashed']
            is_correct_pw = bcrypt.check_password_hash(user_db_pw_hash, plaintext_password)
            if is_correct_pw:
                session['permanent'] = True
                session['email'] = user_obj['email']
                return redirect(url_for('reference_endpoint'))
            else:
                return render_template('login.html', msg="incorrect password")
    else:
        return render_template('login.html')

@app.route('/logout', methods=['GET'])
@requires_permissions('permissions_read')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/restricted_page')
def restricted_page():
    return render_template('restricted_page.html')

@app.route('/search', methods=['GET','POST'])
@requires_permissions('permissions_read')
def search_endpoint():
    if request.form.get("append_button") == "do_and":
        existing_q_str, num_q_lines, final_q_lines_list, results = do_q_append(request.form, "AND")
        results_str = [ str(r) for r in results ]
        search_msg = ''

    elif request.form.get("append_button") == "do_or":
        existing_q_str, num_q_lines, final_q_lines_list, results = do_q_append(request.form, "OR")
        results_str = [ str(r) for r in results ]
        search_msg = ''

    elif request.method == "POST":
        final_q_str = parse_existing_q(request.form)
        final_q_lines_list = []
        if final_q_str != '':
            final_q_lines_list = final_q_str.split('\n')
        
        results, search_msg = perform_search(final_q_lines_list)
        results_str = [ str(r) for r in results ]
        existing_q_str = ''
        num_q_lines = 0

    else:
        existing_q_str = ''
        num_q_lines = 0
        final_q_lines_list = []
        results = []
        results_str = []
        search_msg = ''

    return render_template('search.html', db_name=database_type, existing_query=existing_q_str, search_msg=search_msg, num_q_lines=num_q_lines, final_q=final_q_lines_list, results_str=results_str, results_dict=results)

@app.route('/insert', methods=['GET','POST'])
@requires_permissions('permissions_edit')
def insert_endpoint():
    if request.method == "POST":
        new_doc_id, error_msg = perform_insert(request.form)
        new_doc_msg = 'new doc id: '+str(new_doc_id)
        if new_doc_id is None:
            new_doc_msg = "ERROR: record not inserted because "+error_msg
    else:
        new_doc_msg = ""
    return render_template('insert.html', db_name=database_type, new_doc_msg=new_doc_msg)

@app.route('/update', methods=['GET','POST'])
@requires_permissions('permissions_edit')
def update_endpoint():
    if request.method == "GET":
        return render_template('update.html', db_name=database_type, doc_data=False, message="")

    elif request.form.get("submit_button") == "find_doc":
        doc_id = request.form.get('doc_id', '')
        doc = search_by_id(doc_id)
        print('DOC:::',doc)

        if doc is None:
            return render_template('update.html', db_name=database_type, doc_data=False, message="No document was found with the ID you provided.")
        
        for i in range(len(doc['measurement']['results'])):
            num_vals = len(doc['measurement']['results'][i]['value'])
            if num_vals == 0:
                doc['measurement']['results'][i]['value'] = []
            if num_vals < 2:
                doc['measurement']['results'][i]['value'].append('')
            if num_vals < 3:
                doc['measurement']['results'][i]['value'].append('')

        return render_template('update.html', db_name=database_type, doc_data=True, doc_id=doc['_id'], \
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
        new_doc_id, error_msg = perform_update(doc_id, remove_doc, update_pairs, meas_remove_indices, meas_add_eles)
        if new_doc_id != None:
            message = "update success. New doc version ID: "+str(new_doc_id)
        else:
            message = 'error: '+error_msg
        return render_template('update.html', db_name=database_type, doc_data=False, message=message)
    return None


if __name__ == '__main__':
    global database_type
    parser = argparse.ArgumentParser(description='API code for the DUNE project.')
    parser.add_argument('--port', type=int, default=5000, help='the port number to run the UI on.')
    parser.add_argument('--db', type=str, choices=['radiopurity', 'dune'], required=False, \
        help='the type of data to use with the UI. The "radiopurity" option uses the database \
        containing data extracted from the radiopurity site. The "dune" option uses the database \
        for data from the DUNE project.')
    args = parser.parse_args()

    if args.db == 'dune':
        print('Using dune database')
        db_name = 'dune'
        collection_name = 'dune_data'
        database_type = 'dune'
    elif args.db == 'radiopurity':
        print('Using radiopurity database')
        db_name = 'radiopurity_data'
        collection_name = 'example_data'
        database_type = 'radiopurity'
    else:
        print('No database specified as argument; using default radiopurity testing database (radiopurity_data.testing).')
        db_name = 'radiopurity_data'
        collection_name = 'testing'
        database_type = 'radiopurity testing'
    
    successful_change = set_ui_db(db_name, collection_name)
    if not successful_change:
        print('error: unable to change mongodb to database:',database_type,'and collection:',collection_name)
        sys.exit()

    app.run(host='127.0.0.1', port=args.port)


