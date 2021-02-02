import pytest
import json
import re
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from copy import deepcopy

base_url = 'http://localhost:5000'


def test_search_all():
    browser = prep('DUNEwriter')
    browser.get(base_url+'/assay_request_search')

    select_field('all', browser)
    select_comparison('contains', browser)
    insert_value('', browser)

    search_button = browser.find_element_by_id('submit-button')
    search_button.click()

    result_buttons = browser.find_elements_by_class_name('collapsible')
    assert len(result_buttons) == 6

    teardown_stuff(browser)


def test_all_contains_testing():
    browser = prep('DUNEwriter')
    browser.get(base_url+'/assay_request_search')

    select_field('all', browser)
    select_comparison('contains', browser)
    insert_value('testing', browser)

    search_button = browser.find_element_by_id('submit-button')
    search_button.click()

    result_buttons = browser.find_elements_by_class_name('collapsible')
    assert len(result_buttons) == 3

    for i, collapsible_button in enumerate(result_buttons):
        collapsible_button.click()
        doc_info_obj = browser.find_element_by_xpath("//div[contains(@class, 'collapsible-content')]["+str(i+1)+"]")
        doc_html = doc_info_obj.get_attribute('innerHTML')
        soup = BeautifulSoup(doc_html, features="html.parser")
        found_value = False
        for field_ele in soup.find_all('p', {'class':'collapsible-field'}):
            if field_ele.text.strip().replace(':', '') in ['grouping', 'name', 'description', 'source', 'technique']:
                val_ele = field_ele.find_next('p', {'class':'collapsible-value'})
                if 'test' in val_ele.get_text().lower():
                    found_value = True
        assert found_value == True
    
    teardown_stuff(browser)

'''
def test_assay_request_search_with_meas():
    browser = prep('DUNEwriter')
    browser.get(base_url+'/assay_request_search')

    q_elements = [{'field':'measurement.results.value', 'comparison':'lt', 'value':'10', 'append':'and'}, {'field':'measurement.results.value', 'comparison':'gte', 'value':'5', 'append':''}] 

    browser = do_query(browser, q_elements)

    results = browser.page_source
    soup = BeautifulSoup(results, features="html.parser")
    result_docs = soup.find('div', {'id':'query-results-container'}).find_all('div', {'class':'collapsible-content'})
    parsed_results = parse_html(result_docs)

    for doc in parsed_results:
        assert 'measurement' in list(doc.keys())
        assert 'results' in list(doc['measurement'].keys())
        found = False
        for meas_ele in doc['measurement']['results']:
            if meas_ele['type'] == 'measurement':
                val = meas_ele['value'][0]
                if val < 10.0 and val >= 5.0:
                    found = True
            elif meas_ele['type'] == 'range':
                lower_limit = meas_ele['value'][0]
                upper_limit = meas_ele['value'][1]
                if lower_limit >= 5.0 and upper_limit < 10.0:
                    found = True
        assert found == True

    teardown_stuff(browser)


def test_assay_request_search_complicated():
    browser = prep('DUNEwriter')
    browser.get(base_url+'/assay_request_search')

    q_elements = [{'field':'measurement.results.isotope', 'comparison':'eq', 'value':'K-40', 'append':'and'}, {'field':'measurement.results.unit', 'comparison':'eq', 'value':'ppm', 'append':'and'}, {'field':'measurement.results.value', 'comparison':'gt', 'value':'0.1', 'append':'and'}, {'field':'measurement.results.value', 'comparison':'lte', 'value':'1', 'append':''}]
    browser = do_query(browser, q_elements)

    results = browser.page_source
    soup = BeautifulSoup(results, features="html.parser")
    result_docs = soup.find('div', {'id':'query-results-container'}).find_all('div', {'class':'collapsible-content'})
    parsed_results = parse_html(result_docs)

    for doc in parsed_results:
        assert 'measurement' in list(doc.keys())
        assert 'results' in list(doc['measurement'].keys())
        found = False
        for meas_ele in doc['measurement']['results']:
            if meas_ele['isotope'] == 'K-40' and meas_ele['unit'] == 'ppm':
                if meas_ele['type'] == 'measurement':
                    val = meas_ele['value'][0]
                    if val > 0.1 and val <= 1.0:
                        found = True
                elif meas_ele['type'] == 'range':
                    lower_limit = meas_ele['value'][0]
                    upper_limit = meas_ele['value'][1]
                    if lower_limit <= 1.0 and upper_limit > 0.1:
                        found = True
        assert found == True

    teardown_stuff(browser)
'''

def do_query(browser, query_elements):
    for query_element_parts in query_elements:
        field = query_element_parts['field']
        comp = query_element_parts['comparison']
        value = query_element_parts['value']
        append_type = query_element_parts['append']
        append_button_name = 'query-'+append_type+'-button' if append_type != '' else None
        
        select_field(field, browser)
        select_comparison(comp, browser)
        insert_value(value, browser)

        if append_button_name is not None:
            append_button = browser.find_element_by_id(append_button_name)
            append_button.click()

    submit_button = browser.find_element_by_id('submit-button')
    submit_button.click()

    return browser

