import re
import pytest
from query_class import Query

data_load_from_str = [
    ("all contains ", {}),
    ("all contains testing", {'$text': {'$search': 'testing'}}),
    ("grouping equals ", {"grouping": {"$regex": re.compile('^$', re.IGNORECASE)}}),
    ("grouping contains one\nOR\nsample.name does not contain two\nAND\nsample.description equals three", {"$or": [{'grouping': {"$regex": re.compile('^.*one.*$', re.IGNORECASE)}}, {"$and":[{'sample.name': {'$not': re.compile('^two$', re.IGNORECASE)}}, {'sample.description': {"$regex": re.compile('^three$', re.IGNORECASE)}}]}]}),
    ("measurement.results.value is less than 10\nAND\nmeasurement.results.value is greater than or equal to 5", {'$or': [{'measurement.results': {'$elemMatch': {'type': 'measurement', 'value.0': {'$lt': 10, '$gte': 5}}}}, {'measurement.results': {'$elemMatch': {'type': 'range', 'value.1': {'$gt': 10}, 'value.0': {'$lte': 5}}}}]}),
    ("measurement.results.unit equals ppm\nAND\nmeasurement.results.value equals 37.2\nOR\nmeasurement.results.value is greater than 20.4\nAND\nmeasurement.results.value is less than or equal to 40.6\nAND\ngrouping contains majorana", {'$or': [{'measurement.results': {'$elemMatch': {'unit': {'$regex': re.compile('^ppm$', re.IGNORECASE)}, 'type': 'measurement', 'value.0': {'$eq': 37.2}}}}, {'$and': [{'$or': [{'measurement.results': {'$elemMatch': {'type': 'measurement', 'value.0': {'$gt': 20.4, '$lte': 40.6}}}}, {'measurement.results': {'$elemMatch': {'type': 'range', 'value.0': {'$lt': 20.4}, 'value.1': {'$gte': 40.6}}}}]}, {'grouping': {'$regex': re.compile('^.*majorana.*$', re.IGNORECASE)}}]}]}),
    ('grouping contains ["copper", "Cu"]', {'$or': [{'grouping': {'$regex': re.compile('^.*copper.*$', re.IGNORECASE)}}, {'grouping': {'$regex': re.compile('^.*Cu.*$', re.IGNORECASE)}}]}),
    ('measurement.results.isotope equals K-40\nAND\nmeasurement.results.unit equals ppm\nAND\nmeasurement.results.value is greater than 0.1\nAND\nmeasurement.results.value is less than or equal to 1', {'$or': [{'measurement.results': {'$elemMatch': {'isotope': {'$regex': re.compile('^K-40$', re.IGNORECASE)}, 'unit': {'$regex': re.compile('^ppm$', re.IGNORECASE)}, 'type': 'measurement', 'value.0': {'$gt': 0.1, '$lte': 1}}}}, {'measurement.results': {'$elemMatch': {'isotope': {'$regex': re.compile('^K-40$', re.IGNORECASE)}, 'unit': {'$regex': re.compile('^ppm$', re.IGNORECASE)}, 'type': 'range', 'value.0': {'$lt': 0.1}, 'value.1': {'$gte': 1}}}}]}),
    ('measurement.results.type equals range\nAND\nmeasurement.results.value is greater than 200\nAND\nmeasurement.results.value is less than 1', {'measurement.results': {'$elemMatch': {'type': 'range', 'value.0': {'$lt': 200}, 'value.1': {'$gt': 1}}}})
]
@pytest.mark.parametrize("base_str,correct_q_dict", data_load_from_str)
def test_load_from_str(base_str, correct_q_dict):
    q_obj = Query(query_str=base_str)
    q_str = q_obj.to_human_string()
    q_dict = q_obj.to_query_lang()
    print('ACTUAL:',q_dict)
    print('CORRCT:',correct_q_dict)
    assert q_str == base_str
    assert q_dict == correct_q_dict


