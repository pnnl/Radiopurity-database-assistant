"""
.. module:: python_mongo_toolkit
   :synopsis: The main code for the radiopurity database assistant.

.. moduleauthor:: Elise Saxon
"""

import os
import argparse
import json
import re
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
from copy import deepcopy
from dunetoolkit.validate import DuneValidator, validate_meas_remove_indices
from dunetoolkit.query_class import Query

##########################################
# IN ORDER TO CONNECT TO DB:
# ssh -L 27017:localhost:27017 bgtest01
##########################################

def _configure():
    """Reads the contents of the config JSON file at the path specified in the environment variable named `TOOLKIT_CONFIG_NAME`, then parses out the information and returns it. If no ppath is specified with the environment variable `TOOLKIT_CONFIG_NAME`, then this defaults to a file named toolkit_config.json in the dunetoolkit directory.

    returns:
        * str. The hostname of the machine where MongoDB is running.
        * str. The port number that can be used to connect to MongoDB on the host.
        * str. The name of the MongoDB database to use for queries.
    """
    config_name = os.getenv('TOOLKIT_CONFIG_NAME')
    if config_name is None:
        config_name = os.path.dirname(os.path.abspath(__file__)) + '/toolkit_config.json'
    config_dict = None

    with open(config_name, 'r') as config:
        config_dict = json.load(config)

    return config_dict['mongodb_host'], config_dict['mongodb_port'], config_dict['database']

def _create_db_obj():
    """This function is useful when the python toolkit is being used directly by the user, instead of in conjunction with the UI. The UI is responsible for creating a persisting, shared database connection and passing it to functions as needed. When the search, insert, and update python functions are being called directly, no existing database connection is required, so this function gets called to set one up.

    returns:
        pymongo.database.Database. A pymongo database object that, once a collection has been selected, can be used to query.
    """
    # TODO: use a config object, access it with an environment variable (just like with the UI). If scripting, create a configure() function
    mongo_host, mongo_port, db_name = _configure()

    client = MongoClient(mongo_host, mongo_port)
    db_obj = client[db_name]
    return db_obj

def _get_specified_collection(collection_name, db_obj):
    """Selects the proper MongoDB collection object based on the collection type specified by the user (collection_name is not the full collection name, just the suffix. E.g. if the actual collection name is "dune_data", then passing "assay_requests" as the collection_name would cause this function to return the collection object with name "dune_data_assay_requests")

    args:
        * collection_name (str): The type of the database collection to use.
        * db_obj (pymongo.database.Database): A pymongo database object that, once a collection has been selected, can be used to query.

    returns:
        * pymongo.collection.Collection. The MongoDB collection specified by the user.
    """
    if collection_name == 'old_versions':
        collection = db_obj.assays_old_versions
    else:
        collection = db_obj.assays
    return collection


def create_query_object(query_string=None):
    """Creates a Query object that is used to parse queries, add to queries, and translate between human-readable and pymongo-syntax queries.

    args:
        * query_string (str) (optional): The human-readable string that represents the query. If no argument query_string is provided, this function returns a Query object with no starting query loaded up. This string MUST be in the format given by the UI's search page. That is, "<field1> <comparison1> <value1>\\n<append_mode>\\n<field2> <comparison2> <value2>\\n<append_mode>\\n..."

    returns:
        * dunetoolkit.Query. The object that stores and parses a user's query
    """
    return Query(query_string)


def search(query, db_obj=None, coll_type=""):
    """Queries the specified MongoDB collection in order to find the documents that fit the given query

    args:
        * query (str or dict): If "query" is a string, it is translated into a pymongo query dict. Otherwise, it is assumed to be a pymongo query dict that can be used as-is to query the collection.
        * db_obj (pymongo.database.Database): A pymongo database object that, once a collection has been selected, can be used to query.
        * coll_type (str) (optional): Dictates which database collection will queried. If no value is provided, this function queries the main assay collection by default (as opposed to old_versions).

    returns:
        * list of dict. The documents found in the MongoDB collection using the provided query.
    """
    # user can enter a string or dict query. If string, we parse it into a dict.
    if type(query) is str:
        q_obj = Query(query)
        query = q_obj.to_query_language()
    '''
    if type(query) is not dict:
        print("Error: the query argument must be a dictionary.")
        return None
    '''
    if db_obj is None:
        db_obj = _create_db_obj()
    collection = _get_specified_collection(coll_type, db_obj)
    resp = collection.find(query)
    resp = list(resp)
    for i, ele in enumerate(resp):
        ele['_id'] = str(ele['_id'])
        resp[i] = ele
    return resp


