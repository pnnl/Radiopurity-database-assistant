import pytest
import json
from pymongo import MongoClient
from bson.objectid import ObjectId
from dunetoolkit import set_ui_db
import datetime
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

base_url = 'http://localhost:5000'


test_data = [
    ([{'field':'all', 'comparison':'contains', 'value':'', 'append':''}], 'all contains ', 45),
    ([{'field':'all', 'comparison':'contains', 'value':'testing', 'append':''}], 'all contains testing', 7),
    ([{'field':'grouping', 'comparison':'contains', 'value':'one', 'append':'or'}, {'field':'sample.name', 'comparison':'notcontains', 'value':'two', 'append':'and'}, {'field':'sample.description', 'comparison':'eq', 'value':'three', 'append':''}], 'grouping contains one\nOR\nsample.name does not contain two\nAND\nsample.description equals three', 0),
    ([{'field':'measurement.results.value', 'comparison':'lt', 'value':'10', 'append':'and'}, {'field':'measurement.results.value', 'comparison':'gte', 'value':'5', 'append':''}], "measurement.results.value is less than 10.0\nAND\nmeasurement.results.value is greater than or equal to 5.0", 5),
    ([{'field':'measurement.results.unit', 'comparison':'eq', 'value':'ppm', 'append':'and'}, {'field':'measurement.results.value', 'comparison':'eq', 'value':'37.2', 'append':'or'}, {'field':'measurement.results.value', 'comparison':'gt', 'value':'20.4', 'append':'and'}, {'field':'measurement.results.value', 'comparison':'lte', 'value':'40.6', 'append':'and'}, {'field':'grouping', 'comparison':'contains', 'value':'majorana', 'append':''}], "measurement.results.unit equals ppm\nAND\nmeasurement.results.value equals 37.2\nOR\nmeasurement.results.value is greater than 20.4\nAND\nmeasurement.results.value is less than or equal to 40.6\nAND\ngrouping contains majorana", 0),
    ([{'field':'sample.description', 'comparison':'contains', 'value':'copper', 'append':''}], 'sample.description contains ["Copper", "Cu"]', 24),
    ([{'field':'measurement.results.isotope', 'comparison':'eq', 'value':'K-40', 'append':'and'}, {'field':'measurement.results.unit', 'comparison':'eq', 'value':'ppm', 'append':'and'}, {'field':'measurement.results.value', 'comparison':'gt', 'value':'0.1', 'append':'and'}, {'field':'measurement.results.value', 'comparison':'lte', 'value':'1', 'append':''}], 'measurement.results.isotope equals K-40\nAND\nmeasurement.results.unit equals ppm\nAND\nmeasurement.results.value is greater than 0.1\nAND\nmeasurement.results.value is less than or equal to 1.0', 4),
    ([{'field':'measurement.results.type', 'comparison':'eq', 'value':'range', 'append':'and'}, {'field':'measurement.results.value', 'comparison':'gt', 'value':'200', 'append':'and'}, {'field':'measurement.results.value', 'comparison':'lt', 'value':'1', 'append':''}], 'measurement.results.type equals range\nAND\nmeasurement.results.value is greater than 200.0\nAND\nmeasurement.results.value is less than 1.0', 0),
    ([{'field':'grouping', 'comparison':'contains', 'value':'majorana', 'append':'and'}, {'field':'measurement.results.isotope', 'comparison':'eq', 'value':'U-238', 'append':'and'}, {'field':'measurement.results.value', 'comparison':'lte', 'value':'1.0', 'append':'and'}, {'field':'measurement.results.unit', 'comparison':'eq', 'value':'ppt', 'append':''}], "grouping contains majorana\nAND\nmeasurement.results.isotope equals U-238\nAND\nmeasurement.results.value is less than or equal to 1.0\nAND\nmeasurement.results.unit equals ppt", 15),
    ([{'field':'grouping', 'comparison':'contains', 'value':'testing', 'append':'or'}, {'field':'measurement.results.isotope', 'comparison':'eq', 'value':'actinium', 'append':''}], 'grouping contains testing\nOR\nmeasurement.results.isotope equals ["Actinium", "Ac"]', 1),
    ([{'field':'grouping', 'comparison':'contains', 'value':'testing', 'append':'or'}, {'field':'measurement.results.isotope', 'comparison':'eq', 'value':'actinium', 'append':'and'}, {'field':'measurement.results.unit', 'comparison':'eq', 'value':'ppm', 'append':'or'}, {'field':'measurement.results.unit', 'comparison':'eq', 'value':'ppb', 'append':''}], 'grouping contains testing\nOR\nmeasurement.results.isotope equals ["Actinium", "Ac"]\nAND\nmeasurement.results.unit equals ppm\nOR\nmeasurement.results.unit equals ppb', 14),
    #([{'field':'', 'comparison':'', 'value':'', 'append':''}], '', 0),
]
@pytest.mark.parametrize('query_elements,human_query_string,num_expected_results',test_data)
def test_search(query_elements, human_query_string, num_expected_results):
    browser = prep('DUNEreader')

    browser.get(base_url+'/search')

    browser = do_query(browser, query_elements)

    assert browser.current_url == base_url+'/search'

    results = browser.page_source

    soup = BeautifulSoup(results)
    result_docs = soup.find('div', {'id':'query-results-container'}).find_all('div', {'class':'collapsible-content'})
    num_docs = len(result_docs)
    query_text = '\n'.join([ p_ele.get_text() for p_ele in soup.find('div', {'id':'final-query-text-container'}).find_all('p') ])
    assert query_text == human_query_string

    #parse_html(result_docs)

    assert num_docs==num_expected_results

    teardown_stuff(browser)



def test_examine_results_1():
    browser = prep('DUNEreader')

    browser.get(base_url+'/search')

    # "measurement.results.value is less than 10.0\nAND\nmeasurement.results.value is greater than or equal to 5.0"
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


def test_examine_results_2():
    browser = prep('DUNEreader')

    browser.get(base_url+'/search')

    # 'measurement.results.isotope equals K-40\nAND\nmeasurement.results.unit equals ppm\nAND\nmeasurement.results.value is greater than 0.1\nAND\nmeasurement.results.value is less than or equal to 1.0'
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

    
def do_query(browser, query_elements):
    for query_element_parts in query_elements:
        field = query_element_parts['field']
        comp = query_element_parts['comparison']
        value = query_element_parts['value']
        append_type = query_element_parts['append']
        append_button_name = 'query-'+append_type+'-button' if append_type != '' else None

        field_select = webdriver.support.ui.Select(browser.find_element_by_id('query_field'))
        field_select.select_by_value(field)

        comparison_select = webdriver.support.ui.Select(browser.find_element_by_id('comparison_operator'))
        comparison_options = comparison_select.options
        #assert [ comparison_options[i].text for i in range(len(comparison_options)) ] == ['contains']
        comparison_select.select_by_value(comp)

        browser.find_element_by_id('query_value').clear()
        value_input = browser.find_element_by_id('query_value')
        value_input.send_keys(value)

        if append_button_name is not None:
            append_button = browser.find_element_by_id(append_button_name)
            append_button.click()

    submit_button = browser.find_element_by_id('submit-query')
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
            #print(keys)
            #print(values)
            if (len(keys) > 0 and keys[0] == 'data input') or (len(values) == 0 and len(keys) == 1 and keys[0] in ['grouping', 'sample', 'measurement', 'measurement values']):
                section_name = keys[0]
            
            if 'grouping' in keys:
                #print('found grouping', keys)
                doc_info['grouping'] = values[keys.index('grouping')]
            elif 'sample' in keys:
                #print('found sample',keys)
                doc_info['sample'] = {}
            elif section_name == 'sample' and 'sample' in list(doc_info.keys()):
                #print('found sample subsec',keys)
                if 'name' in keys:
                    doc_info['sample']['name'] = values[keys.index('name')]
                elif 'description' in keys:
                    doc_info['sample']['description'] = values[keys.index('description')]
                elif 'source' in keys:
                    doc_info['sample']['source'] = values[keys.index('source')]
            elif 'measurement' in keys:
                #print('found meas',keys)
                doc_info['measurement'] = {}
            elif section_name == 'measurement' and 'measurement' in list(doc_info.keys()):
                #print('found meas subsec',keys)
                if 'technique' in keys:
                    doc_info['measurement']['technique'] = values[keys.index('technique')]
                elif 'institution' in keys:
                    doc_info['measurement']['institution'] = values[keys.index('institution')]
                elif 'description' in keys:
                    doc_info['measurement']['description'] = values[keys.index('description')]
            elif 'measurement values' in keys:
                #print('found meas values',keys)
                doc_info['measurement']['results'] = []
            elif section_name == 'measurement values' and 'measurement' in list(doc_info.keys()) and 'results' in list(doc_info['measurement'].keys()) and ('value' in keys or 'less than' in keys or 
'greater than' in keys):
                #print('found meas values subsec',keys)
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
            #elif 'data input' in keys:
            #    doc_info['data_input'] = {'name':values[keys.index('data input')]}
            #elif 'data_input' in list(doc_info).keys()):
            else:
                #print('OTHER',keys)
                pass
            #print(doc_info)
            #print()
        #print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

        '''
        print(doc_info)
        print(query_elements)

        for query_element in query_elements:
            field = query_element['field']
            comparison = query_element['comparison']
            value = 
        '''
        all_doc_info.append(doc_info)

    return all_doc_info

