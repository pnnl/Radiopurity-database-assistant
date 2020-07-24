import pytest
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime
import re

from python_mongo_toolkit import set_ui_db
from python_mongo_toolkit import search_by_id
from python_mongo_toolkit import update_with_versions
from python_mongo_toolkit import search
from python_mongo_toolkit import add_to_query
from python_mongo_toolkit import insert
from python_mongo_toolkit import convert_str_to_date
from python_mongo_toolkit import convert_date_to_str
from python_mongo_toolkit import _validate_measurement_results_data


# OTHER POSSIBLE TESTS
# try to add same field twice? w same val/compare? w diff val/compare?
# add every single field
#TODO query with dates!!!
# q starts with measurement.results object, adds another measurement.results object (AND, OR)
# q starts with measurement.results object, adds non-measurement.results object (AND, OR)
# q starts with measurement.results object, adds non, adds another measurement.results object (AND, OR)
# q starts with non, adds measurement.results object, adds another measurement.results object (AND, OR)
# q starts with non, adds measurement.results object, adds another non (AND, OR)


def test_add_to_query_with_search_a():
    field = 'grouping'
    comp = 'contains'
    val = 'testing'
    existing_q, error_msg = add_to_query(field=field, comparison=comp, value=val, existing_q={})
    assert existing_q == {'grouping':re.compile('^.*testing.*$',re.IGNORECASE)}

    field = 'measurement.results.isotope'
    comp = 'eq'
    val = 'U'
    append_mode = 'OR'
    existing_q, error_msg = add_to_query(field=field, comparison=comp, value=val, existing_q=existing_q, append_mode=append_mode)
    assert existing_q == {'$or':[{'grouping':re.compile('^.*testing.*$',re.IGNORECASE)}, {'measurement.results':{'$elemMatch':{'isotope':re.compile('^U$',re.IGNORECASE)}}}]}

    field = 'measurement.results.value'
    comp = 'gte'
    val = 100.0
    append_mode = 'AND'
    existing_q, error_msg = add_to_query(field=field, comparison=comp, value=val, existing_q=existing_q, append_mode=append_mode)
    assert existing_q == {'$or':[{'grouping':re.compile('^.*testing.*$',re.IGNORECASE)}, {'measurement.results':{'$elemMatch':{'$and':[{'isotope':re.compile('^U$',re.IGNORECASE)}, {'value.0':{'$gte':100.0}}]}}}]}

    field = 'measurement.results.unit'
    comp = 'eq'
    val = 'ppt'
    append_mode = 'AND'
    existing_q, error_msg = add_to_query(field=field, comparison=comp, value=val, existing_q=existing_q, append_mode=append_mode)
    assert existing_q == {'$or':[{'grouping':re.compile('^.*testing.*$',re.IGNORECASE)}, {'measurement.results':{'$elemMatch':{'$and':[{'isotope':re.compile('^U$',re.IGNORECASE)}, {'value.0':{'$gte':100.0}}, {'unit':re.compile('^ppt$', re.IGNORECASE)}]}}}]}


    search_resp = search(existing_q)
    for doc in search_resp:
        grouping = doc['grouping']
        valid_meas_found = False
        for meas_result in doc['measurement']['results']:
            if len(meas_result['value']) > 0:
                if meas_result['value'][0] >= 100 and meas_result['isotope'] == 'U' and meas_result['unit'] == 'ppt':
                    valid_meas_found = True
        assert 'testing' in grouping or valid_meas_found


def test_add_to_query_bad_field_name():
    field = 'test' # not a valid field name
    comp = 'contains'
    val = 'testing'
    existing_q, error_msg = add_to_query(field=field, comparison=comp, value=val, existing_q={})
    assert existing_q == {}

def test_add_to_query_bad_comparison():
    field = 'grouping'
    comp = 'test' # not a valid comparator; must be one of ['contains', 'notcontains', 'eq', 'gt', 'gte', 'lt', 'lte']
    val = 'testing'
    existing_q, error_msg = add_to_query(field=field, comparison=comp, value=val, existing_q={})
    assert existing_q == {}

def test_add_to_query_bad_comparison_num_comp_on_str():
    field = 'grouping'
    comp = 'gt' # not a string comparator
    val = 'testing'
    existing_q, error_msg = add_to_query(field=field, comparison=comp, value=val, existing_q={})
    assert existing_q == {}

def test_add_to_query_bad_comparison_str_comp_on_num():
    field = 'measurement.results.value'
    comp = 'contains' # not a numerical comparator
    val = 10
    existing_q, error_msg = add_to_query(field=field, comparison=comp, value=val, existing_q={})
    assert existing_q == {}

def test_add_to_query_bad_val():
    field = 'measurement.results.value'
    comp = 'gt'
    val = 'test' # must be num, not str
    existing_q, error_msg = add_to_query(field=field, comparison=comp, value=val, existing_q={})
    assert existing_q == {}

def test_add_to_query_bad_append_mode():
    field = 'grouping'
    comp = 'contains'
    val = 'testing'
    append_mode = 'testing' # must be one of ['AND', 'OR']
    existing_q, error_msg = add_to_query(field=field, comparison=comp, value=val, existing_q={}, append_mode='testing')
    assert existing_q == {}


