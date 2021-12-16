import os
import json
import pytest
from bson.objectid import ObjectId
import datetime
from test_auxiliary import set_up_db_for_test, teardown_db_for_test, query_for_all_docs
from dunetoolkit import search_by_id, update, convert_str_to_date


# OTHER POSSIBLE TESTS:
# a bunch of updates --> does doc maintain truth?
# 

'''
testing update
'''
def test_update_remove_doc():
    os.environ['TOOLKIT_CONFIG_NAME'] = '../dunetoolkit/toolkit_config_test.json'

    # set up database to be updated
    teardown_db_for_test()
    db_obj = set_up_db_for_test(_get_docs())

    # perform update
    doc_id = '000000000000000000000002'
    doc = search_by_id(doc_id) #, db_obj=db_obj)
    new_doc_id, error_msg = update(doc_id, remove_doc=True) #, db_obj=db_obj)
    assert new_doc_id == None

    oldversion_doc = search_by_id(doc_id, coll_type='old_versions')
    assert doc == oldversion_doc

def test_update_nochange():
    os.environ['TOOLKIT_CONFIG_NAME'] = '../dunetoolkit/toolkit_config_test.json'

    # set up database to be updated
    teardown_db_for_test()
    db_obj = set_up_db_for_test(_get_docs())

    # perform update
    doc_id = '000000000000000000000002'
    doc = search_by_id(doc_id) #, db_obj=db_obj)
    new_doc_id, error_msg = update(doc_id, remove_doc=False, \
        update_pairs={}, \
        new_meas_objects=[], \
        meas_remove_indices=[] \
    )
    assert new_doc_id != None
    assert type(new_doc_id) is ObjectId
    new_doc_id = str(new_doc_id)

    # test value in oldversion database
    oldversion_doc = search_by_id(doc_id, coll_type='old_versions')
    assert doc == oldversion_doc

    # test currversion doc
    currversion_doc = search_by_id(new_doc_id) #, db_obj=db_obj)

    # test version num
    doc.pop('_version')
    new_version = currversion_doc.pop('_version')
    assert new_version == 2
    
    # test parent id
    doc.pop('_id')
    parent_id = currversion_doc.pop('_parent_id')
    assert parent_id == doc_id

    # test id once more
    new_version_doc_id = str(currversion_doc.pop('_id'))
    assert new_doc_id == new_version_doc_id

    # test orig doc and curr version doc equality
    assert doc == currversion_doc


def test_update_bad_field():
    os.environ['TOOLKIT_CONFIG_NAME'] = '../dunetoolkit/toolkit_config_test.json'

    # set up database to be updated
    teardown_db_for_test()
    db_obj = set_up_db_for_test(_get_docs())

    # perform update
    doc_id = '000000000000000000000002'
    doc = search_by_id(doc_id)
    new_doc_id, error_msg = update(doc_id, remove_doc=False, \
        update_pairs={'bad_field':'val'}, \
        new_meas_objects=[], \
        meas_remove_indices=[] \
    )
    assert new_doc_id == None

    # test that doc did not get transferred
    oldversion_doc = search_by_id(doc_id, coll_type='old_versions')
    assert oldversion_doc == None

    #test that currversion doc was not inserted
    all_docs = query_for_all_docs()
    for doc in all_docs:
        assert 'bad_field' not in list(doc.keys())


