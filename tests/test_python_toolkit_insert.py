import pytest
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime

from dunetoolkit import set_ui_db, search_by_id, update, search, add_to_query, insert, convert_str_to_date, convert_date_to_str
#from python_mongo_toolkit import set_ui_db
#from python_mongo_toolkit import search_by_id
#from python_mongo_toolkit import update
#from python_mongo_toolkit import search
#from python_mongo_toolkit import add_to_query
#from python_mongo_toolkit import insert
#from python_mongo_toolkit import convert_str_to_date
#from python_mongo_toolkit import convert_date_to_str


def test_insert_partial_doc():
    # set up database
    teardown_db_for_test()
    set_up_db_for_test()
    successful_db_change = set_ui_db('dune_pytest_data', 'test_data')

    # perform insert
    sample_name = 'testing sample name'
    sample_description = 'testing sample description'
    data_reference = 'testing data reference'
    data_input_name = 'testing data input name'
    data_input_contact = 'testing data input contact'
    data_input_date = ['2020-02-20']
    measurement_description = 'testing measurement description'
    data_input_notes = 'testing data input notes'

    new_doc_id, error_msg = insert(sample_name, sample_description, data_reference, data_input_name, data_input_contact, data_input_date, \
    measurement_description=measurement_description, data_input_notes=data_input_notes)
    assert new_doc_id != None, error_msg

    new_doc = search_by_id(new_doc_id)
    assert new_doc['sample']['name'] == sample_name
    assert new_doc['sample']['description'] == sample_description
    assert new_doc['data_source']['reference'] == data_reference
    assert new_doc['data_source']['input']['name'] == data_input_name
    assert new_doc['data_source']['input']['contact'] == data_input_contact
    assert [ date_obj.strftime('%Y-%m-%d') for date_obj in new_doc['data_source']['input']['date'] ] == data_input_date
    assert new_doc['grouping'] == ''
    assert new_doc['sample']['source'] == ''
    assert new_doc['sample']['id'] == ''
    assert new_doc['sample']['owner']['name'] == ''
    assert new_doc['sample']['owner']['contact'] == ''
    assert new_doc['measurement']['results'] == []
    assert new_doc['measurement']['practitioner']['name'] == ''
    assert new_doc['measurement']['practitioner']['contact'] == ''
    assert new_doc['measurement']['technique'] == ''
    assert new_doc['measurement']['institution'] == ''
    assert new_doc['measurement']['date'] == []
    assert new_doc['measurement']['description'] == measurement_description
    assert new_doc['measurement']['requestor']['name'] == ''
    assert new_doc['measurement']['requestor']['contact'] == ''
    assert new_doc['data_source']['input']['notes'] == data_input_notes


def test_insert_complete_doc():
    # set up database
    teardown_db_for_test()
    set_up_db_for_test()
    successful_db_change = set_ui_db('dune_pytest_data', 'test_data')

    # perform insert
    sample_name = 'testing sample name'
    sample_description = 'testing sample description'
    data_reference = 'testing data reference'
    data_input_name = 'testing data input name'
    data_input_contact = 'testing data input contact'
    data_input_date = ['2020-02-20']
    grouping = 'testing grouping'
    sample_source = 'testing sample source'
    sample_id = 'testing sample id'
    sample_owner_name = 'testing sample owner name'
    sample_owner_contact = 'testing sample owner contact'
    measurement_results = [{'isotope':'K-40', 'type':'measurement', 'unit':'ppm', 'value':[1.3,3.1]}, {'isotope':'U-235', 'type':'limit', 'unit':'g', 'value':[555,900]}]
    measurement_practitioner_name = 'testing measurement practitioner name'
    measurement_practitioner_contact = 'testing measurement practitioner contact'
    measurement_technique = 'testing measurement technique'
    measurement_institution = 'testing measurement institution'
    measurement_date = ['2020-20-02','1940-20-10']
    measurement_description = 'testing measurement description'
    measurement_requestor_name = 'testing measurement requestor name'
    measurement_requestor_contact = 'testing measurement requestor contact'
    data_input_notes = 'testing data input notes'

    new_doc_id, error_msg = insert(sample_name, sample_description, data_reference, data_input_name, data_input_contact, data_input_date, \
    grouping, sample_source, sample_id, sample_owner_name, sample_owner_contact, \
    measurement_results, measurement_practitioner_name, measurement_practitioner_contact, \
    measurement_technique, measurement_institution, measurement_date, measurement_description, \
    measurement_requestor_name, measurement_requestor_contact, data_input_notes)
    assert new_doc_id != None, error_msg

    new_doc = search_by_id(new_doc_id)
    assert new_doc['sample']['name'] == sample_name
    assert new_doc['sample']['description'] == sample_description
    assert new_doc['data_source']['reference'] == data_reference
    assert new_doc['data_source']['input']['name'] == data_input_name
    assert new_doc['data_source']['input']['contact'] == data_input_contact
    assert [ date_obj.strftime('%Y-%m-%d') for date_obj in new_doc['data_source']['input']['date'] ] == data_input_date
    assert new_doc['grouping'] == grouping
    assert new_doc['sample']['source'] == sample_source
    assert new_doc['sample']['id'] == sample_id
    assert new_doc['sample']['owner']['name'] == sample_owner_name
    assert new_doc['sample']['owner']['contact'] == sample_owner_contact
    assert new_doc['measurement']['results'] == measurement_results
    assert new_doc['measurement']['practitioner']['name'] == measurement_practitioner_name
    assert new_doc['measurement']['practitioner']['contact'] == measurement_practitioner_contact
    assert new_doc['measurement']['technique'] == measurement_technique
    assert new_doc['measurement']['institution'] == measurement_institution
    assert [ date_obj.strftime('%Y-%d-%m') for date_obj in new_doc['measurement']['date'] ] == measurement_date
    assert new_doc['measurement']['description'] == measurement_description
    assert new_doc['measurement']['requestor']['name'] == measurement_requestor_name
    assert new_doc['measurement']['requestor']['contact'] == measurement_requestor_contact
    assert new_doc['data_source']['input']['notes'] == data_input_notes