def parse_html(soup_results):
    all_doc_info = []
    for doc in soup_results:
        doc_info = {}
        section_name = ''
        for line_ele in doc.find_all('div', {'class':'collapsible-line'}):
            keys = [ ele.get_text().replace(':', '').replace(' info', '') for ele in line_ele.find_all('p', {'class':'collapsible-field'}) ]
            values = [ ele.get_text() for ele in line_ele.find_all('p', {'class':'collapsible-value'}) ]
            if (len(keys) > 0 and keys[0] == 'data input') or (len(values) == 0 and len(keys) == 1 and keys[0] in ['grouping', 'sample', 'measurement', 'measurement values']):
                section_name = keys[0]
            if 'grouping' in keys:
                doc_info['grouping'] = values[keys.index('grouping')]
            elif 'sample' in keys:
                doc_info['sample'] = {}
            elif section_name == 'sample' and 'sample' in list(doc_info.keys()):
                if 'name' in keys:
                    doc_info['sample']['name'] = values[keys.index('name')]
                elif 'description' in keys:
                    doc_info['sample']['description'] = values[keys.index('description')]
                elif 'source' in keys:
                    doc_info['sample']['source'] = values[keys.index('source')]
            elif 'measurement' in keys:
                doc_info['measurement'] = {}
            elif section_name == 'measurement' and 'measurement' in list(doc_info.keys()):
                if 'technique' in keys:
                    doc_info['measurement']['technique'] = values[keys.index('technique')]
                elif 'institution' in keys:
                    doc_info['measurement']['institution'] = values[keys.index('institution')]
                elif 'description' in keys:
                    doc_info['measurement']['description'] = values[keys.index('description')]
            elif 'measurement values' in keys:
                doc_info['measurement']['results'] = []
            elif section_name == 'measurement values' and 'measurement' in list(doc_info.keys()) and 'results' in list(doc_info['measurement'].keys()) and ('value' in keys or 'less than' in keys or 
'greater than' in keys):
                meas_results_ele = {'isotope':values[0]}
                if keys[0] == 'value':
                    meas_results_ele['type'] = 'measurement'
                    val_eles = values[keys.index('value')+1].split()
                    meas_results_ele['value'] = [float(val_eles[0])]
                    meas_results_ele['unit'] = val_eles[-1]
                elif keys[0] == 'less than':
                    meas_results_ele['type'] = 'limit'
                    val_eles = values[keys.index('less than')+1].split()
                    meas_results_ele['value'] = [float(val_eles[0])]
                    meas_results_ele['unit'] = val_eles[-1]
                elif keys[0] == 'greater than':
                    meas_results_ele['type'] = 'range'
                    gt_eles = values[keys.index('greater than')+1].split()
                    lt_eles = values[keys.index('less than')+1].split()
                    meas_results_ele['value'] = [float(gt_eles[0]), int(lt_eles[0])]
                    meas_results_ele['unit'] = gt_eles[-1]

                doc_info['measurement']['results'].append(meas_results_ele)
            else:
                pass
        all_doc_info.append(doc_info)
    return all_doc_info

def select_field(field, browser):
    field_selector = webdriver.support.ui.Select(browser.find_element_by_name('query_field'))
    field_selector.select_by_value(field)
def select_comparison(comp, browser):
    comparison_selector = webdriver.support.ui.Select(browser.find_element_by_name('comparison_operator'))
    comparison_selector.select_by_value(comp)
def insert_value(val, browser):
    browser.find_element_by_name('query_value').clear()
    value_input = browser.find_element_by_name('query_value')
    value_input.send_keys(val)

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
    coll.insert_one({ "_id" : ObjectId("000000000000000000000004"), "measurement" : { "description" : "", "practitioner" : { "name" : "RAL", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "", "results" : [ ] }, "grouping" : "ILIAS testing UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Salt, ICI, pure dried vacuum", "id" : "ILIAS UKDM #273", "owner" : { "name" : "", "contact" : "" }, "name" : "Salt, ICI, pure dried vacuum", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000005"), "measurement" : { "description" : "Lu < 1ppb, Rb < 10ppb", "practitioner" : { "name" : "Charles Evans/Cascade Scientific", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "", "results" : [ ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Si test", "id" : "ILIAS UKDM #279", "owner" : { "name" : "", "contact" : "" }, "name" : "Si", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000006"), "measurement" : { "description" : "", "practitioner" : { "name" : "Supplier's data", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "?", "results" : [ { "unit" : "ppm", "value" : [ 0.03 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2013, 1, 30, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Silica fibre, TSL, 'Spectrosil'", "id" : "ILIAS UKDM #289", "owner" : { "name" : "", "contact" : "" }, "name" : "Silica fibre, TSL, 'Spectrosil'", "source" : "" }, "type" : "measurement", "_version" : 1 })

    # start with one unfinished assay request in the database
    assay_requests_coll = client.dune_pytest_data.assay_requests
    coll.insert_one({ "_id" : ObjectId("000000000000000000000007"), "measurement" : { "description" : "test thing", "practitioner" : { "name" : "", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "", "results" : [ ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ ], "name" : "", "contact" : "", "notes" : "" }, "reference" : "" }, "sample" : { "description" : "This would be something", "id" : "Sure", "owner" : { "name" : "Jonna Smith", "contact" : "jonna.smith@email.com" }, "name" : "This is a required field", "source" : "" }, "type" : "measurement", "_version" : 1 })


def _teardown_db_for_test():
    client = MongoClient('localhost', 27017)
    coll = client.dune_pytest_data.assays
    assay_requests_coll = client.dune_pytest_data.assay_requests
    old_versions_coll = client.dune_pytest_data.assay_requests_old_versions
    remove_resp = coll.delete_many({})
    remove_assay_requests_resp = assay_requests_coll.delete_many({})
    remove_oldversions_resp = old_versions_coll.delete_many({})


