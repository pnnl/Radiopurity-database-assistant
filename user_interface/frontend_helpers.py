"""
.. module:: frontend_helpers
   :synopsis: Auxiliary functions for the radiopurity API.

.. moduleauthor:: Elise Saxon
"""

import re
import scrypt
import base64
import logging
import binascii
import datetime
from dunetoolkit import Query, add_to_query, search, insert, update, convert_date_to_str

logger = logging.getLogger('dune_ui')

def _get_httprequest_username(http_auth):
    """Parses the http_authentication portion of an HTTP request's header to extract the logged in user's username. The username should be within the string, encoded as base64.

    args:
        * http_auth (str): the http_authorization part of an HTTP request's header.

    returns:
        * str. The username of the logged in user making the request. None if no user is logged in or if error.
    """
    user = None
    if http_auth and http_auth.lower().startswith('basic'):
        auth = http_auth.split(" ", 1)
        if len(auth) == 2:
            try:
                auth = base64.b64decode(auth[1].strip().encode('utf-8'))
                auth = auth.decode('utf-8')
                auth = auth.split(":", 1)
            except (TypeError, binascii.Error, UnicodeDecodeError) as exc:
                logger.warn("Couldn't get username: {}\n".format(exc))
            if len(auth) == 2:
                user = auth[0]
    return user

def _get_date_now():
    """Gets the current date.

    returns:
        * str. Date in "YYYY-mm-dd" format.
    """
    return datetime.datetime.now().strftime("%Y-%m-%d")

def _log_in_experiment(experiment_name, plaintext_password, salt, db_obj):
    """Searches for credentials in the database matching the user-entered experiment_name and, if an entry with the same name is found, compares the user-entered password with the encrypted one in the database.

    args:
        * experiment_name (str): user-entered credential name. 
        * plaintext_password (str): user-entered password to accompany experiment_name.
        * salt (int): necessary for safe encryption.
        * db_obj (pymongo.database.Database): a pymongo database object that can be used to query for users.

    returns:
        * bool. True if a proper match for the user-entered credentials was found in the database.
    """
    coll = db_obj.users
    find_experiment_q = {'experiment_name':{'$eq':experiment_name}}
    find_experiment_resp = coll.find(find_experiment_q)
    find_experiment_resp = list(find_experiment_resp)
    if len(find_experiment_resp) <= 0:
        return False
    else:
        experiment_creds_obj = find_experiment_resp[0]

    db_pw_hash = experiment_creds_obj['password_hashed']
    is_correct_pw = (scrypt.hash(plaintext_password, salt, N=16) == db_pw_hash)
    if is_correct_pw:
        return True
    else:
        return False

def do_q_append(form):
    """Parses out the form input to get the new query term field, comparison, and value, then adds the new query term to whatever query already exists, if there is one. 

    args:
        * form (werkzeug.datastructures.ImmutableMultiDict): an immutable dictionary containing the information passed by the user as key-value pairs.

    returns:
        * dict. The new valid pymongo query.
        * str. The human-readable version of the new query.
        * int. The number of lines in the human-readable query (for UI purposes).
        * str. An error message (empty string if no errors happened).
    """
    existing_q_text, field, comparison, value, append_mode, include_synonyms = parse_existing_q(form)
    q_str, q_dict = add_to_query(field, comparison, value, append_mode=append_mode, include_synonyms=include_synonyms, query_string=existing_q_text)
    q_obj = Query(q_str)
    q_dict = q_obj.to_query_language()
    q_str = q_obj.to_string()
    num_q_lines = q_str.count('\n') + 1

    error_msg = ''

    return q_dict, q_str, num_q_lines, error_msg