#meas values are strings (string numbers, string alpha)
def test_insert_meas_values_strings_a():
    # set up database
    teardown_db_for_test()
    set_up_db_for_test()
    successful_db_change = set_ui_db('dune_pytest_data', 'test_data')

    # perform insert
    sample_name = 'testing sample name'
    sample_description = 'testing sample description'
    data_reference = 'testing data reference'
    data_input_name = 'testing data input name'
    data_input_contact = 'testing data input contact'
    data_input_date = ['2020-02-20']
    measurement_results = [{'isotope':'K-40', 'type':'measurement', 'unit':'ppm', 'value':[1.3,3.1]}]

    new_doc_id, error_msg = insert(sample_name, sample_description, data_reference, data_input_name, data_input_contact, data_input_date, \
    measurement_results=measurement_results)
    assert new_doc_id != None, error_msg

    new_doc = search_by_id(new_doc_id)
    assert new_doc['sample']['name'] == sample_name
    assert new_doc['sample']['description'] == sample_description
    assert new_doc['data_source']['reference'] == data_reference
    assert new_doc['data_source']['input']['name'] == data_input_name
    assert new_doc['data_source']['input']['contact'] == data_input_contact
    assert [ date_obj.strftime('%Y-%m-%d') for date_obj in new_doc['data_source']['input']['date'] ] == data_input_date
    assert new_doc['measurement']['results'] == measurement_results


def test_insert_meas_values_strings_b():
    # set up database
    teardown_db_for_test()
    set_up_db_for_test()
    successful_db_change = set_ui_db('dune_pytest_data', 'test_data')

    # perform insert
    sample_name = 'testing sample name'
    sample_description = 'testing sample description'
    data_reference = 'testing data reference'
    data_input_name = 'testing data input name'
    data_input_contact = 'testing data input contact'
    data_input_date = ['2020-02-20']
    measurement_results = [{'isotope':'K-40', 'type':'measurement', 'unit':'ppm', 'value':['a','b']}]

    new_doc_id, error_msg = insert(sample_name, sample_description, data_reference, data_input_name, data_input_contact, data_input_date, \
    measurement_results=measurement_results)
    assert new_doc_id == None


def test_insert_bad_date_a():
    # set up database
    teardown_db_for_test()
    set_up_db_for_test()
    successful_db_change = set_ui_db('dune_pytest_data', 'test_data')

    # perform insert
    sample_name = 'testing sample name'
    sample_description = 'testing sample description'
    data_reference = 'testing data reference'
    data_input_name = 'testing data input name'
    data_input_contact = 'testing data input contact'
    data_input_date = ['testing']

    new_doc_id, error_msg = insert(sample_name, sample_description, data_reference, data_input_name, data_input_contact, data_input_date)
    assert new_doc_id == None


def test_insert_bad_date_b():
    # set up database
    teardown_db_for_test()
    set_up_db_for_test()
    successful_db_change = set_ui_db('dune_pytest_data', 'test_data')

    # perform insert
    sample_name = 'testing sample name'
    sample_description = 'testing sample description'
    data_reference = 'testing data reference'
    data_input_name = 'testing data input name'
    data_input_contact = 'testing data input contact'
    data_input_date = '2020-02-20'

    new_doc_id, error_msg = insert(sample_name, sample_description, data_reference, data_input_name, data_input_contact, data_input_date)
    assert new_doc_id == None


