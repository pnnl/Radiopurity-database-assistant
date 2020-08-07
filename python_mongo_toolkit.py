import argparse
import json
import re
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
from copy import deepcopy

numeric_fields = ["measurement.results.value"]
date_fields = ["measurement.date", "data_source.input.date"]
valid_fields = ["grouping", "sample.name", "sample.description", "sample.source", "sample.id", "sample.owner.name", "sample.owner.contact", "measurement.results.isotope", "measurement.results.type", "measurement.results.unit", "measurement.results.value", "measurement.practitioner.name", "measurement.practitioner.contact", "measurement.technique","measurement.institution", "measurement.date", "measurement.description", "measurement.requestor.name", "measurement.requestor.contact", "data_source.reference", "data_source.input.name", "data_source.input.contact", "data_source.input.date", "data_source.input.notes"]
valid_str_comparisons = ["contains", "notcontains", "eq"]
valid_num_comparisons = ["eq", "lt", "lte", "gt", "gte"]
valid_appendmodes = ["AND", "OR"]

valid_isotopes = open('isotopes.csv', 'r').read().strip().split(',')
valid_units = open('units.csv', 'r').read().strip().split(',')


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

    valid_dbs = [ ele['name'] for ele in list(client.list_databases()) ]
    if db_name not in valid_dbs:
        return False

    valid_colls = [ ele['name'] for ele in list(client[db_name].list_collections()) ]
    if coll_name not in valid_colls:
        return False

    old_versions_coll_name = coll_name + '_oldversions'
    coll = client[db_name][coll_name]
    old_versions_coll = client[db_name][old_versions_coll_name]
    return True


'''
RETURNS: list (documents found)
'''
def search(query):
    if type(query) is not dict:
        print("Error: the query argument must be a dictionary.")
        return None
    resp = coll.find(query)
    resp = list(resp)
    for i, ele in enumerate(resp):
        ele['_id'] = str(ele['_id'])
        resp[i] = ele
    return resp


'''
RETURNS: dict (doc found)
'''
def search_by_id(doc_id):
    try:
        id_obj = ObjectId(doc_id)
    except:
        print("Error: you did not enter a valid MongoDB ObjectId string.")
        return None
    q = {'_id':id_obj}
    resp = coll.find(q)
    resp = list(resp)

    if len(resp) > 1:
        ret_doc = resp[0]
    elif len(resp) < 1:
        ret_doc = None
    else:
        ret_doc = resp[0]

    return ret_doc