def test_update_update_pairs_all():
    os.environ['TOOLKIT_CONFIG_NAME'] = '../dunetoolkit/toolkit_config_test.json'

    # set up database to be updated
    teardown_db_for_test()
    db_obj = set_up_db_for_test(_get_docs())

    # perform update
    doc_id = '000000000000000000000002'
    doc = search_by_id(doc_id)
    update_pairs={
        'grouping':'new test value', 
        'sample.name':'testing sample name',
        'sample.description':'test descrip',
        'sample.source':'example src',
        'sample.id':'123456test',
        'sample.owner.name':'test',
        'sample.owner.contact':'test@test.com',
        'measurement.results.0.isotope':'K-40',
        'measurement.results.0.type':'range',
        'measurement.results.0.unit':'g',
        'measurement.results.0.value':[10.3,12.9],
        'measurement.practitioner.name':'tester',
        'measurement.practitioner.contact':'tester@testing.edu',
        'measurement.technique':'test',
        'measurement.institution':'test place',
        'measurement.date':['2020-10-21'],
        'measurement.description':'test descrip',
        'measurement.requestor.name':'test requestor',
        'measurement.requestor.contact':'requestor@test.gov',
        'data_source.reference':'testing',
        'data_source.input.name':'testing',
        'data_source.input.contact':'testing@test.org', 
        'data_source.input.date':['2010/18/02','2020-10-21'],
        'data_source.input.notes':'test test test',
    }
    new_doc_id, error_msg = update(doc_id, remove_doc=False, \
        update_pairs=update_pairs, \
        new_meas_objects=[], \
        meas_remove_indices=[] \
    )
    assert new_doc_id != None
    new_doc_id = str(new_doc_id)

    # test value in oldversion database
    oldversion_doc = search_by_id(doc_id, coll_type='old_versions')
    assert(doc == oldversion_doc)

    # test currversion doc
    currversion_doc = search_by_id(new_doc_id)

    # test version num
    doc.pop('_version')
    new_version = currversion_doc.pop('_version')
    assert new_version == 2
    
    # test parent id
    doc.pop('_id')
    parent_id = currversion_doc.pop('_parent_id')
    assert parent_id == doc_id

    # test id once more
    new_version_doc_id = str(currversion_doc.pop('_id'))
    assert new_doc_id == new_version_doc_id

    # correct the date values to be datetime objects now, not strings
    for update_key in ['measurement.date', 'data_source.input.date']:
        for i in range(len(update_pairs[update_key])):
            update_pairs[update_key][i] = convert_str_to_date(update_pairs[update_key][i])

    # test orig doc and curr version doc equality
    for update_key in update_pairs:
        new_val = update_pairs[update_key]
        key_parts = update_key.split('.')

        if len(key_parts) == 1:
            doc.pop(key_parts[0])
            assert currversion_doc.pop(key_parts[0]) == new_val
        elif len(key_parts) == 2:
            doc[key_parts[0]].pop(key_parts[1])
            assert currversion_doc[key_parts[0]].pop(key_parts[1]) == new_val
        elif len(key_parts) == 3:
            if update_key == "data_source.input.name":
                # data input gets appended to, not fully replaced
                new_val = "{}, {}".format(oldversion_doc[key_parts[0]][key_parts[1]][key_parts[2]], new_val)
            else:
                doc[key_parts[0]][key_parts[1]].pop(key_parts[2])

            assert currversion_doc[key_parts[0]][key_parts[1]].pop(key_parts[2]) == new_val
        elif len(key_parts) == 4:
            try:
                key_parts_2 = int(key_parts[2])
            except:
                key_parts_2 = key_parts[2]
            doc[key_parts[0]][key_parts[1]][key_parts_2].pop(key_parts[3])
            assert currversion_doc[key_parts[0]][key_parts[1]][key_parts_2].pop(key_parts[3]) == new_val
        else:
            assert 0 == 1


