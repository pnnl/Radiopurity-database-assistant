import pytest
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime
import re

from python_mongo_toolkit import set_ui_db
from python_mongo_toolkit import search_by_id
from python_mongo_toolkit import update_with_versions
from python_mongo_toolkit import search
from python_mongo_toolkit import add_to_query
from python_mongo_toolkit import insert
from python_mongo_toolkit import convert_str_to_date
from python_mongo_toolkit import convert_date_to_str
from python_mongo_toolkit import _validate_measurement_results_data


def test_search():
    # set up database to be updated
    teardown_db_for_test()
    set_up_db_for_test()
    successful_db_change = set_ui_db('dune_pytest_data', 'test_data')

    q = {'measurement.technique': re.compile('^NAA$', re.IGNORECASE)}
    docs = search(q)

    for doc in docs:
        assert doc['measurement']['technique'] == 'NAA'


def test_search_isotope():
    # set up database to be updated
    teardown_db_for_test()
    set_up_db_for_test()
    successful_db_change = set_ui_db('dune_pytest_data', 'test_data')

    q = {'$and': [{'measurement.results': {'$elemMatch': {'$and': [{'isotope': re.compile('^Th-232$', re.IGNORECASE)}, {'type': re.compile('^limit$', re.IGNORECASE)}]}}}]}
    docs = search(q)

    for doc in docs:
        isotopes_and_their_meas_types = [ (ele['isotope'], ele['type']) for ele in doc['measurement']['results'] ]
        assert ('Th-232','limit') in isotopes_and_their_meas_types


def test_search_all():
    # set up database to be updated
    teardown_db_for_test()
    set_up_db_for_test()
    successful_db_change = set_ui_db('dune_pytest_data', 'test_data')

    q = {'$or': [{'grouping': re.compile('^.*COPPEr.*$', re.IGNORECASE)}, {'sample.name': re.compile('^.*COPPEr.*$', re.IGNORECASE)}, {'sample.description': re.compile('^.*COPPEr.*$', re.IGNORECASE)}, {'sample.source': re.compile('^.*COPPEr.*$', re.IGNORECASE)}, {'sample.id': re.compile('^.*COPPEr.*$', re.IGNORECASE)}, {'measurement.technique': re.compile('^.*COPPEr.*$', re.IGNORECASE)}, {'measurement.description': re.compile('^.*COPPEr.*$', re.IGNORECASE)}, {'data_source.reference': re.compile('^.*COPPEr.*$', re.IGNORECASE)}, {'data_source.input.notes': re.compile('^.*COPPEr.*$', re.IGNORECASE)}]}
    docs = search(q)

    for doc in docs:
        copper_found = False
        if 'copper' in doc['grouping'].lower():
            copper_found = True
        elif 'copper' in doc['sample']['name'].lower():
            copper_found = True
        elif 'copper' in doc['sample']['description'].lower():
            copper_found = True
        elif 'copper' in doc['sample']['source'].lower():
            copper_found = True
        elif 'copper' in doc['sample']['id'].lower():
            copper_found = True
        elif 'copper' in doc['measurement']['technique'].lower():
            copper_found = True
        elif 'copper' in doc['measurement']['description'].lower():
            copper_found = True
        elif 'copper' in doc['data_source']['reference'].lower():
            copper_found = True
        elif 'copper' in doc['data_source']['input']['notes'].lower():
            copper_found = True
        assert copper_found


def set_up_db_for_test():
    client = MongoClient('localhost', 27017)
    coll = client.dune_pytest_data.test_data
    coll.insert_one({ "_id" : ObjectId("000000000000000000000001"), "type" : "testing_doc" })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000002"), "measurement" : { "description" : "", "practitioner" : { "name" : "ICI Tracerco", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "NAA", "results" : [ { "unit" : "ppb", "value" : [ 18, 2 ], "isotope" : "U-238", "type" : "measurement" }, { "unit" : "ppb", "value" : [ 59, 2 ], "isotope" : "Th-232", "type" : "measurement" }, { "unit" : "ppm", "value" : [ 0.78, 0.02 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2013, 7, 22, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Resin, Magnex, 2:1 Thiokol 308, RAL", "id" : "ILIAS UKDM #249", "owner" : { "name" : "", "contact" : "" }, "name" : "Resin, Magnex, 2:1 Thiokol 308", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000003"), "measurement" : { "description" : "", "practitioner" : { "name" : "ICI Tracerco", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "NAA", "results" : [ { "unit" : "ppb", "value" : [ 3 ], "isotope" : "U-238", "type" : "limit" }, { "unit" : "ppb", "value" : [ 1 ], "isotope" : "Th-232", "type" : "limit" }, { "unit" : "ppm", "value" : [ 8.9, 0.2 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2016, 7, 14, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Rexalite, copper removed", "id" : "ILIAS UKDM #266", "owner" : { "name" : "", "contact" : "" }, "name" : "Rexalite, copper removed", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000004"), "measurement" : { "description" : "", "practitioner" : { "name" : "RAL", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "AA", "results" : [ { "unit" : "ppm", "value" : [ 15 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2016, 7, 14, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Salt, ICI, pure dried vacuum", "id" : "ILIAS UKDM #273", "owner" : { "name" : "", "contact" : "" }, "name" : "Salt, ICI, pure dried vacuum", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000005"), "measurement" : { "description" : "Lu < 1ppb, Rb < 10ppb", "practitioner" : { "name" : "Charles Evans/Cascade Scientific", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "GD-MS", "results" : [ { "unit" : "ppb", "value" : [ 1 ], "isotope" : "U-238", "type" : "limit" }, { "unit" : "ppb", "value" : [ 1 ], "isotope" : "Th-232", "type" : "limit" }, { "unit" : "ppm", "value" : [ 0.22 ], "isotope" : "K-40", "type" : "limit" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2013, 7, 22, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "copper COPPER" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Si", "id" : "ILIAS UKDM #279", "owner" : { "name" : "", "contact" : "" }, "name" : "Si", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000006"), "measurement" : { "description" : "", "practitioner" : { "name" : "Supplier's data", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "?", "results" : [ { "unit" : "ppm", "value" : [ 0.03 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2013, 1, 30, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "this has a COPPER test phrase" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Silica fibre, TSL, 'Spectrosil'", "id" : "ILIAS UKDM #289", "owner" : { "name" : "", "contact" : "" }, "name" : "Silica fibre, TSL, 'Spectrosil'", "source" : "" }, "type" : "measurement", "_version" : 1 })

def teardown_db_for_test():
    client = MongoClient('localhost', 27017)
    coll = client.dune_pytest_data.test_data
    old_versions_coll = client.dune_pytest_data.test_data_oldversions
    remove_resp = coll.delete_many({})
    resmove_oldversions_resp = old_versions_coll.delete_many({})



