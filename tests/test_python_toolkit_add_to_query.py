import os
import pytest
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime
import re

from dunetoolkit import search, add_to_query

# OTHER POSSIBLE TESTS
# try to add same field twice? w same val/compare? w diff val/compare?
# add every single field
#TODO query with dates!!!
# q starts with measurement.results object, adds another measurement.results object (AND, OR)
# q starts with measurement.results object, adds non-measurement.results object (AND, OR)
# q starts with measurement.results object, adds non, adds another measurement.results object (AND, OR)
# q starts with non, adds measurement.results object, adds another measurement.results object (AND, OR)
# q starts with non, adds measurement.results object, adds another non (AND, OR)


def test_add_to_query_with_search_a():
    os.environ['TOOLKIT_CONFIG_NAME'] = '../dunetoolkit/toolkit_config_test.json'

    # set up database to be updated
    teardown_db_for_test()
    db_obj = set_up_db_for_test()

    field = 'grouping'
    comp = 'contains'
    val = 'testing'
    q_string, q_dict = add_to_query(field=field, comparison=comp, value=val, query_string='')
    assert q_dict == {'grouping':{'$regex':re.compile('^.*testing.*$',re.IGNORECASE)}}
    
    field = 'measurement.results.isotope'
    comp = 'eq'
    val = 'U'
    append_mode = 'OR'
    q_string, q_dict = add_to_query(field=field, comparison=comp, value=val, query_string=q_string, append_mode=append_mode)
    assert q_dict == {'$or': [{'grouping': {'$regex': re.compile('^.*testing.*$', re.IGNORECASE)}}, {'$or': [{'measurement.results': {'$elemMatch': {'isotope': {'$regex': re.compile('^Uranium$', re.IGNORECASE)}}}}, {'measurement.results': {'$elemMatch': {'isotope': {'$regex': re.compile('^U$', re.IGNORECASE)}}}}]}]}

    field = 'measurement.results.value'
    comp = 'gte'
    val = 100.0
    append_mode = 'AND'
    q_string, q_dict = add_to_query(field=field, comparison=comp, value=val, query_string=q_string, append_mode=append_mode)
    assert q_dict == {'$or': [{'grouping': {'$regex': re.compile('^.*testing.*$', re.IGNORECASE)}}, {'$or': [{'measurement.results': {'$elemMatch': {'type': {'$regex': re.compile('^measurement$', re.IGNORECASE)}, 'value.0': {'$gte': 100.0}, 'isotope': {'$regex': re.compile('^Uranium$', re.IGNORECASE)}}}}, {'measurement.results': {'$elemMatch': {'type': {'$regex': re.compile('^measurement$', re.IGNORECASE)}, 'value.0': {'$gte': 100.0}, 'isotope': {'$regex': re.compile('^U$', re.IGNORECASE)}}}}, {'measurement.results': {'$elemMatch': {'type': {'$regex': re.compile('^range$', re.IGNORECASE)}, 'value.0': {'$gte': 100.0}, 'isotope': {'$regex': re.compile('^Uranium$', re.IGNORECASE)}}}}, {'measurement.results': {'$elemMatch': {'type': {'$regex': re.compile('^range$', re.IGNORECASE)}, 'value.0': {'$gte': 100.0}, 'isotope': {'$regex': re.compile('^U$', re.IGNORECASE)}}}}]}]}

    field = 'measurement.results.unit'
    comp = 'eq'
    val = 'ppt'
    append_mode = 'AND'
    q_string, q_dict = add_to_query(field=field, comparison=comp, value=val, query_string=q_string, append_mode=append_mode)
    assert q_dict == {'$or': [{'grouping': {'$regex': re.compile('^.*testing.*$', re.IGNORECASE)}}, {'$or': [{'measurement.results': {'$elemMatch': {'type': {'$regex': re.compile('^measurement$', re.IGNORECASE)}, 'value.0': {'$gte': 100.0}, 'isotope': {'$regex': re.compile('^Uranium$', re.IGNORECASE)}, 'unit': {'$regex': re.compile('^ppt$', re.IGNORECASE)}}}}, {'measurement.results': {'$elemMatch': {'type': {'$regex': re.compile('^measurement$', re.IGNORECASE)}, 'value.0': {'$gte': 100.0}, 'isotope': {'$regex': re.compile('^U$', re.IGNORECASE)}, 'unit': {'$regex': re.compile('^ppt$', re.IGNORECASE)}}}}, {'measurement.results': {'$elemMatch': {'type': {'$regex': re.compile('^range$', re.IGNORECASE)}, 'value.0': {'$gte': 100.0}, 'isotope': {'$regex': re.compile('^Uranium$', re.IGNORECASE)}, 'unit': {'$regex': re.compile('^ppt$', re.IGNORECASE)}}}}, {'measurement.results': {'$elemMatch': {'type': {'$regex': re.compile('^range$', re.IGNORECASE)}, 'value.0': {'$gte': 100.0}, 'isotope': {'$regex': re.compile('^U$', re.IGNORECASE)}, 'unit': {'$regex': re.compile('^ppt$', re.IGNORECASE)}}}}]}]}

    search_resp = search(q_dict) #, db_obj)
    # NOTE: no docs match this at the moment
    for doc in search_resp:
        grouping = doc['grouping']
        valid_meas_found = False
        for meas_result in doc['measurement']['results']:
            if len(meas_result['value']) > 0:
                if meas_result['value'][0] >= 100 and meas_result['isotope'] == 'U' and meas_result['unit'] == 'ppt':
                    valid_meas_found = True
        assert 'testing' in grouping or valid_meas_found