def test_update_update_pairs_update_twice():
    os.environ['TOOLKIT_CONFIG_NAME'] = '../dunetoolkit/toolkit_config_test.json'

    # set up database to be updated
    teardown_db_for_test()
    db_obj = set_up_db_for_test(_get_docs())

    # PERFORM AND TEST FIRST UPDATE
    u1_doc_id = '000000000000000000000002'
    u1_doc = search_by_id(u1_doc_id)
    u1_update_pairs={'grouping':'new test value', 'data_source.input.contact':'testing@test.org', 'measurement.results.0.unit':'g', 'measurement.date':['2020-10-21']}
    u1_new_doc_id, u1_error_msg = update(u1_doc_id, remove_doc=False, \
        update_pairs=u1_update_pairs, \
        new_meas_objects=[], \
        meas_remove_indices=[] \
    )
    assert u1_new_doc_id != None
    u1_new_doc_id = str(u1_new_doc_id)

    # test value in oldversion database
    u1_oldversion_doc = search_by_id(u1_doc_id, coll_type='old_versions')
    assert(u1_doc == u1_oldversion_doc)

    # test new (current version) doc
    u1_new_doc = search_by_id(u1_new_doc_id)

    # test version num
    u1_doc.pop('_version')
    u1_new_version = u1_new_doc.pop('_version')
    assert u1_new_version == 2
    
    # test parent id
    u1_doc.pop('_id')
    u1_parent_id = u1_new_doc.pop('_parent_id')
    assert u1_parent_id == u1_doc_id

    # test id once more
    u1_new_version_doc_id = str(u1_new_doc.pop('_id'))
    assert u1_new_doc_id == u1_new_version_doc_id

    # test orig doc and curr version doc equality
    u1_doc.pop('grouping')
    u1_doc['data_source']['input'].pop('contact')
    u1_doc['measurement']['results'][0].pop('unit')
    u1_doc['measurement'].pop('date')
    assert u1_new_doc.pop('grouping') == 'new test value'
    assert u1_new_doc['data_source']['input'].pop('contact') == 'testing@test.org'
    assert u1_new_doc['measurement']['results'][0].pop('unit') == 'g'
    assert u1_new_doc['measurement'].pop('date') == [datetime.datetime(2020,10,21)]
    assert u1_doc == u1_new_doc

    # PERFORM AND TEST SECOND UPDATE
    u2_doc_id = u1_new_version_doc_id
    u2_doc = search_by_id(u2_doc_id)
    u2_update_pairs = {'grouping':'test value two'}
    u2_new_doc_id, u2_error_msg = update(u2_doc_id, remove_doc=False, update_pairs=u2_update_pairs)
    assert u2_new_doc_id != None
    u2_new_doc_id = str(u2_new_doc_id)

    u2_oldversion_doc = search_by_id(u2_doc_id, coll_type='old_versions')
    assert u2_doc == u2_oldversion_doc

    u2_new_doc = search_by_id(u2_new_doc_id)

    u2_doc.pop('_version')
    u2_new_version = u2_new_doc.pop('_version')
    assert u2_new_version == 3

    u2_doc.pop('_id')
    u2_parent_id = u2_new_doc.pop('_parent_id')
    assert u2_parent_id == u2_doc_id

    u2_new_doc.pop('_id')
    u2_doc.pop('grouping')
    assert u2_new_doc.pop('grouping') == 'test value two'


def test_update_new_meas_objects_bad_object():
    os.environ['TOOLKIT_CONFIG_NAME'] = '../dunetoolkit/toolkit_config_test.json'

    # set up database to be updated
    teardown_db_for_test()
    db_obj = set_up_db_for_test(_get_docs())

    new_meas_objects = [
        {'bad_field':1}
    ]
    doc_id = '000000000000000000000002'
    new_doc_id, error_msg = update(doc_id, remove_doc=False, new_meas_objects=new_meas_objects)
    assert new_doc_id == None

    # test that doc did not get transferred
    oldversion_doc = search_by_id(doc_id, coll_type='old_versions')
    assert oldversion_doc == None

    #test that currversion doc was not inserted
    all_docs = query_for_all_docs()
    for doc in all_docs:
        assert 'bad_field' not in list(doc.keys())


def test_update_new_meas_objects():
    os.environ['TOOLKIT_CONFIG_NAME'] = '../dunetoolkit/toolkit_config_test.json'

    # set up database to be updated
    teardown_db_for_test()
    db_obj = set_up_db_for_test(_get_docs())

    new_meas_objects = [
        {'isotope':'K-40', 'type':'measurement', 'unit':'g/cm', 'value':[0.2]},
        {'isotope':'U-235', 'type':'range', 'unit':'g', 'value':[0.3, 2.1]}
    ]
    doc_id = '000000000000000000000002'
    orig_doc = search_by_id(doc_id)
    new_doc_id, error_msg = update(doc_id, remove_doc=False, new_meas_objects=new_meas_objects)
    assert new_doc_id != None
    new_doc_id = str(new_doc_id)

    # test that doc got transferred
    oldversion_doc = search_by_id(doc_id, coll_type='old_versions')
    assert oldversion_doc == orig_doc

    # test new (current version) doc
    new_doc = search_by_id(new_doc_id)

    # test version num
    orig_doc.pop('_version')
    new_version = new_doc.pop('_version')
    assert new_version == 2
    
    # test parent id
    orig_doc.pop('_id')
    parent_id = new_doc.pop('_parent_id')
    assert parent_id == doc_id

    # test id once more
    new_version_doc_id = str(new_doc.pop('_id'))
    assert new_doc_id == new_version_doc_id

    # test orig doc and curr version doc equality
    len_orig_meas_results = len(orig_doc['measurement'].pop('results'))
    assert new_doc['measurement'].pop('results')[len_orig_meas_results:] == new_meas_objects
    assert orig_doc == new_doc