'''
"measurement.results.value is less than 10\nAND\nmeasurement.results.value is greater than or equal to 5"
{'$or': [{'measurement.results': {'$elemMatch': {'value.0': {'$lt': 10, '$gte': 5}}}}, {'measurement.results': {'$elemMatch': {'value.1': {'$gt': 10}, 'value.0': {'$lte': 5}}}}]}
{'$or': [{'measurement.results': {'$elemMatch': {'type': 'measurement', 'value.0': {'$lt': 10, '$gte': 5}}}}, {'measurement.results': {'$elemMatch': {'type': 'range', 'value.1': {'$gt': 10}, 'value.0': {'$lte': 5}}}}]}
'''

'''
'measurement.results.type equals range\nAND\nmeasurement.results.value is greater than 200\nAND\nmeasurement.results.value is less than 1'
 {'measurement.results': {'$elemMatch': {'type': 'range', 'value.0': {'$lt': 200}, 'value.1': {'$gt': 1}}}}
'''

'''
{'$or': [
    {'measurement.results': {'$elemMatch': {
        'isotope': {'$regex': re.compile('^K-40$', re.IGNORECASE)}, 
        'unit': {'$regex': re.compile('^ppm$', re.IGNORECASE)}, 
        'type': 'measurement', 
        'value.0': {'$gt': 0.1, '$lte': 1}
    }}}, 
    {'measurement.results': {'$elemMatch': {
        'isotope': {'$regex': re.compile('^K-40$', re.IGNORECASE)}, 
        'unit': {'$regex': re.compile('^ppm$', re.IGNORECASE)}, 
        'type': 'range', 
        'value.0': {'$lt': 0.1}, 
        'value.1': {'$gte': 1}
    }}}
]}
'''


"measurement.results.unit equals ppm\nAND\nmeasurement.results.value equals 37.2\nOR\nmeasurement.results.value is greater than 20.4\nAND\nmeasurement.results.value is less than or equal to 40.6\nAND\ngrouping contains majorana"

'''
{'measurement.results': {'$elemMatch': {'type': 'measurement', 'unit': re.compile('^ppm$', re.IGNORECASE), 'value.0': {'$eq': 37.2}}}}
{'$or': [{'measurement.results': {'$elemMatch': {'type': 'measurement', 'value.0': {'$gt': 20.4, '$lte': 40.6}}}}, {'measurement.results': {'$elemMatch': {'type': 'range', 'value.0': {'$lt': 20.4}, 'value.1': {'$gte': 40.6}}}}]}
{'grouping': re.compile('^.*majorana.*$', re.IGNORECASE)}

{'$or': [{'measurement.results': {'$elemMatch': {'type': 'measurement', 'unit': re.compile('^ppm$', re.IGNORECASE), 'value.0': {'$eq': 37.2}}}}, '$and': [{'$or': [{'measurement.results': {'$elemMatch': {'type': 'measurement', 'value.0': {'$gt': 20.4, '$lte': 40.6}}}}, {'measurement.results': {'$elemMatch': {'type': 'range', 'value.0': {'$lt': 20.4}, 'value.1': {'$gte': 40.6}}}}]}, {'grouping': re.compile('^.*majorana.*$', re.IGNORECASE)}]]}

{'$or': [{'measurement.results': {'$elemMatch': {'unit': {'$regex': re.compile('^ppm$', re.IGNORECASE)}, 'type': 'measurement', 'value.0': {'$eq': 37.2}}}}, {'$and': [{'$or': [{'measurement.results': {'$elemMatch': {'type': 'measurement', 'value.0': {'$gt': 20.4, '$lte': 40.6}}}}, {'measurement.results': {'$elemMatch': {'type': 'range', 'value.0': {'$lt': 20.4}, 'value.1': {'$gte': 40.6}}}}]}, {'grouping': {'$regex': re.compile('^.*majorana.*$', re.IGNORECASE)}}]}]}
'''

'''
grouping contains majorana
AND
measurement.results.value is greater than or equal to 10.0
AND
measurement.results.value is less than or equal to 20.0
AND
measurement.results.unit equals ppm 
gives weird results where not all response docs are between 10 and 20 because the value arrays are searched separately (you could have 3 values)
'''