def search_by_id(doc_id, db_obj=None, coll_type=""):
    """Queries the specified MongoDB collection in order to find the document with the specified doc_id.
    
    args:
        * doc_id (str): The string representation of the MongoDB document ID for the document the user wishes to find.
        * db_obj (pymongo.database.Database): A pymongo database object that, once a collection has been selected, can be used to query.
        * coll_type (str) (optional): Dictates which database collection will queried. If no value is provided, this function queries the main assay collection by default (as opposed to old_versions).

    returns:
        * dict. The document found by in the MongoDB collection with the given document ID. If no document is found with a matching ID, then None is returned.
    """
    try:
        id_obj = ObjectId(doc_id)
    except:
        print("Error: you did not enter a valid MongoDB ObjectId string.")
        return None
    q = {'_id':id_obj}

    if db_obj is None:
        db_obj = _create_db_obj()
    collection = _get_specified_collection(coll_type, db_obj)
    resp = collection.find(q)
    resp = list(resp)

    if len(resp) > 1:
        ret_doc = resp[0]
    elif len(resp) < 1:
        ret_doc = None
    else:
        ret_doc = resp[0]

    return ret_doc

#'''
def _get_existing_doc(doc_id, db_obj, update_from_coll_name):
    """This is a helper function for updating documents in the collection. It queries the database in order to find the document with the specified doc_id.

    args:
        * doc_id (str): The string representation of the MongoDB document ID for the document the user wishes to find.
        * db_obj (pymongo.database.Database): A pymongo database object that, once a collection has been selected, can be used to query.
        * update_from_coll_name (str): Dictates which database collection will queried. If no value is provided, this function queries the main assay collection by default (as opposed to old_versions).

    returns:
        * dict. The document found by in the MongoDB collection with the given document ID. If no document is found with a matching ID, then None is returned.
    """
    #TODO couldn't we just use "search_by_id" for this?
    parent_q = {'_id':ObjectId(doc_id)}
    collection = _get_specified_collection(update_from_coll_name, db_obj)
    parent_resp = collection.find(parent_q)
    parent_doc = list(parent_resp)[0]
    return parent_doc

def _remove_meas_objects(new_doc, meas_remove_indices):
    """This is a helper function for updating documents in the collection. Each document in the database has a list of dictionaries under the top-level field "measurements" and the sub-field "results" where each dict in the list represents the measurement result for a given isotope. One of the updates a user can make to a given document is to remove any of the existing measurement results objects. This function performs the actual removal of those measurement results from the document.

    args:
        * new_doc (dict): The version of the database document that is in the process of being updated so it can be reinserted into the database as a newer version.
        * meas_remove_indices (list of int): The list of indices for which elements of new_doc's measurement.results objects will be removed.

    returns:
        * dict. A new version of new_doc with the measurement objects at the specified meas_remove_indices removed.
        * str. The error message that arose while trying to update new_doc. This would happen when validating the meas_remove_indices against new_doc to make sure they are not out of bounds or anything.
    """
    is_valid, error_msg = validate_meas_remove_indices(new_doc, meas_remove_indices)
    if not is_valid:
        print(error_msg)
        return None, error_msg
    meas_remove_indices.sort(reverse=True) #must sort descending to keep removal indices correct
    for rm_idx in meas_remove_indices:
        new_doc['measurement']['results'].pop(rm_idx)
    return new_doc, ''