#NOTE this test has been changed to use numeric values for the measurement values, instead
#  of strings (i.e. 0.3 instead of '0.3') because I decided we should always be able to expect
#  that the incoming doc to an update or insert should have proper formatting, other than dates
def test_update_new_meas_objects_str_for_val_a():
    os.environ['TOOLKIT_CONFIG_NAME'] = '../dunetoolkit/toolkit_config_test.json'

    # set up database to be updated
    teardown_db_for_test()
    db_obj = set_up_db_for_test(_get_docs())

    new_meas_objects = [
        {'isotope':'U-235', 'type':'range', 'unit':'g', 'value':[0.3, 2.1]}
    ]
    doc_id = '000000000000000000000002'
    orig_doc = search_by_id(doc_id)
    new_doc_id, error_msg = update(doc_id, remove_doc=False, new_meas_objects=new_meas_objects)
    assert new_doc_id != None
    new_doc_id = str(new_doc_id)

    # test that doc got transferred
    oldversion_doc = search_by_id(doc_id, coll_type='old_versions')
    assert oldversion_doc == orig_doc

    # test new (current version) doc
    new_doc = search_by_id(new_doc_id)

    # test version num
    orig_doc.pop('_version')
    new_version = new_doc.pop('_version')
    assert new_version == 2
    
    # test parent id
    orig_doc.pop('_id')
    parent_id = new_doc.pop('_parent_id')
    assert parent_id == doc_id

    # test id once more
    new_version_doc_id = str(new_doc.pop('_id'))
    assert new_doc_id == new_version_doc_id

    # test orig doc and curr version doc equality
    len_orig_meas_results = len(orig_doc['measurement'].pop('results'))
    new_doc_meas_results = new_doc['measurement'].pop('results')
    assert new_doc_meas_results[len_orig_meas_results:] == new_meas_objects
    assert new_doc_meas_results[-1]['value'] == [0.3, 2.1]
    assert orig_doc == new_doc


def test_update_new_meas_objects_str_for_val_b():
    os.environ['TOOLKIT_CONFIG_NAME'] = '../dunetoolkit/toolkit_config_test.json'

    # set up database to be updated
    teardown_db_for_test()
    db_obj = set_up_db_for_test(_get_docs())

    new_meas_objects = [
        {'isotope':'U-235', 'type':'range', 'unit':'g', 'value':['a', 'b']}
    ]
    doc_id = '000000000000000000000002'
    orig_doc = search_by_id(doc_id)
    new_doc_id, error_msg = update(doc_id, remove_doc=False, new_meas_objects=new_meas_objects)
    assert new_doc_id == None

    # test that doc got transferred
    oldversion_doc = search_by_id(doc_id, coll_type='old_versions')
    assert oldversion_doc == None

    # test no change to original doc
    new_doc = search_by_id(doc_id)
    assert len(new_doc['measurement']['results']) == len(orig_doc['measurement']['results'])


def test_update_meas_remove_indices_bad_idx():
    os.environ['TOOLKIT_CONFIG_NAME'] = '../dunetoolkit/toolkit_config_test.json'

    # set up database to be updated
    teardown_db_for_test()
    db_obj = set_up_db_for_test(_get_docs())

    remove_indices = [4] # list len is 3
    doc_id = '000000000000000000000002'
    orig_doc = search_by_id(doc_id)
    new_doc_id, error_msg = update(doc_id, remove_doc=False, meas_remove_indices=remove_indices)
    assert new_doc_id == None

    # test that doc did not get transferred
    oldversion_doc = search_by_id(doc_id, coll_type='old_versions')
    assert oldversion_doc == None

    # test no change to original doc
    new_doc = search_by_id(doc_id)
    assert len(new_doc['measurement']['results']) == len(orig_doc['measurement']['results'])


