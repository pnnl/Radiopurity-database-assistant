import argparse
import json
import re
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
from copy import deepcopy
from .validate import DuneValidator, validate_meas_remove_indices, validate_query_terms
from .query_class import Query

##########################################
# IN ORDER TO CONNECT TO DB:
# ssh -L 27017:localhost:27017 bgtest01
##########################################
client = MongoClient('localhost', 27017)

# set default database
coll = client.radiopurity_data.testing
old_versions_coll = client.radiopurity_data.testing_oldversions


'''
RETURNS: bool (successful db change)
'''
def set_ui_db(db_name, coll_name):
    global coll
    global old_versions_coll
    global assay_requests_coll

    valid_dbs = [ ele['name'] for ele in list(client.list_databases()) ]
    if db_name not in valid_dbs:
        return False

    valid_colls = [ ele['name'] for ele in list(client[db_name].list_collections()) ]
    if coll_name not in valid_colls:
        return False

    old_versions_coll_name = coll_name + '_oldversions'
    assay_requests_coll_name = coll_name + '_assay_requests'

    coll = client[db_name][coll_name]
    old_versions_coll = client[db_name][old_versions_coll_name]
    assay_requests_coll = client[db_name][assay_requests_coll_name]
    return True

def _get_specified_collection(collection_name):
    collection = coll
    if collection_name == 'old_versions':
        collection = old_versions_coll
    elif collection_name == 'assay_requests':
        collection = assay_requests_coll
    return collection


def create_query_object(query_string=None):
    return Query(query_string)


'''
RETURNS: list (documents found)
'''
def search(query, coll_type=''):
    # user can enter a string or dict query. If string, we parse it into a dict.
    if type(query) is str:
        q_obj = Query(query)
        query = q_obj.to_query_lang()
    '''
    if type(query) is not dict:
        print("Error: the query argument must be a dictionary.")
        return None
    '''
    collection = _get_specified_collection(coll_type)
    resp = collection.find(query)
    resp = list(resp)
    for i, ele in enumerate(resp):
        ele['_id'] = str(ele['_id'])
        resp[i] = ele
    return resp


'''
RETURNS: dict (doc found)
'''
def search_by_id(doc_id, coll_type=''):
    try:
        id_obj = ObjectId(doc_id)
    except:
        print("Error: you did not enter a valid MongoDB ObjectId string.")
        return None
    q = {'_id':id_obj}

    collection = _get_specified_collection(coll_type)
    resp = collection.find(q)
    resp = list(resp)

    if len(resp) > 1:
        ret_doc = resp[0]
    elif len(resp) < 1:
        ret_doc = None
    else:
        ret_doc = resp[0]

    return ret_doc


'''
helper functions for update
'''
def _get_existing_doc(doc_id, update_from_coll):
    parent_q = {'_id':ObjectId(doc_id)}
    collection = _get_specified_collection(update_from_coll)
    parent_resp = collection.find(parent_q)
    parent_doc = list(parent_resp)[0]
    return parent_doc

def _remove_meas_objects(new_doc, meas_remove_indices):
    is_valid, error_msg = validate_meas_remove_indices(new_doc, meas_remove_indices) #TODO: should this be "new_doc" not "parent_doc"
    if not is_valid:
        print(error_msg)
        return None, error_msg
    meas_remove_indices.sort(reverse=True) #must sort descending to keep removal indices correct
    for rm_idx in meas_remove_indices:
        new_doc['measurement']['results'].pop(rm_idx)
    return new_doc, ''

def _validate_new_meas_objects(new_meas_objects):
    meas_validator = DuneValidator("measurement_result")
    is_valid = True
    error_message = ''
    for new_meas_obj in new_meas_objects:
        is_valid, error_message = meas_validator.validate(new_meas_obj)
        if not is_valid:
            print(error_message)
            return False, error_message
    return is_valid, error_message