def add_protected_groupings_term_to_query(q_dict, q_str, logged_in_experiments, db_obj):
    """Adds an invisible term to the query that ensures the query will exclude all datapoints whre the "grouping" value is not in the list of private experiments that the user is not logged-in to.

    args:
        * q_dict (dict): the final user-specified query.
        * q_str (str): the human-readable version of the final user-specified query, used to create a Query object so we can add a query term.
        * logged_in_experiments (list of str): the names of all experiments that the user is currently logged-in to.
        * db_obj (pymongo.database.Database): a pymongo database object that can be used to query for the private experiment names that the user is not logged-in to.

    returns:
        * dict. The new query in MongoDB query language with a term to exclude records that the user is not logged-in to.
    """
    # get all valid experiments from user db
    protected_experiments = []
    resp = db_obj.users.find({})
    for r in resp:
        protected_experiments.append(r["experiment_name"])

    # subtract logged_in_experiments from all_experiments
    excluded_experiments = [ exp for exp in protected_experiments if exp not in logged_in_experiments ]

    # can't add to a query that searches for all docs
    if q_dict == {}:
        q_str = ""

    # add "AND grouping not in [that list]"
    q_obj = Query(q_str)
    for excluded_experiment in excluded_experiments:
        q_obj.add_query_term("grouping", "notcontains", excluded_experiment, append_type="AND", include_synonyms=False)

    # get query dict
    q_dict = q_obj.to_query_language()
    return q_dict

def make_experiment_public(experiment_name, db_obj):
    """Removes the normal and admin user records from the database, thus removing the privacy constraints on the corresponding experiment.

    args: 
        * experiment_name (str): the name of the experiment to remove all privacy restrictions for.
        * db_obj (pymongo.database.Database): a pymongo database object that can be used to remove records from the users collection.

    returns:
        * bool. True if the removal of both the normal and admin credentials was successful.
    """
    for name in [experiment_name, "{}_ADMIN".format(experiment_name)]:
        resp = db_obj.users.delete_one({'experiment_name':{'$eq':name}})
        if resp.deleted_count == 1:
            success = True
        else:
            logger.warn("When removing experiment {} from the protected experiments database collection, expected to get response of 1 deleted; got {} deleted, instead".format(name, resp.deleted_count))
            success = False
        if not success:
            break
    return success

def _convert_logged_in_users_to_unique_experiment_names(credentials, admin_only=False):
    """Deduplicates the list of logged-in credentials for a user from all credentials to just experiment names. This list requires deduplication because, for each private experiment, there are two "user" credentials: the normal reader and the admin. For querying we need this list to only contain valid values for the data record "grouping" field, so admin credentials must be thought of the same way as normal users.

    args:
        * credentials (list of str): The names of all the credentials that the user is currently logged in with.
        * admin_only (bool) (optional): True if we only want the list of experiment names the user is currently logged in with admin credentials for.

    returns:
        * list of str. The list of experiment names that the user is currently logged in to. If admin_only, then this is the list of only experiments for which the user is currently logged in as an admin.
    """
    admin_experiments = []
    experiments = []
    for credential_name in credentials:
        if credential_name.endswith("_ADMIN"):
            experiment_name = credential_name.strip("_ADMIN")
            if experiment_name not in admin_experiments:
                admin_experiments.append(experiment_name)
        else:
            experiment_name = credential_name
        if experiment_name not in experiments:
            experiments.append(experiment_name)
    if admin_only:
        return admin_experiments
    else:
        return experiments

def convert_str_to_float(value):
    """Converts the given value to a float type object, if possible. If the object cannot be converted into a float, nothing happens.

    args:
        * value (any type): generally this will be a string object where the content of the string is a numeric digits.
    returns:
        * float (or the original type). If successful, the original value as type float is returned. Otherwise, the value as its original type is returned.
    """
    try:
        value = float(value)
    except:
        pass
    return value

def parse_existing_q(form_obj):
    """Parses out the form input to get all the query term, comparison operator, value, and other query options.

    args:
        * form_obj (werkzeug.datastructures.ImmutableMultiDict): an immutable dictionary containing the information passed by the user as key-value pairs.

    returns:
        * str. The existing query, if present, in human-readable form.
        * str. The field to compare.
        * str. The comparison operator to use.
        * float (or str). The value to compare against.
        * str. How to append this query term to the existing query ("and" or "or").
        * bool. Whether to search for all synonyms of the value or just the value itself.
    """
    existing_q = form_obj.get('existing_query', '').strip()
    field = form_obj.get('query_field', '').strip()
    comparison = form_obj.get('comparison_operator', '').strip()
    value = form_obj.get('query_value', '').strip()
    if field in ['measurement.results.value']:
        value = convert_str_to_float(value)
    include_synonyms = form_obj.get('include_synonyms', '').strip() == "true"
    append_mode = form_obj.get('append_mode', '').strip()
    return existing_q, field, comparison, value, append_mode, include_synonyms