def test_update_meas_remove_indices():
    os.environ['TOOLKIT_CONFIG_NAME'] = '../dunetoolkit/toolkit_config_test.json'

    # set up database to be updated
    teardown_db_for_test()
    db_obj = set_up_db_for_test(_get_docs())

    remove_indices = [0, 2] # list len is 3
    doc_id = '000000000000000000000002'
    orig_doc = search_by_id(doc_id, db_obj=db_obj)
    new_doc_id, error_msg = update(doc_id, remove_doc=False, meas_remove_indices=remove_indices)
    assert new_doc_id != None
    new_doc_id = str(new_doc_id)

    # test that doc got transferred
    oldversion_doc = search_by_id(doc_id, coll_type='old_versions')
    assert oldversion_doc == orig_doc

    # test new (current version) doc
    new_doc = search_by_id(new_doc_id)

    # test version num
    orig_doc.pop('_version')
    new_version = new_doc.pop('_version')
    assert new_version == 2
    
    # test parent id
    orig_doc.pop('_id')
    parent_id = new_doc.pop('_parent_id')
    assert parent_id == doc_id

    # test id once more
    new_version_doc_id = str(new_doc.pop('_id'))
    assert new_doc_id == new_version_doc_id

    # test orig doc and curr version doc equality
    orig_meas_results = orig_doc['measurement'].pop('results')
    new_meas_results = new_doc['measurement'].pop('results')
    assert len(new_meas_results) == 1
    assert new_meas_results[0] == orig_meas_results[1]
    assert orig_doc == new_doc


def test_update_all():
    os.environ['TOOLKIT_CONFIG_NAME'] = '../dunetoolkit/toolkit_config_test.json'

    # set up database to be updated
    teardown_db_for_test()
    db_obj = set_up_db_for_test(_get_docs())

    update_pairs={'grouping':'new test value', 'data_source.input.contact':'testing@test.org', 'measurement.results.0.unit':'g', 'measurement.date':['2020-10-21']}
    new_meas_objects = [
        {'isotope':'K-40', 'type':'measurement', 'unit':'g/cm', 'value':[0.2]},
        {'isotope':'U-235', 'type':'range', 'unit':'g', 'value':[0.3, 2.1]}
    ]
    remove_indices = [1, 2]
    doc_id = '000000000000000000000002'
    orig_doc = search_by_id(doc_id)
    new_doc_id, error_msg = update(doc_id, remove_doc=False, update_pairs=update_pairs, new_meas_objects=new_meas_objects, meas_remove_indices=remove_indices)
    assert new_doc_id != None
    new_doc_id = str(new_doc_id)

    # test that doc got transferred
    oldversion_doc = search_by_id(doc_id, coll_type='old_versions')
    assert oldversion_doc == orig_doc

    # test new (current version) doc
    new_doc = search_by_id(new_doc_id)

    # test version num
    orig_doc.pop('_version')
    new_version = new_doc.pop('_version')
    assert new_version == 2
    
    # test parent id
    orig_doc.pop('_id')
    parent_id = new_doc.pop('_parent_id')
    assert parent_id == doc_id

    # test id once more
    new_version_doc_id = str(new_doc.pop('_id'))
    assert new_doc_id == new_version_doc_id

    # correct the date values to be datetime objects now, not strings
    for update_key in ['measurement.date', 'data_source.input.date']:
        if update_key in list(update_pairs.keys()):
            for i in range(len(update_pairs[update_key])):
                update_pairs[update_key][i] = convert_str_to_date(update_pairs[update_key][i])

    # test orig doc and curr version doc equality
    for update_key in update_pairs:
        new_val = update_pairs[update_key]
        key_parts = update_key.split('.')
        if len(key_parts) == 1:
            orig_doc.pop(key_parts[0])
            assert new_doc.pop(key_parts[0]) == new_val
        elif len(key_parts) == 2:
            orig_doc[key_parts[0]].pop(key_parts[1])
            assert new_doc[key_parts[0]].pop(key_parts[1]) == new_val
        elif len(key_parts) == 3:
            orig_doc[key_parts[0]][key_parts[1]].pop(key_parts[2])
            assert new_doc[key_parts[0]][key_parts[1]].pop(key_parts[2]) == new_val
        elif len(key_parts) == 4:
            try:
                key_parts_2 = int(key_parts[2])
            except:
                key_parts_2 = key_parts[2]
            orig_doc[key_parts[0]][key_parts[1]][key_parts_2].pop(key_parts[3])
            assert new_doc[key_parts[0]][key_parts[1]][key_parts_2].pop(key_parts[3]) == new_val
        else:
            assert 0 == 1

    orig_meas = orig_doc['measurement'].pop('results')
    meas_eles = new_doc['measurement'].pop('results')
    for new_meas in new_meas_objects:
        assert new_meas in meas_eles
    for removed_meas in [orig_meas[1], orig_meas[2]]:
        assert removed_meas not in meas_eles

    assert orig_doc == new_doc