def test_add_to_query_bad_field_name():
    field = 'test' # not a valid field name
    comp = 'contains'
    val = 'testing'
    q_string, q_dict = add_to_query(field=field, comparison=comp, value=val, query_string='')
    assert q_dict == {}

def test_add_to_query_bad_comparison():
    field = 'grouping'
    comp = 'test' # not a valid comparator; must be one of ['contains', 'notcontains', 'eq', 'gt', 'gte', 'lt', 'lte']
    val = 'testing'
    q_string, q_dict = add_to_query(field=field, comparison=comp, value=val, query_string='')
    assert q_dict == {}

def test_add_to_query_bad_comparison_num_comp_on_str():
    field = 'grouping'
    comp = 'gt' # not a string comparator
    val = 'testing'
    q_string, q_dict = add_to_query(field=field, comparison=comp, value=val, query_string='')
    assert q_dict == {}

def test_add_to_query_bad_comparison_str_comp_on_num():
    field = 'measurement.results.value'
    comp = 'contains' # not a numerical comparator
    val = 10
    q_string, q_dict = add_to_query(field=field, comparison=comp, value=val, query_string='')
    assert q_dict == {}

def test_add_to_query_bad_val():
    field = 'measurement.results.value'
    comp = 'gt'
    val = 'test' # must be num, not str
    q_string, q_dict = add_to_query(field=field, comparison=comp, value=val, query_string='')
    assert q_dict == {}

def test_add_to_query_bad_append_mode():
    field = 'grouping'
    comp = 'contains'
    val = 'testing'
    append_mode = 'testing' # must be one of ['AND', 'OR']
    q_string, q_dict = add_to_query(field=field, comparison=comp, value=val, query_string='', append_mode='testing')
    assert q_dict == {}

def get_mongodb_config_info():
    with open(os.environ.get('TOOLKIT_CONFIG_NAME'), 'r') as rf:
        config = json.load(rf)
        return config['mongodb_host'], config['mongodb_port'], config['database']