def perform_search(curr_q, db_obj, coll_type=''):
    """Calls the dunetoolkit search function to retrieve documents from the database with the given query, then formats and returns the documents.

    args:
        * curr_q (dict): a valid pymongo query to use to search the database.
        * db_obj (pymongo.database.Database): a pymongo database object that, once a collection has been selected, can be used to query.
        * coll_type (str) (optional): if provided, this field specifies which column of the database to search (e.g. assays or assay_requests). If not provided, the dunetoolkit automatically searches the assays collection.

    returns:
        * list of dict. The list of found documents.
        * str. An error message (empty string if no errors happened).
    """
    # query for results
    results = search(curr_q, db_obj, coll_type)

    # convert datetime objects to strings for UI display
    for i in range(len(results)):
        for j in range(len(results[i]['measurement']['date'])):
                results[i]['measurement']['date'][j] = convert_date_to_str(results[i]['measurement']['date'][j])
        for j in range(len(results[i]['data_source']['input']['date'])):
            results[i]['data_source']['input']['date'][j] = convert_date_to_str(results[i]['data_source']['input']['date'][j])

    return results, ''


def perform_insert(form, db_obj, coll_type=''):
    """Parses the form data into a dict with the proper format of a radiopurity database document, then passes that dict to the dunetoolkit insert function to be inserted into the database.

    args:
        * form (werkzeug.datastructures.ImmutableMultiDict): an immutable dictionary containing the information passed by the user as key-value pairs.
        * db_obj (pymongo.database.Database): a pymongo database object that, once a collection has been selected, can be used to query.
        * coll_type (str) (optional): if provided, this field specifies which column of the database to search (e.g. assays or assay_requests). If not provided, the dunetoolkit automatically searches the assays collection.

    returns:
        * bson.objectid.ObjectId. The ID of the document that was just inserted (None if unsuccessful).
        * str. An error message (empty string if no error happened).
    """
    # start by parsing all the measurement results elements into a separate list of dicts, which will be added as the value for the "measurement.results" field
    meas_results = []
    i = 1
    form_keys = list(form.to_dict().keys())
    while True:
        # check if there are no more measurement elements
        if 'measurement.results.isotope'+str(i) not in form_keys:
            break

        # format values
        vals = []
        for val_key in ['measurement.results.valueA'+str(i), 'measurement.results.valueB'+str(i), 'measurement.results.valueC'+str(i)]:
            if form.get(val_key).strip() != '':
                # currently not enforcing any missing value rules
                vals.append(float(form.get(val_key).strip()))

        # create measurement element
        meas_ele = {'isotope':form.get('measurement.results.isotope'+str(i), ''),
            'type':form.get('measurement.results.type'+str(i), ''),
            'unit':form.get('measurement.results.unit'+str(i), ''),
            'value': vals
        }

        # add to measurements list
        meas_results.append(meas_ele)
        i += 1

    # properly format dates
    data_input_date = form.get('data_source.input.date','')
    if data_input_date == '':
        data_input_date = []
    else:
        data_input_date = data_input_date.split(' ')
        for i in range(len(data_input_date)):
            data_input_date[i] = data_input_date[i].strip()
    measurement_date = form.get('measurement.date','')
    if measurement_date == '':
        measurement_date = []
    else:
        measurement_date = measurement_date.split(' ')
        for i in range(len(measurement_date)):
            measurement_date[i] = measurement_date[i].strip()

    new_doc_id, error_msg = insert(sample_name=form.get('sample.name',''), \
        sample_description=form.get('sample.description',''), \
        data_reference=form.get('data_source.reference',''), \
        data_input_name=form.get('data_source.input.name',''), \
        data_input_contact=form.get('data_source.input.contact',''), \
        data_input_date=data_input_date, \
        db_obj=db_obj, \
        grouping=form.get('grouping',''), \
        sample_source=form.get('sample.source',''), \
        sample_id=form.get('sample.id',''), \
        sample_owner_name=form.get('sample.owner.name',''), \
        sample_owner_contact=form.get('sample.owner.contact',''), \
        measurement_results=meas_results, \
        measurement_practitioner_name=form.get('measurement.practitioner.name',''), \
        measurement_practitioner_contact=form.get('measurement.practitioner.contact',''), \
        measurement_technique=form.get('measurement.technique',''), \
        measurement_institution=form.get('measurement.institution',''), \
        measurement_date=measurement_date, \
        measurement_description=form.get('measurement.description',''), \
        measurement_requestor_name=form.get('measurement.requestor.name',''), \
        measurement_requestor_contact=form.get('measurement.requestor.contact',''), \
        data_input_notes=form.get('data_source.input.notes',''),
        coll_type=coll_type
    )
    
    return new_doc_id, error_msg


