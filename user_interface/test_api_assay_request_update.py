import pytest
import json
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from copy import deepcopy

base_url = 'http://localhost:5000'


def test_update_remove_doc():
    browser = prep('DUNEwriter')
    browser.get(base_url+'/assay_request_update')
    doc_id = '000000000000000000000007'

    find_doc_with_id(browser, doc_id)    

    # check box to remove doc from db and submit that update
    remove_doc_checkbox = browser.find_element_by_id('remove-checkbox-ele')
    remove_doc_checkbox.click()

    # update
    update_button = browser.find_element_by_id('update-doc-button')
    update_button.click()

    # verify orig doc in assay_requests_old_versions collection
    old_doc = search_oldversions(doc_id)
    assert old_doc is not None

    # verify doc is removed from assay_requests collection
    new_doc = get_curr_version(doc_id)
    assert new_doc is None

    teardown_stuff(browser)   


def test_verify_remove_doc():
    browser = prep('DUNEwriter')
    browser.get(base_url+'/assay_request_update')
    doc_id = '000000000000000000000007'

    find_doc_with_id(browser, doc_id)    

    # check box to remove doc from db and submit that update
    remove_doc_checkbox = browser.find_element_by_id('remove-checkbox-ele')
    remove_doc_checkbox.click()

    # verify doc
    verify_button = browser.find_element_by_id('verify-doc-button')
    verify_button.click()

    # no doc sould be in assay_requests_old_versions collection b/c there should be no update
    old_doc = search_oldversions(doc_id)
    assert old_doc is not None

    # verify current version of doc is in assay_requests collection
    new_doc = get_curr_version(doc_id)
    assert new_doc is None

    teardown_stuff(browser)   


def test_update_no_change():
    browser = prep('DUNEwriter')
    browser.get(base_url+'/assay_request_update')
    doc_id = '000000000000000000000007'
    orig_doc = get_curr_version(doc_id)

    find_doc_with_id(browser, doc_id)    

    # update with no changes
    # this should error because data_input.name is required
    update_button = browser.find_element_by_id('update-doc-button')
    update_button.click()

    # old doc should not be in assay_requests_old_versions collection because no update was made
    old_doc = search_oldversions(doc_id)
    assert old_doc is None

    # there should be no current version of doc in assay_requests collection
    new_doc = get_curr_version(doc_id)
    assert new_doc is not None
    assert new_doc == orig_doc

    teardown_stuff(browser)   