def _add_new_meas_objects(new_doc, new_meas_objects):
    is_valid, error_msg = _validate_new_meas_objects(new_meas_objects)
    if not is_valid:
        return None, error_msg
    for new_meas_obj in new_meas_objects:
        for i in range(len(new_meas_obj['value'])):
            try:
                new_meas_obj['value'][i] = float(new_meas_obj['value'][i]) #ensure meas values are floats
            except:
                error_msg = 'measurement value '+str(new_meas_obj['value'][i])+' cannot be converted to a number'
                print(error_msg)
                return None, error_msg
        new_doc['measurement']['results'].append(new_meas_obj)
    return new_doc, ''

def _update_nonmeas_fields(new_doc, update_pairs_copy):
    for update_key in update_pairs_copy:
        update_val = update_pairs_copy[update_key]
        update_keys = update_key.split('.')

        # convert date strings to datetime objects
        if update_keys[-1] == 'date':
            update_val = convert_str_list_to_date(update_val)
            if update_val is None:
                error_msg = 'one of the values for '+update_key+' cannot be converted to a date object'
                print(error_msg)
                return None, error_msg

        # set update values in new_doc
        if len(update_keys) == 1:
            new_doc[update_keys[0]] = update_val
        elif len(update_keys) == 2:
            new_doc[update_keys[0]][update_keys[1]] = update_val
        elif len(update_keys) > 2:
            try:
                update_key_2 = int(update_keys[2])
            except:
                update_key_2 = update_keys[2]

            if len(update_keys) == 3:
                new_doc[update_keys[0]][update_keys[1]][update_key_2] = update_val
            elif len(update_keys) == 4:
                new_doc[update_keys[0]][update_keys[1]][update_key_2][update_keys[3]] = update_val

    return new_doc, ''

def _update_new_doc(new_doc, meas_remove_indices, new_meas_objects, update_pairs_copy):
    # validate remove indices, do meas removal - MUST do removal before add/update to keep original indices 
    new_doc, error_msg = _remove_meas_objects(new_doc, meas_remove_indices)
    if new_doc is None:
        return None, error_msg

    # add new measurement result
    new_doc, error_msg = _add_new_meas_objects(new_doc, new_meas_objects)
    if new_doc is None:
        return None, error_msg

    # update existing non-meas_result values
    new_doc, error_msg = _update_nonmeas_fields(new_doc, update_pairs_copy)
    if new_doc is None:
        return None, error_msg

    # validate new doc
    validator = DuneValidator("whole_record")
    is_valid, error_message = validator.validate(new_doc)
    if not is_valid:
        print(error_message)
        return None, error_msg

    return new_doc, ''

def _update_databases(new_doc, parent_doc, do_remove_doc, update_from_coll, update_to_coll, do_update_assay_request):
    new_doc_id = None
    update_ok = True
    collection = _get_specified_collection(update_to_coll)
    if not do_remove_doc:
        # insert new doc into current versions collection
        try:
            new_doc_id = collection.insert_one(new_doc).inserted_id
            update_ok = True
        except:
            update_ok = False

    # clean up database if there is an issue inserting the new doc
    if not do_remove_doc and not update_ok:
        collection.delete_one(new_doc)

    if update_ok:
        if not do_update_assay_request:
            try:
                # add old doc to old versions collection (unless it's an update of an assay request, in which we don't add the old doc to anything, we just get rid of it)
                old_versions_coll.insert_one(parent_doc)
                update_ok = True
            except:
                update_ok = False

        if update_ok:
            # remove old doc from current versions collection
            collection = _get_specified_collection(update_from_coll)
            parent_q = {'_id':parent_doc['_id']}
            removeold_resp = collection.delete_one(parent_q)

    return new_doc_id