def parse_update(form):
    """Parses the form data into fields and corresponding update values, then constructs a set of update objects that can be passed to the dunetoolkit's update function in order to actually update the specified document in the database. This function parses all the measurement results objects first, in order to find which measurement results are being updated, entirely deleted, or added as new objects. Then it processes the non-measurement results fields, figuring out which fields have values to be updated and which fields need their values removed.

    args:
        * form (werkzeug.datastructures.ImmutableMultiDict): an immutable dictionary containing the information passed by the user as key-value pairs.

    returns:
        * str. The ID of the document to update, extracted from the form data.
        * bool. Whether to remove the entire document from the database (if True).
        * dict. A set of (non-measurement results) fields and corresponding values to update in the document in the database.
        * list of int. The integer indices of measurement results objects to remove entirely from the measurement results field. 
        * list of dict. The new measurement results objects to add to the measurement results field.
    """
    remove_meas_indices = []
    update_pairs = {}
    add_eles = []

    doc_id = form.get('current_doc_id')
    remove_doc = form.get("remove.doc", "") == "remove"

    # gather updates for current measurement results objects
    num_measurement_results = 0
    while True:
        # check if this is the last of the existing measurement results objects
        if form.get("measurement.results.isotope"+str(num_measurement_results+1)) is None:
            break
        num_measurement_results += 1

        # check if entire object is to be removed
        if form.get('remove.measurement.results'+str(num_measurement_results)) is not None:
            remove_meas_indices.append(num_measurement_results - 1)
            continue

        for field in ["isotope", "type", "unit"]:
            # get form values
            curr_val = form.get('current.measurement.results.'+field+str(num_measurement_results), '')
            val = form.get('measurement.results.'+field+str(num_measurement_results), '')
            do_remove = form.get('remove.measurement.results.'+field+str(num_measurement_results), '') != ''

            # remove field's value by updating it with an empty string value. Use mongodb list indices, not html element numbers
            if do_remove:
                # add field to the "update values" list with an empty field (we don't want to completely delete the field)
                update_pairs['measurement.results.'+str(num_measurement_results-1)+'.'+field] = ''

            # val not empty means perform some update
            elif val != '':
                if val != curr_val: # dropdowns are pre-selected with the curr_val by default, so same value means no change
                    # add field to the "update values" list
                    update_pairs['measurement.results.'+str(num_measurement_results-1)+'.'+field] = val

        # handle the measurement results values
        curr_A = form.get('current.measurement.results.valueA'+str(num_measurement_results), '')
        curr_B = form.get('current.measurement.results.valueB'+str(num_measurement_results), '')
        curr_C = form.get('current.measurement.results.valueC'+str(num_measurement_results), '')
        vals = [curr_A, curr_B, curr_C]
        val_A = form.get('measurement.results.valueA'+str(num_measurement_results), '')
        val_B = form.get('measurement.results.valueB'+str(num_measurement_results), '')
        val_C = form.get('measurement.results.valueC'+str(num_measurement_results), '')
        if val_A != '':
            vals[0] = val_A
        if val_B != '':
            vals[1] = val_B
        if val_C != '':
            vals[2] = val_C
        if form.get('remove.measurement.results.valueA'+str(num_measurement_results), '') != '':
            vals[0] = None
        if form.get('remove.measurement.results.valueB'+str(num_measurement_results), '') != '':
            vals[1] = None
        if form.get('remove.measurement.results.valueC'+str(num_measurement_results), '') != '':
            vals[2] = None
        if vals[0] == curr_A and vals[1] == curr_B and vals[2] == curr_C:
            # no update
            pass
        else:
            if vals[2] is None or vals[2] == '':
                update = [vals[0], vals[1]]
            else:
                update = [vals[0], vals[1], vals[2]]

            if vals[1] is None or vals[1] == '':
                update = [vals[0]]

            if vals[0] is None or vals[0] == '':
                update = []

            for i in range(len(update)):
                update[i] = convert_str_to_float(update[i])

            update_pairs['measurement.results.'+str(num_measurement_results-1)+'.value'] = update

    # assemble newly-added measurement results
    num_new_measurement_results = 0
    while True:
        # check if this is the last of the new measurement results objects
        if form.get("new.measurement.results.isotope"+str(num_new_measurement_results+1)) is None:
            break
        num_new_measurement_results += 1
        
        # assemble a new result object
        new_meas_element = {}
        for meas_field in ["measurement.results.isotope", "measurement.results.type", "measurement.results.unit"]:
            new_val = form.get('new.'+meas_field+str(num_new_measurement_results), '')
            new_meas_element[meas_field.split('.')[-1]] = new_val
        new_meas_element["value"] = [form.get('new.measurement.results.valueA'+str(num_new_measurement_results), ''), \
            form.get('new.measurement.results.valueB'+str(num_new_measurement_results), ''), \
            form.get('new.measurement.results.valueC'+str(num_new_measurement_results), '')
        ]
        if new_meas_element["value"][2] == '':
            new_meas_element["value"] = [new_meas_element["value"][0], new_meas_element["value"][1]]
        else:
            new_meas_element["value"] = [new_meas_element["value"][0], new_meas_element["value"][1], new_meas_element["value"][2]]
        if new_meas_element["value"][1] == '':
            new_meas_element["value"] = [new_meas_element["value"][0]]
        if new_meas_element["value"][0] == '':
            new_meas_element["value"] = []

        for i in range(len(new_meas_element["value"])):
            new_meas_element["value"][i] = convert_str_to_float(new_meas_element["value"][i])

        # add new object to the "new additions" list
        add_eles.append(new_meas_element)

    # go over non-measurement_result fields looking for updates
    non_meas_result_fields = ["grouping", "sample.name", "sample.description", "sample.source", "sample.id", "sample.owner.name", "sample.owner.contact", "measurement.practitioner.name", "measurement.practitioner.contact", "measurement.technique","measurement.institution", "measurement.date", "measurement.description", "measurement.requestor.name", "measurement.requestor.contact", "data_source.reference", "data_source.input.name", "data_source.input.contact", "data_source.input.date", "data_source.input.notes"]
    for field in non_meas_result_fields:
        val = form.get(field, '') #convert_str_to_float(form.get(field, ''))
        do_remove = form.get('remove.'+field, '') != ''
    
        if do_remove:
            if 'date' in field:
                update_pairs[field] = []
            else:
                update_pairs[field] = ''
        elif val != '':
            if 'date' in field:
                val = val.split(' ')
            update_pairs[field] = val

    return doc_id, remove_doc, update_pairs, remove_meas_indices, add_eles


