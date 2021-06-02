import pytest
import requests
import json
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

base_url = 'http://localhost:5000'


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



def setup_browser():
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('headless')
    options.add_argument('window-size=1200x600')
    browser = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    return browser
def teardown_browser(browser):
    browser.quit()



