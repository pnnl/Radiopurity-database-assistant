from datetime import datetime
import json
import jsonschema
from jsonschema import validate, ValidationError

class DuneValidator:
    def __init__(self, schema_type, datetime_str=False):
        if schema_type == 'measurement_result':
            self.schema = self._load_meas_result_schema()
        elif schema_type == 'measurement':
            self.schema = self._load_meas_schema()
        elif schema_type == 'sample':
            self.schema = self._load_sample_schema()
        elif schema_type == 'data_source':
            self.schema = self._load_datasource_schema()
        else:
            self.schema = self._load_record_schema()
        
        if datetime_str:
            self.validator = self._init_validator_datetime_str()
        else:
            self.validator = self._init_validator_datetime_obj()

    def _init_validator_datetime_str(self):
        BaseVal = jsonschema.Draft7Validator 
        def _is_datetime_str(checker, val):
            valid = False
            date_formats = ["%Y-%m-%d", "%Y/%m/%d", "%m-%d-%Y", "%m/%d/%Y", "%Y-%d-%m", "%Y/%d/%m", "%d-%m-%Y", "%d/%m/%Y"]
            for date_format in date_formats:
                try:
                    new_date_obj = datetime.strptime(val, date_format)
                    valid = True
                    break
                except:
                    pass
            return valid
        date_check = BaseVal.TYPE_CHECKER.redefine('datetime', _is_datetime_str)
        Validator = jsonschema.validators.extend(BaseVal, type_checker=date_check)
        return Validator

    def _init_validator_datetime_obj(self):
        BaseVal = jsonschema.Draft7Validator 
        def _is_datetime(checker, val):
            return isinstance(val, datetime)
        date_check = BaseVal.TYPE_CHECKER.redefine('datetime', _is_datetime)
        Validator = jsonschema.validators.extend(BaseVal, type_checker=date_check)
        return Validator

    def _load_meas_result_schema(self):
        valid_isotopes = open('isotopes.csv', 'r').read().strip().split(',')
        valid_units = open('units.csv', 'r').read().strip().split(',')
        measurement_result_schema = {
            "type": "object",
            "additionalProperties": False,
            "required": ["isotope", "type", "unit", "value"],
            "properties": {
                "isotope": {"type":"string", "enum":valid_isotopes},
                "type": {"type":"string", "enum":["measurement", "limit", "range"]},
                "unit": {"type":"string", "enum":valid_units},
                "value": {"type":"array", "maxItems": 3, "items":{"type":"number"}}
            }
        }
        return measurement_result_schema

    def _load_meas_schema(self):
        measurement_result_schema = self._load_meas_result_schema()
        measurement_schema = {
            "type": "object",
            "additionalProperties": False,
            "required": ["results", "practitioner", "technique", "institution", "date", "description", "requestor"],
            "properties": {
                "results": {"type":"array", "items":{"$ref":"#/definitions/measurement_value"}},
                "practitioner": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["name", "contact"],
                    "properties": {
                        "name": {"type":"string", "default":""},
                        "contact": {"type":"string", "default":""},
                    }
                },
                "technique": {"type":"string", "default":""},
                "institution": {"type":"string", "default":""},
                "date": {"type":"array", "maxItems": 2,  "items":{"type":"datetime"}},
                "description": {"type":"string", "default":""},
                "requestor": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["name", "contact"], 
                    "properties": {
                        "name": {"type":"string", "default":""},
                        "contact": {"type":"string", "default":""},
                    }
                }
            },
            "definitions": {
                "measurement_value": measurement_result_schema
            }
        }
        return measurement_schema

    def _load_sample_schema(self):
        sample_schema = {
            "type": "object",
            "additionalProperties": False,
            "required": ["name", "description", "source", "id"],
            "properties": {
                "name": {"type":"string", "default":""},
                "description": {"type":"string", "default":""},
                "source": {"type":"string", "default":""},
                "id": {"type":"string", "default":""},
                "owner": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["name", "contact"],
                    "properties": {
                        "name": {"type":"string", "default":""},
                        "contact": {"type":"string", "default":""},
                    }
                }
            }
        }
        return sample_schema

    def _load_datasource_schema(self):
        datasource_schema = {
            "type": "object",
            "additionalProperties": False,
            "required": ["reference", "input"],
            "properties": {
                "reference": {"type":"string", "default":""},
                "input": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["name", "contact", "date", "notes"],
                    "properties": {
                        "name": {"type":"string", "default":""},
                        "contact": {"type":"string", "default":""},
                        "date": {"type":"array", "maxItems": 2, "items":{"type":"datetime"}},
                        "notes": {"type":"string", "default":""},
                    }
                }
            }
        }
        return datasource_schema

    def _load_record_schema(self):
        sample_schema = self._load_sample_schema()
        datasource_schema = self._load_datasource_schema()
        measurement_result_schema = self._load_meas_result_schema()
        record_schema = {
            "type": "object",
            "additionalProperties": False,
            "required": ["type", "grouping", "sample", "data_source", "measurement"],
            "properties": {
                "_parent_id":{"type":"string"}, 
                "specification":{"type":"string"}, 
                "_version":{"type":"integer"},
                "type": {"type":"string", "default":"assay"},
                "grouping": {"type":"string", "default":""},
                "sample": sample_schema,
                "data_source": datasource_schema,
                "measurement": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["results", "practitioner", "technique", "institution", "date", "description", "requestor"],
                    "properties": {
                        "results": {"type":"array", "items":{"$ref":"#/definitions/measurement_value"}},
                        "practitioner": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["name", "contact"],
                            "properties": {
                                "name": {"type":"string", "default":""},
                                "contact": {"type":"string", "default":""},
                            }
                        },
                        "technique": {"type":"string", "default":""},
                        "institution": {"type":"string", "default":""},
                        "date": {"type":"array", "maxItems": 2,  "items":{"type":"datetime"}},
                        "description": {"type":"string", "default":""},
                        "requestor": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["name", "contact"],
                            "properties": {
                                "name": {"type":"string", "default":""},
                                "contact": {"type":"string", "default":""},
                            }
                        }
                    }
                }
            },
            "definitions": {
                "measurement_value": measurement_result_schema
            }
        }
        return record_schema

    def validate(self, data):
        error_msg = ''
        try:
            resp = self.validator(schema=self.schema).validate(data)
            success = True
        except ValidationError as e:
            success = False
            error_msg = e.message + ' in field: ' + '.'.join([ str(ele) for ele in list(e.absolute_path) ])
        return success, error_msg

