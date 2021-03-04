"""
.. module:: query_class
   :synopsis: The class that defines a Query object, which is used to parse specifically formatted strings into pymongo query dicts and vice versa. This class also keeps track of an existing query and can add to it.

.. moduleauthor:: Elise Saxon
"""

import os
import re
import json
import datetime
from copy import deepcopy

class Query():
    """This class enables the database toolkit to form complicated queries that will return expectable results.
    """
    def __init__(self, query_str=None):
        """The Query class can be instantiated from scratch with no existing query, or it can be instantiated with existing query text, where that query text will be loaded up and stored in this class so future query terms will be added to it.

        args:
            * query_str (str) (optional): If provided, this string will be parsed and loaded into the Query class's "terms" and "appends" lists so that future query terms can be added to it. This string MUST be in the format given by the UI's search page. That is, "<field1> <comparison1> <value1>\\n<append_mode>\\n<field2> <comparison2> <value2>\\n<append_mode>\\n..."

        :ivar terms (list of dict): The current set of query terms that this the Query object is keeping track of. As terms get added to this Query object, the field, comparison, and value get added to this list. Each dictionary element of this list should have the following structure: {"field":str, "comparison":str, "value":int/str/float/list}. 
        :ivar appends (list of str): The current set of append modes ("AND" or "OR") that combine query terms from the terms field. As query terms get added to the Query object, the append mode that adds a new term to the existing list gets added to this list. For the append mode in this list at index i, that append mode will combine the query term in the terms list at index i and the term in the terms list at index i+1. There should always be len(terms)-1 in the appends list.
        :ivar all_fields (list of str): A list of all the fields that are being compared in the terms list. This list helps keep track of which fields already exist in the query so that the terms can be combined if applicable. For example, two terms like "all contains testing" and "all contains example" can be combined into something like "all contains ['testing', 'example'].
        :ivar synonyms (list of list of str): Stores the contents of synonyms.txt as a lookup table.
        :ivar valid_append_modes (list of str): List of the valid values for append_mode variables. Valid values are "AND" and "OR".
        :ivar valid_field_names (list of str): A list of all the valid values for query fields. These are essentially all the valid fields in an assay document.
        :ivar str_fields (list of str): A list of all the field names whose values should always be of type string. This list is used in order to assemble query terms where strings are being compared.
        :ivar num_fields (list of str): A list of all the field names whose values should always be numeric types (or lists of numeric types). This list is used in order to assemble query terms where numbers are being compared. These terms will only be measurement result values, and due to the nature of the assay document format, queries of the measurement result values are complex.
        :ivar date_fields (list of str): A list of all the field names whose values should always be lists of datetime.datetime objects. This list is used in order to assemble query terms where datetime objects are being compared, as this happens differently from other queries.
        :ivar str_comparisons (list of str): A list of all the valid comparison operators that can be used to compare strings in a query.
        :ivar num_comparisons (list of str): A list of all the valid comparison operators that can be used to compare numbers in a query.
        :ivar date_comparisons (list of str): A list of all the valid comparison operators that can be used to compare dates in a query.
        """
        self.terms = []
        self.appends = []
        self.all_fields = []

        synonyms_filepath = os.path.dirname(os.path.abspath(__file__)) + '/synonyms.txt'
        self.synonyms = self._load_synonyms(synonyms_filepath)

        self.valid_append_modes = ['AND', 'OR']
        self.valid_field_names = ["all", "grouping", "sample.name", "sample.description", "sample.source", "sample.id", "sample.owner.name", "sample.owner.contact", "measurement.results.isotope", "measurement.results.type", "measurement.results.unit", "measurement.results.value", "measurement.practitioner.name", "measurement.practitioner.contact", "measurement.technique","measurement.institution", "measurement.date", "measurement.description", "measurement.requestor.name", "measurement.requestor.contact", "data_source.reference", "data_source.input.name", "data_source.input.contact", "data_source.input.date", "data_source.input.notes"]
        self.str_fields = ["all", "grouping", "sample.name", "sample.description", "sample.source", "sample.id", "sample.owner.name", "sample.owner.contact", "measurement.results.isotope", "measurement.results.type", "measurement.results.unit", "measurement.practitioner.name", "measurement.practitioner.contact", "measurement.technique","measurement.institution", "measurement.date", "measurement.description", "measurement.requestor.name", "measurement.requestor.contact", "data_source.reference", "data_source.input.name", "data_source.input.contact", "data_source.input.date", "data_source.input.notes"]
        self.num_fields = ['measurement.results.value']
        self.date_fields = ["measurement.date", "data_source.input.date"]
        self.str_comparisons = ["eq", "contains", "notcontains"]
        self.num_comparisons = ["eq", "lt", "lte", "gt", "gte"]
        self.date_comparisons = ["eq", "lt", "lte", "gt", "gte"]

        if query_str is not None and query_str != '':
            self._load_from_str(query_str)

    def _load_synonyms(self, filepath):
        """This function reads in the path to a text file where synonyms are stored and returns a list of lists of strings, which will be set to the "synonyms" class variable.

        args:
            * filepath (str): The absolute path to the file where the synonyms lists are stored. The file should be a text file where each line is a comma-separated list of strings where each string is a synonym for the others in the line.

        returns:
            * list of list of str. The list of the lists of synonyms for each word on record.
        """
        synonyms_list = []
        with open(filepath, 'r') as read_file:
            for line in read_file:
                line_elements = line.strip().split(',')
                synonyms_list.append(line_elements)
        return synonyms_list

    def _get_field_from_str(self, line):
        """This function identifies the first space in the input string that represents a human-readable query string (this space should separate the field from the comparison) and pulls all the characters from the start of the string until that first space, setting those characters to be the field in the string.

        args:
            * line (str): A query string that must be in the human-readable format: "<field1> <comparison1> <value1>"

        return:
            * str. The characters from the line variable identified to be the field.
            * str. The modified line with the characters of the field removed. This means the string now starts with the comparison operator.
        """
        end_idx = line.find(' ')
        field = line[:end_idx]
        line = line[end_idx+1:]
        return field, line
    def _get_comparison_from_str(self, line):
        """This function tries to match the beginning of the line with any of the possible human-readable comparison strings. After identifying a comparison string, that comparison is translated into a more query-friendly version and returned.

        args:
            * line (str): The modified human-readable query line that starts with the comparison operator. The line must now start with one of "is less than or equal to", "is greater than or equal to", "equals", "contains", "is less than", or "is greater than".

        returns:
            * str. The comparison operator converted into query syntax, based on the characters of the line variable that were identified to be the comparison operator string.
            * str. The modified line with the characters of the comparison (and field) removed. This means that the string now only contains the value.
        """
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
    def _get_value_from_str(self, field, line):
        """This function assumes that the contents of the line variable is just the value. It tries to convert the rest of the contents of the line into the appropriate type based on the field that it corresponds to. 

        args:
            * field (str): The field of the term that was identified from the line. This is used to decide what type of value the text of the line is. E.g. If the field is known to correspond to values that are numerical, then this function will try and convert the text of the line into a number.
            * line (str): The rest of the original line, which now should only contain the value, since the text for the field and the comparison have been removed.

        returns:
            * str or float or int. The value, in its appropriate type, that was found in the line.
        """
        if field == 'all':
            value = line.replace('["', '').replace('"]', '').split('", "')
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
        """This function orchestrates the parsing of a human-readable string into this Query object's "terms" and "appends" lists. It calls the _get_field_from_str, _get_comparison_from_str, and _get_value_from_str functions to get the field, comparison, and value variables, then passes those to the add_query_term function, which validates the variables and adds them to the Query object's "terms" and "appends" lists.

        args:
            * query (str): A human-readable string in the format "<field1> <comparison1> <value1>\\n<append_mode>\\n<field2> <comparison2> <value2>\\n<append_mode>\\n...".

        returns:
            * bool. Whether the process of parsing and loading the string was successful.
            * str. An empty string.
        """
        lines = query.split('\n')
        append_type = ''
        for line in lines:
            line = line.strip()
            if line in ['AND', 'OR']:
                append_type = line
            else:
                field, line = self._get_field_from_str(line)
                comparison, line = self._get_comparison_from_str(line)
                value = self._get_value_from_str(field, line)
                self.add_query_term(field, comparison, value, append_type, include_synonyms=False)
        #TODO: remove this return statement and its documentation.
        return True, ''

    def _find_synonyms(self, value):
        """This function iterates through the list of synonyms, searching for the specified value. If the value is found in any of the lists, the entire list in which the value was found contains all the synonyms for that value.

        args:
            * value (str): The string to find synonyms for.

        returns:
            * list of str. The list of synonyms that was found for the given value. If no synonyms were found, this function returns None.
        """
        for word_list in self.synonyms:
            for word in word_list:
                if re.match(value, word, re.IGNORECASE):
                    return word_list
        return None

    def _add_query_term_all(self, value, append_type):
        """This function adds a query term whose field is "all" to the Query object's lists of terms and appends. The "all" query term must be handled differently from other terms due to the nature of MongoDB (the "all" search is enabled by the use of $text indices in the MongoDB collections, so any questions can be answered by looking at the MongoDB $text index documentation). There can only be one "all" comparison in an entire query, so if the user tries to enter multiple terms whose field is "all", the values for each of those terms will be combined into one list and be searched for in one term. The comparison for the "all" field is always "contains" (again, due to the nature of the MongoDB $text index). Since there can only be one "all" term in a given query, the append mode that is used on the general "all" term in the final query is the append mode that was passed for the first "all" term.

        args:
            * value (str or list): The value or values of the query term. If "value" is a list, it is converted into a space-separated string (this will only happen if the field is "all").
            * append_type (str): Must be one of "AND" or "OR". This value is the append type for the given term. This is only used for the first "all" term of the query.
        """
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
        """This function adds a query term to the Query object's lists of terms and appends (unless the field is "all", in which case the _add_query_term_all function will handle it). A term dictionary is created from the field, comparison, and value, and it is added to the Query object's list of terms. The append_type is added to the Query object's list of appends.

        args: 
            * field (str): The field whose value will be compared in the query term.
            * comparison (str): The comparison operator that will be used to compare field values against the provided value.
            * value (str or int or float): The value that will be compared against.
            * append_type (str): Must be one of "AND" or "OR". This is the append type for the given term. It will be the conjunction between the last-added query term and this (about to be added) query term.
        """
        term = {"field":field, "comparison":comparison, "value":value}
        self.terms.append(term)
        if append_type != '':
            self.appends.append(append_type)
        self.all_fields.append(field)
    def add_query_term(self, field, comparison, value, append_type='', include_synonyms=True):
        """This is the main function that orchestrates adding a query term to the Query object's lists of terms and appends. This function first validates the arguments, then gathers the specified value's synonyms if include_synonyms is True, then adds the new query term and append mode to the terms and appends lists based on whether the field is "all" or not. The _add_query_term_all function documentation describes more on why the "all" terms must be handled separately.

        args:
            * field (str): The field whose value to compare.
            * comparison (str): The comparison to use to compare the field's value against the specified value.
            * value (str or int or float): The value to compare against.
            * append_type (str): The append mode to use for this query term. Must be one of "AND" or "OR" or "". If append_type is an empty string, this is the first/only term in the Query object.
            * include_synonyms (bool): Whether or not to include the value's synonyms in the query term or to only search for the value itself.
        """
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
        """This function intakes a string, tries to convert it into a datetime object, and returns that datetime object.

        args:
            * date_str (str): The string that will be converted into a datetime object.

        returns:
            * datetime.datetime. The datetime object that resulted from the string. If the string could not be converted into a datetime object, then this returns None.
        """
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
        """This function intakes a list of strings, tries to convert each one into a datetime object, and returns the list of datetime objects.

        args:
            * str_list (lit of str): The list of strings that will be converted into datetime objects.

        returns:
            * list of datetime.datetime. The list of datetime objects that each resulted from their corresponding strings. If any of the strings cannot be converted into datetime objects, then this function returns None.
        """
        date_objects = []
        for date_str in str_list:
            date_obj = convert_str_to_date(date_str)
            if date_obj is None:
                return None
            else:
                date_objects.append(date_objects)
        return date_objects

    def _assemble_qterm_all(self, field, comparison, value):
        """This function creates a pymongo query language dictionary out of a given field, comparison, and value where the field is "all".

        args:
            * field (str): The field to query for
            * comparison (str): The comparison operator to use to compare the field's value against the specified value.
            * value (str): The value to compare against.

        returns:
            * dict. The query term in pymongo query language.
        """
        # douple quotes around value indicate that it is a phrase and each word should not be searched for separately
        # space-separated words in string are searched for separately
        if value == '':
            term = {}
        else:
            term = {"$text":{"$search":value}}
        return term
    def _assemble_qterm_date(self, field, comparison, value):
        """This function creates a pymongo query language dictionary out of a given field, comparison, and value where the field is one of the date fields, meaning that term does a date comparison. To do date comparison, the string date value must be converted into a datetime.datetime object (all dates in the database are datetime.datetime objects).

        args:
            * field (str): The field to query for
            * comparison (str): The comparison operator to use to compare the field's value against the specified value.
            * value (str): The value to compare against.

        returns:
            * dict. The query term in pymongo query language.
        """
        #TODO: implement date comparison taking second value into account (aka range)
        field += '.0' # only look at first date
        
        # comparison values in raw form are already in pymongo form, except the leading "$"
        comparison = '$' + comparison
        
        # the date value has already been validated so we need not worry about improper formatting
        search_val = self._convert_str_to_date(value)

        term = {field:{comparison:search_val}}
        return term
    def _assemble_qterm_str(self, field, comparison, value):
        """This function creates a pymongo query language dictionary out of a given field, comparison, and value where the field is one of the string fields, meaning that term does a string comparison. To do string comparisons, the Query class uses pre-compiled regex statements. The comparison operator dictates how the regex statement is formed. For example, if the comparison is "contains", then the regex pattern would have the value surrounded by ".*" to indicate that any characters can come before or after the value, so long as the value is in there.

        args:
            * field (str): The field to query for
            * comparison (str): The comparison operator to use to compare the field's value against the specified value.
            * value (str or list): The value(s) to compare against.

        returns:
            * dict. The query term in pymongo query language.
        """
        def _create_contains_regex(token):
            return re.compile('^.*'+token+'.*$', re.IGNORECASE)
        def _create_equals_regex(token):
            return re.compile('^'+token+'$', re.IGNORECASE)
        def _create_regex(token, comparison):
            if comparison == 'contains':
                #search_val  = _create_contains_regex(token)
                search_val = {"$regex":_create_contains_regex(token)}
            elif comparison == 'notcontains':
                search_val = {'$not':_create_equals_regex(token)}
            else: #equals
                #search_val = _create_equals_regex(token)
                search_val = {"$regex":_create_equals_regex(token)}
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
        """This function assembles a pymongo query language dictionary out of a given field, comparison, and value where the field is a numeric field, meaning that term does a number comparison.

        args:
            * field (str): The field to query for
            * comparison (str): The comparison operator to use to compare the field's value against the specified value.
            * value (str): The value to compare against.

        returns:
            * dict. The query term in pymongo query language.
        """
        # comparison values in raw form are already in pymongo form, except the leading "$"
        comparison = '$' + comparison
        return {field:{comparison:value}}

    def _convert_append_str_to_q_operator(self, append_str):
        """Converts a human-readable append mode string into its pymongo query language counterpart.

        args:
            * append_str (str): The human-readable string that corresponds to the append mode. Must be one of "AND" or "OR".

        returns:
            * str. The append mode in pymongo query language.
        """
        if append_str == 'AND':
            operator = '$and'
        else:
            operator = '$or'
        return operator

    def _consolidate_measurement_results(self):
        """Measurement result objects are elements in a list. To search for one element of a list that satisfies multiple criteria, MongoDB provides an `$elemMatch operator <https://docs.mongodb.com/manual/tutorial/query-arrays/#query-for-an-array-element-that-meets-multiple-criteria>`_. To use $elemMatch, all the criteria (terms) must be combined into one query term under $elemMatch. To do this, this function separates the list of terms into sections where each term in the section is appended with "AND" and each section is appended to to the next section with "OR" (splitting the list on "OR"s). All the terms in a section that query a measurement results field get combined into one element that will eventually be queried with $elemMatch. Once the terms list copy is separated into sections, the measurement results query terms are identified and combined into one term. The combined term should have the following format: {"field":"measurement.results", "comparison":None, "value":[{"field":<one of isotope, type, unit, value>, "comparison":<the original comparison for this term>, "value":<the original value for this term>}, ...]}

        returns:
            * list of dict. A possibly modified copy of the terms list after consolidating all query terms that deal with measurement results.
            * list of str. A possibly modified copy of the appends list after consolidating all query terms that compare measurement results.
        """
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

    def _get_valid_meas_types(self, meas_val_terms, specified_meas_type):
        """There are three different "type"s of measurements that a measurement result object could have: "measurement", "range", and "limit". The type of the measurement dictates what the numbers in the "value" field represent. If the type is "measurement" there should be two or three values: [central value, symmetric error] or [central value, positive asymmetric error, negative asymmetric error]. If the type is "range" there should be tow or three values: [lower limit, upper limit] or [lower limit, upper limit, confidence level]. If the type is "limit" there should be one to two values: [upper limit] or [upper limit, confidence level]. This means that if a user searched for a measurement result where the value equals x, no results of type "range" or "limit" should be returned because measurement results with these types contain values that are limits, not exact values. Thus, this function uses the comparison types of the value terms to determine how to constrain the "type" field in order to only return accurate results.

        args:
            * meas_val_terms (list of dict): The list of terms, for a given group of consolidated measurement results terms, where the field is "value". 
            * specified_meas_type (str): The value specified for "type" if given in one of the terms in the group of consolidated measurement results terms (must be one of "measurement", "range", "limit", or None).

        returns:
            * list of str. The list of all "type" values that can be queried for.
        """
        if specified_meas_type is not None:
            # if the query specifies to search for docs with a specific measurement type, then we only want to use that one
            valid_meas_types = [specified_meas_type]
        else:
            # certain measurement types only support certain comparison types
            val_comparisons = [ term['comparison'] for term in meas_val_terms if term['field'] == 'value' ]

            if 'eq' in val_comparisons:
                # the "measurement" type is the only one with a single value that we can compare "eq" against
                valid_meas_types = ['measurement']

            elif 'gt' in val_comparisons or 'gte' in val_comparisons:
                # the "limit" type only has an upper bound, so we have to exclude it from queries that include a "eq"/"gt"/"gte" comparison
                valid_meas_types = ['measurement', 'range']

            elif 'lt' in val_comparisons or 'lte' in val_comparisons:
                # the "lt"/"lte" comparison can be done with any of the three measurement types
                valid_meas_types = ['measurement', 'range', 'limit']

            else:
                valid_meas_types = []

        return valid_meas_types

    def _get_meas_value_variations(self, valid_meas_types, val_terms):
        """The type of value (e.g. central value, upper limit, confidence, etc.) in the measurement value list for each measurement results object for a document in the database depends on the measurement type ("measurement", "limit", "range") for the corresponding measurement results object ("measurement", "limit", "range"). For example, if one of the measurement results objects for a document has a "value" of [1, 2], then 1 is the upper limit and 2 is the confidence if the "type" of the measurement results object is "limit". But if the "type" is "measurement", then 1 is the central value and 2 is the symmetric error. Thus, we must assemble sub-terms for the query where the measurement type is specified along with the corresponding value comparison. This function facilitates the assembly of sub-terms for each measurement type, and the corresponding value comparisons for each of those measurement type terms.

        args:
            * valid_meas_types (list of str): The list of measurement types that were determined to be applicable to this query, given the measurement value comparisons and whether the user specified one measurement type.
            * val_terms (list of dict): A list of individual terms that each query for a measurement result object's value.

        returns:
            * list of dict. One pymongo query for each of the valid measurement types. Each query queries for the value and the measurement type.
        """
        # add terms to the meas_obj according to their appropriate measurement type
        def _gather_value_variations(meas_obj, term):
            """This function creates a pymongo query dict for each of the valid measurement types, where the type and the comparison dictate which index of the "value" array should be compared.

            args:
                * meas_obj (dict): The object that will be filled with pymongo query dicts for each measurement type. The top-level fields of this dict are each of the valid measurement types for this group of value terms.
                * term (dict): An individual term that queries for a measurement result object's value.

            returns:
                * dict. The meas_obj that was passed in, now containing lists of pymongo query dicts for each of the valid measurement types.
            """
            comparison = term['comparison']
            value = term['value']

            # the "measurement" type is the only one with a single value that we can compare "eq" against
            if comparison == 'eq' and 'measurement' in valid_meas_types:
                meas_obj['measurement'].append({'value.0':{'$eq':value}})

            # the "lt"/"lte" comparison can be done with any of the three measurement types
            elif comparison == 'lt':
                if 'measurement' in valid_meas_types:
                    meas_obj['measurement'].append({'value.0':{'$lt':value}}) # value 0 is the central value
                if 'range' in valid_meas_types:
                    meas_obj['range'].append({'value.1':{'$lt':value}}) # value 1 is the upper bound
                if 'limit' in valid_meas_types:
                    meas_obj['limit'].append({'value.0':{'$lt':value}}) # value 0 is the upper bound
            elif comparison == 'lte':
                if 'measurement' in valid_meas_types:
                    meas_obj['measurement'].append({'value.0':{'$lte':value}})
                if 'range' in valid_meas_types:
                    meas_obj['range'].append({'value.1':{'$lte':value}})
                if 'limit' in valid_meas_types:
                    meas_obj['limit'].append({'value.0':{'$lte':value}})

            # the "limit" type only has an upper bound, so we have to exclude it from queries that include a "eq"/"gt"/"gte" comparison
            elif comparison == 'gt':
                if 'measurement' in valid_meas_types:
                    meas_obj['measurement'].append({'value.0':{'$gt':value}})
                if 'range' in valid_meas_types:
                    meas_obj['range'].append({'value.0':{'$gt':value}}) # value 0 is the lower bound
            elif comparison == 'gte':
                if 'measurement' in valid_meas_types:
                    meas_obj['measurement'].append({'value.0':{'$gte':value}})
                if 'range' in valid_meas_types:
                    meas_obj['range'].append({'value.0':{'$gte':value}})

            return meas_obj

        # convert the variations into actual mongodb query language format
        def _aggregate_value_variations(meas_obj):
            """This function converts the lists of queries for each of the valid measurement types into one valid pymongo query. For each measurement type in the list of valid measurement types, it creates a pymongo query that searches for the given measurement type. It then iterates over the list of query dicts for each of the measurement types and adds those query dicts to the term that queries for the measurement type. In this way, there is one query term for each of the valid measurement types which contains a query for the measurement type and the corresponding values.

            args:
                * meas_obj (dict): Each field is one of the valid measurement types and the values for each field are the pymongo query dicts that query for value.

            returns:
                * list of dict. One pymongo query for each of the valid measurement types. Each query queries for the value and the measurement type.
            """
            aggregated_terms = []
            for meas_type in list(meas_obj.keys()):
                term = self._assemble_qterm_str('type', 'equals', meas_type) # this func will return a dictionary we can add fields and their comparisons/values to

                for val_ele in meas_obj[meas_type]:
                    val_field = list(val_ele.keys())[0] # we expect field to be one of: "value.0" or "value.1"
                    val_comp = list(val_ele[val_field].keys())[0] # we expect the first sub-field to be the comparison operator
                    val_val = val_ele[val_field][val_comp] # we expect the sub-sub field to be the number to compare against

                    # add value query to measurement type query
                    if val_field in list(term.keys()):
                        term[val_field][val_comp] = val_val
                    else:
                        term[val_field] = val_ele[val_field]
                aggregated_terms.append(term)

            return aggregated_terms

        # create a dict where the keys are the valid measurement types found in _get_valid_meas_types
        meas_obj = { meas_type:[] for meas_type in valid_meas_types }

        # fill meas_obj dict with lists of pymongo query dicts for each valid type
        for val_term in val_terms:
            meas_obj = _gather_value_variations(meas_obj, val_term)

        # combine 
        aggregated_terms = _aggregate_value_variations(meas_obj)
        return aggregated_terms

    def _assemble_meas_result_terms(self, val_terms, isotope_terms, unit_term):
        """This function combines all the separately assembled sub-terms for this measurement result query term. Each sub-term is a valid pymongo query dictionary on its own, so all the dictionaries are combined together to be used in the final query.

        args:
            * val_terms (list of dict): A list of valid pymongo queries for the value and the measurement type.
            * isotope_terms (dict): A valid pymongo query that queries for the measurement isotope.
            * unit_term (dict): A valid pymongo query that queries for the measurement unit.

        returns:
            * dict or list of dict. A valid pymongo query which is the result of combining the sub-terms which specify the isotope, unit, and values to search for.
        """
        combined_terms = []
        if len(val_terms) > 0 and len(isotope_terms) > 0:
            for val_term in val_terms:
                for isotope_term in isotope_terms:
                    combined_terms.append({**val_term, **isotope_term, **unit_term})
        elif len(isotope_terms) > 0:
            for isotope_term in isotope_terms:
                combined_terms.append({**isotope_term, **unit_term})
        elif len(val_terms) > 0:
            for val_term in val_terms:
                combined_terms.append({**val_term, **unit_term})
        else:
            combined_terms = [unit_term]
        
        combined_terms = [{"measurement.results":{"$elemMatch":term}} for term in combined_terms]

        if len(combined_terms) > 1:
            combined_terms = {'$or':combined_terms}
        else:
            combined_terms = combined_terms[0]
        return combined_terms

    def _assemble_qterm_meas_results(self, terms):
        """This function orchestrates the conversion of one consolidated group of measurement results query terms into a valid pymongo query. It iterates over the each term in the consolidated group and consolidates them based on the field they compare. This is because, in MongoDB, if multiple query terms compare the same field, they can be consolidated into one sub-term within the $elemMatch operator. This function assumes a user may specify multiple terms comparing a measurement result object's value. It also assumes that only one measurement type, isotope, and unit is specified. 

This function assumes a user may specify multiple terms comparing a measurement result object's value and that only one measurement type, isotope, and unit are specified. It iterates over each term in the terms list and consolidates terms whose field is "value". If a term queries on the "unit" field, that term is converted into a valid pymongo query. If a term queries on the "isotope" field, that term is converted into a valid pymongo query. If a term queries on the "type" field, the value is stored as specified_measurement_type (which will be used when assembling the query for the "values" field). Once all the terms have been handled and sorted, the value terms are converted into 

        args:
            * terms (list of dict): The list of consolidated measurement.results query terms which will be further-consolidated into one MongoDB query term.

        returns:
            * dict. The fully-consolidated query term in MongoDB query format.
        """
        val_terms_raw = []
        isotope_terms = []
        unit_term = {}
        specified_measurement_type = None

        # the terms object is the list of all consolidated meas results terms in an "and"ed list of terms
        for raw_term in terms:
            field = raw_term['field']
            comparison = raw_term['comparison']
            value = raw_term['value']

            # assemble query term
            if field == 'value':
                val_terms_raw.append(raw_term)
            elif field == 'type':
                # we expect at most one term specifying a measurement type
                # "value" should be one of "measurement", "limit", or "range"
                specified_measurement_type = value
            elif field == 'isotope':
                # we expect at most one term specifying an isotope symbol
                # "value" should be an isotope symbol, e.g. "K-40"
                isotope_terms = self._assemble_qterm_str(field, comparison, value)
                term_keys = list(isotope_terms.keys())
                if len(term_keys) == 1 and term_keys[0] in ['$and', '$or']:
                    # term would start with "$and" or "$or" if the value is a list of terms (e.g. synonyms: ['K-40', "potassium'])
                    # we want the list of terms that are being "and"ed or "or"ed together, e.g. {'$or': [{'isotope':{'$eq':'K-40'}}, {'isotope':{'$eq':'potassium'}}]}
                    isotope_terms = isotope_terms.pop(term_keys[0])
                else:
                    # in _assemble_meas_result_terms, the isotope_terms field is expected to be a list, so we convert this into a one-element list, e.g. {'isotope':{'$eq':'K-40'}} ==> [{'isotope':{'$eq':'K-40'}}]
                    isotope_terms = [isotope_terms]
            elif field == 'unit':
                # we expect at most one term specifying a measurement unit
                # "value" should be a measurement unit, e.g. "g" or "ppm"
                unit_term = self._assemble_qterm_str(field, comparison, value)
            else:
                print("field wasn't in [value, type, isotope, unit]")
                terms = None

        valid_meas_types = self._get_valid_meas_types(val_terms_raw, specified_measurement_type)
        val_terms = self._get_meas_value_variations(valid_meas_types, val_terms_raw)
        term = self._assemble_meas_result_terms(val_terms, isotope_terms, unit_term)
        return term

    def to_query_language(self):
        """This function converts the terms and appends lists into a valid pymongo query. It starts by consolidating the query terms that deal with measurement results dicts (for a description of why we do this, see the documentation for _consolidate_measurement_results). The order of the terms and appends lists matter when assembling the final query, since the Query class creates the query in the order in which the terms were added. For each query term (where some terms are now consolidated), the field, comparison, and value are converted into a valid pymongo query based on the type of the query ("all", measurement results, date comparison, string comparison, number comparison). Then the query created for the given term is added, using the corresponding append mode, to the main query.

        returns:
            * dict. The query dict in pymongo query language.
        """
        query = {}

        # preprocess all measurement.results terms 
        terms, appends = self._consolidate_measurement_results()

        for i in range(len(terms)-1,-1,-1): # iterate backwards to keep the proper order when nesting
            ele = terms[i]
            field = ele['field']
            comparison = ele['comparison']
            value = ele['value']

            if i < len(terms)-1:
                append_mode = self._convert_append_str_to_q_operator(appends[i])
            else:
                append_mode = None

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
        """Converts the query term comparison operator from internal Query class format to human-readable format. This uses a dictionary as a lookup table, where the keys are comparison operators in internal Query class format, and the values are the corresponding comparison operators in human-readable format.

        args:
            * comparison (str): The comparison operator for this query term.

        returns:
            str. The human-readable version of the query operator for this query term.
        """
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
        """Converts a query term value to a human-readable string. All query term values whose query term field is not "all" are simply cast to a string type and returned. Query term values where the query term field is "all" are split on whitespaces, where each individual element is treated as one value. Due to the nature of the MongoDB $text query, we can only have one $text term per query and the value of the $text term must be one string where each space-separated token is searched for on its own. We cannot search for more than one multi-token phrases in one $text query. This should not affect most queries, as we anticipate that much of the querying people will be doing will be quite simple.

        args:
            * field (str): The field name for this query term.
            * value (str or float): The value for this query term.

        returns:
            * str. The stringified value for this query term.
        """
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
    def to_string(self):
        """This function converts the query terms and appends lists into a human-readable string and returns it. It does this by iterating over the query terms and append modes, converts the fields, comparisons, and values into human-readable strings, and appends them to a cumulative query string.

        returns:
            * str. The query in human-readable format.
        """
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

    #'''
    def _validate_append_mode(self, append_type):
        msg = ''
        is_valid = True
        if append_type != '' and append_type not in self.valid_append_modes:
            msg = 'Error: append mode '+str(append_type)+' not one of: '+str(self.valid_append_modes)
            is_valid = False
        return is_valid, msg
    '''
    '''
    def _validate_field_name(self, field):
        msg = ''
        is_valid = True
        if field not in self.valid_field_names:
            msg = 'Error: field name '+str(field)+' is not a valid field name. Must be one of: '+str(self.valid_field_names)
            is_valid = False
        return is_valid, msg
    '''
    '''
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
    '''
    '''
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
    #'''
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
    #'''

if __name__ == '__main__':
    #q_str = 'all contains '
    #q_str = 'grouping equals '
    #q_str = "all contains testing"
    #q_str = "grouping contains one\nOR\nsample.name does not contain two\nAND\nsample.description equals three"
    q_str = 'grouping contains ["copper", "Cu"]'
    q_obj = Query(query_str=q_str)
    print(q_obj.to_string())
    print(q_obj.to_query_language())
    q_obj.add_query_term('measurement.description', 'contains', 'helium', "AND")
    print(q_obj.to_string())
    print(q_obj.to_query_language())