def test_update_update_many():
    browser = prep('DUNEwriter')
    browser.get(base_url+'/assay_request_update')
    doc_id = '000000000000000000000007'
    orig_doc = get_curr_version(doc_id)

    find_doc_with_id(browser, doc_id)    

    # enter updates into update fields
    update_pairs={
        'sample.description':'test descrip',
        'sample.source':'example src',
        'sample.id':'123456test',
        'measurement.practitioner.name':'tester',
        'measurement.practitioner.contact':'tester@testing.edu',
        'measurement.technique':'test',
        'measurement.institution':'test place',
        'measurement.date':'2020-10-21',
        'measurement.description':'test descrip',
        'measurement.requestor.name':'test requestor',
        'measurement.requestor.contact':'requestor@test.gov',
        'data_source.reference':'testing',
        'data_source.input.name':'testing',
        'data_source.input.contact':'testing@test.org', 
        'data_source.input.date':'2010/18/02 2020-10-21',
        'data_source.input.notes':'test test test',
    }
    for key in update_pairs.keys():
        input_obj = browser.find_element_by_name(key)
        input_obj.send_keys(update_pairs[key])

    # update measurement values separately
    browser.find_element_by_id('add-meas-button').click()

    browser.find_element_by_name('new.measurement.results.isotope1').send_keys('K-40')

    meas_type_select = webdriver.support.ui.Select(browser.find_element_by_name('new.measurement.results.type1'))
    meas_type_select.select_by_value('range')

    meas_unit_select = webdriver.support.ui.Select(browser.find_element_by_name('new.measurement.results.unit1'))
    meas_unit_select.select_by_value('g')

    browser.find_element_by_name('new.measurement.results.valueA1').send_keys('10.3')
    browser.find_element_by_name('new.measurement.results.valueB1').send_keys('12.9')

    # update doc
    update_button = browser.find_element_by_id('update-doc-button')
    update_button.click() 

    # verify previous version of doc is in assay_requests_old_versions collection
    verify_original_doc_in_oldversions(doc_id, orig_doc)

    # verify current version of doc is in assay_requests collection
    new_doc = get_curr_version(doc_id)
    assert new_doc is not None

    # verify that all changes are present in current doc
    for key in update_pairs.keys():
        if key == 'measurement.date':
            assert new_doc['measurement']['date'][0] == datetime.datetime(2020,10,21,0,0,0)
        elif key == 'data_source.input.date':
            assert new_doc['data_source']['input']['date'][0] == datetime.datetime(2010,2,18,0,0,0)
            assert new_doc['data_source']['input']['date'][1] == datetime.datetime(2020,10,21,0,0,0)
        else:
            expected_val = update_pairs[key]
            key_parts = key.split('.')
            if len(key_parts) == 1:
                assert new_doc[key_parts[0]] == expected_val
            elif len(key_parts) == 2:
                assert new_doc[key_parts[0]][key_parts[1]] == expected_val
            elif len(key_parts) == 3:
                assert new_doc[key_parts[0]][key_parts[1]][key_parts[2]] == expected_val
    assert new_doc['measurement']['results'][0]['isotope'] == 'K-40'
    assert new_doc['measurement']['results'][0]['type'] == 'range'
    assert new_doc['measurement']['results'][0]['unit'] == 'g'
    assert new_doc['measurement']['results'][0]['value'][0] == 10.3
    assert new_doc['measurement']['results'][0]['value'][1] == 12.9

    teardown_stuff(browser)


def test_update_remove_fields():
    browser = prep('DUNEwriter')
    browser.get(base_url+'/assay_request_update')
    doc_id = '000000000000000000000002'
    orig_doc = get_curr_version(doc_id)

    find_doc_with_id(browser, doc_id)    

    remove_fields = ['grouping', 'sample.name', 'sample.source', 'measurement.date', 'measurement.description', 'measurement.results2', 'measurement.results.valueA3', 'measurement.results.valueB3', 'measurement.results.valueC3', 'data_source.input.notes']
    for field in remove_fields:
        browser.find_element_by_name('remove.'+field).click()

    # update doc
    update_button = browser.find_element_by_id('update-doc-button')
    update_button.click() 

    # verify previous version of doc is in assay_requests_old_versions collection
    verify_original_doc_in_oldversions(doc_id, orig_doc)

    # verify that all changes are present in new doc
    new_doc = get_curr_version(doc_id)
    assert new_doc is not None

    assert new_doc['grouping'] == ''
    assert new_doc['sample']['name'] == ''
    assert new_doc['sample']['source'] == ''
    assert new_doc['measurement']['date'] == []
    assert new_doc['measurement']['description'] == ''
    
    # check removed measurement result
    assert len(new_doc['measurement']['results']) == len(orig_doc['measurement']['results'])-1
    assert new_doc['measurement']['results'][0]['isotope'] == 'U-238'
    assert new_doc['measurement']['results'][1]['isotope'] == 'K-40'
    
    assert new_doc['measurement']['results'][-1]['value'] == []

    teardown_stuff(browser)


def test_verify_no_change():
    browser = prep('DUNEwriter')
    browser.get(base_url+'/assay_request_update')
    doc_id = '000000000000000000000002'
    orig_doc = get_curr_version(doc_id)

    find_doc_with_id(browser, doc_id)    

    # verify doc
    verify_button = browser.find_element_by_id('verify-doc-button')
    verify_button.click()

    # verify previous version of doc is in assay_requests_old_versions collection
    verify_original_doc_in_oldversions(doc_id, orig_doc)

    # verify current version of doc is in main data (not assay_requests) collection
    new_doc = get_validated_version(doc_id)
    assert new_doc is not None

    new_doc.pop('_id')
    new_doc.pop('_version')
    new_doc.pop('_parent_id')
    orig_doc.pop('_id')
    orig_doc.pop('_version')
    assert new_doc == orig_doc

    teardown_stuff(browser)