'''
RETURNS: ObjectId or None (new document ID)
         str (error message)
'''
def update(doc_id, remove_doc=False, update_pairs={}, new_meas_objects=[], meas_remove_indices=[], do_update_assay_request=False):
    # make copy of update_pairs dict in case values change; don't want that to change values in the func calling this
    update_pairs_copy = deepcopy(update_pairs)

    if do_update_assay_request:
        update_from_coll = 'assay_requests'
        update_to_coll = ''
    else:
        update_from_coll = ''
        update_to_coll = ''

    # find existing doc to update
    parent_doc = _get_existing_doc(doc_id, update_from_coll)

    # create child (new record) based off of parent doc
    new_doc = deepcopy(parent_doc)
    new_doc.pop('_id')
    new_doc['_version'] += 1
    new_doc['_parent_id'] = doc_id

    # make updates and validate new doc
    new_doc, error_msg = _update_new_doc(new_doc, meas_remove_indices, new_meas_objects, update_pairs_copy)
    if new_doc is None:
        return None, error_msg

    # do update in database, move old version, etc.
    new_doc_id = _update_databases(new_doc, parent_doc, remove_doc, update_from_coll, update_to_coll, do_update_assay_request)

    return new_doc_id, ''

"""
RETURNS: str (new version of query string)
         dict (new version of query in query langage)
"""
def add_to_query(field, comparison, value, query_object=None, query_string='', append_mode='', include_synonyms=True):
    if query_object is None:
        query_object = Query(query_string) #NOTE: query string must be in the specific format like "field1 compare1 value1\nAND\nfield2 compare2 value2\nOR\n..."
    query_object.add_query_term(field, comparison, value, append_mode, include_synonyms)
    query_string = query_object.to_string()
    query_dict = query_object.to_query_language()
    return query_string, query_dict

'''
RETURNS: ObjectId or None (id of new doc)
         str (error message)
'''
def insert(sample_name, sample_description, data_reference, data_input_name, data_input_contact, data_input_date, \
    grouping="", sample_source="", sample_id="", sample_owner_name="", sample_owner_contact="", \
    measurement_results=[], measurement_practitioner_name="", measurement_practitioner_contact="", \
    measurement_technique="", measurement_institution="", measurement_date=[], measurement_description="", \
    measurement_requestor_name="", measurement_requestor_contact="", data_input_notes="", coll_type=''):

    # convert date string lists to date object lists
    data_input_date = convert_str_list_to_date(data_input_date)
    measurement_date = convert_str_list_to_date(measurement_date)
    if data_input_date is None or measurement_date is None:
        return None, 'a value in one of the date arguments could not be converted to a datetime object'

    # assemble insertion object
    doc = {"specification":"3.00", "grouping":grouping, "type":"assay", 
        "sample": {
            "name":sample_name,
            "description":sample_description,
            "source":sample_source,
            "id":sample_id,
            "owner": {
                "name":sample_owner_name, 
                "contact":sample_owner_contact
            }
        },
        "measurement": {
            "description":measurement_description,
            "requestor": {
                "name":measurement_requestor_name, 
                "contact":measurement_requestor_contact
            },
            "practitioner": {
                "name":measurement_practitioner_name, 
                "contact":measurement_practitioner_contact
            },
            "technique":measurement_technique,
            "institution":measurement_institution,
            "date":measurement_date,
            "results":measurement_results
        },
        "data_source": {
            "reference":data_reference,
            "input": {
                "notes":data_input_notes,
                "date":data_input_date,
                "name":data_input_name,
                "contact":data_input_contact
            }
        },
        "_version":1
    }
    print(doc)

    # validate doc
    validator = DuneValidator("whole_record")
    is_valid, error_message = validator.validate(doc) 
    if not is_valid:
        return None, error_message

    # perform doc insert
    collection = _get_specified_collection(coll_type)
    mongo_id = collection.insert_one(doc).inserted_id

    try:
        print("Successfully inserted doc with id:",mongo_id)
        msg = ''
    except:
        print("Error inserting doc")
        msg = 'unsuccessful insert into mongodb'

    return mongo_id, msg


