import pytest
import requests
from selenium import webdriver
from test_auxiliary import base_url, setup_browser, teardown_browser
from test_auxiliary import setup_browser, teardown_browser

endpoints = [
    '/',
    '/simple_search',
    '/search',
    '/edit/insert',
    '/edit/update'
]
@pytest.mark.parametrize('endpoint', endpoints)
def test_api_up(endpoint):
    url = base_url + endpoint
    resp = requests.get(url)
    assert resp.status_code == 200, 'Error: status code is '+str(resp.status_code)+', not 200 for endpoint:'+endpoint
    assert resp.url == url

endpoints = [
    '/',
    '/about',
    '/simple_search',
    '/search',
    '/edit/insert',
    '/edit/update',
]
@pytest.mark.parametrize('endpoint', endpoints)
def test_logo_links(endpoint):
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