'''
RETURNS: ObjectId or None (new document ID)
         str (error message)
'''
def update_with_versions(doc_id, remove_doc=False, update_pairs={}, new_meas_objects=[], meas_remove_indices=[]):
    # make copy of update_pairs dict in case values change; don't want that to change values in the func calling this
    update_pairs_copy = deepcopy(update_pairs)

    # validate foramt of new_meas_objects
    valid_measurement_results, error_msg = _validate_measurement_results_data(new_meas_objects)
    if not valid_measurement_results:
        return None, error_msg

    # validate fields in update_pairs_copy
    for update_key in update_pairs_copy:
        key_eles = update_key.split('.')
        if len(key_eles) == 4:
            try:
                int(key_eles[2])
                update_key = '.'.join([key_eles[0], key_eles[1], key_eles[3]])
            except:
                pass
        if update_key not in valid_fields:
            error_msg = 'the "field" argument must be one of: '+', '.join(valid_fields)+' and you entered: '+update_key
            print('Error:',error_msg)
            return None, error_msg
        
        # convert date vals to datetime objects
        if update_key in date_fields:
            for i in range(len(update_pairs_copy[update_key])):
                update_val = convert_str_to_date(update_pairs_copy[update_key][i])
                if update_val is not None:
                    update_pairs_copy[update_key][i] = convert_str_to_date(update_pairs_copy[update_key][i])
                else:
                    error_msg = 'the "'+update_key+'" value, '+update_pairs_copy[update_key][i]+', is not a valid date'
                    print('Error:',error_msg)
                    return None, error_msg

    parent_q = {'_id':ObjectId(doc_id)}
    parent_resp = coll.find(parent_q)
    parent_doc = list(parent_resp)[0]
    parent_version = parent_doc['_version']
    parent_id = ObjectId(doc_id)

    # validate remove indices
    for rm_idx in meas_remove_indices:
        if rm_idx < 0 or rm_idx >= len(parent_doc['measurement']['results']):
            error_msg = 'you entered an invalid measurement removal of '+str(rm_idx)+' and valid indices must be between 0 and '+str(len(parent_doc['measurement']['results']))
            print('Error:',error_msg)
            return None, error_msg

    print('REMOVE DOC:::::',remove_doc)
    print('UPDATE PAIRS:::',update_pairs_copy)
    print('NEW MEAS:::::::',new_meas_objects)
    print('MEAS REMOVE::::',meas_remove_indices)

    # create child (new record)
    new_doc = deepcopy(parent_doc)
    new_doc.pop('_id')
    new_doc['_version'] += 1
    new_doc['_parent_id'] = doc_id

    # remove meas - MUST do removal before add/update to keep original indices
    meas_remove_indices.sort(reverse=True) #must sort descending to keep removal indices correct
    for rm_idx in meas_remove_indices:
        new_doc['measurement']['results'].pop(rm_idx)

    # add new measurement result
    for new_meas_obj in new_meas_objects:

        # ensure that all measurement values are floats
        for i in range(len(new_meas_obj['value'])):
            new_meas_obj['value'][i] = float(new_meas_obj['value'][i])

        # add meas to new doc
        new_doc['measurement']['results'].append(new_meas_obj)

    # update existing non-meas_result values
    for update_key in update_pairs_copy:
        update_val = update_pairs_copy[update_key]
        update_keys = update_key.split('.')

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

    new_doc_id = None
    update_ok = True
    if not remove_doc:
        # insert new doc into current versions collection
        try:
            new_doc_id = coll.insert_one(new_doc).inserted_id
            update_ok = True
        except:
            update_ok = False

    # clean up database if there is an issue inserting the new doc
    if not remove_doc and not update_ok:
        coll.delete_one(new_doc)

    if update_ok:
        try:
            # add old doc to old versions collection
            old_versions_coll.insert_one(parent_doc)
            update_ok = True
        except:
            update_ok = False

        if update_ok:
            # remove old doc from current versions collection
            removeold_resp = coll.delete_one(parent_q)
    
    return new_doc_id, ''


