import pytest
import requests
from selenium import webdriver
from test_auxiliary import base_url, login, logout, setup_browser, teardown_browser
from test_auxiliary import setup_browser, teardown_browser

endpoints = [
    '/',
    '/simple_search',
    '/search',
    '/login',
    '/restricted_page',
]
@pytest.mark.parametrize('endpoint', endpoints)
def test_api_up(endpoint):
    r = requests.get(base_url + '/logout') #logout for good measure

    url = base_url + endpoint
    resp = requests.get(url)
    assert resp.status_code == 200, 'Error: status code is '+str(resp.status_code)+', not 200 for endpoint:'+endpoint
    assert resp.url == url

restricted_endpoints = [
    '/insert',
    '/update',
]
@pytest.mark.parametrize('endpoint', restricted_endpoints)
def test_restricted_pages_are_restricted(endpoint):
    r = requests.get(base_url + '/logout') #logout for good measure

    url = base_url + endpoint
    resp = requests.post(url)
    assert resp.url == base_url+'/login', 'Error for endpoint: '+endpoint


write_endpoints = [
    '/insert',
    '/update',
]
@pytest.mark.parametrize('endpoint', write_endpoints)
def test_readwrite_endpoints_work_when_logged_in(endpoint):
    browser = setup_browser()

    # logout for good measure
    logout(browser)
    assert browser.current_url == base_url + '/login'

    # login as write user
    login("DUNEwriter", browser)

    # test that write user can access writeuser-allowed endpoints
    url = base_url + endpoint
    browser.get(url)
    assert browser.current_url == url

    # logout
    logout(browser)
    assert browser.current_url == base_url + '/login'

    # test that logged out user cannot access writeuser-allowed endpoints
    browser.get(url)
    assert browser.current_url == base_url + '/login'

    teardown_browser(browser)


#'''
endpoints = [
    '/',
    '/simple_search',
    '/search',
    '/insert',
    '/update',
    '/login',
    '/restricted_page',
]
#'''
#endpoints = ['/about']
@pytest.mark.parametrize('endpoint', endpoints)
def test_logo_links(endpoint):
    r = requests.get(base_url + '/logout') #logout for good measure

    browser = setup_browser()

    # test PNNL logo
    url = base_url + endpoint
    browser.get(url)
    
    pnnl_logo_img = browser.find_element_by_id('pnnl-logo-link')
    pnnl_logo_img.click()

    tab_urls = []
    for handle in browser.window_handles:
        browser.switch_to.window(handle)
        tab_urls.append(browser.current_url)
    assert "https://www.pnnl.gov/" in tab_urls

    # test SNOLAB logo
    browser.get(url)
    
    snolab_logo_img = browser.find_element_by_id('snolab-logo-link')
    snolab_logo_img.click()
    
    tab_urls = []
    for handle in browser.window_handles:
        browser.switch_to.window(handle)
        tab_urls.append(browser.current_url)

    assert "https://www.snolab.ca/" in tab_urls

    teardown_browser(browser)

