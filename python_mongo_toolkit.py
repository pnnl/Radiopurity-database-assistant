import sys
import argparse
import json
import re
from datetime import datetime
from pymongo import MongoClient

numeric_fields = ["measurement.results.value"]
date_fields = ["measurement.date", "data_source.input.date"]
valid_fields = ["grouping", "sample.name", "sample.description", "sample.source", "sample.id", "sample.owner.name", "sample.owner.contact", "measurement.results.isotope", "measurement.results.symbol", "measurement.results.type", "measurement.results.unit", "measurement.results.value", "measurement.practitioner.name", "measurement.practitioner.contact", "measurement.technique","measurement.institution", "measurement.date", "measurement.description", "measurement.requestor.name", "measurement.requestor.contact", "data_source.reference", "data_source.input.name", "data_source.input.contact", "data_source.input.date", "data_source.input.notes"]
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
def insert(sample_name, sample_description, datasource_reference, datasource_input_name, datasource_input_contact, datasource_input_date, \
    grouping="", sample_source="", sample_id="", sample_owner_name="", sample_owner_contact="", \
    measurement_results=[], measurement_practitioner_name="", measurement_practitioner_contact="", \
    measurement_technique="", measurement_institution="", measurement_date=[], measurement_description="", \
    measurement_requestor_name="", measurement_requestor_contact="", datasource_input_notes=""):

    # verify and convert measurement_results arg
    results_keys = ["isotope", "type", "unit", "value"]
    if type(measurement_results) is not list:
        print('Error: the measurement_results argument must be a list containing dictionary objects')
        sys.exit()
    for i, results_element in enumerate(measurement_results):
        if type(results_element) is not dict:
            print('Error: the measurement_results argument must be dictionaries')
            sys.exit()
        for results_key in results_keys:
            if results_key not in list(results_element.keys()):
                print('Error: at least one of the required keys ('+', '.join(results_keys)+') is missing from at least one of the dictionaries in the measurement_results argument')
                sys.exit()
            if results_key == 'type':
                if measurement_results[i][results_key] not in ['measurement', 'range', 'limit']:
                    print('Error: "type" field of the measurement_results dictionaries must be one of: "measurement", "range", "limit"')
                    sys.exit()
            elif results_key == 'value':
                if type(measurement_results[i][results_key]) is not list:
                    print('Error: the "value" field of the dictionaries in the measurement_results list must be a list')
                    sys.exit()
                for j in range(len(measurement_results[i][results_key])):
                    try:
                        measurement_results[i][results_key][j] = float(measurement_results[i][results_key][j])
                    except:
                        print('Error: at least one of the elements in the "value" list of at least one of the dictionaries in the measurement_results list cannot be parsed into a number')
                        sys.exit()

    # verify and convert datasource_input_date arg
    if type(datasource_input_date) is not list:
        print('Error: the datasource_input_date argument must be a list of date strings.')
        sys.exit()
    for d, date_str in enumerate(datasource_input_date):
        new_date_obj = convert_date(date_str)
        if new_date_obj is None:
            print("Error: at least one of the datasource_input_date strings is not in one of the accepted formats")
            sys.exit()
        else:
            datasource_input_date[d] = new_date_obj

    # verify and convert measurement_date arg
    if type(measurement_date) is not list:
        print('Error: the measurement_date argument must be a list of date strings.')
        sys.exit()
    if len(measurement_date) > 0:
        for d, date_str in enumerate(measurement_date):
            new_date_obj = convert_date(date_str)
            if new_date_obj is None:
                print("Error: at least one of the measurement_date strings is not in one of the accepted formats")
                sys.exit()
            else:
                measurement_date[d] = new_date_obj

    # assemble insertion object
    doc = {"specification":3.0, "grouping":grouping, "type":"assay", 
        "sample": {
            "name":sample_name,
            "description":sample_description,
            "source":sample_source,
            "id":sample_id,
            "owner": {
                "name":sample_owner_name, 
                "contact":sample_owner_contact
            }
        },
        "measurement": {
            "description":measurement_description,
            "requestor": {
                "name":measurement_requestor_name, 
                "contact":measurement_requestor_contact
            },
            "practitioner": {
                "name":measurement_practitioner_name, 
                "contact":measurement_practitioner_contact
            },
            "technique":measurement_technique,
            "institution":measurement_institution,
            "date":measurement_date,
            "results":measurement_results
        },
        "data_source": {
            "reference":datasource_reference,
            "input": {
                "notes":datasource_input_notes,
                "date":datasource_input_date,
                "name":datasource_input_name,
                "contact":datasource_input_contact
            }
        }
    }
    print(doc)

    # perform doc insert