def test_verify_with_updates():
    browser = prep('DUNEwriter')
    browser.get(base_url+'/assay_request_update')
    doc_id = '000000000000000000000007'
    orig_doc = get_curr_version(doc_id)

    find_doc_with_id(browser, doc_id)    

    # make updates
    update_pairs={
        'sample.description':'test descrip',
        'sample.source':'example src',
        'sample.id':'123456test',
        'measurement.practitioner.name':'tester',
        'measurement.practitioner.contact':'tester@testing.edu',
        'measurement.technique':'test',
        'measurement.institution':'test place',
        'measurement.date':'2020-10-21',
        'measurement.description':'test descrip',
        'measurement.requestor.name':'test requestor',
        'measurement.requestor.contact':'requestor@test.gov',
        'data_source.reference':'testing',
        'data_source.input.name':'testing',
        'data_source.input.contact':'testing@test.org', 
        'data_source.input.date':'2010/18/02 2020-10-21',
        'data_source.input.notes':'test test test',
    }
    for key in update_pairs.keys():
        input_obj = browser.find_element_by_name(key)
        input_obj.send_keys(update_pairs[key])

    # update measurement values separately
    browser.find_element_by_id('add-meas-button').click()

    browser.find_element_by_name('new.measurement.results.isotope1').send_keys('K-40')

    meas_type_select = webdriver.support.ui.Select(browser.find_element_by_name('new.measurement.results.type1'))
    meas_type_select.select_by_value('range')

    meas_unit_select = webdriver.support.ui.Select(browser.find_element_by_name('new.measurement.results.unit1'))
    meas_unit_select.select_by_value('g')

    browser.find_element_by_name('new.measurement.results.valueA1').send_keys('10.3')
    browser.find_element_by_name('new.measurement.results.valueB1').send_keys('12.9')

    # verify doc with updates
    verify_button = browser.find_element_by_id('verify-doc-button')
    verify_button.click()

    # verify previous version of doc is in assay_requests_old_versions collection
    verify_original_doc_in_oldversions(doc_id, orig_doc)

    # verify current version of doc is in main data (not assay_requests) collection
    new_doc = get_validated_version(doc_id)
    assert new_doc is not None

    # verify that all changes are present in current doc
    for key in update_pairs.keys():
        if key == 'measurement.date':
            assert new_doc['measurement']['date'][0] == datetime.datetime(2020,10,21,0,0,0)
        elif key == 'data_source.input.date':
            assert new_doc['data_source']['input']['date'][0] == datetime.datetime(2010,2,18,0,0,0)
            assert new_doc['data_source']['input']['date'][1] == datetime.datetime(2020,10,21,0,0,0)
        else:
            expected_val = update_pairs[key]
            key_parts = key.split('.')
            if len(key_parts) == 1:
                assert new_doc[key_parts[0]] == expected_val
            elif len(key_parts) == 2:
                assert new_doc[key_parts[0]][key_parts[1]] == expected_val
            elif len(key_parts) == 3:
                assert new_doc[key_parts[0]][key_parts[1]][key_parts[2]] == expected_val
    assert new_doc['measurement']['results'][0]['isotope'] == 'K-40'
    assert new_doc['measurement']['results'][0]['type'] == 'range'
    assert new_doc['measurement']['results'][0]['unit'] == 'g'
    assert new_doc['measurement']['results'][0]['value'][0] == 10.3
    assert new_doc['measurement']['results'][0]['value'][1] == 12.9

    teardown_stuff(browser)