'''
RETURNS: datetime (object representing date) or NONE if error
'''
def convert_str_to_date(date_str):
    new_date_obj = None
    date_formats = ["%Y-%m-%d", "%Y/%m/%d", "%m-%d-%Y", "%m/%d/%Y", "%Y-%d-%m", "%Y/%d/%m", "%d-%m-%Y", "%d/%m/%Y"]
    for date_format in date_formats:
        try:
            new_date_obj = datetime.strptime(date_str, date_format)
            break
        except:
            pass
    return new_date_obj


'''
RETURNS: str (datetime obj converted to str) EMPTY if error
'''
def convert_date_to_str(date_obj):
    try:
        new_date_str = date_obj.strftime("%Y-%m-%d")
    except:
        new_date_str = ''
    return new_date_str

'''
RETURNS: list (strings converted to datetime objects) or NONE if error
'''
def convert_str_list_to_date(str_list):
    date_objects = []
    for date_str in str_list:
        date_obj = convert_str_to_date(date_str)
        if date_obj is None:
            return None
        else:
            date_objects.append(date_obj)
    return date_objects


if __name__ == '__main__':
    valid_fields = ["grouping", "sample.name", "sample.description", "sample.source", "sample.id", "sample.owner.name", "sample.owner.contact", "measurement.results.isotope", "measurement.results.type", "measurement.results.unit", "measurement.results.value", "measurement.practitioner.name", "measurement.practitioner.contact", "measurement.technique","measurement.institution", "measurement.date", "measurement.description", "measurement.requestor.name", "measurement.requestor.contact", "data_source.reference", "data_source.input.name", "data_source.input.contact", "data_source.input.date", "data_source.input.notes"]
    valid_str_comparisons = ["contains", "notcontains", "eq"]
    valid_num_comparisons = ["eq", "lt", "lte", "gt", "gte"]
    valid_appendmodes = ["AND", "OR"]


    parser = argparse.ArgumentParser(description='A python toolkit for interfacing with the radiopurity_example MongoDB.')
    subparsers = parser.add_subparsers(help='options for which function to run', dest='subparser_name')

    search_parser = subparsers.add_parser('search', help='execute search function')
    search_parser.add_argument('--q', type=json.loads, required=True, help='query to execute. *must be surrounded with single quotes, and use double quotes within dict*')

    query_append_parser = subparsers.add_parser('add_query_term', help='execute append function (add new query term to query)')
    query_append_parser.add_argument('--field', type=str, required=True, choices=valid_fields, help='the field to compare the value of')
    query_append_parser.add_argument('--compare', type=str, required=True, choices=list(set(valid_str_comparisons+valid_num_comparisons)), \
        help='comparison operator to use to compare actual field value to given value')
    query_append_parser.add_argument('--val', type=str, required=True, help='the value to compare against. Can be a string or numeric')
    query_append_parser.add_argument('--mode', type=str, choices=["OR", "AND"], default="AND", help='optional argument to define append mode. If not present, defaults to "AND"')
    query_append_parser.add_argument('--q', type=str, default='', \
        help='*must be surrounded with single quotes, and use double quotes within dict* existing query dictionary to add a new term to. If not present, creates a new query')

    insert_parser = subparsers.add_parser('insert', help='execute document insert function')
    insert_parser.add_argument('--sample_name', type=str, required=True, help='concise sample description')
    insert_parser.add_argument('--sample_description', type=str, required=True, help='detailed sample description')
    insert_parser.add_argument('--data_reference', type=str, required=True, help='where the data came from')
    insert_parser.add_argument('--data_input_name', type=str, required=True, help='name of the person/people who performed data input')
    insert_parser.add_argument('--data_input_contact', type=str, required=True, help='email or telephone of the person/people who performed data input')
    insert_parser.add_argument('--data_input_date', nargs='*', required=True, help='list of date strings for dates of input')
    insert_parser.add_argument('--data_input_notes', type=str, default='', help='input simplifications, assumptions')
    insert_parser.add_argument('--grouping', type=str, default='', help='experiment name or similar')
    insert_parser.add_argument('--sample_source', type=str, default='', help='where the sample came from')
    insert_parser.add_argument('--sample_id', type=str, default='', help='identification number')
    insert_parser.add_argument('--sample_owner_name', type=str, default='', help='name of who owns the sample')
    insert_parser.add_argument('--sample_owner_contact', type=str, default='', help='email or telephone of who owns the sample')
    insert_parser.add_argument('--measurement_results', nargs='*', default=[], help='list of measurements')
    insert_parser.add_argument('--measurement_practitioner_name', type=str, default='', help='name of who did the measurement')
    insert_parser.add_argument('--measurement_practitioner_contact', type=str, default='', help='email or telephone of who did the measurement')
    insert_parser.add_argument('--measurement_technique', type=str, default='', help='technique name')
    insert_parser.add_argument('--measurement_institution', type=str, default='', help='institution name')
    insert_parser.add_argument('--measurement_date', nargs='*', default=[], help='list of date strings for dates of measurement')
    insert_parser.add_argument('--measurement_description', type=str, default='', help='detailed description')
    insert_parser.add_argument('--measurement_requestor_name', type=str, default='', help='name of who coordinated the measurement')
    insert_parser.add_argument('--measurement_requestor_contact', type=str, default='', help='email or telephone of who coordinated the measurement')

    update_parser = subparsers.add_parser('update', help='execute document update function')
    update_parser.add_argument('--doc_id', type=str, required=True, help='the id of the document in the database to update')
    update_parser.add_argument('--remove_doc', action='store_true', default=False, help='Remove the entire document from the database')
    update_parser.add_argument('--update_pairs', nargs='*', default=[], help='list of keys to update and the new values to use')
    update_parser.add_argument('--new_meas_objects', nargs='*', default=[], help='list of measurement results dictionaries to add to the document')
    update_parser.add_argument('--meas_remove_indices', nargs='*', default=[], help='list of indices (zero-indexed) corresponding to the document measurement result object to remove')

    args = vars(parser.parse_args())

    if args['subparser_name'] == 'search':
        result = search(args['q'])
    elif args['subparser_name'] == 'add_query_term':
        #TODO: add "include_synonyms" field
        result = add_to_query(args['field'], args['compare'], args['val'], query_string=args['q'], append_mode=args['mode'])
    elif args['subparser_name'] == 'insert':
        for i in range(len(args['measurement_results'])):
            args['measurement_results'][i] = json.loads(args['measurement_results'][i])
        result, error_msg = insert(args['sample_name'], \
            args['sample_description'], \
            args['data_reference'], \
            args['data_input_name'], \
            args['data_input_contact'], \
            args['data_input_date'], \
            datas_input_notes=args['data_input_notes'], \
            grouping=args['grouping'], \
            sample_source=args['sample_source'], \
            sample_id=args['sample_id'], \
            sample_owner_name=args['sample_owner_name'], \
            sample_owner_contact=args['sample_owner_contact'], \
            measurement_results=args['measurement_results'], \
            measurement_practitioner_name=args['measurement_practitioner_name'], \
            measurement_practitioner_contact=args['measurement_practitioner_contact'], \
            measurement_technique=args['measurement_technique'], \
            measurement_institution=args['measurement_institution'], \
            measurement_date=args['measurement_date'], \
            measurement_description=args['measurement_description'], \
            measurement_requestor_name=args['measurement_requestor_name'], \
            measurement_requestor_contact=args['measurement_requestor_contact']
        )
    elif args['subparser_name'] == 'update':
        update_keyval_pairs = {}
        for i in range(len(args['update_pairs'])):
            if i%2 == 0:
                update_key = args['update_pairs'][i]
                update_val = args['update_pairs'][i+1]
                update_keyval_pairs[update_key] = update_val
        result, error_msg = update(args['doc_id'], \
            remove_doc=args['remove_doc'], \
            update_pairs=update_keyval_pairs, \
            new_meas_objects=args['new_meas_objects'], \
            meas_remove_indices=args['meas_remove_indices']
        )
    else:
        print('You must enter an action to perform: search, insert, update, or add_query_term')
        result = None

    print(result)

