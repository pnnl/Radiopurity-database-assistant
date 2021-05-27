import os
import pytest
import json
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

base_url = 'http://localhost:5000'


def test_update_remove_doc():
    browser = prep('DUNEwriter')
    browser.get(base_url+'/update')
    doc_id = '000000000000000000000002'

    find_doc_with_id(browser, doc_id)

    # check box to remove doc from db and submit that update
    remove_doc_checkbox = browser.find_element_by_id('remove-checkbox-ele')
    remove_doc_checkbox.click()

    update_button = browser.find_element_by_id('update-doc-button')
    update_button.click()

    # search the database for all docs
    browser.get(base_url+'/search')
    field_select = webdriver.support.ui.Select(browser.find_element_by_id('query_field'))
    field_select.select_by_value('all')

    comparison_select = webdriver.support.ui.Select(browser.find_element_by_id('comparison_operator'))
    comparison_options = comparison_select.options
    comparison_select.select_by_value('contains')

    browser.find_element_by_id('query_value').clear()
    value_input = browser.find_element_by_id('query_value')
    value_input.send_keys('')

    submit_button = browser.find_element_by_id('submit-query')
    submit_button.click()

    # verify that none of the docs have the id of the doc we just removed
    results = browser.page_source
    soup = BeautifulSoup(results, features="html.parser")
    result_docs = soup.find('div', {'id':'query-results-container'}).find_all('div', {'class':'collapsible-content'})
    found = False
    for doc in result_docs:
        for section in doc.find_all('div', {'class':'collapsible-line'}):
            for field_name in section.find_all('p', {'class':'collapsible-field'}):
                if field_name.get_text() == 'database id:':
                    if section.find('p', {'class':'collapsible-value'}).get_text() == doc_id:
                        found = True
    assert found == False

    # verify that the doc we removed is in the oldversions db
    orig_doc = search_oldversions(doc_id)
    assert orig_doc is not None

    teardown_stuff(browser)


def test_update_nochange():
    browser = prep('DUNEwriter')
    browser.get(base_url+'/update')
    doc_id = '000000000000000000000002'

    # get original doc for future comparison
    orig_doc = get_curr_version(doc_id) 

    find_doc_with_id(browser, doc_id)

    # update with no change
    update_button = browser.find_element_by_id('update-doc-button')
    update_button.click()

    # verify that updated doc is in database
    new_doc = get_curr_version(doc_id)
    assert new_doc is not None

    verify_original_doc_in_oldversions(doc_id, orig_doc)

    teardown_stuff(browser)