'''
RETURNS: dict (new version of query)
         str (error msg)
'''
def add_to_query(field, comparison, value, existing_q={}, append_mode="AND"):
    # validate arguments
    if field not in valid_fields:
        error_msg = 'the "field" argument must be one of: '+', '.join(valid_fields)+' and you entered: '+field
        print('Warning:',error_msg)
        return existing_q, error_msg
    if comparison not in set(valid_str_comparisons+valid_num_comparisons):
        error_msg = 'the "comparison" argument must be one of: '+', '.join(set(valid_str_comparisons+valid_num_comparisons))+' and you entered: '+comparison
        print('Warning:', error_msg)
        return existing_q, error_msg
    if append_mode.upper() not in valid_appendmodes:
        error_msg = 'the "append_mode" argument must be one of: '+', '.join(valid_appendmodes)+' and you entered: '+append_mode.upper()
        print('Warning:',error_msg)
        return existing_q, error_msg
    if field in numeric_fields and type(value) not in [int, float]:
        try:
            value = float(value)
        except:
            error_msg = 'you must enter a numeric value when comparing fields in: '+ ', '.join(numeric_fields)+' (you entered: '+value+')'
            print('Warning:',error_msg)
            return existing_q, error_msg
    if type(value) is str and field not in date_fields and comparison not in valid_str_comparisons:
        error_msg = 'when comparing string values, the comparison operator must be one of: '+', '.join(valid_str_comparisons)+' (you entered: '+comparison+')'
        print('Warning:',error_msg)
        return existing_q, error_msg
    if type(value) is not str and comparison not in valid_num_comparisons:
        error_msg = 'when comparing numeric values, the comparison operator must be one of: '+', '.join(valid_num_comparisons)+' (you entered: '+comparison+')'
        print('Warning:',error_msg)
        return existing_q, error_msg
    if field in date_fields and comparison not in valid_num_comparisons:
        error_msg = 'when comparing date values, the comparison operator must be one of: '+', '.join(valid_num_comparisons)+' (you entered: '+comparison+')'
        print('Warning:',error_msg)
        return existing_q, error_msg

    #TODO: implement date comparison taking second value into account (aka range)
    #TODO: implement measurement value comparison taking second and third values into account for range, measurement, and limit measurement types
    if field.startswith('measurement.results.value'):
        field += '.0'

    if field in date_fields:
        field += '.0'
        search_val = convert_str_to_date(value)
        if search_val is None:
            error_msg = 'the date value, '+value+' is not in a valid date format'
            print('Warning:',error_msg)
            return existing_q, error_msg
        comparison = '$' + comparison
        new_term = {field:{comparison:search_val}}
    elif type(value) is str:
        if comparison == 'contains':
            search_val = re.compile('^.*'+value+'.*$', re.IGNORECASE)
        elif comparison == 'notcontains':
            match_pattern = re.compile('^'+value+'$', re.IGNORECASE)
            search_val = {"$not":match_pattern}
        else:
            search_val = re.compile('^'+value+'$', re.IGNORECASE)
        new_term = {field.replace('measurement.results.', ''):search_val}
    else:
        comparison = '$' + comparison
        new_term = {field.replace('measurement.results.', ''):{comparison:value}}

    existing_keys = list(existing_q.keys())

    # add to elemmatch field if it's part of the measurement results
    if field.startswith('measurement.results'):
        top_level_field = ''
        if '$or' in existing_keys and 'measurement.results' in [list(l.keys())[0] for l in existing_q['$or']]:
            # elemMatch exists in query already, under the top "or" term
            top_level_field = '$or'
        elif '$and' in existing_keys and 'measurement.results' in [list(l.keys())[0] for l in existing_q['$and']]:
            # elemMatch exists in query already, under the top "and" term
            top_level_field = '$and'
        else:
            # elemMatch does not exist in query yet
            top_level_field = None

        # create elemMatch field of query
        if top_level_field == None:
            if append_mode == 'OR':
                if '$or' in existing_keys:
                    existing_q['$or'].append({'measurement.results':{'$elemMatch':new_term}})
                else:
                    if len([field_name for field_name in list(existing_q.keys()) if field_name not in ['$and', '$or'] ]) > 0:
                        existing_field = [field_name for field_name in list(existing_q.keys()) if field_name not in ['$and', '$or'] ][0]
                        existing_q['$or'] = [{existing_field:existing_q.pop(existing_field)}, {'measurement.results':{'$elemMatch':new_term}}]
                    else:
                        existing_q['$or'] = [{'measurement.results':{'$elemMatch':new_term}}]
            else:
                if '$and' in existing_keys:
                    existing_q['$and'].append({'measurement.results':{'$elemMatch':new_term}})
                else:
                    if len([field_name for field_name in list(existing_q.keys()) if field_name not in ['$and', '$or'] ]) > 0:
                        existing_field = [field_name for field_name in list(existing_q.keys()) if field_name not in ['$and', '$or'] ][0]
                        existing_q['$and'] = [{existing_field:existing_q.pop(existing_field)}, {'measurement.results':{'$elemMatch':new_term}}]
                    else:
                        existing_q['$and'] = [{'measurement.results':{'$elemMatch':new_term}}]

        # elemMatch field exists in query; add to it
        else:
            # find index of measurement.results element in top_level_field list
            meas_results_idx = 0
            for i, q_term in enumerate(existing_q[top_level_field]):
                if 'measurement.results' == list(q_term.keys())[0]:
                    meas_results_idx = i
                    break

            append_mode = '$'+append_mode.lower()
            if append_mode in list(existing_q[top_level_field][meas_results_idx]['measurement.results']['$elemMatch'].keys()):
                # append mode list already exists
                existing_q[top_level_field][meas_results_idx]['measurement.results']['$elemMatch'][append_mode].append(new_term)
            else:
                # append mode list does not exist yet; create it
                existing_field = [field_name for field_name in list(existing_q[top_level_field][meas_results_idx]['measurement.results']['$elemMatch'].keys()) if field_name not in ['$and', '$or'] ][0]
                existing_q[top_level_field][meas_results_idx]['measurement.results']['$elemMatch'][append_mode] = [{existing_field:existing_q[top_level_field][meas_results_idx]['measurement.results']['$elemMatch'].pop(existing_field)}, new_term]

    # add to the general query if it's not for measurement results field
    else:
        if append_mode == 'OR':
            if '$or' in existing_keys:
                # add to other $or elements (this groups all $or terms together))
                existing_q['$or'].append(new_term)
            elif len(existing_keys) == 0:
                existing_q[field] = new_term[field]
            else:
                # creates an $or list out of this new term and the most recently added element (query dict --> "Python 3.6 onwards, the standard dict type maintains insertion order by default.")
                existing_q['$or'] = [{existing_keys[-1]:existing_q.pop(existing_keys[-1])}, new_term]
        else:
            if field in existing_q.keys():
                #print('A. creating $and from existing.')
                existing_q['$and'] = [{field:existing_q.pop(field)}, new_term]
            elif '$and' in existing_q.keys() and [list(f.keys())[0] for f in existing_q['$and']]:
                #print('B. adding to existing $and')
                existing_q['$and'].append(new_term)
            else:
                #print('C. new q element')
                existing_q[field] = new_term[field]

    return existing_q, ''