def _validate_new_meas_objects(new_meas_objects):
    """This is a helper function for updating documents in the collection. Each document in the database has a list of dictionaries under the top-level field "measurements" and the sub-field "results" where each dict in the list represents the measurement result for a given isotope. These measurement result dicts must be in a specific format that this project has defined. This function checks if each of the provided measurement results objects follows the desired format.

    args:
        * new_meas_objects (list of dict): A list of measurement results dicts that need to be validated.

    returns:
        * bool. Whether all of the dicts in new_meas_objects are valid or not.
        * str. The error message that arose while trying to update new_doc. This would happen if any of the given new_meas_objects are not vallid according to this project's specified schema.
    """
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
    """This is a helper function for updating documents in the collection. Each document in the database has a list of dictionaries under the top-level field "measurements" and the sub-field "results" where each dict in the list represents the measurement result for a given isotope. One of the updates a user can make to a given document is to add new measurement result objects to the existing list of measurement results. This function performs the actual addition of measurement result objects to the document.

    args:
        * new_doc (dict): The version of the database document that is in the process of being updated so it can be reinserted into the database as a newer version.
        * new_meas_objects (list of dict): A list of new measurement object dicts to add to the document's measurement results list.

    returns:
        * dict. A new version of new_doc with the given new measurement objects added to the measurement results list.
        * str. The error message that arose while trying to update new_doc. This would happen if any of the measurement result objects' "value" field values is not already a valid number or cannot be converted into a number.
    """
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
    """This is a helper function for updating documents in the collection. It handles the updating of values in the document. Any existing field can have its value changed in this function if the existing field name and the new value are specified in the update_pairs_copy dictionary.
    
    args:
        * new_doc (dict): The version of the database document that is in the process of being updated so it can be reinserted into the database as a newer version.
        * update_pairs_copy (dict): A set of key-value pairs that represent the fields of the document that need to be updated and the new values that those fields should point to.

    returns:
        * dict. A new version of new_doc with the given fields in update_pairs_copy updated to correspond to the given values in update_pairs_copy.
        * str. The error message that arose while trying to update new_doc. This would happen if a date field is specified in update_pairs_copy but the value for that field cannot be converted into a python datetime object. 
    """
    for update_key in update_pairs_copy:
        update_val = update_pairs_copy[update_key]
        update_keys = update_key.split('.')

        # if one of the elements in the chain of keys should be a list index, make it an int not a string
        for i, key in enumerate(update_keys):
            try:
                num_key = int(key)
                update_keys[i] = num_key
            except:
                pass
        # convert date strings to datetime objects
        if update_keys[-1] == 'date':
            update_val = convert_str_list_to_date(update_val)
            if update_val is None:
                error_msg = 'one of the values in '+str(update_val)+' for '+update_key+' cannot be converted to a date object'
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
    """This is a helper function for updating documents in the collection. It orchestrates the updating of a document by calling the functions that do the actual updating of the document (_update_nonmeas_fields, _add_new_meas_objects, and _remove_meas_objects) and then validates the fully-updated document against this project's format.
    
    args:
        * new_doc (dict): The non-updated version of the document that will have the specified updates applied.
        * meas_remove_indices (list of int): The list of indices for which elements of new_doc's measurement.results objects will be removed
        * new_meas_objects (list of dict): A list of new measurement object dicts to add to the document's measurement results list.
        * update_pairs_copy (dict): A set of key-value pairs that represent the fields of the document that need to be updated and the new values that those fields should point to.

    returns:
        * dict. The version of new_doc with all the given updates applied. This is the version of the doc that will be inserted into the database as the current version.
        * str. The error message that arose while trying to update new_doc. This would happen if any of the update functions encounter errors or invalid values.
    """
    # update existing non-meas_result values
    new_doc, error_msg = _update_nonmeas_fields(new_doc, update_pairs_copy)
    if new_doc is None:
        return None, error_msg
    
    # add new measurement result
    new_doc, error_msg = _add_new_meas_objects(new_doc, new_meas_objects)
    if new_doc is None:
        return None, error_msg
    
    # validate remove indices, do meas removal
    new_doc, error_msg = _remove_meas_objects(new_doc, meas_remove_indices)
    if new_doc is None:
        return None, error_msg

    # validate new doc
    validator = DuneValidator("whole_record")
    is_valid, error_message = validator.validate(new_doc)
    if not is_valid:
        print(error_message)
        return None, error_msg

    return new_doc, ''

