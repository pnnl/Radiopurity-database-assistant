import os
import json
import scrypt
from bson.objectid import ObjectId
from selenium import webdriver
from pymongo import MongoClient

base_url = "http://localhost:5000"

def experiment_login(experiment_name, test_password, browser):
    login_url = base_url+'/add_experiment_credentials'
    browser.get(login_url)
    
    browser.find_element_by_id("username-text-entry").clear()
    username_input = browser.find_element_by_id("username-text-entry")
    username_input.send_keys(experiment_name)
    password_input = browser.find_element_by_id("password-text-entry")
    password_input.send_keys(test_password)

    submit_button = browser.find_element_by_id("login-submit-button")
    submit_button.click()

def experiment_logout(experiment_name, browser):
    logout_url = base_url+'/remove_experiment_credentials'
    browser.get(logout_url)
    
    user_select = webdriver.support.ui.Select(browser.find_element_by_id('logged_in_experiments'))
    #user_options = user_select.options
    user_select.select_by_value(experiment_name)

    submit_button = browser.find_element_by_id("login-submit-button")
    submit_button.click()

def release_experiment(experiment_name, browser):
    release_url = base_url+'/make_public'
    browser.get(release_url)

    user_select = webdriver.support.ui.Select(browser.find_element_by_id('logged_in_experiments'))
    #user_options = user_select.options
    user_select.select_by_value(experiment_name)

    submit_button = browser.find_element_by_id("login-submit-button")
    submit_button.click()

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

def get_config():
    config_name = os.getenv('DUNE_API_CONFIG_NAME')
    config_dict = {}
    with open(config_name, 'r') as config:
        config_dict = json.load(config)
    return config_dict

def set_up_db_for_test(docs):
    db_host, db_port, db_name = get_mongodb_config_info()
    client = MongoClient(db_host, db_port)
    db_obj = client[db_name]
    
    # add docs
    coll = db_obj.assays
    for doc in docs:
        coll.insert_one(doc)

    # add private exp credentials
    coll = db_obj.users
    config_dict = get_config()
    salt = config_dict['salt']
    '''user_creds = config_dict["users"]
    users = []
    for user in user_creds:
        users.append({"experiment_name":user["experiment_name"], "password_hashed":scrypt.hash(user["password"], salt, N=16)})
        users.append({"experiment_name":user["experiment_name"]+"_ADMIN", "password_hashed":scrypt.hash(user["password"]+"admin", salt, N=16)})
    '''
    users = [
        {"experiment_name":"TEST_EXPERIMENT_1", "password_hashed":scrypt.hash("password1", salt, N=16)},
        {"experiment_name":"TEST_EXPERIMENT_1_ADMIN", "password_hashed":scrypt.hash("password1admin", salt, N=16)},
        {"experiment_name":"TEST_EXPERIMENT_2", "password_hashed":scrypt.hash("password2", salt, N=16)},
        {"experiment_name":"TEST_EXPERIMENT_2_ADMIN", "password_hashed":scrypt.hash("password2admin", salt, N=16)},
    ]
    #'''
    for u in users:
        r = db_obj.users.insert_one(u)

def teardown_db_for_test():
    db_host, db_port, db_name = get_mongodb_config_info()
    client = MongoClient(db_host, db_port)

    # remove all fake docs
    coll = client[db_name].assays
    old_versions_coll = client[db_name].assays_old_versions
    remove_resp = coll.delete_many({})
    remove_oldversions_resp = old_versions_coll.delete_many({})

    # remove all fake experiment creds
    coll = client[db_name].users
    remove_resp = coll.delete_many({})

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