def validate_meas_remove_indices(existing_doc, remove_indices):
    valid_str_comparisons = ["contains", "notcontains", "eq"]
    valid_num_comparisons = ["eq", "lt", "lte", "gt", "gte"]
    valid_appendmodes = ["AND", "OR"]

    valid_indices = True
    error_msg = ''
    for rm_idx in remove_indices:
        if rm_idx < 0 or rm_idx >= len(existing_doc['measurement']['results']):
            error_msg = 'you entered an invalid measurement removal of '+str(rm_idx)+' and valid indices must be between 0 and '+str(len(existing_doc['measurement']['results']))
            valid_indices = False
    return valid_indices, error_msg

def _validate_field_name(field):
    is_valid = True
    error_msg = ''
    valid_fields = ["grouping", "sample.name", "sample.description", "sample.source", "sample.id", "sample.owner.name", "sample.owner.contact", "measurement.results.isotope", "measurement.results.type", "measurement.results.unit", "measurement.results.value", "measurement.practitioner.name", "measurement.practitioner.contact", "measurement.technique","measurement.institution", "measurement.date", "measurement.description", "measurement.requestor.name", "measurement.requestor.contact", "data_source.reference", "data_source.input.name", "data_source.input.contact", "data_source.input.date", "data_source.input.notes"]
    if field not in valid_fields:
        error_msg = 'the "field" argument must be one of: '+', '.join(valid_fields)+' and you entered: '+field
        is_valid = False
    return is_valid, error_msg

def _validate_query_appendmode(append_mode):
    is_valid = True
    error_msg = ''
    if append_mode.upper() not in ['AND', 'OR']:
        is_valid = False
        error_msg = 'the "append_mode" argument must be one of: AND, OR and you entered: '+append_mode.upper()
    return is_valid, error_msg

def _validate_query_numeric_comparison(value, comparison):
    if type(value) in [int, float] and comparison in ["eq", "lt", "lte", "gt", "gte"]:
        is_valid = True
        error_msg = ''
    else:
        print("VAL TYPE:",type(value),'COMP:',comparison)
        is_valid = False
        error_msg = 'when comparing numeric values, the comparison operator must be one of: "eq", "lt", "lte", "gt", "gte" and the value must be a number'
    return is_valid, error_msg

def _validate_query_date_comparison(value, comparison):
    if type(value) == str and comparison in ["eq", "lt", "lte", "gt", "gte"]:
        is_valid = True
        error_msg = ''
    else:
        is_valid = False
        error_msg = 'when comparing date values, the comparison operator must be one of: "eq", "lt", "lte", "gt", "gte" and the value must be a string'
    return is_valid, error_msg

def _validate_query_str_comparison(value, comparison):
    if type(value) == str and comparison in ["eq", "contains", "notcontains"]:
        is_valid = True
        error_msg = ''
    else:
        is_valid = False
        error_msg = 'when comparing string values, the comparison operator must be one of: "eq", "contains", "notcontains" and the value must be a string'
    return is_valid, error_msg

def _validate_query_all_field(existing_q):
    print('existing q:',existing_q)
    existing_q_str = str(existing_q)
    if '$text' in existing_q_str:
        is_valid = False
        error_msg = 'the "all" field can only be specified once in a query; this is due to a MongoDB constraint'
    else:
        is_valid = True
        error_msg = ''
    return is_valid, error_msg

def validate_query_terms(field, comparison, value, append_mode, existing_q):
    if field in ["measurement.results.value"]:
        is_valid, msg = _validate_query_numeric_comparison(value, comparison)
    elif field in ["measurement.date", "data_source.input.date"]:
        is_valid, msg = _validate_query_date_comparison(value, comparison)
    else:
        is_valid, msg = _validate_query_str_comparison(value, comparison)

    if field == 'all':
        is_valid, msg = _validate_query_all_field(existing_q)
    
    if is_valid:
        is_valid, msg = _validate_query_appendmode(append_mode)

    return is_valid, msg