'''
RETURNS: ObjectId or None (id of new doc)
         str (error message)
'''
def insert(sample_name, sample_description, data_reference, data_input_name, data_input_contact, data_input_date, \
    grouping="", sample_source="", sample_id="", sample_owner_name="", sample_owner_contact="", \
    measurement_results=[], measurement_practitioner_name="", measurement_practitioner_contact="", \
    measurement_technique="", measurement_institution="", measurement_date=[], measurement_description="", \
    measurement_requestor_name="", measurement_requestor_contact="", data_input_notes=""):

    # verify and convert measurement_results arg
    valid_measurement_results, error_msg = _validate_measurement_results_data(measurement_results)
    if not valid_measurement_results:
        return None, error_msg

    # verify and convert data_input_date arg
    if type(data_input_date) is not list:
        error_msg = 'the data_input_date argument must be a list of date strings.'
        print('Error:',error_msg)
        return None, error_msg
    for d, date_str in enumerate(data_input_date):
        new_date_obj = convert_str_to_date(date_str)
        if new_date_obj is None:
            error_msg = 'at least one of the data input date strings is not in one of the accepted formats'
            print('Error:', error_msg)
            return None, error_msg
        else:
            data_input_date[d] = new_date_obj

    # verify and convert measurement_date arg
    if type(measurement_date) is not list:
        error_msg = 'the measurement date argument must be a list of date strings'
        print('Error:', error_msg)
        return None, error_msg
    if len(measurement_date) > 0:
        for d, date_str in enumerate(measurement_date):
            new_date_obj = convert_str_to_date(date_str)
            if new_date_obj is None:
                error_msg = 'at least one of the measurement date strings is not in one of the accepted formats'
                print('Error:',error_msg)
                return None, error_msg
            else:
                measurement_date[d] = new_date_obj

    # ensure that all measurement values are floats
    for i in range(len(measurement_results)):
        for j in range(len(measurement_results[i]['value'])):
            measurement_results[i]['value'][j] = float(measurement_results[i]['value'][j])

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

    # perform doc insert
    mongo_id = coll.insert_one(doc).inserted_id

    try:
        print("Successfully inserted doc with id:",mongo_id)
        msg = ''
    except:
        print("Error inserting doc")
        msg = 'unsuccessful insert into mongodb'

    return mongo_id, msg