def _update_databases(new_doc, parent_doc, do_remove_doc, db_obj, update_from_coll_name, old_versions_coll_name, move_to_coll_name):
    """This is a helper function for updating documents in the collection. It performs the insertion of the new (updated) doc into the main collection that holds the most current versions of the docs. This function also moves the original version of the doc to the "old-versions" collection for archival purposes. This function is used for any type of update a user might make to the radiopurity database: updating a normal assay doc, updating an assay request doc, or validating an assay request doc. Below in the arg definitions are examples of how each type of update might be specified.

    args: 
        * new_doc (dict): The fully updated verision of the document. This dict will become the new "current" version of the doc in the main collection.
        * parent_doc (dict): The "original" version of the document that does not have the specified updates applied.
        * do_remove_doc (bool): This option would be true if the user wishes to remove this assay doc from the database entirely. In this case, the current version in the main collection would be moved to the old_versions collection but no updated doc would be inserted into the main collection.
        * db_obj (pymongo.database.Database): A pymongo database object that, once a collection has been selected, can be used to query.
        * update_from_coll_name (str): This arg helps orchestrate what kind of update is happening. It dictates what collection the "original" document was pulled from. If it is a normal update, this would be the main collection. If it is an assay request update/validation, this would be the assay_requests collection.
        * old_versions_coll_name (str): This arg helps orchestrate what kind of update is happening. It dictates what collection the "original" (unupdated) document will be added to once the updated version gets added to the main collection. If it is a normal update, this would be the old versions database. If it is an assay request update/validation, this would be the assay requests old version.
        * move_to_coll_name (str): This arg helps orchestrate what kind of update is happening. It dictates what collection the fully updated document will be added to. If it is a normal update, this would be the main collection. If it is an assay request update, this would be the assay requests database. If it is an assay request validation, this would be the main database (as a validated assay request is ready to be inserted as a normal assay).

    returns:
        * bson.objectid.ObjectId. The MongoDB document ID of the new, fully-updated document that was added into the specified collection.
    """
    new_doc_id = None
    update_ok = True

    collection = _get_specified_collection(move_to_coll_name, db_obj)
    old_versions_collection = _get_specified_collection(old_versions_coll_name, db_obj)
    original_collection = _get_specified_collection(update_from_coll_name, db_obj)

    # if the action is not to remove the entire doc, try to insert it into current versions collection
    if not do_remove_doc:
        try:
            new_doc_id = collection.insert_one(new_doc).inserted_id
            update_ok = True
        except:
            update_ok = False

    # clean up database if there is an issue inserting the new doc
    if not update_ok:
        collection.delete_one(new_doc)
    else:
        try:
            # add old doc to old versions collection (unless it's an update of an assay request, in which we don't add the old doc to anything, we just get rid of it)
            old_versions_collection.insert_one(parent_doc)
            update_ok = True
        except:
            update_ok = False

        if update_ok:
            # remove old doc from current versions collection
            parent_q = {'_id':parent_doc['_id']}
            removeold_resp = original_collection.delete_one(parent_q)

    return new_doc_id
#'''