def test_insert_bad_date_c():
    # set up database
    teardown_db_for_test()
    set_up_db_for_test()
    successful_db_change = set_ui_db('dune_pytest_data', 'test_data')

    # perform insert
    sample_name = 'testing sample name'
    sample_description = 'testing sample description'
    data_reference = 'testing data reference'
    data_input_name = 'testing data input name'
    data_input_contact = 'testing data input contact'
    data_input_date = ['2020-02-20']
    measurement_date = ['testing']

    new_doc_id, error_msg = insert(sample_name, sample_description, data_reference, data_input_name, data_input_contact, data_input_date, \
    measurement_date=measurement_date)
    assert new_doc_id == None


def test_insert_bad_date_d():
    # set up database
    teardown_db_for_test()
    set_up_db_for_test()
    successful_db_change = set_ui_db('dune_pytest_data', 'test_data')

    # perform insert
    sample_name = 'testing sample name'
    sample_description = 'testing sample description'
    data_reference = 'testing data reference'
    data_input_name = 'testing data input name'
    data_input_contact = 'testing data input contact'
    data_input_date = ['2020-02-20']
    measurement_date = '2020-02-20'

    new_doc_id, error_msg = insert(sample_name, sample_description, data_reference, data_input_name, data_input_contact, data_input_date, \
    measurement_date=measurement_date)
    assert new_doc_id == None



def set_up_db_for_test():
    client = MongoClient('localhost', 27017)
    coll = client.dune_pytest_data.test_data
    coll.insert_one({ "_id" : ObjectId("000000000000000000000001"), "type" : "testing_doc" })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000002"), "measurement" : { "description" : "", "practitioner" : { "name" : "ICI Tracerco", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "NAA", "results" : [ { "unit" : "ppb", "value" : [ 18, 2 ], "isotope" : "U-238", "type" : "measurement" }, { "unit" : "ppb", "value" : [ 59, 2 ], "isotope" : "Th-232", "type" : "measurement" }, { "unit" : "ppm", "value" : [ 0.78, 0.02 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2013, 7, 22, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Resin, Magnex, 2:1 Thiokol 308, RAL", "id" : "ILIAS UKDM #249", "owner" : { "name" : "", "contact" : "" }, "name" : "Resin, Magnex, 2:1 Thiokol 308", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000003"), "measurement" : { "description" : "", "practitioner" : { "name" : "ICI Tracerco", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "NAA", "results" : [ { "unit" : "ppb", "value" : [ 3 ], "isotope" : "U-238", "type" : "limit" }, { "unit" : "ppb", "value" : [ 1 ], "isotope" : "Th-232", "type" : "limit" }, { "unit" : "ppm", "value" : [ 8.9, 0.2 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2016, 7, 14, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Rexalite, copper removed", "id" : "ILIAS UKDM #266", "owner" : { "name" : "", "contact" : "" }, "name" : "Rexalite, copper removed", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000004"), "measurement" : { "description" : "", "practitioner" : { "name" : "RAL", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "AA", "results" : [ { "unit" : "ppm", "value" : [ 15 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2016, 7, 14, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Salt, ICI, pure dried vacuum", "id" : "ILIAS UKDM #273", "owner" : { "name" : "", "contact" : "" }, "name" : "Salt, ICI, pure dried vacuum", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000005"), "measurement" : { "description" : "Lu < 1ppb, Rb < 10ppb", "practitioner" : { "name" : "Charles Evans/Cascade Scientific", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "GD-MS", "results" : [ { "unit" : "ppb", "value" : [ 1 ], "isotope" : "U-238", "type" : "limit" }, { "unit" : "ppb", "value" : [ 1 ], "isotope" : "Th-232", "type" : "limit" }, { "unit" : "ppm", "value" : [ 0.22 ], "isotope" : "K-40", "type" : "limit" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2013, 7, 22, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Si", "id" : "ILIAS UKDM #279", "owner" : { "name" : "", "contact" : "" }, "name" : "Si", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000006"), "measurement" : { "description" : "", "practitioner" : { "name" : "Supplier's data", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "?", "results" : [ { "unit" : "ppm", "value" : [ 0.03 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2013, 1, 30, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Silica fibre, TSL, 'Spectrosil'", "id" : "ILIAS UKDM #289", "owner" : { "name" : "", "contact" : "" }, "name" : "Silica fibre, TSL, 'Spectrosil'", "source" : "" }, "type" : "measurement", "_version" : 1 })


def teardown_db_for_test():
    client = MongoClient('localhost', 27017)
    coll = client.dune_pytest_data.test_data
    old_versions_coll = client.dune_pytest_data.test_data_oldversions
    remove_resp = coll.delete_many({})
    resmove_oldversions_resp = old_versions_coll.delete_many({})

def query_for_all_docs():
    client = MongoClient('localhost', 27017)
    coll = client.dune_pytest_data.test_data
    old_versions_coll = client.dune_pytest_data.test_data_oldversions
    all_docs = list(coll.find({}))
    return all_docs