def perform_update(doc_id, remove_doc, update_pairs, meas_remove_indices, meas_add_eles, db_obj, is_assay_request_update=False, is_assay_request_verify=False):
    """This function calls the dunetoolkit update function with the update fields and values parsed from the form data.

    args:
        * doc_id (str): the ID of the document to update, extracted from the form data.
        * remove_doc (bool): whether to remove the entire document from the database (if True).
        * update_pairs (dict): a set of (non-measurement results) fields and corresponding values to update in the document in the database.
        * meas_remove_indices (list of int): the integer indices of measurement results objects to remove entirely from the measurement results field.
        * meas_add_eles (list of dict): the new measurement results objects to add to the measurement results field.
        * db_obj (pymongo.database.Database): a pymongo database object that, once a collection has been selected, can be used to query.
        * is_assay_request_update (bool): whether the document to update is an assay (in the "assays" collection) or an assay request (in the "assay_requests" collection).

    returns:
        * bson.objectid.ObjectId. The ID of the document that was just updated (if successful).
        * str. An error message (if an error happened).
    """
    new_doc_id, error_msg = update(doc_id, db_obj, remove_doc, update_pairs, meas_add_eles, meas_remove_indices, is_assay_request_update=is_assay_request_update, is_assay_request_verify=is_assay_request_verify)
    return new_doc_id, error_msg


