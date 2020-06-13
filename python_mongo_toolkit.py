import argparse
import json
import re
from pymongo import MongoClient

numeric_fields = ["measurements.results.value"]
date_fields = ["measurements.date", "source.input.date"]
valid_fields = ["grouping", "sample.name", "sample.description", "sample.source", "sample.id", "sample.owner.name", "sample.owner.contact", "measurements.results.isotope", "measurements.results.symbol", "measurements.results.unit", "measurements.results.value", "measurements.practitioner.name", "measurements.practitioner.contact", "measurements.technique","measurements.institution", "measurements.date", "measurements.description", "source.reference", "source.input.name", "source.input.contact", "source.input.date", "source.input.notes"]
valid_str_comparisons = ["contains", "notcontains", "eq"]
valid_num_comparisons = ["eq", "lt", "lte", "gt", "gte"]
valid_appendmodes = ["AND", "OR"]

client = MongoClient('130.20.47.128', 27017)
coll = client.radiopurity_data.example_data

# search
def search(query):
    if type(query) is not dict:
        print("Error: the query argument must be a dictionary.")
        return None

    resp = coll.find(query)
    resp = list(resp)
    return resp

# append to existing query
def add_to_query(field, comparison, value, existing_q={}, append_mode="ADD"):
    # validate arguments
    if field not in valid_fields:
        print("Error: the 'field' argument must be one of: "+', '.join(valid_fields))
        return existing_q
    if comparison not in set(valid_str_comparisons+valid_num_comparisons):
        print("Error: the 'comparison' argument must be one of: "+', '.join(set(valid_str_comparisons+valid_num_comparisons)))
        return existing_q
    if append_mode.upper() not in valid_appendmodes:
        print("Error: the 'append_mode' argument must be one of: "+', '.join(valid_appendmodes))
        return existing_q
    if field in numeric_fields and type(value) not in [int, float]:
        try:
            value = float(value)
        except:
            print('Error: you must enter a numeric value when comparing fields in: '+ ', '.join(numeric_fields))
            return existing_q
    if type(value) is str and comparison not in valid_str_comparisons:
        print("Error: when comparing string values, the comparison operator must be one of: "+', '.join(valid_str_comparisons))
        return existing_q
    if type(value) is not str and comparison not in valid_num_comparisons:
        print("Error: when comparing numeric values, the comparison operator must be one of: "+', '.join(valid_int_comparisons))
        return existing_q

    # define new term
    if field in date_fields:
        #TODO: implement date comparisons
        pass
    if type(value) is str:
        if comparison == 'contains':
            search_val = {'$regex':'.*'+value+'.*'}
        elif comparison == 'notcontains':
            match_pattern = re.compile(value)
            search_val = {"$not":match_pattern}
        else:
            search_val = {'$regex':value}
        new_term = {field:search_val}
    else:
        comparison = '$' + comparison
        new_term = {field:{comparison:value}}

    # add new term to existing_q
    #TODO: decide how to go about $or and $and functionality
    existing_keys = list(existing_q.keys())
    if append_mode == 'OR':
        if '$or' in existing_keys:
            # add to other $or elements (this groups all $or terms together))
            existing_q['$or'].append(new_term)
        else:
            # creates an $or list out of this new term and the most recently added element (query dict --> "Python 3.6 onwards, the standard dict type maintains insertion order by default.")
            existing_q['$or'] = [{existing_keys[-1]:existing_q.pop(existing_keys[-1])}, new_term]
    else:
        if field in existing_q.keys():
            print('A. creating $and from existing.')
            existing_q['$and'] = [{field:existing_q.pop(field)}, new_term]
        elif '$and' in existing_q.keys() and [list(f.keys())[0] for f in existing_q['$and']]:
            print('B. adding to existing $and')
            existing_q['$and'].append(new_term)
        else:
            print('C. new element')
            existing_q[field] = new_term[field]

    return existing_q


# insert
#TODO: how to impose MADF format? --> refer to... https://www.sciencedirect.com/science/article/pii/S0168900216309639
def insert(doc):
    madf_required_fields = ["sample.name", "sample.description", "source.reference", "source.input.name", "source.input.contact", "source.input.date"]
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A python toolkit for interfacing with the radiopurity_example MongoDB.')
    subparsers = parser.add_subparsers(help='options for which function to run', dest='subparser_name')

    search_parser = subparsers.add_parser('search', help='execute search function')
    search_parser.add_argument('--q', type=json.loads, required=True, help='query to execute. *must be surrounded with single quotes, and use double quotes within dict*')

    append_parser = subparsers.add_parser('add', help='execute append function (add new query term to query)')
    append_parser.add_argument('--field', type=str, required=True, choices=valid_fields, help='the field to compare the value of')
    append_parser.add_argument('--compare', type=str, required=True, choices=list(set(valid_str_comparisons+valid_num_comparisons)), \
        help='comparison operator to use to compare actual field value to given value')
    append_parser.add_argument('--val', type=str, required=True, help='the value to compare against. Can be a string or numeric')
    append_parser.add_argument('--mode', type=str, choices=["OR", "AND"], default="AND", help='optional argument to define append mode. If not present, defaults to "AND"')
    append_parser.add_argument('--q', type=json.loads, default={}, \
        help='*must be surrounded with single quotes, and use double quotes within dict* existing query dictionary to add a new term to. If not present, creates a new query')

    insert_parser = subparsers.add_parser('insert', help='execute document insert function')
    insert_parser.add_argument('--doc', type=json.loads, required=True, \
        help='The dictinoary document to insert into the database. *must be surrounded with single quotes, and use double quotes within dict*')
    
    args = vars(parser.parse_args())

    if args['subparser_name'] == 'search':
        result = search(args['q'])
    elif args['subparser_name'] == 'add':
        result = add_to_query(args['field'], args['compare'], args['val'], existing_q=args['q'], append_mode=args['mode'])
    elif args['subparser_name'] == 'insert':
        result = insert(args['doc'])

    print(result)