def test_update_update_all():
    browser = prep('DUNEwriter')
    browser.get(base_url+'/update')
    doc_id = '000000000000000000000002'

    # get original doc for future comparison
    orig_doc = get_curr_version(doc_id)

    find_doc_with_id(browser, doc_id)

    # enter updates into update fields
    update_pairs={
        'grouping':'new test value', 
        'sample.name':'testing sample name',
        'sample.description':'test descrip',
        'sample.source':'example src',
        'sample.id':'123456test',
        'sample.owner.name':'test',
        'sample.owner.contact':'test@test.com',
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
    browser.find_element_by_name('measurement.results.isotope1').send_keys('K-40')

    meas_type_select = webdriver.support.ui.Select(browser.find_element_by_name('measurement.results.type1'))
    meas_type_select.select_by_value('range')

    meas_unit_select = webdriver.support.ui.Select(browser.find_element_by_name('measurement.results.unit1'))
    meas_unit_select.select_by_value('g')

    browser.find_element_by_name('measurement.results.valueA1').send_keys('10.3')
    browser.find_element_by_name('measurement.results.valueB1').send_keys('12.9')

    # update doc
    update_button = browser.find_element_by_id('update-doc-button')
    update_button.click() 

    verify_original_doc_in_oldversions(doc_id, orig_doc)

    # verify that all changes are present in new doc
    new_doc = get_curr_version(doc_id)
    assert new_doc is not None

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

def test_update_update_twice():
    browser = prep('DUNEwriter')
    browser.get(base_url+'/update')
    doc_id = '000000000000000000000002'

    # PERFORM FIRST UPDATE AND TEST
    # get original doc for future comparison
    orig_doc = get_curr_version(doc_id)

    find_doc_with_id(browser, doc_id)

    update_pairs = {
        'grouping':'new test value',
        'data_source.input.contact':'testing@test.org',
        'measurement.date':'2020-10-21',
    }
    for key in update_pairs.keys():
        input_obj = browser.find_element_by_name(key)
        input_obj.send_keys(update_pairs[key])

    meas_unit_select = webdriver.support.ui.Select(browser.find_element_by_name('measurement.results.unit1'))
    meas_unit_select.select_by_value('g')

    # update doc
    update_button = browser.find_element_by_id('update-doc-button')
    update_button.click() 

    verify_original_doc_in_oldversions(doc_id, orig_doc)

    # verify that all changes are present in new doc
    new_doc_v1 = get_curr_version(doc_id)
    assert new_doc_v1 is not None

    # ensure updated values are updated
    assert new_doc_v1['grouping'] == 'new test value'
    assert new_doc_v1['data_source']['input']['contact'] == 'testing@test.org'
    assert new_doc_v1['measurement']['date'][0] == datetime.datetime(2020,10,21,0,0,0)
    assert new_doc_v1['measurement']['results'][0]['unit'] == 'g'

    # PERFORM SECOND UPDATE AND TEST
    orig_doc = new_doc_v1
    doc_id = str(orig_doc['_id'])
    
    find_doc_with_id(browser, doc_id)

    update_pairs = {
        'grouping':'test value two',
    }
    for key in update_pairs.keys():
        input_obj = browser.find_element_by_name(key)
        input_obj.send_keys(update_pairs[key])

    # update doc
    update_button = browser.find_element_by_id('update-doc-button')
    update_button.click() 

    verify_original_doc_in_oldversions(doc_id, orig_doc)

    # verify that all changes are present in new doc
    new_doc_v2 = get_curr_version(doc_id)
    assert new_doc_v2 is not None

    # ensure updated values are updated
    assert new_doc_v2['grouping'] == 'test value two'

    teardown_stuff(browser)

def test_update_new_meas_obj():
    browser = prep('DUNEwriter')
    browser.get(base_url+'/update')
    doc_id = '000000000000000000000002'

    # PERFORM FIRST UPDATE AND TEST
    # get original doc for future comparison
    orig_doc = get_curr_version(doc_id)

    find_doc_with_id(browser, doc_id)

    # add a new measurement results field
    add_meas_button = browser.find_element_by_id('add-meas-button')
    add_meas_button.click()
    
    browser.find_element_by_name('measurement.results.isotope2').send_keys('U-235')
    
    meas_type_select = webdriver.support.ui.Select(browser.find_element_by_name('measurement.results.type2'))
    meas_type_select.select_by_value('range')

    meas_type_select = webdriver.support.ui.Select(browser.find_element_by_name('measurement.results.unit2'))
    meas_type_select.select_by_value('g')

    browser.find_element_by_name('measurement.results.valueA2').send_keys('0.3')
    browser.find_element_by_name('measurement.results.valueB2').send_keys('2.1')

    # update doc
    update_button = browser.find_element_by_id('update-doc-button')
    update_button.click() 

    verify_original_doc_in_oldversions(doc_id, orig_doc)

    # verify that all changes are present in new doc
    new_doc = get_curr_version(doc_id)
    assert new_doc is not None

    # ensure updated values are updated
    assert new_doc['measurement']['results'][1]['isotope'] == 'U-235'
    assert new_doc['measurement']['results'][1]['unit'] == 'g'
    assert new_doc['measurement']['results'][1]['type'] == 'range'
    assert new_doc['measurement']['results'][1]['value'] == [0.3, 2.1]

    teardown_stuff(browser) 

def test_update_remove_fields():
    browser = prep('DUNEwriter')
    browser.get(base_url+'/update')
    doc_id = '000000000000000000000002'

    # PERFORM FIRST UPDATE AND TEST
    # get original doc for future comparison
    orig_doc = get_curr_version(doc_id)

    find_doc_with_id(browser, doc_id)

    remove_fields = ['grouping', 'sample.name', 'sample.source', 'measurement.date', 'measurement.description', 'measurement.results2', 'measurement.results.valueA3', 'measurement.results.valueB3', 'measurement.results.valueC3', 'data_source.input.notes']
    for field in remove_fields:
        browser.find_element_by_name('remove.'+field).click()

    # update doc
    update_button = browser.find_element_by_id('update-doc-button')
    update_button.click() 

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

def verify_original_doc_in_oldversions(doc_id, orig_doc):
    # verify that original doc is in oldversions database
    old_doc = search_oldversions(doc_id)
    assert old_doc is not None

    # compare original doc to the one in the oldversions db
    for field in ['_version', '_parent_id', '_id']:
        if field in orig_doc.keys():
            orig_doc.pop(field)
        if field in old_doc.keys():
            old_doc.pop(field)
    assert orig_doc == old_doc

def find_doc_with_id(browser, doc_id):
    browser.find_element_by_id('doc-id-input').clear()
    docid_input = browser.find_element_by_id('doc-id-input')
    docid_input.send_keys(doc_id)

    submit_button = browser.find_element_by_id('find-doc-button')
    submit_button.click()

def search_oldversions(doc_id):
    client = MongoClient('localhost', 27017)
    coll = client.dune_pytest_data.assays_old_versions
    resp = coll.find({'_id':ObjectId(doc_id)})
    resp = list(resp)
    if len(resp) <= 0:
        doc = None
    else:
        doc = resp[0]
    return doc

def get_curr_version(doc_id):
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

def get_mongodb_config_info():
    with open(os.environ.get('DUNE_API_CONFIG_NAME'), 'r') as rf:
        config = json.load(rf)
        return config['mongodb_host'], config['mongodb_port'], config['database']

def _set_up_db_for_test():
    db_host, db_port, db_name = get_mongodb_config_info()
    client = MongoClient(db_host, db_port)
    db_obj = client[db_name]
    coll = db_obj.assays
    coll.insert_one({ "_id" : ObjectId("000000000000000000000002"), "measurement" : { "description" : "", "practitioner" : { "name" : "ICI Tracerco", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "NAA", "results" : [ { "unit" : "ppb", "value" : [ 18, 2 ], "isotope" : "U-238", "type" : "measurement" }, { "unit" : "ppb", "value" : [ 59, 2 ], "isotope" : "Th-232", "type" : "measurement" }, { "unit" : "ppm", "value" : [ 0.78, 0.02 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2013, 7, 22, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Resin, Magnex, 2:1 Thiokol 308, RAL", "id" : "ILIAS UKDM #249", "owner" : { "name" : "", "contact" : "" }, "name" : "Resin, Magnex, 2:1 Thiokol 308", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000003"), "measurement" : { "description" : "", "practitioner" : { "name" : "ICI Tracerco", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "NAA", "results" : [ { "unit" : "ppb", "value" : [ 3 ], "isotope" : "U-238", "type" : "limit" }, { "unit" : "ppb", "value" : [ 1 ], "isotope" : "Th-232", "type" : "limit" }, { "unit" : "ppm", "value" : [ 8.9, 0.2 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2016, 7, 14, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Rexalite, copper removed", "id" : "ILIAS UKDM #266", "owner" : { "name" : "", "contact" : "" }, "name" : "Rexalite, copper removed", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000004"), "measurement" : { "description" : "", "practitioner" : { "name" : "RAL", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "AA", "results" : [ { "unit" : "ppm", "value" : [ 15 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2016, 7, 14, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Salt, ICI, pure dried vacuum", "id" : "ILIAS UKDM #273", "owner" : { "name" : "", "contact" : "" }, "name" : "Salt, ICI, pure dried vacuum", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000005"), "measurement" : { "description" : "Lu < 1ppb, Rb < 10ppb", "practitioner" : { "name" : "Charles Evans/Cascade Scientific", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "GD-MS", "results" : [ { "unit" : "ppb", "value" : [ 1 ], "isotope" : "U-238", "type" : "limit" }, { "unit" : "ppb", "value" : [ 1 ], "isotope" : "Th-232", "type" : "limit" }, { "unit" : "ppm", "value" : [ 0.22 ], "isotope" : "K-40", "type" : "limit" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2013, 7, 22, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Si", "id" : "ILIAS UKDM #279", "owner" : { "name" : "", "contact" : "" }, "name" : "Si", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000006"), "measurement" : { "description" : "", "practitioner" : { "name" : "Supplier's data", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "?", "results" : [ { "unit" : "ppm", "value" : [ 0.03 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2013, 1, 30, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Silica fibre, TSL, 'Spectrosil'", "id" : "ILIAS UKDM #289", "owner" : { "name" : "", "contact" : "" }, "name" : "Silica fibre, TSL, 'Spectrosil'", "source" : "" }, "type" : "measurement", "_version" : 1 })



def _teardown_db_for_test():
    db_host, db_port, db_name = get_mongodb_config_info()
    client = MongoClient(db_host, db_port)
    coll = client[db_name].assays
    old_versions_coll = client[db_name].assays_old_versions
    remove_resp = coll.delete_many({})
    resmove_oldversions_resp = old_versions_coll.delete_many({})