'''
RETURNS: datetime (object representing date)
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
RETURNS: str (datetime obj converted to str)
'''
def convert_date_to_str(date_obj):
    try:
        new_date_str = date_obj.strftime("%Y-%m-%d")
    except:
        new_date_str = ''
    return new_date_str


'''
RETURNS: bool (meas data is valid)
         str (error message)
'''
def _validate_measurement_results_data(measurement_results):
    if type(measurement_results) is not list:
        error_msg = 'the measurement_results argument must be a list containing dictionary objects'
        print('Error:',error_msg)
        return False, error_msg
    for i, results_element in enumerate(measurement_results):
        if type(results_element) is not dict:
            error_msg = 'the measurement_results argument must be dictionaries'
            print('Error:',error_msg)
            return False, error_msg
        for results_key in ["isotope", "type", "unit", "value"]:
            if results_key not in list(results_element.keys()):
                error_msg = 'at least one of the required keys ["isotope", "type", "unit", "value"] is missing from at least one of the dictionaries in the measurement results'
                print('Error:',error_msg)
                return False, error_msg
            if results_key == 'isotope':
                if measurement_results[i][results_key] not in valid_isotopes:
                    error_msg = 'the isotope '+measurement_results[i][results_key]+' is not a valid isotope. Note: Isotopes must be in the following format: <ELEMENT SYMBOL>-<MASS NUMBER>'
                    print('Error:',error_msg)
                    return False, error_msg
            if results_key == 'type':
                if measurement_results[i][results_key] not in ['measurement', 'range', 'limit']:
                    error_msg = '"type" field of the measurement results dictionaries must be one of: "measurement", "range", "limit"'
                    print('Error:',error_msg)
                    return False, error_msg
            if results_key == 'unit':
                if measurement_results[i][results_key] not in valid_units:
                    error_msg = 'the unit '+measurement_results[i][results_key]+' is not a valid measurement unit. Valid units are: '+str(valid_units)
                    print('Error:',error_msg)
                    return False, error_msg
            elif results_key == 'value':
                if type(measurement_results[i][results_key]) is not list:
                    error_msg = 'the "value" field of the dictionaries in the measurement_results list must be a list'
                    print('Error:', error_msg)
                    return False, error_msg
                for j in range(len(measurement_results[i][results_key])):
                    try:
                        measurement_results[i][results_key][j] = float(measurement_results[i][results_key][j])
                    except:
                        error_msg = 'at least one of the elements in the "value" list of at least one of the dictionaries in the measurement_results list cannot be parsed into a number'
                        print('Error:',error_msg)
                        return False, error_msg
    return True, ''

if __name__ == '__main__':
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
    query_append_parser.add_argument('--q', type=json.loads, default={}, \
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
        result = add_to_query(args['field'], args['compare'], args['val'], existing_q=args['q'], append_mode=args['mode'])
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
        result, error_msg = update_with_versions(args['doc_id'], \
            remove_doc=args['remove_doc'], \
            update_pairs=update_keyval_pairs, \
            new_meas_objects=args['new_meas_objects'], \
            meas_remove_indices=args['meas_remove_indices']
        )
    else:
        print('You must enter an action to perform: search, insert, update, or add_query_term')
        result = None

    print(result)