def test_verify_with_removed_fields():
    browser = prep('DUNEwriter')
    browser.get(base_url+'/assay_request_update')
    doc_id = '000000000000000000000002'
    orig_doc = get_curr_version(doc_id)

    find_doc_with_id(browser, doc_id)    

    remove_fields = ['grouping', 'sample.name', 'sample.source', 'measurement.date', 'measurement.description', 'measurement.results2', 'measurement.results.valueA3', 'measurement.results.valueB3', 'measurement.results.valueC3', 'data_source.input.notes']
    for field in remove_fields:
        browser.find_element_by_name('remove.'+field).click()

    # verify doc with updates
    verify_button = browser.find_element_by_id('verify-doc-button')
    verify_button.click()

    # verify previous version of doc is in assay_requests_old_versions collection
    verify_original_doc_in_oldversions(doc_id, orig_doc)

    # verify that all changes are present in new doc and that new doc is in MAIN (not assay_requests) collection
    new_doc = get_validated_version(doc_id)
    assert new_doc is not None

    assert new_doc['grouping'] == ''
    assert new_doc['sample']['name'] == ''
    assert new_doc['sample']['source'] == ''
    assert new_doc['measurement']['date'] == []
    assert new_doc['measurement']['description'] == ''
    
    # check removed measurement result
    assert len(new_doc['measurement']['results']) == len(orig_doc['measurement']['results'])-1
    assert new_doc['measurement']['results'][0]['isotope'] == 'U-238'
    assert new_doc['measurement']['results'][1]['isotope'] == 'K-40'
    
    assert new_doc['measurement']['results'][-1]['value'] == []

    teardown_stuff(browser)




def verify_original_doc_in_oldversions(doc_id, orig_doc):
    orig_doc_copy = deepcopy(orig_doc)

    # verify that original doc is in oldversions database
    old_doc = search_oldversions(doc_id)
    assert old_doc is not None

    # compare original doc to the one in the oldversions db
    for field in ['_version', '_parent_id', '_id']:
        if field in orig_doc_copy.keys():
            orig_doc_copy.pop(field)
        if field in old_doc.keys():
            old_doc.pop(field)
    assert orig_doc_copy == old_doc

def find_doc_with_id(browser, doc_id):
    browser.find_element_by_id('doc-id-input').clear()
    docid_input = browser.find_element_by_id('doc-id-input')
    docid_input.send_keys(doc_id)

    submit_button = browser.find_element_by_id('find-doc-button')
    submit_button.click()

def search_oldversions(doc_id):
    client = MongoClient('localhost', 27017)
    coll = client.dune_pytest_data.assay_requests_old_versions
    resp = coll.find({'_id':ObjectId(doc_id)})
    resp = list(resp)
    if len(resp) <= 0:
        doc = None
    else:
        doc = resp[0]
    return doc

def get_curr_version(doc_id):
    client = MongoClient('localhost', 27017)
    coll = client.dune_pytest_data.assay_requests
    resp = coll.find({})
    resp = list(resp)
    found_doc = None
    for doc in resp:
        if str(doc['_id']) == doc_id:
            found_doc = doc
        if '_parent_id' in doc.keys() and str(doc['_parent_id']) == doc_id:
            found_doc = doc
    return found_doc

def get_validated_version(doc_id):
    client = MongoClient('localhost', 27017)
    coll = client.dune_pytest_data.assays
    resp = coll.find({})
    resp = list(resp)
    found_doc = None
    for doc in resp:
        if str(doc['_id']) == doc_id:
            found_doc = doc
        if '_parent_id' in doc.keys() and str(doc['_parent_id']) == doc_id:
            found_doc = doc
    return found_doc

def prep(username):
    _teardown_db_for_test()
    _set_up_db_for_test()
    
    browser = _setup_browser()
    _logout(browser)
    _login(username, browser)

    return browser

def _login(username, browser):
    login_url = base_url+'/login'
    browser.get(login_url)
    browser.find_element_by_id("username-text-entry").clear()
    username_input = browser.find_element_by_id("username-text-entry")
    username_input.send_keys(username)
    password_input = browser.find_element_by_id("password-text-entry")
    password_input.send_keys(open(username+'_creds.txt', 'r').read().strip())

    submit_button = browser.find_element_by_id("login-submit-button")
    submit_button.click()

def _logout(browser):
    logout_url = base_url+'/logout'
    browser.get(logout_url)

def _setup_browser():
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('headless')
    options.add_argument('window-size=1200x600')
    browser = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    browser.implicitly_wait(10)
    return browser

def _teardown_browser(browser):
    browser.quit()

def teardown_stuff(browser):
    _teardown_browser(browser)
    _teardown_db_for_test()

