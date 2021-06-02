import os
import json
import pytest
import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
from test_auxiliary import set_up_db_for_test, teardown_db_for_test

from dunetoolkit import search_by_id, convert_str_to_date, convert_date_to_str

'''
testing set_ui_db
'''
'''
@pytest.mark.parametrize('db_name,coll_name,expected_success', [
    ('dune', 'dune_data', True), # proper dune strings
    ('radiopurity_data', 'example_data', True), # proper rp strings
    ('radiopurity_data', 'testing', True), # proper testing db strings
    ('dune_pytest_data', 'test_data', True), # proper pytest db strings
    ('pytest_database_bad', 'testing', False), # invalid db name
    ('dune', 'pytest_collection_bad', False), # invalid coll name
    ('radiopurity_data', 'pytest_collection_bad', False),
    ('dune', 'testing', False), # switched coll name
    ('radiopurity_data', 'dune_data', False) # switched coll name
])
def test_set_ui_db(db_name, coll_name, expected_success):
    successful_change = set_ui_db(db_name, coll_name)
    assert successful_change == expected_success
'''

'''
testing search_by_id
'''
@pytest.mark.parametrize('id_str,expected_resp', [
    ('5f08e8e3f35a4b437b3ad', None), # invalid ObjectID (not 24 characters)
    ('000000000000000000000000', None), # no results
    ('000000000000000000000001', { "_id" : ObjectId("000000000000000000000001"), "type" : "testing_doc" }), # valid doc
])
def test_search_by_id(id_str, expected_resp):
    os.environ['TOOLKIT_CONFIG_NAME'] = '../dunetoolkit/toolkit_config_test.json'

    # set up database to be updated
    teardown_db_for_test()
    db_obj = set_up_db_for_test(_get_docs())
    
    #successful_db_change = set_ui_db('dune_pytest_data', db_obj, coll_type='test_data')
    resp = search_by_id(id_str) #, db_obj)
    assert resp == expected_resp


'''
testing convert_date
'''
@pytest.mark.parametrize('date_str,expected_date_obj', [
    ('2018-08-09', datetime.datetime(2018, 8, 9)), # ymd month day both valid months dash
    ('2018/08/09', datetime.datetime(2018, 8, 9)), # ymd month day both valid months slash
    ('2010-08-21', datetime.datetime(2010, 8, 21)), # ymd dash
    ('2010/08/21', datetime.datetime(2010, 8, 21)), # ymd slash
    ('2008-21-08', datetime.datetime(2008, 8, 21)), # ydm dash
    ('2008/21/08', datetime.datetime(2008, 8, 21)), # ydm slash
    ('08-21-2020', datetime.datetime(2020, 8, 21)), # mdy dash
    ('08/21/2020', datetime.datetime(2020, 8, 21)), # mdy slash
    ('21-08-2000', datetime.datetime(2000, 8, 21)), # dmy dash
    ('21/08/2000', datetime.datetime(2000, 8, 21)), # dmy dash
    ('2000-08-21 10:30:05', None), # ydm with time --> INVALID WITH TIME
    ('10/10/20100', None), # invalid - bad year
    ('10-2010', None), # invalid - no day
    ('2020-10', None), # invalid - no day
    ('10-ab-2019', None) # invalid - alpha characters
])
def test_convert_str_to_date(date_str, expected_date_obj):
    date_obj = convert_str_to_date(date_str)
    assert date_obj == expected_date_obj


'''
testing convert_date
'''
@pytest.mark.parametrize('date_obj,expected_date_str', [
    (datetime.datetime(2018, 8, 9), '2018-08-09'), # ymd month day both valid months
    (datetime.datetime(2010, 8, 21), '2010-08-21'), # ymd
    (datetime.datetime(2000, 8, 21, 10, 30, 5), '2000-08-21'), # ydm with time
])
def test_convert_date_to_str(date_obj, expected_date_str):
    date_str = convert_date_to_str(date_obj)
    assert date_str == expected_date_str

