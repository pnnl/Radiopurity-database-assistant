import os
import re
import json
import datetime
from copy import deepcopy

class Query():
    def __init__(self, query_str=None):
        # terms is a list of dicts with the following structure:
        # {"field":str, "comparison":str, "value":int|str|float|list}
        self.terms = []
        self.appends = []
        self.all_fields = []
        self.current_meas_results_obj = {}

        synonyms_filepath = os.getcwd() + '/synonyms.txt'
        self.synonyms = self._load_synonyms(synonyms_filepath)

        self.valid_append_modes = ['AND', 'OR']
        self.valid_field_names = ["all", "grouping", "sample.name", "sample.description", "sample.source", "sample.id", "sample.owner.name", "sample.owner.contact", "measurement.results.isotope", "measurement.results.type", "measurement.results.unit", "measurement.results.value", "measurement.practitioner.name", "measurement.practitioner.contact", "measurement.technique","measurement.institution", "measurement.date", "measurement.description", "measurement.requestor.name", "measurement.requestor.contact", "data_source.reference", "data_source.input.name", "data_source.input.contact", "data_source.input.date", "data_source.input.notes"]
        self.str_fields = ["all", "grouping", "sample.name", "sample.description", "sample.source", "sample.id", "sample.owner.name", "sample.owner.contact", "measurement.results.isotope", "measurement.results.type", "measurement.results.unit", "measurement.practitioner.name", "measurement.practitioner.contact", "measurement.technique","measurement.institution", "measurement.date", "measurement.description", "measurement.requestor.name", "measurement.requestor.contact", "data_source.reference", "data_source.input.name", "data_source.input.contact", "data_source.input.date", "data_source.input.notes"]
        self.num_fields = ['measurement.results.value']
        self.date_fields = ["measurement.date", "data_source.input.date"]
        self.str_comparisons = ["eq", "contains", "notcontains"]
        self.num_comparisons = ["eq", "lt", "lte", "gt", "gte"]
        self.date_comparisons = ["eq", "lt", "lte", "gt", "gte"]

        if query_str is not None:
            self._load_from_str(query_str)

        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print('TERMS:',self.terms)
        print('APNDS:',self.appends)
        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

    def _load_synonyms(self, filepath):
        synonyms_list = []
        with open(filepath, 'r') as read_file:
            for line in read_file:
                line_elements = line.strip().split(',')
                synonyms_list.append(line_elements)
        return synonyms_list

    def _get_field_from_str(self, line):
        end_idx = line.find(' ')
        field = line[:end_idx]
        line = line[end_idx+1:]
        return field, line
    def _get_comparison_from_str(self, line):
        # order matters here because "less than" and "greater than" will always match before "less than or equal to" and "greater than or equal to"
        human_to_raw = {
            "is less than or equal to":"lte",
            "is greater than or equal to":"gte",
            "equals":"eq",
            "contains":"contains",
            "does not contain":"notcontains",
            "is less than":"lt",
            "is greater than":"gt"
        }
        comparison = None
        for human in list(human_to_raw.keys()):
            if line.startswith(human):
                comparison = human_to_raw[human]
                end_idx = len(human)+1
                line = line[end_idx:]
                break
        if comparison is None:
            #TODO: error handling
            print('BAD COMPARISON:::',line)
        return comparison, line
    def _get_value_from_str(self, field, comparison, line):
        if field == 'all':
            #value = line.split()
            value = line.replace('["', '').replace('"]', '').split('", "')
            print('VAL:',value)
            if len(value) < 1:
                value = "" # convert to empty string if no values
            elif len(value) == 1:
                value = value[0] # convert to string if only one value
        elif field in self.str_fields:
            # synonyms
            if line.startswith('[') and line.endswith(']'):
                # added these brackets and double quotes to differentiate between a list and a comma in a search term
                line = line.replace('["', '').replace('"]', '')
                value = line.split('", "')
            else:
                value = line
        elif field in self.num_fields:
            if '.' in line:
                value = float(line.strip())
            else:
                value = int(line.strip())
        elif field in self.date_fields:
            value = line.strip()
        else:
            #TODO: handle error
            value = None
        return value
    def _load_from_str(self, query):
        lines = query.split('\n')
        append_type = ''
        for line in lines:
            line = line.strip()
            if line in ['AND', 'OR']:
                append_type = line
            else:
                field, line = self._get_field_from_str(line)
                comparison, line = self._get_comparison_from_str(line)
                value = self._get_value_from_str(field, comparison, line)
                self.add_query_term(field, comparison, value, append_type, include_synonyms=False)
        return True, ''

    def _find_synonyms(self, value):
        for word_list in self.synonyms:
            for word in word_list:
                if re.match('.*'+value+'.*', word, re.IGNORECASE):
                    #print('found val',value,'in',word)
                    return word_list
        return None

    def _add_query_term_all(self, value, append_type):
        if type(value) is list:
            value = ' '.join(value) #separate words by space so that they can be searched for individually by the text index. This would only be for the field=="all" case
        if 'all' in self.all_fields:
            for i in range(len(self.terms)):
                if self.terms[i]['field'] == 'all':
                    self.terms[i]['value'] += ' '+value
        else:
            term = {"field":'all', "comparison":'contains', "value":value}
            self.terms.append(term)
            if append_type != '':
                self.appends.append(append_type)
            self.all_fields.append('all')
    def _add_query_term_nonall(self, field, comparison, value, append_type):
        term = {"field":field, "comparison":comparison, "value":value}
        self.terms.append(term)
        if append_type != '':
            self.appends.append(append_type)
        self.all_fields.append(field)
    def add_query_term(self, field, comparison, value, append_type='', include_synonyms=True):
        is_valid, error_msg = self._validate_term(field, comparison, value, append_type) #this validates the field, comparison, value, and append_type
        if is_valid:
            if include_synonyms and value != '' and type(value) is str:
                synonyms_list = self._find_synonyms(value)
                if synonyms_list is not None:
                    value = synonyms_list
            if field == 'all':
                self._add_query_term_all(value, append_type) #NOTE: we can't do "and" within an "all" search.
            else:
                self._add_query_term_nonall(field, comparison, value, append_type)
        else:
            print(error_msg)

    def _convert_str_to_date(self, date_str):
        new_date_obj = None
        date_formats = ["%Y-%m-%d", "%Y/%m/%d", "%m-%d-%Y", "%m/%d/%Y", "%Y-%d-%m", "%Y/%d/%m", "%d-%m-%Y", "%d/%m/%Y"]
        for date_format in date_formats:
            try:
                new_date_obj = datetime.strptime(date_str, date_format)
                break
            except:
                pass
        return new_date_obj
    def _convert_str_list_to_date(self, str_list):
        date_objects = []
        for date_str in str_list:
            date_obj = convert_str_to_date(date_str)
            if date_obj is None:
                return None
            else:
                date_objects.append(date_objects)
        return date_objects

    def _assemble_qterm_all(self, field, comparison, value):
        # douple quotes around value indicate that it is a phrase and each word should not be searched for separately
        # space-separated words in string are searched for separately
        if value == '':
            term = {}
        else:
            term = {"$text":{"$search":value}}
        return term
    def _assemble_qterm_date(self, field, comparison, value):
        #TODO: implement date comparison taking second value into account (aka range)
        field += '.0' # only look at first date
        
        # comparison values in raw form are already in pymongo form, except the leading "$"
        comparison = '$' + comparison
        
        # the date value has already been validated so we need not worry about improper formatting
        search_val = self._convert_str_to_date(value)

        term = {field:{comparison:search_val}}
        return term
    def _assemble_qterm_str(self, field, comparison, value):
        def _create_contains_regex(token):
            return re.compile('^.*'+token+'.*$', re.IGNORECASE)
        def _create_equals_regex(token):
            return re.compile('^'+token+'$', re.IGNORECASE)
        def _create_regex(token, comparison):
            if comparison == 'contains':
                #search_val  = _create_contains_regex(token)
                search_val = {"$regex":_create_contains_regex(token)} # NOTE ELISE Dec 8
            elif comparison == 'notcontains':
                search_val = {'$not':_create_equals_regex(token)}
            else: #equals
                #search_val = _create_equals_regex(token)
                search_val = {"$regex":_create_equals_regex(token)} #NOTE: ELISE Dec 8
            return search_val
        def _assemble_list_search_term(field, comparison, value): # this is only for synonyms
            # looking for a field that does not equal/contain any of (A, B, C) --> "not A and not B and not C"
            # looking for a field that does equal/contain any of (A, B, C)     --> "A or B or C"
            if comparison == 'notcontains':
                append_mode = self._convert_append_str_to_q_operator("AND")
            else:
                append_mode = self._convert_append_str_to_q_operator("OR")

            term = {append_mode:[]}
            for word in value:
                search_val = _create_regex(word, comparison)
                search_term = {field:search_val}
                term[append_mode].append(search_term)
            return term

        # we need to assemble a sub-term of "OR" tokens for all synonyms
        if type(value) is list:
            term = _assemble_list_search_term(field, comparison, value)
        else:
            search_val = _create_regex(value, comparison)
            term = {field:search_val} 

        return term
    def _assemble_qterm_num(self, field, comparison, value):
        # comparison values in raw form are already in pymongo form, except the leading "$"
        comparison = '$' + comparison
        return {field:{comparison:value}}

    def _convert_append_str_to_q_operator(self, append_str):
        if append_str == 'AND':
            operator = '$and'
        else:
            operator = '$or'
        return operator

    def _consolidate_measurement_results(self):
        # don't want to alter the persisting terms/appends objects
        terms = deepcopy(self.terms)
        appends = deepcopy(self.appends)

        # separate the list of all terms on the "or" appends; For our purposes, all meas results terms that are "and"ed together get combined into one query. An "or" separates measurement results elemMatch objects.
        sep_indices = [0] + [ i+1 for i, ele in enumerate(appends) if ele == 'OR' ] + [len(terms)]
        separated_terms = []
        if len(sep_indices) > 0:
            for i in range(len(sep_indices)-1):
                start_idx = sep_indices[i]
                end_idx = sep_indices[i+1]
                separated_terms.append(terms[start_idx:end_idx])

        # go through each list which should only contain terms that are to be "and"ed together, find all the meas results terms, and combine them into one elemMatch object
        remove_indices = []
        insert_indices = []
        for i, terms_set in enumerate(separated_terms):
            start_idx = sep_indices[i]
            rm_indices = []
            meas_results_obj = []
            for j, term in enumerate(terms_set):
                if term['field'].startswith('measurement.results.'):
                    rm_indices.append(j+start_idx)
                    term['field'] = term['field'].replace('measurement.results.', '')
                    meas_results_obj.append(term)

            # the first instance of meas results should stay in the list so we can replace it
            if len(meas_results_obj) > 0:
                remove_indices.extend(rm_indices[1:])
                terms[rm_indices[0]] = {'field':'measurement.results', 'comparison':None, 'value':meas_results_obj}

        # remove all (except the first) meas results terms from the original list. the first meas results term should stay because it is now the consolidated object
        if len(remove_indices) > 0:
            remove_indices.sort(reverse=True)
            for i in remove_indices:
                appends.pop(i-1)
                terms.pop(i)

        return terms, appends

    def _get_meas_value_variations(self, val_terms, nonval_raw_terms):
        # figure out which measurement types are valid for this case
        meas_obj = self._get_meas_type_object(val_terms, nonval_raw_terms)

        meas_obj_keys = list(meas_obj.keys()) # get all the measurement types that were determined to be valid based on the comparisons and query terms

        # add terms to the meas_obj according to their appropriate measurement type
        for term in val_terms:
            comparison = term['comparison']
            value = term['value']

            # the "measurement" type is the only one with a single value that we can compare "eq" against
            if comparison == 'eq' and 'measurement' in meas_obj_keys:
                meas_obj['measurement'].append({'value.0':{'$eq':value}})

            # the "lt"/"lte" comparison can be done with any of the three measurement types
            elif comparison == 'lt':
                if 'measurement' in meas_obj_keys:
                    meas_obj['measurement'].append({'value.0':{'$lt':value}})
                if 'range' in meas_obj_keys:
                    meas_obj['range'].append({'value.1':{'$gt':value}})
                if 'limit' in meas_obj_keys:
                    meas_obj['limit'].append({'value.0':{'$gt':value}})
            elif comparison == 'lte':
                if 'measurement' in meas_obj_keys:
                    meas_obj['measurement'].append({'value.0':{'$lte':value}})
                if 'range' in meas_obj_keys:
                    meas_obj['range'].append({'value.1':{'$gte':value}})
                if 'limit' in meas_obj_keys:
                    meas_obj['limit'].append({'value.0':{'$gte':value}})

            # the "limit" type only has an upper bound, so we have to exclude it from queries that include a "eq"/"gt"/"gte" comparison
            elif comparison == 'gt':
                if 'measurement' in meas_obj_keys:
                    meas_obj['measurement'].append({'value.0':{'$gt':value}})
                if 'range' in meas_obj_keys:
                    meas_obj['range'].append({'value.0':{'$lt':value}})
            elif comparison == 'gte':
                if 'measurement' in meas_obj_keys:
                    meas_obj['measurement'].append({'value.0':{'$gte':value}})
                if 'range' in meas_obj_keys:
                    meas_obj['range'].append({'value.0':{'$lte':value}})

        return meas_obj

    def _get_meas_type_object(self, val_terms, nonval_terms):
        # certain measurement types only support certain comparison types
        val_comparisons = [ term['comparison'] for term in val_terms if term['field'] == 'value' ]
        if 'eq' in val_comparisons:
            # the "measurement" type is the only one with a single value that we can compare "eq" against
            meas_type_obj = {'measurement':[]}
        elif 'gt' in val_comparisons or 'gte' in val_comparisons:
            # the "limit" type only has an upper bound, so we have to exclude it from queries that include a "eq"/"gt"/"gte" comparison
            meas_type_obj = {'measurement':[], 'range':[]}
        else:
            # the "lt"/"lte" comparison can be done with any of the three measurement types
            meas_type_obj = {'measurement':[], 'range':[], 'limit':[]}

        # if the query specifies to search for docs with a specific measurement type, then we only want to use that one
        for term in nonval_terms:
            if term['field'] == 'type':
                meas_type_obj = {term['value']:[]}

        return meas_type_obj

    def _convert_meas_result_value_terms(self, meas_type_obj, nonval_terms, val_terms):
        converted_terms = []

        # each measurement type gets its own query term
        for meas_type in list(meas_type_obj.keys()):
            print('TYPE:',meas_type)
            print('VALS:',meas_type_obj[meas_type])
            meas_term = deepcopy(nonval_terms) # start with the query for all non-value fields
            meas_term['type'] = meas_type # add a query for the measurement type
            print('meas_term:',meas_term)

            # consolidate all value terms under the same measurement type
            for val_term in meas_type_obj[meas_type]:
            #for val_term in val_terms:
                print('val term:',val_term)
                val_term_field = list(val_term.keys())[0] # we expect field to be one of: "value.0" or "value.1"
                val_term_comp = list(val_term[val_term_field].keys())[0]

                # either add to an existing value (value.0 or value.1) field or create it 
                if val_term_field in list(meas_term.keys()):
                    meas_term[val_term_field][val_term_comp] = val_term[val_term_field][val_term_comp]
                else:
                    meas_term[val_term_field] = val_term[val_term_field]

            # add term to set of terms
            converted_terms.append({"measurement.results":{"$elemMatch":meas_term}})

        if len(converted_terms) > 1:
            converted_terms = {'$or':converted_terms}
        else:
            converted_terms = converted_terms[0]
        return converted_terms

    def _assemble_qterm_meas_results(self, terms):
        nonval_terms = {}
        nonval_raw_terms = []
        val_terms = []

        # the terms object is the list of all consolidated meas results terms in an "and"ed list of terms
        for raw_term in terms:
            field = raw_term['field']
            comparison = raw_term['comparison']
            value = raw_term['value']

            # assemble query term
            if field in ['unit', 'isotope', 'type']:
                # NOTE: there shouldn't be a case where someone specifies multiple "and"ed units, isotopes, or types in their query, but we should TODO error check for this
                term = self._assemble_qterm_str(field, comparison, value)
                nonval_terms[field] = term[field]
                nonval_raw_terms.append(raw_term)
            else:
                #term = self._assemble_qterm_num(field, comparison, value)
                val_terms.append(raw_term)
                continue

        meas_type_obj = self._get_meas_value_variations(val_terms, nonval_raw_terms)
        term = self._convert_meas_result_value_terms(meas_type_obj, nonval_terms, val_terms)

        return term

    def to_query_lang(self):
        query = {}

        # preprocess all measurement.results terms 
        terms, appends = self._consolidate_measurement_results()

        for i in range(len(terms)-1,-1,-1): # iterate backwards to keep the proper order when nesting
            print()
            ele = terms[i]
            print(i,ele)
            field = ele['field']
            comparison = ele['comparison']
            value = ele['value']

            if i < len(terms)-1:
                append_mode = self._convert_append_str_to_q_operator(appends[i])
            else:
                append_mode = None
            print(append_mode)

            # NOTE: To use a $text query in an $or expression, all clauses in the $or array must be indexed. 
            #   (https://docs.mongodb.com/manual/reference/operator/query/text/#restrictions)

            # create term in query language form
            if field == 'all':
                term = self._assemble_qterm_all(field, comparison, value)
            elif field.startswith('measurement.results'):
                term = self._assemble_qterm_meas_results(value)
            elif field in self.date_fields:
                term = self._assemble_qterm_date(field, comparison, value)
            elif field in self.str_fields:
                term = self._assemble_qterm_str(field, comparison, value)
            else:
                term = self._assemble_qterm_num(field, comparison, value)
            
            # add term to query obj
            if i == len(terms)-1:
                query = term
            else:
                query = {append_mode:[term, query]}

        return query

    def _comparison_to_human(self, comparison):
        raw_to_human = {
            "eq":"equals",
            "contains":"contains",
            "notcontains":"does not contain",
            "lt":"is less than",
            "lte":"is less than or equal to",
            "gt":"is greater than",
            "gte":"is greater than or equal to"
        }
        human = raw_to_human[comparison]
        return human
    def _value_to_human(self, field, value):
        if field == 'all':
            value = value.split()
        if type(value) is list:
            # list value has already been validated so we need not worry about non-string elements in the list
            if len(value) > 1:
                human = '["' + '", "'.join(value) + '"]' # NOTE: is this only in the field=="all" case?
            elif len(value) == 1:
                human = value[0] # if the list contains one item, make the value that item instead of a list
            else:
                human = '' # this would be the case for 'all contains ""'
        else:
            human = str(value)
        return human
    def to_human_string(self):
        query = ''
        for i, ele in enumerate(self.terms):
            field = ele['field']
            comparison = self._comparison_to_human(ele['comparison'])
            value = self._value_to_human(field, ele['value'])

            # add query term in human-readable format
            query += field + ' ' + comparison + ' ' + value

            # only append the "AND"/"OR" if there are more than 1 query terms
            # and this is not the final query term (in which cases there is no next term to append)
            if len(self.appends) > 0 and i < len(self.appends):
                query += '\n' + self.appends[i] + '\n'

        return query 

    def _validate_append_mode(self, append_type):
        msg = ''
        is_valid = True
        if append_type != '' and append_type not in self.valid_append_modes:
            msg = 'Error: append mode '+str(append_type)+' not one of: '+str(self.valid_append_modes)
            is_valid = False
        return is_valid, msg
    def _validate_field_name(self, field):
        msg = ''
        is_valid = True
        if field not in self.valid_field_names:
            msg = 'Error: field name '+str(field)+' is not a valid field name. Must be one of: '+str(self.valid_field_names)
            is_valid = False
        return is_valid, msg
    def _validate_comparison(self, field, comparison):
        msg = ''
        is_valid = True
        if field in self.str_fields and comparison not in self.str_comparisons:
            msg = 'Error: when comparing string values, the comparison operator must be one of: '+str(self.str_comparisons)
            is_valid = False
        elif field in self.num_fields and comparison not in self.num_comparisons:
            msg = 'Error: when comparing numerical values, the comparison operator must be one of: '+str(self.num_comparisons)
            is_valid = False
        elif field in self.date_fields and comparison not in self.date_comparisons:
            msg = 'Error: when comparing date values, the comparison operator must be one of: '+str(self.date_comparisons)
            is_valid = False
        return is_valid, msg
    def _validate_value(self, field, value):
        msg = ''
        is_valid = True
        if field in self.str_fields:
            #TODO: if field is measurement.results.isotope, validate that the value is a proper element symbol?
            if type(value) is list:
                for ele in value:
                    if type(ele) is not str:
                        msg = 'Error: when comparing against the '+field+' field, you must enter a string type value or list of strings. You entered a list which contains an element of type '+str(type(ele))
            elif type(value) is not str:
                msg = 'Error: when comparing against the '+field+' field, you must enter a string type value or list of strings. You entered '+str(value)+' which is type '+str(type(value))
                is_valid = False
        elif field in self.num_fields and type(value) not in [int, float]:
            msg = 'Error: when comparing against the '+field+' field, you must enter an int or float type value. You entered '+str(value)+' which is type '+str(type(value))
            is_valid = False
        elif field in self.date_fields:
            if type(value) is not str:
                msg = 'Error: when comparing against the '+field+' field, you must enter a string type value. You entered '+str(value)+' which is type '+str(type(value))
                is_valid = False
            else:
                if self._convert_str_to_date(value) is None:
                    msg = 'Error: the date value, '+value+' is not in a valid date format'
                    is_valid = False
        #else:
        #    msg = 'Error: field name '+str(field)+' is not a valid field name. Must be one of:'+str(self.valid_field_names)
        #    is_valid = False
        return is_valid, msg
    def _validate_term_against_other_terms(self, field, comparison, value):
        is_valid = True
        msg = ''
        if 'all' in self.all_fields:
            for ele in self.terms:
                if ele['field'] == 'all' and ele['value'] == '':
                    is_valid = False
                    msg = 'Error: you already have a term searching for all documents in this query; when searching for all documents, that must be the only term in the query' 
        elif field == 'all' and value == '':
            if len(self.terms) > 0:
                is_valid = False
                msg = 'Error: when searching for all documents, that must be the only term in the query'
        return is_valid, msg
    def _validate_term(self, field, comparison, value, append_type=''):
        is_valid, msg = self._validate_append_mode(append_type)
        if is_valid:
            is_valid, msg = self._validate_field_name(field)
            if is_valid:
                is_valid, msg = self._validate_comparison(field, comparison)
                if is_valid:
                    is_valid, msg = self._validate_value(field, value)
                    if is_valid:
                        is_valid, msg = self._validate_term_against_other_terms(field, comparison, value)
        #TODO validate that if someone has searched for 'all contains ""' AKA empty query, that we don't let them add to it
        return is_valid, msg


