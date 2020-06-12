import sys
#import argparse
import json
from pymongo import MongoClient

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
def add_to_query(append_mode, field, comparison, value, existing_q={}):
    # validate arguments
    if field not in valid_fields:
        print("Error: the 'field' argument must be one of: "+', '.join(valid_fields))
        return None
    if comparison not in set(valid_str_comparisons+valid_num_comparisons):
        print("Error: the 'comparison' argument must be one of: "+', '.join(set(valid_str_comparisons+valid_num_comparisons)))
        return None
    if append_mode.upper() not in valid_appendmodes:
        print("Error: the 'append_mode' argument must be one of: "+', '.join(valid_appendmodes))
        return None
    if type(value) is str and comparison not in valid_str_comparisons:
        print("Error: when comparing string values, the comparison operator must be one of: "+', '.join(valid_str_comparisons))
        return None
    if type(value) is not str and comparison not in valid_num_comparisons:
        print("Error: when comparing numeric values, the comparison operator must be one of: "+', '.join(valid_int_comparisons))
        return None

    # define new term
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
    #TODO: figure out how to go about $or and $and functionality
    existing_q[field] = new_term[field]
    '''
    if append_mode == 'OR':
        print("HAVEN'T IMPLEMENTED $or FUNCTIONALITY YET.")
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
    '''

    return existing_q


# insert
#TODO: how to impose MADF format? --> refer to... https://www.sciencedirect.com/science/article/pii/S0168900216309639
def insert(doc):
    madf_required_fields = ["sample.name", "sample.description", "source.reference", "source.input.name", "source.input.contact", "source.input.date"]
    pass

if __name__ == '__main__':
    func_keys = ['search','add','insert']
    '''
    parser = argparse.ArgumentParser(description='A python toolkit for interfacing with the radiopurity_example MongoDB.')
    parser.add_argument('--func', choices=['search','add','insert'], help='Specify which function to perform. \
        "search" requires a dictionary query. "add" appends a field, comparison, value search term to an existing \
        query. "insert" requires a single dictionary document in MADF format.')
    args = parser.parse_args()

    if args.func == 'search':
        search()
    elif args.func == 'add':
        add_to_query()
    elif args.func == 'insert':
        insert()
    '''

    if len(sys.argv) < 2:
        print("Error: you must enter the function name to call, as well as all relevant arguments for that function.")
        sys.exit()
    if sys.argv[1] not in func_keys:
        print("Error: the first argument must be one of the function keys: "+', '.join(func_keys))
        sys.exit()

    arg_len = len(sys.argv)

    if sys.argv[1] == 'search':
        if arg_len != 3:
            print("Error: when choosing 'search' you must enter a query dictionary.")
            sys.exit()
        result = search(json.loads(sys.argv[2]))
    elif sys.argv[1] == 'add':
        if arg_len == 6:
            result = add_to_query(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
        elif arg_len == 7:
            result = add_to_query(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], json.loads(sys.argv[6]))
        else:
            print("Error: when choosing 'add' you must enter an append mode, field, comparison operator, value, and an optional existing query to add to.")
            sys.exit()
        result = json.dumps(result)
    elif sys.argv[1] == 'insert':
        if arg_len != 3:
            print("Error: when choosing 'insert' you must enter a document dictionary in MADF format.")
            sys.exit()
        result = insert(json.loads(sys.argv[2]))

    #TODO: cannot return result?
    print(result)