"""
def get_mongodb_config_info():
    with open(os.environ.get('TOOLKIT_CONFIG_NAME'), 'r') as rf:
        config = json.load(rf)
        return config['mongodb_host'], config['mongodb_port'], config['database']

def teardown_db_for_test():
    db_host, db_port, db_name = get_mongodb_config_info()
    client = MongoClient(db_host, db_port)
    coll = client[db_name].assays
    old_versions_coll = client[db_name].assays_old_versions
    remove_resp = coll.delete_many({})
    resmove_oldversions_resp = old_versions_coll.delete_many({})
"""
def _get_docs():
    docs = [{ "_id" : ObjectId("000000000000000000000001"), "type" : "testing_doc" },
        { "_id" : ObjectId("000000000000000000000002"), "measurement" : { "description" : "", "practitioner" : { "name" : "ICI Tracerco", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "NAA", "results" : [ { "unit" : "ppb", "value" : [ 18, 2 ], "isotope" : "U-238", "type" : "measurement" }, { "unit" : "ppb", "value" : [ 59, 2 ], "isotope" : "Th-232", "type" : "measurement" }, { "unit" : "ppm", "value" : [ 0.78, 0.02 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2013, 7, 22, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Resin, Magnex, 2:1 Thiokol 308, RAL", "id" : "ILIAS UKDM #249", "owner" : { "name" : "", "contact" : "" }, "name" : "Resin, Magnex, 2:1 Thiokol 308", "source" : "" }, "type" : "measurement", "_version" : 1 },
        { "_id" : ObjectId("000000000000000000000003"), "measurement" : { "description" : "", "practitioner" : { "name" : "ICI Tracerco", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "NAA", "results" : [ { "unit" : "ppb", "value" : [ 3 ], "isotope" : "U-238", "type" : "limit" }, { "unit" : "ppb", "value" : [ 1 ], "isotope" : "Th-232", "type" : "limit" }, { "unit" : "ppm", "value" : [ 8.9, 0.2 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2016, 7, 14, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Rexalite, copper removed", "id" : "ILIAS UKDM #266", "owner" : { "name" : "", "contact" : "" }, "name" : "Rexalite, copper removed", "source" : "" }, "type" : "measurement", "_version" : 1 },
        { "_id" : ObjectId("000000000000000000000004"), "measurement" : { "description" : "", "practitioner" : { "name" : "RAL", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "AA", "results" : [ { "unit" : "ppm", "value" : [ 15 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2016, 7, 14, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Salt, ICI, pure dried vacuum", "id" : "ILIAS UKDM #273", "owner" : { "name" : "", "contact" : "" }, "name" : "Salt, ICI, pure dried vacuum", "source" : "" }, "type" : "measurement", "_version" : 1 },
        { "_id" : ObjectId("000000000000000000000005"), "measurement" : { "description" : "Lu < 1ppb, Rb < 10ppb", "practitioner" : { "name" : "Charles Evans/Cascade Scientific", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "GD-MS", "results" : [ { "unit" : "ppb", "value" : [ 1 ], "isotope" : "U-238", "type" : "limit" }, { "unit" : "ppb", "value" : [ 1 ], "isotope" : "Th-232", "type" : "limit" }, { "unit" : "ppm", "value" : [ 0.22 ], "isotope" : "K-40", "type" : "limit" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2013, 7, 22, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Si", "id" : "ILIAS UKDM #279", "owner" : { "name" : "", "contact" : "" }, "name" : "Si", "source" : "" }, "type" : "measurement", "_version" : 1 },
        { "_id" : ObjectId("000000000000000000000006"), "measurement" : { "description" : "", "practitioner" : { "name" : "Supplier's data", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "?", "results" : [ { "unit" : "ppm", "value" : [ 0.03 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2013, 1, 30, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Silica fibre, TSL, 'Spectrosil'", "id" : "ILIAS UKDM #289", "owner" : { "name" : "", "contact" : "" }, "name" : "Silica fibre, TSL, 'Spectrosil'", "source" : "" }, "type" : "measurement", "_version" : 1 }
    ]
    return docs