def set_up_db_for_test():
    db_host, db_port, db_name = get_mongodb_config_info()
    client = MongoClient(db_host, db_port)
    db_obj = client[db_name]
    coll = db_obj.assays
    coll.insert_one({ "_id" : ObjectId("000000000000000000000001"), "type" : "testing_doc" })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000002"), "measurement" : { "description" : "", "practitioner" : { "name" : "ICI Tracerco", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "NAA", "results" : [ { "unit" : "ppb", "value" : [ 18, 2 ], "isotope" : "U-238", "type" : "measurement" }, { "unit" : "ppb", "value" : [ 59, 2 ], "isotope" : "Th-232", "type" : "measurement" }, { "unit" : "ppm", "value" : [ 0.78, 0.02 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2013, 7, 22, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Resin, Magnex, 2:1 Thiokol 308, RAL", "id" : "ILIAS UKDM #249", "owner" : { "name" : "", "contact" : "" }, "name" : "Resin, Magnex, 2:1 Thiokol 308", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000003"), "measurement" : { "description" : "", "practitioner" : { "name" : "ICI Tracerco", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "NAA", "results" : [ { "unit" : "ppb", "value" : [ 3 ], "isotope" : "U-238", "type" : "limit" }, { "unit" : "ppb", "value" : [ 1 ], "isotope" : "Th-232", "type" : "limit" }, { "unit" : "ppm", "value" : [ 8.9, 0.2 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2016, 7, 14, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Rexalite, copper removed", "id" : "ILIAS UKDM #266", "owner" : { "name" : "", "contact" : "" }, "name" : "Rexalite, copper removed", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000004"), "measurement" : { "description" : "", "practitioner" : { "name" : "RAL", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "AA", "results" : [ { "unit" : "ppm", "value" : [ 15 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2016, 7, 14, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Salt, ICI, pure dried vacuum", "id" : "ILIAS UKDM #273", "owner" : { "name" : "", "contact" : "" }, "name" : "Salt, ICI, pure dried vacuum", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000005"), "measurement" : { "description" : "Lu < 1ppb, Rb < 10ppb", "practitioner" : { "name" : "Charles Evans/Cascade Scientific", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "GD-MS", "results" : [ { "unit" : "ppb", "value" : [ 1 ], "isotope" : "U-238", "type" : "limit" }, { "unit" : "ppb", "value" : [ 1 ], "isotope" : "Th-232", "type" : "limit" }, { "unit" : "ppm", "value" : [ 0.22 ], "isotope" : "K-40", "type" : "limit" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2013, 7, 22, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Si", "id" : "ILIAS UKDM #279", "owner" : { "name" : "", "contact" : "" }, "name" : "Si", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000006"), "measurement" : { "description" : "", "practitioner" : { "name" : "Supplier's data", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "?", "results" : [ { "unit" : "ppm", "value" : [ 0.03 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2013, 1, 30, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Silica fibre, TSL, 'Spectrosil'", "id" : "ILIAS UKDM #289", "owner" : { "name" : "", "contact" : "" }, "name" : "Silica fibre, TSL, 'Spectrosil'", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("5f1a05bc9aa72b9b0aaedfe4"), "specification" : "3.00", "grouping" : "DUNE", "type" : "assay", "sample" : { "name" : "Rock Sample 1", "description" : "DUNE Ross - #6 Winze", "source" : "DUNE Ross - #6 Winze", "id" : "Sample 1", "owner" : { "name" : "Juergen Reichenbacher", "contact" : "Juergen.Reichenbacher@sdsmt.edu" } }, "measurement" : { "description" : "", "requestor" : { "name" : "", "contact" : "" }, "practitioner" : { "name" : "Juergen Reichenbacher", "contact" : "Juergen.Reichenbacher@sdsmt.edu" }, "technique" : "Ge Counter", "institution" : "SDSM&T", "date" : [ ], "results" : [ { "isotope" : "U-238", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 35.6, 5 ] }, { "isotope" : "Ra-226", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 66, 0.8 ] }, { "isotope" : "Th-232", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 48.9, 0.4 ] }, { "isotope" : "K-40", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 435.3, 1.7 ] } ] }, "data_source" : { "reference" : "", "input" : { "notes" : "", "date" : [ datetime.datetime(2020,7,23,0,0,0) ], "name" : "Sylvia Munson", "contact" : "" } }, "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("5f1f43beed24042684c51145"), "specification" : "3.00", "grouping" : "DUNE", "type" : "assay", "sample" : { "name" : "Rock Sample 3", "description" : "DUNE Ross - Test Blast Site", "source" : "DUNE Ross - Test Blast Site", "id" : "", "owner" : { "name" : "Juergen Reichenbacher", "contact" : "Juergen.Reichenbacher@sdsmt.edu" } }, "measurement" : { "description" : "", "requestor" : { "name" : "", "contact" : "" }, "practitioner" : { "name" : "Juergen Reichenbacher", "contact" : "Juergen.Reichenbacher@sdsmt.edu" }, "technique" : "Ge Counter", "institution" : "SDSM&T", "date" : [ ], "results" : [ { "isotope" : "U-238", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 63, 7.8 ] }, { "isotope" : "Ra-226", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 146, 1.5 ] }, { "isotope" : "Th-232", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 19.6, 0.4 ] }, { "isotope" : "K-40", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 376.3, 2.3 ] } ] }, "data_source" : { "reference" : "", "input" : { "notes" : "", "date" : [ datetime.datetime(2020,7,27,0,0,0) ], "name" : "Sylvia Munson", "contact" : "" } }, "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("5f1f466bed24042684c51146"), "specification" : "3.00", "grouping" : "DUNE", "type" : "assay", "sample" : { "name" : "Rock Sample 2", "description" : "DUNE Ross - Governor's Corner", "source" : "DUNE Ross - Governor's Corner", "id" : "", "owner" : { "name" : "Juergen Reichenbacher", "contact" : "Juergen.Reichenbacher@sdsmt.edu" } }, "measurement" : { "description" : "", "requestor" : { "name" : "", "contact" : "" }, "practitioner" : { "name" : "Juergen Reichenbacher", "contact" : "Juergen.Reichenbacher@sdsmt.edu" }, "technique" : "Ge Counter", "institution" : "SDSM&T", "date" : [ ], "results" : [ { "isotope" : "U-238", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 24.4, 6.9 ] }, { "isotope" : "Ra-226", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 79.1, 1.1 ] }, { "isotope" : "Th-232", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 20.5, 0.4 ] }, { "isotope" : "K-40", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 420.6, 2.4 ] } ] }, "data_source" : { "reference" : "", "input" : { "notes" : "", "date" : [ datetime.datetime(2020,7,27,0,0,0) ], "name" : "Sylvia Munson", "contact" : "" } }, "_version" : 2, "_parent_id" : "5f1f40cbed24042684c51144" })
    coll.insert_one({ "_id" : ObjectId("5f1f4769ed24042684c51147"), "specification" : "3.00", "grouping" : "DUNE", "type" : "assay", "sample" : { "name" : "Rock Sample 4", "description" : "DUNE Ross - #4 Winze", "source" : "DUNE Ross - #4 Winze", "id" : "", "owner" : { "name" : "Juergen Reichenbacher", "contact" : "Juergen.Reichenbacher@sdsmt.edu" } }, "measurement" : { "description" : "", "requestor" : { "name" : "", "contact" : "" }, "practitioner" : { "name" : "Juergen Reichenbacher", "contact" : "Juergen.Reichenbacher@sdsmt.edu" }, "technique" : "Ge Counter", "institution" : "SDSM&T", "date" : [ ], "results" : [ { "isotope" : "U-238", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 107, 9.5 ] }, { "isotope" : "Ra-226", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 172.5, 1.3 ] }, { "isotope" : "Th-232", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 38.1, 0.5 ] }, { "isotope" : "K-40", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 1429.7, 4 ] } ] }, "data_source" : { "reference" : "", "input" : { "notes" : "", "date" : [ datetime.datetime(2020,7,27,0,0,0) ], "name" : "Sylvia Munson", "contact" : "" } }, "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("5f2d8c73ed24042684c51149"), "specification" : "3.00", "grouping" : "DUNE", "type" : "assay", "sample" : { "name" : "shotcrete & concrete ingredients", "description" : "Pete Lien", "source" : "sand (Cheyenne River, Oral/SD)", "id" : "", "owner" : { "name" : "Juergen Reichenbacher", "contact" : "juergen.reichenbacher@sdsmt.edu" } }, "measurement" : { "description" : "", "requestor" : { "name" : "", "contact" : "" }, "practitioner" : { "name" : "Juergen Reichenbacher", "contact" : "juergen.reichenbacher@sdsmt.edu" }, "technique" : "Ge Counter", "institution" : "SDSM&T", "date" : [ ], "results" : [ { "isotope" : "U-238", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 33.9, 12.2 ] }, { "isotope" : "Ra-226", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 38.3, 1.2 ] }, { "isotope" : "Th-232", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 15.8, 0.5 ] }, { "isotope" : "K-40", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 647.3, 3.9 ] } ] }, "data_source" : { "reference" : "", "input" : { "notes" : "", "date" : [ datetime.datetime(2020,8,6,0,0,0) ], "name" : "Sylvia Munson", "contact" : "" } }, "_version" : 2, "_parent_id" : "5f2c544bed24042684c51148" })
    coll.insert_one({ "_id" : ObjectId("5f2d8ddfed24042684c5114a"), "specification" : "3.00", "grouping" : "DUNE", "type" : "assay", "sample" : { "name" : "shotcrete & concrete ingredients", "description" : "TCC", "source" : "sand (commercial bag)", "id" : "", "owner" : { "name" : "Juergen Reichenbacher", "contact" : "juergen.reichenbacher@sdsmt.edu" } }, "measurement" : { "description" : "", "requestor" : { "name" : "", "contact" : "" }, "practitioner" : { "name" : "Juergen Reichenbacher", "contact" : "juergen.reichenbacher@sdsmt.edu" }, "technique" : "Ge Counter", "institution" : "SDSM&T", "date" : [ ], "results" : [ { "isotope" : "U-238", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 54, 18.3 ] }, { "isotope" : "Ra-226", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 42.4, 1.9 ] }, { "isotope" : "Th-232", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 19.1, 0.8 ] }, { "isotope" : "K-40", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 613.1, 5.8 ] } ] }, "data_source" : { "reference" : "", "input" : { "notes" : "", "date" : [ datetime.datetime(2020,8,7,0,0,0) ], "name" : "Sylvia Munson", "contact" : "" } }, "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("5f2d8e64ed24042684c5114b"), "specification" : "3.00", "grouping" : "DUNE", "type" : "assay", "sample" : { "name" : "shotcrete & concrete ingredients", "description" : "Croell", "source" : "sand (Fisher in Nisland/SD)", "id" : "", "owner" : { "name" : "Juergen Reichenbacher", "contact" : "juergen.reichenbacher@sdsmt.edu" } }, "measurement" : { "description" : "", "requestor" : { "name" : "", "contact" : "" }, "practitioner" : { "name" : "Juergen Reichenbacher", "contact" : "juergen.reichenbacher@sdsmt.edu" }, "technique" : "Ge Counter", "institution" : "SDSM&T", "date" : [ ], "results" : [ { "isotope" : "U-238", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 75.4, 24.5 ] }, { "isotope" : "Ra-226", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 119.3, 3.1 ] }, { "isotope" : "Th-232", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 40.3, 1.2 ] }, { "isotope" : "K-40", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 442.8, 6 ] } ] }, "data_source" : { "reference" : "", "input" : { "notes" : "", "date" : [ datetime.datetime(2020,8,7,0,0,0) ], "name" : "Sylvia Munson", "contact" : "" } }, "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("5f2d92e4ed24042684c5114c"), "specification" : "3.00", "grouping" : "DUNE", "type" : "assay", "sample" : { "name" : "shotcrete & concrete ingredients", "description" : "Pete Lien", "source" : "gravel (Rapid City limestone quarry)", "id" : "", "owner" : { "name" : "Juergen Reichenbacher", "contact" : "juergen.reichenbacher@sdsmt.edu" } }, "measurement" : { "description" : "", "requestor" : { "name" : "", "contact" : "" }, "practitioner" : { "name" : "Juergen Reichenbacher", "contact" : "juergen.reichenbacher@sdsmt.edu" }, "technique" : "Ge Counter", "institution" : "SDSM&T", "date" : [ ], "results" : [ { "isotope" : "U-238", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 28.1, 6.5 ] }, { "isotope" : "Ra-226", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 38.2, 0.9 ] }, { "isotope" : "Th-232", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 0.8, 0.3 ] }, { "isotope" : "K-40", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 28.1, 6.5 ] } ] }, "data_source" : { "reference" : "", "input" : { "notes" : "", "date" : [ datetime.datetime(2020,8,7,0,0,0) ], "name" : "Sylvia Munson", "contact" : "" } }, "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("5f2d9356ed24042684c5114d"), "specification" : "3.00", "grouping" : "DUNE", "type" : "assay", "sample" : { "name" : "shotcrete & concrete ingredients", "description" : "TCC", "source" : "gravel (bag from South America)", "id" : "", "owner" : { "name" : "Juergen Reichenbacher", "contact" : "juergen.reichenbacher@sdsmt.edu" } }, "measurement" : { "description" : "", "requestor" : { "name" : "", "contact" : "" }, "practitioner" : { "name" : "Juergen Reichenbacher", "contact" : "juergen.reichenbacher@sdsmt.edu" }, "technique" : "Ge Counter", "institution" : "SDSM&T", "date" : [ ], "results" : [ { "isotope" : "U-238", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 42.6, 11.2 ] }, { "isotope" : "Ra-226", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 98.2, 1.5 ] }, { "isotope" : "Th-232", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 7.8, 0.4 ] }, { "isotope" : "K-40", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 42.6, 11.2 ] } ] }, "data_source" : { "reference" : "", "input" : { "notes" : "", "date" : [ datetime.datetime(2020,8,7,0,0,0) ], "name" : "Sylvia Munson", "contact" : "" } }, "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("5f2d93c6ed24042684c5114e"), "specification" : "3.00", "grouping" : "DUNE", "type" : "assay", "sample" : { "name" : "shotcrete & concrete ingredients", "description" : "Croell", "source" : "gravel (Rogers Pit, Sundance/WY)", "id" : "", "owner" : { "name" : "Juergen Reichenbacher", "contact" : "juergen.reichenbacher@sdsmt.edu" } }, "measurement" : { "description" : "", "requestor" : { "name" : "", "contact" : "" }, "practitioner" : { "name" : "Juergen Reichenbacher", "contact" : "juergen.reichenbacher@sdsmt.edu" }, "technique" : "Ge Counter", "institution" : "SDSM&T", "date" : [ ], "results" : [ { "isotope" : "U-238", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 15.1, 7.6 ] }, { "isotope" : "Ra-226", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 27.1, 1 ] }, { "isotope" : "Th-232", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 1, 0.3 ] }, { "isotope" : "K-40", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 15.1, 7.6 ] } ] }, "data_source" : { "reference" : "", "input" : { "notes" : "", "date" : [ datetime.datetime(2020,8,7,0,0,0) ], "name" : "Sylvia Munson", "contact" : "" } }, "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("5f2d9449ed24042684c5114f"), "specification" : "3.00", "grouping" : "DUNE", "type" : "assay", "sample" : { "name" : "shotcrete & concrete ingredients", "description" : "GCC", "source" : "Portland cement (Rapid City)", "id" : "", "owner" : { "name" : "Juergen Reichenbacher", "contact" : "juergen.reichenbacher@sdsmt.edu" } }, "measurement" : { "description" : "", "requestor" : { "name" : "", "contact" : "" }, "practitioner" : { "name" : "Juergen Reichenbacher", "contact" : "juergen.reichenbacher@sdsmt.edu" }, "technique" : "Ge Counter", "institution" : "SDSM&T", "date" : [ ], "results" : [ { "isotope" : "U-238", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 47.1, 16.4 ] }, { "isotope" : "Ra-226", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 65.1, 2.1 ] }, { "isotope" : "Th-232", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 12.7, 0.7 ] }, { "isotope" : "K-40", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 147.7, 3.3 ] } ] }, "data_source" : { "reference" : "", "input" : { "notes" : "8/7/2020", "date" : [ ], "name" : "Sylvia Munson", "contact" : "" } }, "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("5f2d94d4ed24042684c51150"), "specification" : "3.00", "grouping" : "DUNE", "type" : "assay", "sample" : { "name" : "shotcrete & concrete ingredients", "description" : "Whelan Energy", "source" : "fly ash (power plant, Hastings/NE)", "id" : "", "owner" : { "name" : "Juergen Reichenbacher", "contact" : "juergen.reichenbacher@sdsmt.edu" } }, "measurement" : { "description" : "", "requestor" : { "name" : "", "contact" : "" }, "practitioner" : { "name" : "Juergen Reichenbacher", "contact" : "juergen.reichenbacher@sdsmt.edu" }, "technique" : "Ge Counter", "institution" : "SDSM&T", "date" : [ ], "results" : [ { "isotope" : "U-238", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 100.7, 21.5 ] }, { "isotope" : "Ra-226", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 174.6, 3.3 ] }, { "isotope" : "Th-232", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 80.6, 1.4 ] }, { "isotope" : "K-40", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 119.4, 3.2 ] } ] }, "data_source" : { "reference" : "", "input" : { "notes" : "", "date" : [ datetime.datetime(2020,8,7,0,0,0) ], "name" : "Sylvia Munson", "contact" : "" } }, "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("5f2d955ced24042684c51151"), "specification" : "3.00", "grouping" : "DUNE", "type" : "assay", "sample" : { "name" : "shotcrete & concrete ingredients", "description" : "SURF", "source" : "water (4850 Davis industrial & sump)", "id" : "", "owner" : { "name" : "Juergen Reichenbacher", "contact" : "juergen.reichenbacher@sdsmt.edu" } }, "measurement" : { "description" : "", "requestor" : { "name" : "", "contact" : "" }, "practitioner" : { "name" : "Juergen Reichenbacher", "contact" : "juergen.reichenbacher@sdsmt.edu" }, "technique" : "Ge Counter", "institution" : "SDSM&T", "date" : [ ], "results" : [ { "isotope" : "U-238", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 3.8, 6.4 ] }, { "isotope" : "Ra-226", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 0.6, 0.7 ] }, { "isotope" : "Th-232", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 0.1, 0.2 ] }, { "isotope" : "K-40", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 0, 0 ] } ] }, "data_source" : { "reference" : "", "input" : { "notes" : "", "date" : [ datetime.datetime(2020,8,7,0,0,0) ], "name" : "Sylvia Munson", "contact" : "" } }, "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("5f2d95e2ed24042684c51152"), "specification" : "3.00", "grouping" : "DUNE", "type" : "assay", "sample" : { "name" : "Steel Samples", "description" : "Steel I-beams", "source" : "ProtoDUNE", "id" : "", "owner" : { "name" : "Juergen Reichenbacher", "contact" : "juergen.reichenbacher@sdsmt.edu" } }, "measurement" : { "description" : "", "requestor" : { "name" : "", "contact" : "" }, "practitioner" : { "name" : "Juergen Reichenbacher", "contact" : "juergen.reichenbacher@sdsmt.edu" }, "technique" : "Ge Counter", "institution" : "SDSM&T", "date" : [ ], "results" : [ { "isotope" : "U-238", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 2.6, 0.8 ] }, { "isotope" : "Ra-226", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 1.1 ] }, { "isotope" : "Th-232", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 0.1 ] } ] }, "data_source" : { "reference" : "", "input" : { "notes" : "", "date" : [ datetime.datetime(2020,8,7,0,0,0) ], "name" : "Sylvia Munson", "contact" : "" } }, "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("5f2d9638ed24042684c51153"), "specification" : "3.00", "grouping" : "DUNE", "type" : "assay", "sample" : { "name" : "Steel Samples", "description" : "SS of cryostat wall", "source" : "ProtoDUNE", "id" : "", "owner" : { "name" : "Juergen Reichenbacher", "contact" : "juergen.reichenbacher@sdsmt.edu" } }, "measurement" : { "description" : "", "requestor" : { "name" : "", "contact" : "" }, "practitioner" : { "name" : "Juergen Reichenbacher", "contact" : "juergen.reichenbacher@sdsmt.edu" }, "technique" : "Ge Counter", "institution" : "SDSM&T", "date" : [ ], "results" : [ { "isotope" : "U-238", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 3.3, 2.3 ] }, { "isotope" : "Ra-226", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 1.7 ] }, { "isotope" : "Th-232", "type" : "measurement", "unit" : "Bq/kg", "value" : [ 0.1 ] } ] }, "data_source" : { "reference" : "", "input" : { "notes" : "", "date" : [ datetime.datetime(2020,8,7,0,0,0) ], "name" : "Sylvia Munson", "contact" : "" } }, "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("5f2d97e8ed24042684c51154"), "specification" : "3.00", "grouping" : "DUNE", "type" : "assay", "sample" : { "name" : "APA Wire (BeCu)", "description" : "-", "source" : "-", "id" : "", "owner" : { "name" : "Dave Waters", "contact" : "-" } }, "measurement" : { "description" : "", "requestor" : { "name" : "", "contact" : "" }, "practitioner" : { "name" : "Dave Waters", "contact" : "-" }, "technique" : "-", "institution" : "-", "date" : [ ], "results" : [ { "isotope" : "U-238", "type" : "measurement", "unit" : "mBq/kg", "value" : [ 3000, 300 ] }, { "isotope" : "U-238", "type" : "measurement", "unit" : "mBq/kg", "value" : [ 4 ] }, { "isotope" : "Th-232", "type" : "measurement", "unit" : "mBq/kg", "value" : [ 100, 6 ] }, { "isotope" : "Th-232", "type" : "measurement", "unit" : "mBq/kg", "value" : [ 114, 5 ] }, { "isotope" : "K-40", "type" : "measurement", "unit" : "mBq/kg", "value" : [ 45, 17 ] } ] }, "data_source" : { "reference" : "", "input" : { "notes" : "", "date" : [ datetime.datetime(2020,8,7,0,0,0) ], "name" : "Sylvia Munson", "contact" : "" } }, "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("60130b83c5e095da01c42e9e"), "specification" : "3.00", "grouping" : "Test assay", "type" : "assay", "sample" : { "name" : "description", "description" : "", "source" : "", "id" : "", "owner" : { "name" : "Elise Saxon", "contact" : "elise.saxon@pnnl.gov" } }, "measurement" : { "description" : "", "requestor" : { "name" : "", "contact" : "" }, "practitioner" : { "name" : "", "contact" : "" }, "technique" : "", "institution" : "", "date" : [ ], "results" : [ { "isotope" : "K-40", "type" : "measurement", "unit" : "g", "value" : [ 1, 2 ] } ] }, "data_source" : { "reference" : "", "input" : { "notes" : "", "date" : [ ], "name" : "Chris Jackson", "contact" : "test@test.com" } }, "_version" : 3, "_parent_id" : "60130b59827db8bc4e38930d" })
    return db_obj

def teardown_db_for_test():
    db_host, db_port, db_name = get_mongodb_config_info()
    client = MongoClient(db_host, db_port)
    coll = client[db_name].assays
    old_versions_coll = client[db_name].assays_old_versions
    remove_resp = coll.delete_many({})
    resmove_oldversions_resp = old_versions_coll.delete_many({})



