import os
import json
from bson.objectid import ObjectId
from selenium import webdriver
from pymongo import MongoClient

base_url = "http://localhost:5000"

'''
def login(username, browser):
    login_url = base_url+'/login'
    browser.get(login_url)
    browser.find_element_by_id("username-text-entry").clear()
    username_input = browser.find_element_by_id("username-text-entry")
    username_input.send_keys(username)
    password_input = browser.find_element_by_id("password-text-entry")
    password_input.send_keys(open(username+'_creds.txt', 'r').read().strip())

    submit_button = browser.find_element_by_id("login-submit-button")
    submit_button.click()

def logout(browser):
    logout_url = base_url+'/logout'
    browser.get(logout_url)
'''

from webdriver_manager.chrome import ChromeDriverManager
def setup_browser():
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('headless')
    options.add_argument('window-size=1200x600')
    options.add_argument('--disable-dev-shm-usage')
    browser = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    return browser

def setup_browser_old():
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('headless')
    options.add_argument('window-size=1200x600')
    options.add_argument('--disable-dev-shm-usage')
    browser = webdriver.Chrome(options=options)
    return browser

def teardown_browser(browser):
    browser.quit()

def get_mongodb_config_info():
    with open(os.environ.get('DUNE_API_CONFIG_NAME'), 'r') as rf:
        config = json.load(rf)
        return config['mongodb_host'], config['mongodb_port'], config['database']

def set_up_db_for_test(docs):
    db_host, db_port, db_name = get_mongodb_config_info()
    client = MongoClient(db_host, db_port)
    db_obj = client[db_name]
    coll = db_obj.assays
    for doc in docs:
        coll.insert_one(doc)

def teardown_db_for_test():
    db_host, db_port, db_name = get_mongodb_config_info()
    client = MongoClient(db_host, db_port)
    coll = client[db_name].assays
    old_versions_coll = client[db_name].assays_old_versions
    remove_resp = coll.delete_many({})
    remove_oldversions_resp = old_versions_coll.delete_many({})


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
    host, port, db_name = get_mongodb_config_info()
    client = MongoClient(host, port)
    coll = client[db_name].assays_old_versions
    resp = coll.find({'_id':ObjectId(doc_id)})
    resp = list(resp)
    if len(resp) <= 0:
        doc = None
    else:
        doc = resp[0]
    return doc

def get_curr_version(doc_id):
    host, port, db_name = get_mongodb_config_info()
    client = MongoClient(host, port)
    coll = client[db_name].assays
    resp = coll.find({})
    resp = list(resp)
    found_doc = None
    for doc in resp:
        if str(doc['_id']) == doc_id:
            found_doc = doc
        if '_parent_id' in doc.keys() and str(doc['_parent_id']) == doc_id:
            found_doc = doc
    return found_doc