def _get_docs():
    docs = [
        { "_id" : ObjectId("000000000000000000000001"), "type" : "testing_doc" },
        { "_id" : ObjectId("000000000000000000000002"), "measurement" : { "description" : "", "practitioner" : { "name" : "ICI Tracerco", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "NAA", "results" : [ { "unit" : "ppb", "value" : [ 18, 2 ], "isotope" : "U-238", "type" : "measurement" }, { "unit" : "ppb", "value" : [ 59, 2 ], "isotope" : "Th-232", "type" : "measurement" }, { "unit" : "ppm", "value" : [ 0.78, 0.02 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2013, 7, 22, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Resin, Magnex, 2:1 Thiokol 308, RAL", "id" : "ILIAS UKDM #249", "owner" : { "name" : "", "contact" : "" }, "name" : "Resin, Magnex, 2:1 Thiokol 308", "source" : "" }, "type" : "measurement", "_version" : 1 },
        { "_id" : ObjectId("000000000000000000000003"), "measurement" : { "description" : "", "practitioner" : { "name" : "ICI Tracerco", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "NAA", "results" : [ { "unit" : "ppb", "value" : [ 3 ], "isotope" : "U-238", "type" : "limit" }, { "unit" : "ppb", "value" : [ 1 ], "isotope" : "Th-232", "type" : "limit" }, { "unit" : "ppm", "value" : [ 8.9, 0.2 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2016, 7, 14, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Rexalite, copper removed", "id" : "ILIAS UKDM #266", "owner" : { "name" : "", "contact" : "" }, "name" : "Rexalite, copper removed", "source" : "" }, "type" : "measurement", "_version" : 1 },
        { "_id" : ObjectId("000000000000000000000004"), "measurement" : { "description" : "", "practitioner" : { "name" : "RAL", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "AA", "results" : [ { "unit" : "ppm", "value" : [ 15 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2016, 7, 14, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Salt, ICI, pure dried vacuum", "id" : "ILIAS UKDM #273", "owner" : { "name" : "", "contact" : "" }, "name" : "Salt, ICI, pure dried vacuum", "source" : "" }, "type" : "measurement", "_version" : 1 },
        { "_id" : ObjectId("000000000000000000000005"), "measurement" : { "description" : "Lu < 1ppb, Rb < 10ppb", "practitioner" : { "name" : "Charles Evans/Cascade Scientific", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "GD-MS", "results" : [ { "unit" : "ppb", "value" : [ 1 ], "isotope" : "U-238", "type" : "limit" }, { "unit" : "ppb", "value" : [ 1 ], "isotope" : "Th-232", "type" : "limit" }, { "unit" : "ppm", "value" : [ 0.22 ], "isotope" : "K-40", "type" : "limit" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2013, 7, 22, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Si", "id" : "ILIAS UKDM #279", "owner" : { "name" : "", "contact" : "" }, "name" : "Si", "source" : "" }, "type" : "measurement", "_version" : 1 },
        { "_id" : ObjectId("000000000000000000000006"), "measurement" : { "description" : "", "practitioner" : { "name" : "Supplier's data", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "?", "results" : [ { "unit" : "ppm", "value" : [ 0.03 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2013, 1, 30, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Silica fibre, TSL, 'Spectrosil'", "id" : "ILIAS UKDM #289", "owner" : { "name" : "", "contact" : "" }, "name" : "Silica fibre, TSL, 'Spectrosil'", "source" : "" }, "type" : "measurement", "_version" : 1 }
    ]
    return docs