def update(doc_id, db_obj=None, remove_doc=False, update_pairs={}, new_meas_objects=[], meas_remove_indices=[], is_assay_request_update=False, is_assay_request_verify=False):
    """This is the main function that orchestrates a document update. It uses the is_assay_request_update and is_assay_request_verify args to discern what type of update is happening and uses that knowledge to decide which collections to use to pull the original document from, move the non-updated original document to, and insert the fully-updated document to. It calls the function _update_new_doc to actually update the original doc and then calls _update_databases to perform all aspects of the update in the MongoDB collections.

    args:
        * doc_id (str): The string representation of the MongoDB document ID for the document that the user wishes to update. This will be used to find the original doc (in the database collection) that will be copied and have updates applied.
        * db_obj (pymongo.database.Database): A pymongo database object that, once a collection has been selected, can be used to query.
        * remove_doc (bool): This option would be true if the user wishes to remove this assay doc from the database entirely. In this case, the current version in the main collection would be moved to the old_versions collection but no updated doc would be inserted into the main collection.
        * update_pairs (dict): A set of key-value pairs that represent the fields of the document that need to be updated and the new values that those fields should point to.
        * new_meas_objects (list of dict): A list of new measurement object dicts to add to the document's measurement results list.
        * meas_remove_indices (list of int): The list of indices for which elements of new_doc's measurement.results objects will be removed.
        * is_assay_request_update (bool): This arg specifies what type of update should happen. If this is False and is_assay_request_verify is False, the update will happen within the main collection. If this arg is True, the update will happen within the assay request collection.
        * is_assay_request_verify (bool): This arg specifies what type of update should happen. If this is False and is_assay_request_update is False, the update will happen within the main collection. If is_assay_request_update is False and this is True, the update will move a document from the assay requests collection to the main collection.

    returns:
        * bson.objectid.ObjectId. The MongoDB document ID of the new, fully-updated document that was added into the specified collection.
        * stE: The error message that arose while trying to update new_doc. This would happen if any of the updates to the document resulted in errors or if an invalid format/value was found.
    """
    # make copy of update_pairs dict in case values change; don't want that to change values in the func calling this
    update_pairs_copy = deepcopy(update_pairs)

    # get appropriate database collection names for the situation
    if is_assay_request_verify:
        update_from_coll_name = 'assay_requests' # find old doc in requests collection
        update_to_coll_name = '' # insert verified doc into main collection
        old_versions_coll_name = 'assay_requests_old_versions'
    elif is_assay_request_update:
        update_from_coll_name = 'assay_requests'
        update_to_coll_name = 'assay_requests' # insert updated doc into requests collection
        old_versions_coll_name = 'assay_requests_old_versions'
    else:
        update_from_coll_name = '' # find old doc in main collection
        update_to_coll_name = '' # insert updated doc into main colleciton
        old_versions_coll_name = 'old_versions'

    #print('UPDATING:','|',update_from_coll_name,'|',update_to_coll_name,'|',old_versions_coll_name,'|')
    if db_obj is None:
        db_obj = _create_db_obj()

    # find existing doc to update
    parent_doc = _get_existing_doc(doc_id, db_obj, update_from_coll_name)

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
    new_doc_id = _update_databases(new_doc, parent_doc, remove_doc, db_obj, update_from_coll_name, old_versions_coll_name, update_to_coll_name)

    return new_doc_id, ''


def add_to_query(field, comparison, value, query_object=None, query_string="", append_mode="", include_synonyms=True):
    """This function intakes the elements of a new query term (field, comparison, value, and append_mode) and either creates a new query containing that term, or adds the new term to an existing query using the existing query object argument or the existing query string argument.

    args:
        * field (str): The field name whose value is to be compared.
        * comparison (str): How to compare the specified value to the existing value for the specified field.
        * value (str): The value to be compared against.
        * query_object (dunetoolkit.Query) (optional): A pre-existing Query object that the new query term can be added to.
        * query_string (str) (optional): A pre-existing human-readable query string that can be loaded into a new Query object. This string MUST be in the format given by the UI's search page. That is, "<field1> <comparison1> <value1>\\n<append_mode>\\n<field2> <comparison2> <value2>\\n<append_mode>\\n..."
        * append_mode (str) (optional): How this new term should be added to an existing query (can be "AND" or "OR" or "", in which case this is the only term in the query).
        * include_synonyms (bool) (optional): Specifies whether or not to search for all synonyms of the specified value, in addition to that value, as opposed to searching only for the specified value.

    returns:
        * str. The human-readable version of the query that can be displayed to the user with the UI.
        * dict. The query dictionary in pymongo syntax. This dictionary can be directly used as a query for the database.
    """
    if query_object is None:
        query_object = Query(query_string)
    query_object.add_query_term(field, comparison, value, append_mode, include_synonyms)
    query_string = query_object.to_string()
    query_dict = query_object.to_query_language()
    return query_string, query_dict

