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

insert_pairs = {
    'grouping':'', #required
    'sample.name':'', #required
    'sample.description':'',
    'sample.source':'',
    'sample.id':'',
    'sample.owner.name':'', #required
    'sample.owner.contact':'' #required (email)
}

def test_insert_full_doc():
    browser = prep('DUNEreader')
    browser.get(base_url+'/assay_request')

    # insert values 
    insert_pairs = {
        'grouping':'Testing',
        'sample.name':'some type of sample',
        'sample.description':'this is a test sample and it should pass',
        'sample.source':'another test value',
        'sample.id':'testing id',
        'sample.owner.name':'my name',
        'sample.owner.contact':'tester@testing.com'
    }
    
    for key in insert_pairs:
        value = insert_pairs[key]
        browser.find_element_by_name(key).send_keys(value)

    # submit
    submit_button = browser.find_element_by_id('submit-record-button')
    submit_button.click()

    # get new doc id
    new_doc_message = browser.find_element_by_tag_name('h3').text
    assert 'assay request doc id: ' in new_doc_message
    doc_id = new_doc_message.replace('assay request doc id: ', '').strip()

    # find doc we just inserted and verify it has the correct values
    new_doc = get_curr_version(doc_id)
    assert new_doc is not None
    for key in insert_pairs:
        assert check_if_keypair_in_doc(key, insert_pairs[key], new_doc) == True

    teardown_stuff(browser)   

insert_pairs = [
    ({'sample.name':'some type of sample','sample.owner.name':'my name','sample.owner.contact':'tester@testing.com'}),
    ({'grouping':'Testing','sample.owner.name':'my name','sample.owner.contact':'tester@testing.com'}),
    ({'grouping':'Testing','sample.name':'some type of sample','sample.owner.contact':'tester@testing.com'}),
    ({'grouping':'Testing','sample.name':'some type of sample','sample.owner.name':'my name'}),
]
@pytest.mark.parametrize('key_val_pairs', insert_pairs)
def test_missing_required_fields(key_val_pairs):
    browser = prep('DUNEreader')
    browser.get(base_url+'/assay_request')
    orig_docs = get_all_curr_docs()
    orig_num_docs = len(orig_docs)

    # insert values 
    for key in key_val_pairs:
        value = key_val_pairs[key]
        browser.find_element_by_name(key).send_keys(value)

    # submit
    submit_button = browser.find_element_by_id('submit-record-button')
    submit_button.click()
    
    # verify no doc was inserted
    docs = get_all_curr_docs()
    assert len(docs) == orig_num_docs

    # verify no doc has these values
    found_accumulator = True
    for doc in docs:
        found_pair = False
        for key in key_val_pairs:
            found_pair = check_if_keypair_in_doc(key, key_val_pairs[key], doc)
        found_accumulator = found_accumulator and found_pair
    assert found_accumulator == False

    teardown_stuff(browser)

bad_emails = [
    ('test'),
    ('test@'),
    ('@test'),
    ('@test.com'),
    ('test testing'),
]
@pytest.mark.parametrize('bad_email', bad_emails)
def test_bad_email(bad_email):
    browser = prep('DUNEreader')
    browser.get(base_url+'/assay_request')
    orig_docs = get_all_curr_docs()
    orig_num_docs = len(orig_docs)

    # insert values 
    insert_pairs = {
        'grouping':'Testing',
        'sample.name':'some type of sample',
        'sample.description':'this is a test sample and it should pass',
        'sample.source':'another test value',
        'sample.id':'testing id',
        'sample.owner.name':'my name',
    }
    for key in insert_pairs:
        value = insert_pairs[key]
        browser.find_element_by_name(key).send_keys(value)
    browser.find_element_by_name('sample.owner.contact').send_keys(bad_email) # insert bad email

    # submit
    submit_button = browser.find_element_by_id('submit-record-button')
    submit_button.click()
    
    # verify no doc was inserted
    docs = get_all_curr_docs()
    assert len(docs) == orig_num_docs
    for doc in docs:
        assert check_if_keypair_in_doc('sample.owner.contact', bad_email, doc) == False

    teardown_stuff

def check_if_keypair_in_doc(html_key, val, doc):
    found_pair = False
    key_parts = html_key.split('.')
    if len(key_parts) == 1:
        if doc[key_parts[0]] == val:
            found_pair = True
    elif len(key_parts) == 2:
        if doc[key_parts[0]][key_parts[1]] == val:
            found_pair = True
    elif len(key_parts) == 3:
        if doc[key_parts[0]][key_parts[1]][key_parts[2]] == val:
            found_pair = True
    return found_pair

def get_all_curr_docs():
    client = MongoClient('localhost', 27017)
    coll = client.dune_pytest_data.assay_requests
    resp = coll.find({})
    resp = list(resp)
    return resp

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