#    mongo_id = coll.insert_one(doc).inserted_id
    try:
        print("Successfully inserted doc with id:",mongo_id)
    except:
        print("Error inserting doc")

    return mongo_id


def convert_date(date_str):
    new_date_obj = None
    date_formats = ["%Y-%m-%d", "%Y/%m/%d", "%Y-%d-%m", "%Y/%d/%m", "%m-%d-%Y", "%m/%d/%Y", "%d-%m-%Y", "%d/%m/%Y"]
    for date_format in date_formats:
        try:
            new_date_obj = datetime.strptime(date_str, date_format)
            break
        except:
            pass
    return new_date_obj


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
    insert_parser.add_argument('--sample_name', type=str, required=True, help='concise sample description')
    insert_parser.add_argument('--sample_description', type=str, required=True, help='detailed sample description')
    insert_parser.add_argument('--datasource_reference', type=str, required=True, help='where the data came from')
    insert_parser.add_argument('--datasource_input_name', type=str, required=True, help='name of the person/people who performed data input')
    insert_parser.add_argument('--datasource_input_contact', type=str, required=True, help='email or telephone of the person/people who performed data input')
    insert_parser.add_argument('--datasource_input_date', nargs='*', required=True, help='list of date strings for dates of input')
    insert_parser.add_argument('--datasource_input_notes', type=str, default='', help='input simplifications, assumptions')
    insert_parser.add_argument('--grouping', type=str, default='', help='experiment name or similar')
    insert_parser.add_argument('--sample_source', type=str, default='', help='where the sample came from')
    insert_parser.add_argument('--sample_id', type=str, default='', help='identification number')
    insert_parser.add_argument('--sample_owner_name', type=str, default='', help='name of who owns the sample')
    insert_parser.add_argument('--sample_owner_contact', type=str, default='', help='email or telephone of who owns the sample')
    insert_parser.add_argument('--measurement_results', nargs='*', default=[], help='list of measurements')
    insert_parser.add_argument('--measurement_practitioner_name', type=str, default='', help='name of who did the measurement')
    insert_parser.add_argument('--measurement_practitioner_contact', type=str, default='', help='email or telephone of who did the measurement')
    insert_parser.add_argument('--measurement_technique', type=str, default='', help='technique name')
    insert_parser.add_argument('--measurement_institution', type=str, default='', help='institution name')
    insert_parser.add_argument('--measurement_date', nargs='*', default=[], help='list of date strings for dates of measurement')
    insert_parser.add_argument('--measurement_description', type=str, default='', help='detailed description')
    insert_parser.add_argument('--measurement_requestor_name', type=str, default='', help='name of who coordinated the measurement')
    insert_parser.add_argument('--measurement_requestor_contact', type=str, default='', help='email or telephone of who coordinated the measurement')

    args = vars(parser.parse_args())
    print(args['datasource_input_date'])

    if args['subparser_name'] == 'search':
        result = search(args['q'])
    elif args['subparser_name'] == 'add':
        result = add_to_query(args['field'], args['compare'], args['val'], existing_q=args['q'], append_mode=args['mode'])
    elif args['subparser_name'] == 'insert':
        for i in range(len(args['measurement_results'])):
            args['measurement_results'][i] = json.loads(args['measurement_results'][i])
        result = insert(args['sample_name'], \
            args['sample_description'], \
            args['datasource_reference'], \
            args['datasource_input_name'], \
            args['datasource_input_contact'], \
            args['datasource_input_date'], \
            datasource_input_notes=args['datasource_input_notes'], \
            grouping=args['grouping'], \
            sample_source=args['sample_source'], \
            sample_id=args['sample_id'], \
            sample_owner_name=args['sample_owner_name'], \
            sample_owner_contact=args['sample_owner_contact'], \
            measurement_results=args['measurement_results'], \
            measurement_practitioner_name=args['measurement_practitioner_name'], \
            measurement_practitioner_contact=args['measurement_practitioner_contact'], \
            measurement_technique=args['measurement_technique'], \
            measurement_institution=args['measurement_institution'], \
            measurement_date=args['measurement_date'], \
            measurement_description=args['measurement_description'], \
            measurement_requestor_name=args['measurement_requestor_name'], \
            measurement_requestor_contact=args['measurement_requestor_contact']
        )

    print(result)