def insert(sample_name, sample_description, data_reference, data_input_name, data_input_contact, data_input_date, db_obj=None, \
    grouping="", sample_source="", sample_id="", sample_owner_name="", sample_owner_contact="", \
    measurement_results=[], measurement_practitioner_name="", measurement_practitioner_contact="", \
    measurement_technique="", measurement_institution="", measurement_date=[], measurement_description="", \
    measurement_requestor_name="", measurement_requestor_contact="", data_input_notes="", coll_type=''):
    """This function intakes all the individual fields that make up an assay document in the database, combines them into a dictionary document, validates that dict, and inserts it into the specified colletion.

    args:
        * sample_name (str): A concise description of the sample.
        * sample_description (str): A detailed description of the sample.
        * data_reference (str): Reference for where the data came from.
        * data_input_name (str): Name of the person/people who performed data input.
        * data_input_contact (str): Email of the person who performed the data input (must be a valid email address).
        * data_input_date (list of str): A list of strings that can be converted into datetime objects. This represents the date or date range when the data was input.
        * db_obj (pymongo.database.Database): A pymongo database object that, once a collection has been selected, can be used to query.
        * grouping (str) (optional): Experiment name.
        * sample_source (str) (optional): Where the sample came from.
        * sample_id (str) (optional): Sample identification number or string.
        * sample_owner_name (str) (optional): Name of the person/people who own(s) the sample.
        * sample_owner_contact (str) (optional): Email of the person who owns the sample (must be a valid email address).
        * measurement_results (list of dict) (optional): List of measurement dictionaries that MUST contain the following fields: isotope, unit, type, value. The isotope field must be a (str) valid isotope name (e.g. K or Th). The unit must be a (str) valid unit type (e.g. ppm or g). The type must be a (str) representing the type of measurement, which must be one of: "measurement", "range", or "limit". The value must be a (list of str, int, or float) list of values that can ve converted into a float, which represent the values of the measurement. For a measurement of type "measurement" there should be two or three values: [central value, symmetric error] or [central value, positive asymmetric error, negative asymmetric error]. For a measurement of type "range" there should be tow or three values: [lower limit, upper limit] or [lower limit, upper limit, confidence level]. For a measurement of type "limit" there shoul be one to two values: [upper limit] or [upper limit, confidence level].
        * measurement_practitioner_name (str) (optional): Name of the person/people who performed the measurement.
        * measurement_practitioner_contact (str) (optional): Email of the person who performed the measurement (must be a valid email address).
        * measurement_technique (str) (optional): Measurement technique.
        * measurement_institution (str) (optional): Institution name.
        * measurement_date (list of str) (optional): A list of strings that can be converted into datetime objects. This represents the date or date range when the measurements happened.
        * measurement_description (str) (optional): Detailed measurement description.
        * measurement_requestor_name (str) (optional): Name of the person/people who coordinated the measurement.
        * measurement_requestor_contact (str) (optional): Email of the person who coordinated the measurement (must be a valid email).
        * data_input_notes (str) (optional): Data input notes (simplifications, assumptions).
        * coll_type (str) (optional): The type of the collection where the new doc should be inserted. If no value is specified, it is inserted into the main assay collection. If this argument is "assay_requests" then this doc is inserted as an assay request into the asasy requests collection.

    returns:
        * bson.objectid.ObjectId. The MongoDB ID of the new document that was added into the database. If the insertion was unsuccessful, this value is None.
        * str. The error message that arose while trying to update new_doc. This would happen if the document created with all the insert args is in valid or if the insertion of the new document resulted in an error.
    """
    # convert date string lists to date object lists
    data_input_date = convert_str_list_to_date(data_input_date)
    measurement_date = convert_str_list_to_date(measurement_date)
    if data_input_date is None:
        return None, 'a value in the data_input_date argument could not be converted to a datetime object'
    if measurement_date is None:
        return None, 'a value in the measurement_date argument could not be converted to a datetime object'

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
    print('DOC TO INSERT:',doc)

    # validate doc
    # TODO: verify that sample.ownder.contact, measurement.requestor.contact, measurement.practitioner.contact, and data_source.input.contact are valid emails
    validator = DuneValidator("whole_record")
    is_valid, error_message = validator.validate(doc) 
    if not is_valid:
        return None, error_message

    # perform doc insert
    if db_obj is None:
        db_obj = _create_db_obj()
    collection = _get_specified_collection(coll_type, db_obj)
    mongo_id = collection.insert_one(doc).inserted_id

    try:
        print("Successfully inserted doc with id:",mongo_id)
        msg = ''
    except:
        #print("Error inserting doc")
        mongo_id = None
        msg = 'unsuccessful insert into mongodb'

    return mongo_id, msg