def prep(username):
    _teardown_db_for_test()
    _set_up_db_for_test()
#    successful_db_change = set_ui_db('dune_pytest_data', 'test_data')
    
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
    coll = client.dune_pytest_data.test_data
    coll.insert_one({ "_id" : ObjectId("000000000000000000000002"), "measurement" : { "description" : "", "practitioner" : { "name" : "ICI Tracerco", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "NAA", "results" : [ { "unit" : "ppb", "value" : [ 0.18, 2 ], "isotope" : "U-238", "type" : "measurement" }, { "unit" : "ppb", "value" : [ 59, 2 ], "isotope" : "Th-232", "type" : "measurement" }, { "unit" : "ppm", "value" : [ 0.78, 0.02 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "Majorana (2016)", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2013, 7, 22, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "we are performing a test right now" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Resin, Magnex, 2:1 Thiokol 308, RAL", "id" : "ILIAS UKDM #249", "owner" : { "name" : "", "contact" : "" }, "name" : "Resin, Magnex, 2:1 Thiokol 308", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000003"), "measurement" : { "description" : "", "practitioner" : { "name" : "ICI Tracerco", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "NAA testing", "results" : [ { "unit" : "ppb", "value" : [ 3 ], "isotope" : "U-238", "type" : "limit" }, { "unit" : "ppb", "value" : [ 1 ], "isotope" : "Th-232", "type" : "limit" }, { "unit" : "ppm", "value" : [ 0.89, 0.2 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2016, 7, 14, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Rexalite, copper removed", "id" : "ILIAS UKDM #266", "owner" : { "name" : "", "contact" : "" }, "name" : "Rexalite, copper removed", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000004"), "measurement" : { "description" : "", "practitioner" : { "name" : "RAL", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "AA", "results" : [ { "unit" : "ppb", "value" : [ 150 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2016, 7, 14, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Salt, ICI, pure dried vacuum TESTING", "id" : "ILIAS UKDM #273", "owner" : { "name" : "", "contact" : "" }, "name" : "Salt, ICI, pure dried vacuum", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000005"), "measurement" : { "description" : "Lu < 1ppb, Rb < 10ppb", "practitioner" : { "name" : "Charles Evans/Cascade Scientific", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "GD-MS", "results" : [ { "unit" : "ppb", "value" : [ 1 ], "isotope" : "U-238", "type" : "limit" }, { "unit" : "ppb", "value" : [ 1 ], "isotope" : "Th-232", "type" : "limit" }, { "unit" : "ppm", "value" : [ 0.22 ], "isotope" : "K-40", "type" : "limit" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2013, 7, 22, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "copper COPPER" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Si", "id" : "ILIAS UKDM #279", "owner" : { "name" : "", "contact" : "" }, "name" : "Si", "source" : "" }, "type" : "measurement", "_version" : 1 })
    coll.insert_one({ "_id" : ObjectId("000000000000000000000006"), "measurement" : { "description" : "", "practitioner" : { "name" : "Supplier's data", "contact" : "" }, "requestor" : { "name" : "", "contact" : "" }, "date" : [ ], "institution" : "", "technique" : "?", "results" : [ { "unit" : "ppm", "value" : [ 0.03 ], "isotope" : "K-40", "type" : "measurement" } ] }, "grouping" : "ILIAS UKDM", "specification" : "3.00", "data_source" : { "input" : { "date" : [ datetime.datetime(2013, 1, 30, 0, 0) ], "name" : "Ben Wise / James Loach", "contact" : "bwise@smu.edu / james.loach@gmail.com", "notes" : "this has a COPPER test phrase" }, "reference" : "ILIAS Database http://radiopurity.in2p3.fr/" }, "sample" : { "description" : "Silica fibre, TSL, 'Spectrosil'", "id" : "ILIAS UKDM #289", "owner" : { "name" : "", "contact" : "" }, "name" : "Silica fibre, TSL, 'Spectrosil'", "source" : "" }, "type" : "measurement", "_version" : 1 })

    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb85ee8'), 'measurement': {'description': '', 'practitioner': {'name': 'ICI Tracerco', 'contact': ''}, 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'technique': 'NAA', 'results': [{'unit': 'ppb', 'value': [18, 2], 'isotope': 'U-238', 'type': 'measurement'}, {'unit': 'ppb', 'value': [59, 2], 'isotope': 'Th-232', 'type': 'measurement'}, {'unit': 'ppm', 'value': [0.78, 0.02], 'isotope': 'K-40', 'type': 'measurement'}]}, 'grouping': 'ILIAS UKDM', 'specification': '3.00', 'data_source': {'input': {'date': [datetime.datetime(2013, 7, 22, 0, 0)], 'name': 'Ben Wise / James Loach', 'contact': 'bwise@smu.edu / james.loach@gmail.com', 'notes': ''}, 'reference': 'ILIAS Database http://radiopurity.in2p3.fr/'}, 'sample': {'description': 'Resin, Magnex, 2:1 Thiokol 308, RAL', 'id': 'ILIAS UKDM #249', 'owner': {'name': '', 'contact': ''}, 'name': 'Resin, Magnex, 2:1 Thiokol 308', 'source': ''}, 'type': 'measurement', '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb85ee9'), 'measurement': {'description': '', 'practitioner': {'name': 'ICI Tracerco', 'contact': ''}, 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'technique': 'NAA', 'results': [{'unit': 'ppb', 'value': [3], 'isotope': 'U-238', 'type': 'limit'}, {'unit': 'ppb', 'value': [1], 'isotope': 'Th-232', 'type': 'limit'}, {'unit': 'ppb', 'value': [890, 0.2], 'isotope': 'K-40', 'type': 'measurement'}]}, 'grouping': 'ILIAS UKDM', 'specification': '3.00', 'data_source': {'input': {'date': [datetime.datetime(2013, 7, 22, 0, 0)], 'name': 'Ben Wise / James Loach', 'contact': 'bwise@smu.edu / james.loach@gmail.com', 'notes': ''}, 'reference': 'ILIAS Database http://radiopurity.in2p3.fr/'}, 'sample': {'description': 'Rexalite, copper removed', 'id': 'ILIAS UKDM #266', 'owner': {'name': '', 'contact': ''}, 'name': 'Rexalite, copper removed', 'source': ''}, 'type': 'measurement', '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb85eea'), 'measurement': {'description': '', 'practitioner': {'name': 'RAL', 'contact': ''}, 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'technique': 'AA', 'results': [{'unit': 'ppm', 'value': [0.15], 'isotope': 'K-40', 'type': 'measurement'}]}, 'grouping': 'Majorana(2016)', 'specification': '3.00', 'data_source': {'input': {'date': [datetime.datetime(2013, 7, 22, 0, 0)], 'name': 'Ben Wise / James Loach', 'contact': 'bwise@smu.edu / james.loach@gmail.com', 'notes': ''}, 'reference': 'ILIAS Database http://radiopurity.in2p3.fr/'}, 'sample': {'description': 'Salt, ICI, pure dried vacuum', 'id': 'ILIAS UKDM #273', 'owner': {'name': '', 'contact': ''}, 'name': 'Salt, ICI, pure dried vacuum', 'source': ''}, 'type': 'measurement', '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb85eeb'), 'measurement': {'description': 'Lu < 1ppb, Rb < 10ppb', 'practitioner': {'name': 'Charles Evans/Cascade Scientific', 'contact': ''}, 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'technique': 'GD-MS', 'results': [{'unit': 'ppb', 'value': [1], 'isotope': 'U-238', 'type': 'limit'}, {'unit': 'ppb', 'value': [1], 'isotope': 'Th-232', 'type': 'limit'}, {'unit': 'ppm', 'value': [0.22], 'isotope': 'K-40', 'type': 'limit'}]}, 'grouping': 'Majorana(2016)', 'specification': '3.00', 'data_source': {'input': {'date': [datetime.datetime(2013, 7, 22, 0, 0)], 'name': 'Ben Wise / James Loach', 'contact': 'bwise@smu.edu / james.loach@gmail.com', 'notes': ''}, 'reference': 'ILIAS Database http://radiopurity.in2p3.fr/'}, 'sample': {'description': 'Si', 'id': 'ILIAS UKDM #279', 'owner': {'name': '', 'contact': ''}, 'name': 'Si', 'source': ''}, 'type': 'measurement', '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb85eec'), 'measurement': {'description': '', 'practitioner': {'name': "Supplier's data", 'contact': ''}, 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'technique': '?', 'results': [{'unit': 'ppm', 'value': [0.03], 'isotope': 'K-40', 'type': 'measurement'}]}, 'grouping': 'Majorana(2016)', 'specification': '3.00', 'data_source': {'input': {'date': [datetime.datetime(2013, 7, 22, 0, 0)], 'name': 'Ben Wise / James Loach', 'contact': 'bwise@smu.edu / james.loach@gmail.com', 'notes': ''}, 'reference': 'ILIAS Database http://radiopurity.in2p3.fr/'}, 'sample': {'description': "Silica fibre, TSL, 'Spectrosil'", 'id': 'ILIAS UKDM #289', 'owner': {'name': '', 'contact': ''}, 'name': "Silica fibre, TSL, 'Spectrosil'", 'source': ''}, 'type': 'measurement', '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb85eed'), 'measurement': {'description': 'From previously unused 250g bottle', 'practitioner': {'name': 'ICI Tracerco', 'contact': ''}, 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'technique': 'NAA', 'results': [{'unit': 'ppb', 'value': [1], 'isotope': 'U-238', 'type': 'limit'}, {'unit': 'ppb', 'value': [1.7], 'isotope': 'Th-232', 'type': 'limit'}, {'unit': 'ppm', 'value': [0.099, 0.002], 'isotope': 'K-40', 'type': 'measurement'}]}, 'grouping': 'ILIAS UKDM', 'specification': '3.00', 'data_source': {'input': {'date': [datetime.datetime(2013, 7, 22, 0, 0)], 'name': 'Ben Wise / James Loach', 'contact': 'bwise@smu.edu / james.loach@gmail.com', 'notes': ''}, 'reference': 'ILIAS Database testing http://radiopurity.in2p3.fr/'}, 'sample': {'description': 'Silicone grease, DC/200/500000 (IC) (n = 5.e+5 )', 'id': 'ILIAS UKDM #304', 'owner': {'name': '', 'contact': ''}, 'name': 'Silicone grease, DC/200/500000, IC', 'source': ''}, 'type': 'measurement', '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb85eee'), 'measurement': {'description': 'U conc. from 226Ra gamma count, U chain assumed in eq.  Th conc. from 228Ac, Th chain assumed in eq. 137Cs < 20 kru,  60Co < 20 kru', 'practitioner': {'name': 'Harwell (AEA Technology) (Harwell Scientifics after mid-1999)', 'contact': ''}, 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'technique': 'Ge', 'results': [{'unit': 'ppb', 'value': [160], 'isotope': 'U-238', 'type': 'limit'}, {'unit': 'ppm', 'value': [150], 'isotope': 'Th-232', 'type': 'limit'}]}, 'grouping': 'ILIAS TeStInG UKDM', 'specification': '3.00', 'data_source': {'input': {'date': [datetime.datetime(2013, 7, 22, 0, 0)], 'name': 'Ben Wise / James Loach', 'contact': 'bwise@smu.edu / james.loach@gmail.com', 'notes': ''}, 'reference': 'ILIAS Database http://radiopurity.in2p3.fr/'}, 'sample': {'description': 'Steel, test sheet', 'id': 'ILIAS UKDM #320', 'owner': {'name': '', 'contact': ''}, 'name': 'Steel, sheet', 'source': ''}, 'type': 'measurement', '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb85eef'), 'measurement': {'description': '(14/10/04) DRIFT-II vessel, frame (Manufacturer: Royal Welding)', 'practitioner': {'name': 'Charles Evans/Cascade Scientific', 'contact': ''}, 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'technique': 'GD-MS', 'results': [{'unit': 'ppb', 'value': [0.37, 0.04], 'isotope': 'U-238', 'type': 'measurement'}, {'unit': 'ppb', 'value': [1.6, 0.2], 'isotope': 'Th-232', 'type': 'measurement'}, {'unit': 'ppb', 'value': [905], 'isotope': 'K-40', 'type': 'limit'}]}, 'grouping': 'ILIAS UKDM', 'specification': '3.00', 'data_source': {'input': {'date': [datetime.datetime(2013, 7, 22, 0, 0)], 'name': 'Ben Wise / James Loach', 'contact': 'bwise@smu.edu / james.loach@gmail.com', 'notes': ''}, 'reference': 'ILIAS Database http://radiopurity.in2p3.fr/'}, 'sample': {'description': 'Steel (stainless, frame) (USA)', 'id': 'ILIAS test UKDM #330', 'owner': {'name': '', 'contact': ''}, 'name': 'Steel, stainless, frame, USA', 'source': ''}, 'type': 'measurement', '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb85ef0'), 'measurement': {'description': '', 'practitioner': {'name': 'Charles Evans/Cascade Scientific', 'contact': ''}, 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'technique': 'GD-MS', 'results': [{'unit': 'ppb', 'value': [0.9, 0.1], 'isotope': 'U-238', 'type': 'measurement'}, {'unit': 'ppb', 'value': [0.6, 0.1], 'isotope': 'Th-232', 'type': 'measurement'}, {'unit': 'ppm', 'value': [0.21], 'isotope': 'K-40', 'type': 'limit'}]}, 'grouping': 'Majorana', 'specification': '3.00', 'data_source': {'input': {'date': [datetime.datetime(2013, 7, 22, 0, 0)], 'name': 'Ben Wise / James Loach', 'contact': 'bwise@smu.edu / james.loach@gmail.com', 'notes': ''}, 'reference': 'ILIAS Database http://radiopurity.in2p3.fr/'}, 'sample': {'description': 'Steel, stainless, USA', 'id': 'ILIAS UKDM #340', 'owner': {'name': '', 'contact': ''}, 'name': 'Steel, stainless, USA', 'source': ''}, 'type': 'measurement', '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb85ef1'), 'measurement': {'description': 'Results taken from a weighted average of selected quality lines with a 1-sigma error or 90% CL Upper Limits.', 'practitioner': {'name': 'Mark Pepin / Prisca Cushman', 'contact': 'pepin@physics.umn.edu / prisca@physics.umn.edu'}, 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': 'Soudan Underground Laboratory - Gopher', 'technique': 'Ge', 'results': [{'unit': 'mBq/kg', 'value': [2.791, 0.885], 'isotope': 'U-238', 'type': 'measurement'}, {'unit': 'mBq/kg', 'value': [0.707, 1.39], 'isotope': 'Th-232', 'type': 'measurement'}, {'unit': 'mBq/kg', 'value': [24.0, 4.96], 'isotope': 'K-40', 'type': 'measurement'}]}, 'grouping': 'SuperCDMS', 'specification': '3.00', 'data_source': {'input': {'date': [datetime.datetime(2013, 10, 8, 0, 0)], 'name': 'Matthew Bruemmer / James Loach / Jodi Cooley', 'contact': 'mbruemmer@smu.edu / james.loach@gmail.com / cooley@physics.smu.edu', 'notes': ''}, 'reference': 'Gopher: High-Purity Ge gamma counter at Soudan'}, 'sample': {'description': 'Carbon fiber, 97 separator rods, diameter 0.158 inches, length ~ 9.92 inches, total mass 0.468 kg, total volume ~18.866 in^3. Composed of carbon fill (we do not know anything about the purity of the carbon or the CF composition, but a rough estimate is 67% carbon by volume), epoxy (Bisphenol F Epoxy, C:H:0 is 13:12:02, ~33% Bis F Epoxy by volume), hardener (type Unknown)', 'id': 'Sample 19', 'owner': {'name': '', 'contact': ''}, 'name': 'Carbon fiber rods', 'source': ''}, 'type': 'measurement', '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb85ef2'), 'measurement': {'description': '1.3 ?µS, Apr 93', 'practitioner': {'name': 'RAL', 'contact': ''}, 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'technique': 'AA', 'results': [{'unit': 'ppb', 'value': [210.9], 'isotope': 'K-40', 'type': 'measurement'}]}, 'grouping': 'ILIAS UKDM', 'specification': '3.00', 'data_source': {'input': {'date': [datetime.datetime(2013, 7, 22, 0, 0)], 'name': 'Ben Wise / James Loach', 'contact': 'bwise@smu.edu / james.loach@gmail.com', 'notes': ''}, 'reference': 'ILIAS Database http://radiopurity.in2p3.fr/'}, 'sample': {'description': 'Water (Boulby tank)', 'id': 'ILIAS UKDM #361', 'owner': {'name': '', 'contact': ''}, 'name': 'Water, Boulby tank', 'source': ''}, 'type': 'measurement', '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb85ef3'), 'measurement': {'description': '', 'practitioner': {'name': 'Harwell (AEA Technology) (Harwell Scientifics after mid-1999)', 'contact': ''}, 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'technique': 'ICP-MS', 'results': [{'unit': 'ppb', 'value': [0.0004], 'isotope': 'U-238', 'type': 'measurement'}, {'unit': 'ppb', 'value': [0.0001], 'isotope': 'Th-232', 'type': 'measurement'}]}, 'grouping': 'ILIAS UKDM', 'specification': '3.00', 'data_source': {'input': {'date': [datetime.datetime(2013, 7, 22, 0, 0)], 'name': 'Ben Wise / James Loach', 'contact': 'bwise@smu.edu / james.loach@gmail.com', 'notes': ''}, 'reference': 'ILIAS Database http://radiopurity.in2p3.fr/'}, 'sample': {'description': 'Water, Fisons demin', 'id': 'ILIAS UKDM #366', 'owner': {'name': '', 'contact': ''}, 'name': 'Water, Fisons demin', 'source': ''}, 'type': 'measurement', '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb85ef4'), 'measurement': {'description': '', 'practitioner': {'name': 'J.Puimedón & A.Ortiz', 'contact': ''}, 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': 'LSC', 'technique': 'Ge', 'results': [{'unit': 'Bq/kg', 'value': [50, 6], 'isotope': 'Th-234', 'type': 'measurement'}, {'unit': 'Bq/kg', 'value': [50, 6], 'isotope': 'Pb-214', 'type': 'measurement'}, {'unit': 'Bq/kg', 'value': [50, 6], 'isotope': 'Bi-214', 'type': 'measurement'}, {'unit': 'Bq/kg', 'value': [30, 5], 'isotope': 'Ac-228', 'type': 'measurement'}, {'unit': 'Bq/kg', 'value': [30, 5], 'isotope': 'Pb-212', 'type': 'measurement'}, {'unit': 'Bq/kg', 'value': [30, 5], 'isotope': 'Tl-208', 'type': 'measurement'}, {'unit': 'Bq/kg', 'value': [2.0, 0.6], 'isotope': 'U-235', 'type': 'measurement'}, {'unit': 'Bq/kg', 'value': [70, 10], 'isotope': 'K-40', 'type': 'measurement'}]}, 'grouping': 'ILIAS CAST', 'specification': '3.00', 'data_source': {'input': {'date': [datetime.datetime(2013, 4, 9, 0, 0)], 'name': 'Benjamin Wise / James Loach', 'contact': 'bwise@smu.edu / james.loach@gmail.com', 'notes': ''}, 'reference': 'ILIAS Database http://radiopurity.in2p3.fr/'}, 'sample': {'description': 'Laminate', 'id': 'Conc. #7', 'owner': {'name': '', 'contact': ''}, 'name': 'Laminate, Stesalit', 'source': 'Stesalit'}, 'type': 'measurement', '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb85ef5'), 'measurement': {'description': '', 'practitioner': {'name': 'J.Puimedón & A.Ortiz', 'contact': ''}, 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': 'LSC', 'technique': 'Ge', 'results': [{'unit': 'mBq', 'value': [120, 30], 'isotope': 'Th-234', 'type': 'measurement'}, {'unit': 'mBq', 'value': [65, 10], 'isotope': 'Pb-214', 'type': 'measurement'}, {'unit': 'mBq', 'value': [65, 10], 'isotope': 'Bi-214', 'type': 'measurement'}, {'unit': 'mBq', 'value': [90, 10], 'isotope': 'Ac-228', 'type': 'measurement'}, {'unit': 'mBq', 'value': [90, 10], 'isotope': 'Pb-212', 'type': 'measurement'}, {'unit': 'mBq', 'value': [90, 10], 'isotope': 'Tl-208', 'type': 'measurement'}, {'unit': 'mBq', 'value': [6, 2], 'isotope': 'U-235', 'type': 'measurement'}, {'unit': 'mBq', 'value': [42, 14], 'isotope': 'K-40', 'type': 'measurement'}]}, 'grouping': 'ILIAS CAST', 'specification': '3.00', 'data_source': {'input': {'date': [datetime.datetime(2013, 4, 9, 0, 0)], 'name': 'Benjamin Wise / James Loach', 'contact': 'bwise@smu.edu / james.loach@gmail.com', 'notes': ''}, 'reference': 'ILIAS Database http://radiopurity.in2p3.fr/'}, 'sample': {'description': 'Zero force socket', 'id': 'Conc. #11', 'owner': {'name': '', 'contact': ''}, 'name': 'Zero force socket', 'source': ''}, 'type': 'measurement', '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb85ef6'), 'measurement': {'description': '', 'practitioner': {'name': '', 'contact': ''}, 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': 'LGNS', 'technique': 'Ge', 'results': [{'unit': 'mBq/kg', 'value': [2.4, 95], 'isotope': 'Ra-228', 'type': 'limit'}, {'unit': 'mBq/kg', 'value': [1.0, 95], 'isotope': 'Th-228', 'type': 'limit'}, {'unit': 'mBq/kg', 'value': [130, 95], 'isotope': 'U-238', 'type': 'limit'}, {'unit': 'mBq/kg', 'value': [1.9, 95], 'isotope': 'Ra-226', 'type': 'limit'}, {'unit': 'mBq/kg', 'value': [2.0, 95], 'isotope': 'U-235', 'type': 'limit'}, {'unit': 'mBq/kg', 'value': [10, 4], 'isotope': 'K-40', 'type': 'measurement'}, {'unit': 'mBq/kg', 'value': [0.9, 95], 'isotope': 'Cs-137', 'type': 'limit'}, {'unit': 'mBq/kg', 'value': [8.5, 9], 'isotope': 'Co-60', 'type': 'measurement'}]}, 'grouping': 'XENON100 (2011) ', 'specification': '3.00', 'data_source': {'input': {'date': [datetime.datetime(2013, 3, 22, 0, 0)], 'name': 'Matthew Bruemmer / James Loach / Jodi Cooley', 'contact': 'mbruemmer@smu.edu / james.loach@gmail.com / cooley@physics.smu.edu', 'notes': ''}, 'reference': 'E. Aprile et al., Astropart. Phys., 35 (2011)  (http://dx.doi.org/10.1016/j.astropartphys.2011.06.001)'}, 'sample': {'description': 'Stainless steel, 316Ti, NIRONIT, 1.5mm, cryostat wall', 'id': 'Table 1. #7', 'owner': {'name': '', 'contact': ''}, 'name': 'Stainless steel, 316Ti, NIRONIT', 'source': 'NIRONIT'}, 'type': 'measurement', '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb85ef7'), 'measurement': {'description': '', 'practitioner': {'name': '', 'contact': ''}, 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': 'LNGS', 'technique': 'Ge', 'results': [{'unit': 'mBq/kg', 'value': [0.92, 95], 'isotope': 'Ra-228', 'type': 'limit'}, {'unit': 'mBq/kg', 'value': [2.9, 7], 'isotope': 'Th-228', 'type': 'measurement'}, {'unit': 'mBq/kg', 'value': [20, 95], 'isotope': 'U-238', 'type': 'limit'}, {'unit': 'mBq/kg', 'value': [1.3, 95], 'isotope': 'Ra-226', 'type': 'limit'}, {'unit': 'mBq/kg', 'value': [1.3, 95], 'isotope': 'U-235', 'type': 'limit'}, {'unit': 'mBq/kg', 'value': [7.1, 95], 'isotope': 'K-40', 'type': 'limit'}, {'unit': 'mBq/kg', 'value': [0.82, 95], 'isotope': 'Cs-137', 'type': 'limit'}, {'unit': 'mBq/kg', 'value': [1.4, 3], 'isotope': 'Co-60', 'type': 'measurement'}]}, 'grouping': 'XENON100 (2011) ', 'specification': '3.00', 'data_source': {'input': {'date': [datetime.datetime(2013, 3, 22, 0, 0)], 'name': 'Matthew Bruemmer / James Loach / Jodi Cooley', 'contact': 'mbruemmer@smu.edu / james.loach@gmail.com / cooley@physics.smu.edu', 'notes': ''}, 'reference': 'E. Aprile et al., Astropart. Phys., 35 (2011)  (http://dx.doi.org/10.1016/j.astropartphys.2011.06.001)'}, 'sample': {'description': 'Stainless steel, 316Ti, NIRONIT, 25mm, top flange/support bars', 'id': 'Table 1. #10', 'owner': {'name': '', 'contact': ''}, 'name': 'Stainless steel, 316Ti, NIRONIT', 'source': 'NIRONIT'}, 'type': 'measurement', '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb85ef8'), 'measurement': {'description': '', 'practitioner': {'name': '', 'contact': ''}, 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': 'University of Zurich', 'technique': 'Ge', 'results': [{'unit': 'mBq/kg', 'value': [0.16, 95], 'isotope': 'Ra-228', 'type': 'limit'}, {'unit': 'mBq/kg', 'value': [0.1, 95], 'isotope': 'Th-228', 'type': 'limit'}, {'unit': 'mBq/kg', 'value': [3.0, 95], 'isotope': 'U-238', 'type': 'limit'}, {'unit': 'mBq/kg', 'value': [0.06, 95], 'isotope': 'Ra-226', 'type': 'limit'}, {'unit': 'mBq/kg', 'value': [0.13, 95], 'isotope': 'U-235', 'type': 'limit'}, {'unit': 'mBq/kg', 'value': [0.75, 95], 'isotope': 'K-40', 'type': 'limit'}, {'unit': 'mBq/kg', 'value': [0.07, 95], 'isotope': 'Cs-137', 'type': 'limit'}, {'unit': 'mBq/kg', 'value': [0.03, 95], 'isotope': 'Co-60', 'type': 'limit'}]}, 'grouping': 'XENON100 (2011) ', 'specification': '3.00', 'data_source': {'input': {'date': [datetime.datetime(2013, 3, 22, 0, 0)], 'name': 'Matthew Bruemmer / James Loach / Jodi Cooley', 'contact': 'mbruemmer@smu.edu / james.loach@gmail.com / cooley@physics.smu.edu', 'notes': ''}, 'reference': 'E. Aprile et al., Astropart. Phys., 35 (2011) (http://dx.doi.org/10.1016/j.astropartphys.2011.06.001)'}, 'sample': {'description': 'PTFE, Maagtechnic, TPC', 'id': 'Table 1. #16', 'owner': {'name': '', 'contact': ''}, 'name': 'PTFE, Maagtechnic', 'source': 'Maagtechnic'}, 'type': 'measurement', '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb85ef9'), 'measurement': {'description': '', 'practitioner': {'name': '', 'contact': ''}, 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': 'LNGS', 'technique': 'Ge', 'results': [{'unit': 'mBq/unit', 'value': [0.087, 3], 'isotope': 'Ra-228', 'type': 'measurement'}, {'unit': 'mBq/unit', 'value': [0.11, 1], 'isotope': 'Th-228', 'type': 'measurement'}, {'unit': 'mBq/unit', 'value': [4.7, 95], 'isotope': 'U-238', 'type': 'limit'}, {'unit': 'mBq/unit', 'value': [0.12, 1], 'isotope': 'Ra-226', 'type': 'measurement'}, {'unit': 'mBq/unit', 'value': [0.04, 1], 'isotope': 'U-235', 'type': 'measurement'}, {'unit': 'mBq/unit', 'value': [6.9, 7], 'isotope': 'K-40', 'type': 'measurement'}, {'unit': 'mBq/unit', 'value': [0.027, 7], 'isotope': 'Cs-137', 'type': 'measurement'}, {'unit': 'mBq/unit', 'value': [1.5, 1], 'isotope': 'Co-60', 'type': 'measurement'}]}, 'grouping': 'XENON100 (2011) ', 'specification': '3.00', 'data_source': {'input': {'date': [datetime.datetime(2013, 3, 22, 0, 0)], 'name': 'Matthew Bruemmer / James Loach / Jodi Cooley', 'contact': 'mbruemmer@smu.edu / james.loach@gmail.com / cooley@physics.smu.edu', 'notes': ''}, 'reference': 'E. Aprile et al., Astropart. Phys., 35 (2011) (http://dx.doi.org/10.1016/j.astropartphys.2011.06.001)'}, 'sample': {'description': 'PMT, Hamamatsu R8520 - batch 7, top/bottom array, veto', 'id': 'Table 1. #26', 'owner': {'name': '', 'contact': ''}, 'name': 'PMT, Hamamatsu R8520 - batch 7', 'source': 'Hamamatsu'}, 'type': 'measurement', '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb85efa'), 'measurement': {'description': '', 'practitioner': {'name': '', 'contact': ''}, 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': 'LNGS', 'technique': 'Ge', 'results': [{'unit': 'uBq/m', 'value': [20, 10], 'isotope': 'Ra-228', 'type': 'measurement'}, {'unit': 'uBq/m', 'value': [19, 95], 'isotope': 'Th-228', 'type': 'limit'}, {'unit': 'uBq/m', 'value': [180, 95], 'isotope': 'U-238', 'type': 'limit'}, {'unit': 'uBq/m', 'value': [8.9, 95], 'isotope': 'Ra-226', 'type': 'limit'}, {'unit': 'uBq/m', 'value': [14, 95], 'isotope': 'U-235', 'type': 'limit'}, {'unit': 'uBq/m', 'value': [200, 80], 'isotope': 'K-40', 'type': 'measurement'}, {'unit': 'uBq/m', 'value': [12, 95], 'isotope': 'Cs-137', 'type': 'limit'}, {'unit': 'uBq/m', 'value': [3.9, 95], 'isotope': 'Co-60', 'type': 'limit'}]}, 'grouping': 'XENON100 (2011) ', 'specification': '3.00', 'data_source': {'input': {'date': [datetime.datetime(2013, 3, 22, 0, 0)], 'name': 'Matthew Bruemmer / James Loach / Jodi Cooley', 'contact': 'mbruemmer@smu.edu / james.loach@gmail.com / cooley@physics.smu.edu', 'notes': ''}, 'reference': 'E. Aprile et al., Astropart. Phys., 35 (2011) (http://dx.doi.org/10.1016/j.astropartphys.2011.06.001)'}, 'sample': {'description': 'Coaxial cable (RG174), PMT Signal', 'id': 'Table 1. #42', 'owner': {'name': '', 'contact': ''}, 'name': 'Coaxial cable (RG174), Caburn-MDC', 'source': 'Caburn-MDC'}, 'type': 'measurement', '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb85efb'), 'measurement': {'description': '', 'practitioner': {'name': '', 'contact': ''}, 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': 'University of Zurich', 'technique': 'Ge', 'results': [{'unit': 'Bq/kg', 'value': [7, 2], 'isotope': 'Ra-228', 'type': 'measurement'}, {'unit': 'Bq/kg', 'value': [8, 2], 'isotope': 'Th-228', 'type': 'measurement'}, {'unit': 'Bq/kg', 'value': [190, 95], 'isotope': 'U-238', 'type': 'limit'}, {'unit': 'Bq/kg', 'value': [26, 5], 'isotope': 'Ra-226', 'type': 'measurement'}, {'unit': 'Bq/kg', 'value': [8.5, 95], 'isotope': 'U-235', 'type': 'limit'}, {'unit': 'Bq/kg', 'value': [170, 30], 'isotope': 'K-40', 'type': 'measurement'}, {'unit': 'Bq/kg', 'value': [0.9, 3], 'isotope': 'Cs-137', 'type': 'measurement'}, {'unit': 'Bq/kg', 'value': [0.58, 95], 'isotope': 'Co-60', 'type': 'limit'}]}, 'grouping': 'XENON100 (2011) ', 'specification': '3.00', 'data_source': {'input': {'date': [datetime.datetime(2013, 3, 22, 0, 0)], 'name': 'Matthew Bruemmer / James Loach / Jodi Cooley', 'contact': 'mbruemmer@smu.edu / james.loach@gmail.com / cooley@physics.smu.edu', 'notes': ''}, 'reference': 'E. Aprile et al., Astropart. Phys., 35 (2011) (http://dx.doi.org/10.1016/j.astropartphys.2011.06.001)'}, 'sample': {'description': 'Concrete, LNGS floor', 'id': 'Table 1. #49', 'owner': {'name': '', 'contact': ''}, 'name': 'Concrete, LNGS floor', 'source': ''}, 'type': 'measurement', '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb86290'), 'specification': '3.00', 'data_source': {'input': {'name': 'James Loach', 'contact': 'james.loach@gmail.com', 'notes': '', 'date': [datetime.datetime(2016, 7, 14, 0, 0)]}, 'reference': 'N. Abgrall et al., Nucl. Instr. and Meth. A 828 (2016) (doi:10.1016/j.nima.2016.04.070)'}, 'grouping': 'Majorana (2016)', 'sample': {'name': 'Copper, electroformed', 'source': '', 'description': 'Copper, electroformed, stock sample', 'owner': {'name': '', 'contact': ''}, 'id': 'Table 3. (metals) #001'}, 'type': 'measurement', 'measurement': {'description': '', 'technique': 'ICP-MS', 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'results': [{'type': 'limit', 'value': [0.17, 68], 'isotope': 'Th-232', 'unit': 'ppt'}], 'practitioner': {'name': '', 'contact': ''}}, '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb86291'), 'specification': '3.00', 'data_source': {'input': {'name': 'James Loach', 'contact': 'james.loach@gmail.com', 'notes': '', 'date': [datetime.datetime(2016, 7, 14, 0, 0)]}, 'reference': 'N. Abgrall et al., Nucl. Instr. and Meth. A 828 (2016) (doi:10.1016/j.nima.2016.04.070)'}, 'grouping': 'Majorana (2016)', 'sample': {'name': 'Copper, electroformed', 'source': '', 'description': 'Copper, electroformed, stock sample', 'owner': {'name': '', 'contact': ''}, 'id': 'Table 3. (metals) #002'}, 'type': 'measurement', 'measurement': {'description': '', 'technique': 'ICP-MS', 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'results': [{'type': 'measurement', 'value': [0.011, 0.005], 'isotope': 'Th-232', 'unit': 'ppt'}, {'type': 'measurement', 'value': [0.017, 0.003], 'isotope': 'U-238', 'unit': 'ppt'}], 'practitioner': {'name': '', 'contact': ''}}, '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb86292'), 'specification': '3.00', 'data_source': {'input': {'name': 'James Loach', 'contact': 'james.loach@gmail.com', 'notes': '', 'date': [datetime.datetime(2016, 7, 14, 0, 0)]}, 'reference': 'N. Abgrall et al., Nucl. Instr. and Meth. A 828 (2016) (doi:10.1016/j.nima.2016.04.070)'}, 'grouping': 'Majorana (2016)', 'sample': {'name': 'Copper, electroformed', 'source': '', 'description': 'Copper, electroformed, stock sample', 'owner': {'name': '', 'contact': ''}, 'id': 'Table 3. (metals) #003'}, 'type': 'measurement', 'measurement': {'description': '', 'technique': 'GD-MS', 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'results': [{'type': 'limit', 'value': [2.2, 68], 'isotope': 'K', 'unit': 'ppb'}, {'type': 'limit', 'value': [50, 68], 'isotope': 'Th-232', 'unit': 'ppt'}, {'type': 'limit', 'value': [70, 68], 'isotope': 'U-238', 'unit': 'ppt'}], 'practitioner': {'name': '', 'contact': ''}}, '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb86293'), 'specification': '3.00', 'data_source': {'input': {'name': 'James Loach', 'contact': 'james.loach@gmail.com', 'notes': '', 'date': [datetime.datetime(2016, 7, 14, 0, 0)]}, 'reference': 'N. Abgrall et al., Nucl. Instr. and Meth. A 828 (2016) (doi:10.1016/j.nima.2016.04.070)'}, 'grouping': 'Majorana (2016)', 'sample': {'name': 'Copper, electroformed', 'source': '', 'description': 'Copper, electroformed, stock sample', 'owner': {'name': '', 'contact': ''}, 'id': 'Table 3. (metals) #004'}, 'type': 'measurement', 'measurement': {'description': '', 'technique': 'ICP-MS', 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'results': [{'type': 'limit', 'value': [0.029, 68], 'isotope': 'Th-232', 'unit': 'ppt'}, {'type': 'limit', 'value': [0.008, 68], 'isotope': 'U-238', 'unit': 'ppt'}], 'practitioner': {'name': '', 'contact': ''}}, '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb86294'), 'specification': '3.00', 'data_source': {'input': {'name': 'James Loach', 'contact': 'james.loach@gmail.com', 'notes': '', 'date': [datetime.datetime(2016, 7, 14, 0, 0)]}, 'reference': 'N. Abgrall et al., Nucl. Instr. and Meth. A 828 (2016) (doi:10.1016/j.nima.2016.04.070)'}, 'grouping': 'Majorana (2016)', 'sample': {'name': 'Copper, electroformed', 'source': '', 'description': 'Copper, electroformed, stock sample', 'owner': {'name': '', 'contact': ''}, 'id': 'Table 3. (metals) #005'}, 'type': 'measurement', 'measurement': {'description': '', 'technique': 'ICP-MS', 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'results': [{'type': 'limit', 'value': [0.029, 68], 'isotope': 'Th-232', 'unit': 'ppt'}, {'type': 'limit', 'value': [0.009, 68], 'isotope': 'U-238', 'unit': 'ppt'}], 'practitioner': {'name': '', 'contact': ''}}, '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb86295'), 'specification': '3.00', 'data_source': {'input': {'name': 'James Loach', 'contact': 'james.loach@gmail.com', 'notes': '', 'date': [datetime.datetime(2016, 7, 14, 0, 0)]}, 'reference': 'N. Abgrall et al., Nucl. Instr. and Meth. A 828 (2016) (doi:10.1016/j.nima.2016.04.070)'}, 'grouping': 'Majorana (2016)', 'sample': {'name': 'Copper, electroformed', 'source': '', 'description': 'Copper, electroformed, stock sample', 'owner': {'name': '', 'contact': ''}, 'id': 'Table 3. (metals) #006'}, 'type': 'measurement', 'measurement': {'description': '', 'technique': 'ICP-MS', 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'results': [{'type': 'limit', 'value': [0.029, 68], 'isotope': 'Th-232', 'unit': 'ppt'}, {'type': 'limit', 'value': [0.008, 68], 'isotope': 'U-238', 'unit': 'ppt'}], 'practitioner': {'name': '', 'contact': ''}}, '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb86296'), 'specification': '3.00', 'data_source': {'input': {'name': 'James Loach', 'contact': 'james.loach@gmail.com', 'notes': '', 'date': [datetime.datetime(2016, 7, 14, 0, 0)]}, 'reference': 'N. Abgrall et al., Nucl. Instr. and Meth. A 828 (2016) (doi:10.1016/j.nima.2016.04.070)'}, 'grouping': 'Majorana (2016)', 'sample': {'name': 'Copper, electroformed', 'source': '', 'description': 'Copper, electroformed, stock sample', 'owner': {'name': '', 'contact': ''}, 'id': 'Table 3. (metals) #007'}, 'type': 'measurement', 'measurement': {'description': '', 'technique': 'ICP-MS', 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'results': [{'type': 'limit', 'value': [0.03, 68], 'isotope': 'Th-232', 'unit': 'ppt'}, {'type': 'limit', 'value': [0.009, 68], 'isotope': 'U-238', 'unit': 'ppt'}], 'practitioner': {'name': '', 'contact': ''}}, '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb86297'), 'specification': '3.00', 'data_source': {'input': {'name': 'James Loach', 'contact': 'james.loach@gmail.com', 'notes': '', 'date': [datetime.datetime(2016, 7, 14, 0, 0)]}, 'reference': 'N. Abgrall et al., Nucl. Instr. and Meth. A 828 (2016) (doi:10.1016/j.nima.2016.04.070)'}, 'grouping': 'Majorana (2016)', 'sample': {'name': 'Copper, electroformed, machined parts', 'source': '', 'description': 'Copper, electroformed, machined part, guide clip', 'owner': {'name': '', 'contact': ''}, 'id': 'Table 3. (metals) #008'}, 'type': 'measurement', 'measurement': {'description': '', 'technique': 'ICP-MS', 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'results': [{'type': 'measurement', 'value': [0.33, 0.022], 'isotope': 'Th-232', 'unit': 'ppt'}, {'type': 'measurement', 'value': [0.123, 0.005], 'isotope': 'U-238', 'unit': 'ppt'}], 'practitioner': {'name': '', 'contact': ''}}, '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb86298'), 'specification': '3.00', 'data_source': {'input': {'name': 'James Loach', 'contact': 'james.loach@gmail.com', 'notes': '', 'date': [datetime.datetime(2016, 7, 14, 0, 0)]}, 'reference': 'N. Abgrall et al., Nucl. Instr. and Meth. A 828 (2016) (doi:10.1016/j.nima.2016.04.070)'}, 'grouping': 'Majorana (2016)', 'sample': {'name': 'Copper, electroformed, machined part', 'source': '', 'description': 'Copper, electroformed, machined part, guide clip', 'owner': {'name': '', 'contact': ''}, 'id': 'Table 3. (metals) #009'}, 'type': 'measurement', 'measurement': {'description': '', 'technique': 'ICP-MS', 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'results': [{'type': 'measurement', 'value': [0.112, 0.009], 'isotope': 'Th-232', 'unit': 'ppt'}, {'type': 'measurement', 'value': [0.078, 0.002], 'isotope': 'U-238', 'unit': 'ppt'}], 'practitioner': {'name': '', 'contact': ''}}, '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb86299'), 'specification': '3.00', 'data_source': {'input': {'name': 'James Loach', 'contact': 'james.loach@gmail.com', 'notes': '', 'date': [datetime.datetime(2016, 7, 14, 0, 0)]}, 'reference': 'N. Abgrall et al., Nucl. Instr. and Meth. A 828 (2016) (doi:10.1016/j.nima.2016.04.070)'}, 'grouping': 'Majorana (2016)', 'sample': {'name': 'Copper, electroformed, machined part', 'source': '', 'description': 'Copper, electroformed, machined part, guide clip', 'owner': {'name': '', 'contact': ''}, 'id': 'Table 3. (metals) #010'}, 'type': 'measurement', 'measurement': {'description': '', 'technique': 'ICP-MS', 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'results': [{'type': 'measurement', 'value': [0.17, 0.008], 'isotope': 'Th-232', 'unit': 'ppt'}, {'type': 'measurement', 'value': [0.087, 0.002], 'isotope': 'U-238', 'unit': 'ppt'}], 'practitioner': {'name': '', 'contact': ''}}, '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb8629a'), 'specification': '3.00', 'data_source': {'input': {'name': 'James Loach', 'contact': 'james.loach@gmail.com', 'notes': '', 'date': [datetime.datetime(2016, 7, 14, 0, 0)]}, 'reference': 'N. Abgrall et al., Nucl. Instr. and Meth. A 828 (2016) (doi:10.1016/j.nima.2016.04.070)'}, 'grouping': 'Majorana (2016)', 'sample': {'name': 'Copper, electroformed, machined part', 'source': '', 'description': 'Copper, electroformed, machined part, spring clip', 'owner': {'name': '', 'contact': ''}, 'id': 'Table 3. (metals) #011'}, 'type': 'measurement', 'measurement': {'description': '', 'technique': 'ICP-MS', 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'results': [{'type': 'measurement', 'value': [0.215, 0.009], 'isotope': 'Th-232', 'unit': 'ppt'}, {'type': 'measurement', 'value': [0.13, 0.01], 'isotope': 'U-238', 'unit': 'ppt'}], 'practitioner': {'name': '', 'contact': ''}}, '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb8629b'), 'specification': '3.00', 'data_source': {'input': {'name': 'James Loach', 'contact': 'james.loach@gmail.com', 'notes': '', 'date': [datetime.datetime(2016, 7, 14, 0, 0)]}, 'reference': 'N. Abgrall et al., Nucl. Instr. and Meth. A 828 (2016) (doi:10.1016/j.nima.2016.04.070)'}, 'grouping': 'Majorana (2016)', 'sample': {'name': 'Copper, electroformed, machined part', 'source': '', 'description': 'Copper, electroformed, machined part, hex bolt', 'owner': {'name': '', 'contact': ''}, 'id': 'Table 3. (metals) #012'}, 'type': 'measurement', 'measurement': {'description': '', 'technique': 'ICP-MS', 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'results': [{'type': 'measurement', 'value': [0.118, 0.011], 'isotope': 'Th-232', 'unit': 'ppt'}, {'type': 'measurement', 'value': [0.035, 0.004], 'isotope': 'U-238', 'unit': 'ppt'}], 'practitioner': {'name': '', 'contact': ''}}, '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb8629c'), 'specification': '3.00', 'data_source': {'input': {'name': 'James Loach', 'contact': 'james.loach@gmail.com', 'notes': '', 'date': [datetime.datetime(2016, 7, 14, 0, 0)]}, 'reference': 'N. Abgrall et al., Nucl. Instr. and Meth. A 828 (2016) (doi:10.1016/j.nima.2016.04.070)'}, 'grouping': 'Majorana (2016)', 'sample': {'name': 'Copper, electroformed, machined part', 'source': '', 'description': 'Copper, electroformed, machined part, hex bolt', 'owner': {'name': '', 'contact': ''}, 'id': 'Table 3. (metals) #013'}, 'type': 'measurement', 'measurement': {'description': '', 'technique': 'ICP-MS', 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'results': [{'type': 'measurement', 'value': [0.119, 0.014], 'isotope': 'Th-232', 'unit': 'ppt'}, {'type': 'measurement', 'value': [0.041, 0.003], 'isotope': 'U-238', 'unit': 'ppt'}], 'practitioner': {'name': '', 'contact': ''}}, '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb8629d'), 'specification': '3.00', 'data_source': {'input': {'name': 'James Loach', 'contact': 'james.loach@gmail.com', 'notes': '', 'date': [datetime.datetime(2016, 7, 14, 0, 0)]}, 'reference': 'N. Abgrall et al., Nucl. Instr. and Meth. A 828 (2016) (doi:10.1016/j.nima.2016.04.070)'}, 'grouping': 'Majorana (2016)', 'sample': {'name': 'Copper, electroformed, machined part', 'source': '', 'description': 'Copper, electroformed, machined part, hex bolt', 'owner': {'name': '', 'contact': ''}, 'id': 'Table 3. (metals) #014'}, 'type': 'measurement', 'measurement': {'description': '', 'technique': 'ICP-MS', 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'results': [{'type': 'measurement', 'value': [0.148, 0.021], 'isotope': 'Th-232', 'unit': 'ppt'}, {'type': 'measurement', 'value': [0.051, 0.002], 'isotope': 'U-238', 'unit': 'ppt'}], 'practitioner': {'name': '', 'contact': ''}}, '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb8629e'), 'specification': '3.00', 'data_source': {'input': {'name': 'James Loach', 'contact': 'james.loach@gmail.com', 'notes': '', 'date': [datetime.datetime(2016, 7, 14, 0, 0)]}, 'reference': 'N. Abgrall et al., Nucl. Instr. and Meth. A 828 (2016) (doi:10.1016/j.nima.2016.04.070)'}, 'grouping': 'Majorana (2016)', 'sample': {'name': 'Copper, C10100, cake stock', 'source': '', 'description': 'Copper, C10100, cake stock, (source for #016 and #017)', 'owner': {'name': '', 'contact': ''}, 'id': 'Table 3. (metals) #015'}, 'type': 'measurement', 'measurement': {'description': '', 'technique': 'ICP-MS', 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'results': [{'type': 'measurement', 'value': [0.46, 0.06], 'isotope': 'Th-232', 'unit': 'ppt'}, {'type': 'measurement', 'value': [0.21, 0.06], 'isotope': 'U-238', 'unit': 'ppt'}], 'practitioner': {'name': '', 'contact': ''}}, '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb8629f'), 'specification': '3.00', 'data_source': {'input': {'name': 'James Loach', 'contact': 'james.loach@gmail.com', 'notes': '', 'date': [datetime.datetime(2016, 7, 14, 0, 0)]}, 'reference': 'N. Abgrall et al., Nucl. Instr. and Meth. A 828 (2016) (doi:10.1016/j.nima.2016.04.070)'}, 'grouping': 'Majorana (2016)', 'sample': {'name': 'Copper, C10100, plate stock', 'source': '', 'description': 'Copper, C10100, 2.5 in. plate stock, exterior sample', 'owner': {'name': '', 'contact': ''}, 'id': 'Table 3. (metals) #016'}, 'type': 'measurement', 'measurement': {'description': '', 'technique': 'ICP-MS', 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'results': [{'type': 'measurement', 'value': [0.27, 0.05], 'isotope': 'Th-232', 'unit': 'ppt'}, {'type': 'measurement', 'value': [0.1, 0.02], 'isotope': 'U-238', 'unit': 'ppt'}], 'practitioner': {'name': '', 'contact': ''}}, '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb862a0'), 'specification': '3.00', 'data_source': {'input': {'name': 'James Loach', 'contact': 'james.loach@gmail.com', 'notes': '', 'date': [datetime.datetime(2016, 7, 14, 0, 0)]}, 'reference': 'N. Abgrall et al., Nucl. Instr. and Meth. A 828 (2016) (doi:10.1016/j.nima.2016.04.070)'}, 'grouping': 'Majorana (2016)', 'sample': {'name': 'Copper, C10100, plate stock', 'source': '', 'description': 'Copper, C10100, 2.5 in. plate stock, interior sample', 'owner': {'name': '', 'contact': ''}, 'id': 'Table 3. (metals) #017'}, 'type': 'measurement', 'measurement': {'description': '', 'technique': 'ICP-MS', 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'results': [{'type': 'measurement', 'value': [0.27, 0.05], 'isotope': 'Th-232', 'unit': 'ppt'}, {'type': 'measurement', 'value': [0.12, 0.02], 'isotope': 'U-238', 'unit': 'ppt'}], 'practitioner': {'name': '', 'contact': ''}}, '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb862a1'), 'specification': '3.00', 'data_source': {'input': {'name': 'James Loach', 'contact': 'james.loach@gmail.com', 'notes': '', 'date': [datetime.datetime(2016, 7, 14, 0, 0)]}, 'reference': 'N. Abgrall et al., Nucl. Instr. and Meth. A 828 (2016) (doi:10.1016/j.nima.2016.04.070)'}, 'grouping': 'Majorana (2016)', 'sample': {'name': 'Copper, C10100, plate stock, saw cut', 'source': '', 'description': 'Copper, C10100, 1 in. plate stock, saw cut (same stock #019)', 'owner': {'name': '', 'contact': ''}, 'id': 'Table 3. (metals) #018'}, 'type': 'measurement', 'measurement': {'description': '', 'technique': 'ICP-MS', 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'results': [{'type': 'measurement', 'value': [10.2, 1.0], 'isotope': 'Th-232', 'unit': 'ppt'}, {'type': 'measurement', 'value': [6.62, 0.58], 'isotope': 'U-238', 'unit': 'ppt'}], 'practitioner': {'name': '', 'contact': ''}}, '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb862a2'), 'specification': '3.00', 'data_source': {'input': {'name': 'James Loach', 'contact': 'james.loach@gmail.com', 'notes': '', 'date': [datetime.datetime(2016, 7, 14, 0, 0)]}, 'reference': 'N. Abgrall et al., Nucl. Instr. and Meth. A 828 (2016) (doi:10.1016/j.nima.2016.04.070)'}, 'grouping': 'Majorana (2016)', 'sample': {'name': 'Copper, C10100, plate stock, machined surfaces', 'source': '', 'description': 'Copper, C10100, 1 in. plate stock, machined surfaces', 'owner': {'name': '', 'contact': ''}, 'id': 'Table 3. (metals) #019'}, 'type': 'measurement', 'measurement': {'description': '', 'technique': 'ICP-MS', 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'results': [{'type': 'measurement', 'value': [1.88, 0.45], 'isotope': 'Th-232', 'unit': 'ppt'}, {'type': 'measurement', 'value': [3.11, 0.39], 'isotope': 'U-238', 'unit': 'ppt'}], 'practitioner': {'name': '', 'contact': ''}}, '_version': 1})
    coll.insert_one({'_id': ObjectId('5f18a7020a51fbd22bb862a3'), 'specification': '3.00', 'data_source': {'input': {'name': 'James Loach', 'contact': 'james.loach@gmail.com', 'notes': '', 'date': [datetime.datetime(2016, 7, 14, 0, 0)]}, 'reference': 'N. Abgrall et al., Nucl. Instr. and Meth. A 828 (2016) (doi:10.1016/j.nima.2016.04.070)'}, 'grouping': 'Majorana (2016)', 'sample': {'name': 'Copper, C10100, bar stock, machined surfaces', 'source': '', 'description': 'Copper, C10100, 1 in. x 2 in. bar stock, machined surfaces', 'owner': {'name': '', 'contact': ''}, 'id': 'Table 3. (metals) #020'}, 'type': 'measurement', 'measurement': {'description': '', 'technique': 'ICP-MS', 'requestor': {'name': '', 'contact': ''}, 'date': [], 'institution': '', 'results': [{'type': 'measurement', 'value': [2.12, 0.39], 'isotope': 'Th-232', 'unit': 'ppt'}, {'type': 'measurement', 'value': [2.25, 0.15], 'isotope': 'U-238', 'unit': 'ppt'}], 'practitioner': {'name': '', 'contact': ''}}, '_version': 1})



def _teardown_db_for_test():
    client = MongoClient('localhost', 27017)
    coll = client.dune_pytest_data.test_data
    old_versions_coll = client.dune_pytest_data.test_data_oldversions
    remove_resp = coll.delete_many({})
    resmove_oldversions_resp = old_versions_coll.delete_many({})