if __name__ == '__main__':
    #q_str = 'all contains '
    #q_str = 'grouping equals '
    #q_str = "all contains testing"
    #q_str = "grouping contains one\nOR\nsample.name does not contain two\nAND\nsample.description equals three"
    q_str = 'grouping contains ["copper", "Cu"]'
    q_obj = Query(query_str=q_str)
    print(q_obj.to_human_string())
    print(q_obj.to_query_lang())
    q_obj.add_query_term('measurement.description', 'contains', 'helium', "AND")
    print(q_obj.to_human_string())
    print(q_obj.to_query_lang())


'''
EQ      measurement.results.type == "measurement" and measurement.results.value.0 == VAL
LT      measurement.results.type == "measurement" and measurement.results.value.0 < VAL
LTE     measurement.results.type == "measurement" and measurement.results.value.0 <= VAL
GT      measurement.results.type == "measurement" and measurement.results.value.0 > VAL
GTE     measurement.results.type == "measurement" and measurement.results.value.0 >= VAL
CONF    -
SYM     measurement.results.type == "measurement" and measurement.results.value.1 < > <= >= == VAL
ASYM    measurement.results.type == "measurement" and measurement.results.value.2 < > <= >= == VAL

EQ      -
LT      measurement.results.type == "range" and measurement.results.value.1 > VAL
LTE     measurement.results.type == "range" and measurement.results.value.1 >= VAL
GT      measurement.results.type == "range" and measurement.results.value.0 < VAL
GTE     measurement.results.type == "range" and measurement.results.value.0 <= VAL
CONF    measurement.results.type == "range" and measurement.results.value.2 < > <= >= == VAL
SYM     -
ASYM    -

EQ      -
LT      measurement.results.type == "limit" and measurement.results.value.0 > VAL
LTE     measurement.results.type == "limit" and measurement.results.value.0 >= VAL
GT      -
GTE     -
CONF    measurement.results.type == "limit" and measurement.results.value.1 < > <= >= == VAL
SYM     -
ASYM    -
'''

'''
EQ
measurement.results.type == "measurement" and measurement.results.value.0 == VAL

LT
measurement.results.type == "measurement" and measurement.results.value.0 < VAL
or
measurement.results.type == "range" and measurement.results.value.1 > VAL
or
measurement.results.type == "limit" and measurement.results.value.0 > VAL

LTE
measurement.results.type == "measurement" and measurement.results.value.0 <= VAL
or
measurement.results.type == "range" and measurement.results.value.1 >= VAL
or
measurement.results.type == "limit" and measurement.results.value.0 >= VAL

GT
measurement.results.type == "measurement" and measurement.results.value.0 > VAL
or
measurement.results.type == "range" and measurement.results.value.0 < VAL

GTE 
measurement.results.type == "measurement" and measurement.results.value.0 >= VAL
or 
measurement.results.type == "range" and measurement.results.value.0 <= VAL
'''