def convert_str_to_date(date_str):
    """This function intakes a string, tries to convert it into a datetime object, and returns that datetime object.

    args:
        * date_str (str): The string that will be converted into a datetime object.

    returns:
        * datetime.datetime. The datetime object that resulted from the string. If the string could not be converted into a datetime object, then this returns None.
    """
    new_date_obj = None
    date_formats = ["%Y-%m-%d", "%Y/%m/%d", "%m-%d-%Y", "%m/%d/%Y", "%Y-%d-%m", "%Y/%d/%m", "%d-%m-%Y", "%d/%m/%Y"]
    for date_format in date_formats:
        try: 
            new_date_obj = datetime.strptime(date_str, date_format)
            break
        except:
            pass
    return new_date_obj


def convert_date_to_str(date_obj):
    """This function intakes a datetime object, tries to convert it into a string, and returns that string.

    args:
        * date_obj (datetime.datetime): The datetime object that will be converted into a string.

    returns:
        * str. The string that resulted from the datetime object. If the datetime object could not be converted into a string, then this returns an empty string.
    """
    try:
        new_date_str = date_obj.strftime("%Y-%m-%d")
    except:
        new_date_str = ''
    return new_date_str


def convert_str_list_to_date(str_list):
    """This function intakes a list of strings, tries to convert each one into a datetime object, and returns the list of datetime objects.

    args:
        * str_list (lit of str): The list of strings that will be converted into datetime objects.

    returns:
        * list of datetime.datetime. The list of datetime objects that each resulted from their corresponding strings. If any of the strings cannot be converted into datetime objects, then this function returns None.
    """
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

    search_parser = subparsers.add_parser('search', help='search for an assay in the database')
    search_parser.add_argument('--q', required=True, help='query to execute. *must be surrounded with single quotes, and use double quotes within dict*')

    query_append_parser = subparsers.add_parser('add_query_term', help='adds a new query term to an existing query')
    query_append_parser.add_argument('--field', type=str, required=True, choices=valid_fields, help='the field to compare the value of')
    query_append_parser.add_argument('--compare', type=str, required=True, choices=list(set(valid_str_comparisons+valid_num_comparisons)), \
        help='comparison operator to use to compare actual field value to given value')
    query_append_parser.add_argument('--val', type=str, required=True, help='the value to compare against. Can be a string or numeric')
    query_append_parser.add_argument('--mode', type=str, choices=["OR", "AND"], default="", required=False, help='optional argument to define append mode. If not present, defaults to "AND"')
    query_append_parser.add_argument('--q', type=str, default='', \
        help='existing query dictionary to add a new term to. If not present, creates a new query *must be surrounded with single quotes, and use double quotes within dict*')

    insert_parser = subparsers.add_parser('insert', help='inserts a new assay into the database')
    insert_parser.add_argument('--sample_name', type=str, required=True, help='concise sample description')
    insert_parser.add_argument('--sample_description', type=str, required=True, help='detailed sample description')
    insert_parser.add_argument('--data_reference', type=str, required=True, help='where the data came from')
    insert_parser.add_argument('--data_input_name', type=str, required=True, help='name of the person/people who performed data input')
    insert_parser.add_argument('--data_input_contact', type=str, required=True, help='email of the person/people who performed data input')
    insert_parser.add_argument('--data_input_date', nargs='*', required=True, help='series of date strings for dates of input')
    insert_parser.add_argument('--data_input_notes', type=str, default='', help='input simplifications, assumptions')
    insert_parser.add_argument('--grouping', type=str, default='', help='experiment name or similar')
    insert_parser.add_argument('--sample_source', type=str, default='', help='where the sample came from')
    insert_parser.add_argument('--sample_id', type=str, default='', help='identification number')
    insert_parser.add_argument('--sample_owner_name', type=str, default='', help='name of who owns the sample')
    insert_parser.add_argument('--sample_owner_contact', type=str, default='', help='email of who owns the sample')
    insert_parser.add_argument('--measurement_results', type=json.loads, nargs='*', default=[], help='series of measurement dictionaries (each must have the following fields: "type", "unit", "value", "isotope")')
    insert_parser.add_argument('--measurement_practitioner_name', type=str, default='', help='name of who did the measurement')
    insert_parser.add_argument('--measurement_practitioner_contact', type=str, default='', help='email of who did the measurement')
    insert_parser.add_argument('--measurement_technique', type=str, default='', help='technique name')
    insert_parser.add_argument('--measurement_institution', type=str, default='', help='institution name')
    insert_parser.add_argument('--measurement_date', nargs='*', default=[], help='series of date strings for dates of measurement')
    insert_parser.add_argument('--measurement_description', type=str, default='', help='detailed description')
    insert_parser.add_argument('--measurement_requestor_name', type=str, default='', help='name of who coordinated the measurement')
    insert_parser.add_argument('--measurement_requestor_contact', type=str, default='', help='email of who coordinated the measurement')

    update_parser = subparsers.add_parser('update', help='updates an existing assay in the database')
    update_parser.add_argument('--doc_id', type=str, required=True, help='the MongoDB id of the document in the database to update')
    update_parser.add_argument('--remove_doc', action='store_true', default=False, help='if present, remove the entire document from the database')
    update_parser.add_argument('--update_pairs', type=json.loads, default=[], help='series of keys to update and the new values to use')
    update_parser.add_argument('--new_meas_objects', type=json.loads, nargs='*', default=[], help='series of measurement results dictionaries to add to the document')
    update_parser.add_argument('--meas_remove_indices', nargs='*', default=[], help='series of indices (zero-indexed) corresponding to the document measurement result object to remove')

    args = vars(parser.parse_args())

    if args['subparser_name'] == 'search':
        result = search(args['q'])
    elif args['subparser_name'] == 'add_query_term':
        #TODO: add "include_synonyms" field
        q_str, q_dict = add_to_query(args['field'], args['compare'], args['val'], query_string=args['q'], append_mode=args['mode'])
        result = "QUERY STRING: "+str(q_str.replace('\n', '\\n'))+"\nQUERY DICT:   "+str(q_dict)
    elif args['subparser_name'] == 'insert':
        '''
        for i in range(len(args['measurement_results'])):
            args['measurement_results'][i] = json.loads(args['measurement_results'][i])
        '''
        result, error_msg = insert(args['sample_name'], \
            args['sample_description'], \
            args['data_reference'], \
            args['data_input_name'], \
            args['data_input_contact'], \
            args['data_input_date'], \
            data_input_notes=args['data_input_notes'], \
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
        if error_msg != '':
            print(error_msg)
        result = 'NEW DOC ID: '+str(result)
    elif args['subparser_name'] == 'update':
        '''
        update_keyval_pairs = {}
        for i in range(len(args['update_pairs'])):
            if i%2 == 0:
                update_key = args['update_pairs'][i]
                update_val = args['update_pairs'][i+1]
                update_keyval_pairs[update_key] = update_val
        '''
        result, error_msg = update(args['doc_id'], \
            remove_doc=args['remove_doc'], \
            update_pairs=args['update_pairs'], \
            new_meas_objects=args['new_meas_objects'], \
            meas_remove_indices=[ int(i) for i in args['meas_remove_indices'] ]
        )
        if result is None and error_msg == '':
            result = 'REMOVED.'
        elif result is not None:
            result = 'UPDATED DOC ID: '+str(result)
        else:
            result = error_msg
    else:
        print('You must enter an action to perform: search, insert, update, or add_query_term')
        result = None

    print(result)