def _set_up_db_for_test():
    client = MongoClient('localhost', 27017)
    coll = client.dune_pytest_data.assay_requests
    coll.insert_one({ "_id" : ObjectId("000000000000000000000002"), "measurement" : { "description" : "", "practitioner" : { "name" : "ICI Tracerco", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "NAA", "results" : [ { "unit" : "ppb", "value" : [ 18, 2 ], "isotope" : "U-238", "type" : "measurement" }, { "unit" : "ppb", "value" : [ 59, 2 ], "isotope" : "Th-232", "type" : "measurement" }, { "unit" : "ppm", "value" : [ 0.78, 0.02 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2013, 7, 22, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Resin, Magnex, 2:1 Thiokol 308, RAL", "id" : "ILIAS UKDM #249", "owner" : { "name" : "", "contact" : "" }, "name" : "Resin, Magnex, 2:1 Thiokol 308", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000003"), "measurement" : { "description" : "", "practitioner" : { "name" : "ICI Tracerco", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "NAA", "results" : [ { "unit" : "ppb", "value" : [ 3 ], "isotope" : "U-238", "type" : "limit" }, { "unit" : "ppb", "value" : [ 1 ], "isotope" : "Th-232", "type" : "limit" }, { "unit" : "ppm", "value" : [ 8.9, 0.2 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2016, 7, 14, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Rexalite, copper removed", "id" : "ILIAS UKDM #266", "owner" : { "name" : "", "contact" : "" }, "name" : "Rexalite, copper removed", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000004"), "measurement" : { "description" : "", "practitioner" : { "name" : "RAL", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "AA", "results" : [ { "unit" : "ppm", "value" : [ 15 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2016, 7, 14, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Salt, ICI, pure dried vacuum", "id" : "ILIAS UKDM #273", "owner" : { "name" : "", "contact" : "" }, "name" : "Salt, ICI, pure dried vacuum", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000005"), "measurement" : { "description" : "Lu < 1ppb, Rb < 10ppb", "practitioner" : { "name" : "Charles Evans/Cascade Scientific", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "GD-MS", "results" : [ { "unit" : "ppb", "value" : [ 1 ], "isotope" : "U-238", "type" : "limit" }, { "unit" : "ppb", "value" : [ 1 ], "isotope" : "Th-232", "type" : "limit" }, { "unit" : "ppm", "value" : [ 0.22 ], "isotope" : "K-40", "type" : "limit" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2013, 7, 22, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Si", "id" : "ILIAS UKDM #279", "owner" : { "name" : "", "contact" : "" }, "name" : "Si", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000006"), "measurement" : { "description" : "", "practitioner" : { "name" : "Supplier's data", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "?", "results" : [ { "unit" : "ppm", "value" : [ 0.03 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2013, 1, 30, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Silica fibre, TSL, 'Spectrosil'", "id" : "ILIAS UKDM #289", "owner" : { "name" : "", "contact" : "" }, "name" : "Silica fibre, TSL, 'Spectrosil'", "source" : "" }, "type" : "measurement", "_version" : 1 })

    # start with one unfinished assay request in the database
    assay_requests_coll = client.dune_pytest_data.assay_requests
    coll.insert_one({ "_id" : ObjectId("000000000000000000000007"), "measurement" : { "description" : "", "practitioner" : { "name" : "", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "", "results" : [ ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ ], "name" : "", "contact" : "", "notes" : "" }, "reference" : "" }, "sample" : { "description" : "This would be something", "id" : "Sure", "owner" : { "name" : "Jonna Smith", "contact" : "jonna.smith@email.com" }, "name" : "This is a required field", "source" : "" }, "type" : "measurement", "_version" : 1 })


def _teardown_db_for_test():
    client = MongoClient('localhost', 27017)
    coll = client.dune_pytest_data.assays
    assay_requests_coll = client.dune_pytest_data.assay_requests
    old_versions_coll = client.dune_pytest_data.assay_requests_old_versions
    remove_resp = coll.delete_many({})
    remove_assay_requests_resp = assay_requests_coll.delete_many({})
    remove_oldversions_resp = old_versions_coll.delete_many({})



