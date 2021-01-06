#!/bin/bash

#    insert_parser.add_argument('--sample_name', type=str, required=True, help='concise sample description')
#    insert_parser.add_argument('--sample_description', type=str, required=True, help='detailed sample description')
#    insert_parser.add_argument('--datasource_reference', type=str, required=True, help='where the data came from')
#    insert_parser.add_argument('--datasource_input_name', type=str, required=True, help='name of the person/people who performed data input')
#    insert_parser.add_argument('--datasource_input_contact', type=str, required=True, help='email or telephone of the person/people who performed data input')
#    insert_parser.add_argument('--datasource_input_date', nargs='*', required=True, help='list of date strings for dates of input')
#    insert_parser.add_argument('--datasource_input_notes', type=str, default='', help='input simplifications, assumptions')
#    insert_parser.add_argument('--grouping', type=str, default='', help='experiment name or similar')
#    insert_parser.add_argument('--sample_source', type=str, default='', help='where the sample came from')
#    insert_parser.add_argument('--sample_id', type=str, default='', help='identification number')
#    insert_parser.add_argument('--sample_owner_name', type=str, default='', help='name of who owns the sample')
#    insert_parser.add_argument('--sample_owner_contact', type=str, default='', help='email or telephone of who owns the sample')
#    insert_parser.add_argument('--measurement_results', nargs='*', default=[], help='list of measurements')
#    insert_parser.add_argument('--measurement_practitioner_name', type=str, default='', help='name of who did the measurement')
#    insert_parser.add_argument('--measurement_practitioner_contact', type=str, default='', help='email or telephone of who did the measurement')
#    insert_parser.add_argument('--measurement_technique', type=str, default='', help='technique name')
#    insert_parser.add_argument('--measurement_institution', type=str, default='', help='institution name')
#    insert_parser.add_argument('--measurement_date', nargs='*', default=[], help='list of date strings for dates of measurement')
#    insert_parser.add_argument('--measurement_description', type=str, default='', help='detailed description')
#    insert_parser.add_argument('--measurement_requestor_name', type=str, default='', help='name of who coordinated the measurement')
#    insert_parser.add_argument('--measurement_requestor_contact', type=str, default='', help='email or telephone of who coordinated the measurement')


# SDSMT
python python_mongo_toolkit.py insert --sample_name "" --sample_description "DUNE Ross - #6 Winze" --datasource_reference "" --datasource_input_name "" --datasource_input_contact "" --datasource_input_date "2020-06-04" --grouping "" --measurement_results '{"isotope:"U-238", "type":"measurement", "unit":"bq", "value":[50.8, 9.5]}' '{"isotope:"U-238", "type":"measurement", "unit":"ppm", "value":[4.11, 0.77]}' '{"isotope:"Ra", "type":"measurement", "unit":"Bq", "value":[99.9, 1.3]}' '{"isotope:"Th-232", "type":"measurement", "unit":"Bq", "value":[64.9, 0.5]}' '{"isotope:"Th-232", "type":"measurement", "unit":"ppm", "value":[15.95, 0.13]}' '{"isotope:"K-40", "type":"measurement", "unit":"Bq", "value":[526.3, 2.2]}' '{"isotope:"K-40", "type":"measurement", "unit":"pct", "value":[1.7, 0.007]}' --measurement_institution "SDSMT" --measurement_practitioner_name "Juergen Reichenbacher" --measurement_practitioner_contact ""

python python_mongo_toolkit.py insert --sample_name "" --sample_description "DUNE Ross - Governor's Corner" --datasource_reference "" --datasource_input_name "" --datasource_input_contact "" --datasource_input_date "2020-06-04" --grouping "" --measurement_results '{"isotope:"U-238", "type":"measurement", "unit":"bq", "value":[65.7, 18.1]}' '{"isotope:"U-238", "type":"measurement", "unit":"ppm", "value":[5.32, 1.46]}' '{"isotope:"Ra", "type":"measurement", "unit":"Bq", "value":[123.9, 2.4]}' '{"isotope:"Th-232", "type":"measurement", "unit":"Bq", "value":[27.9, 0.8]}' '{"isotope:"Th-232", "type":"measurement", "unit":"ppm", "value":[6.86, 0.2]}' '{"isotope:"K-40", "type":"measurement", "unit":"Bq", "value":[508.5, 4.4]}' '{"isotope:"K-40", "type":"measurement", "unit":"pct", "value":[1.643, 0.014]}' --measurement_institution "SDSMT" --measurement_practitioner_name "Juergen Reichenbacher" --measurement_practitioner_contact ""

python python_mongo_toolkit.py insert --sample_name "" --sample_description "DUNE Ross - Test Blast Site" --datasource_reference "" --datasource_input_name "" --datasource_input_contact "" --datasource_input_date "2020-06-04" --grouping "" --measurement_results '{"isotope:"U-238", "type":"measurement", "unit":"bq", "value":[76.8, 12.6]}' '{"isotope:"U-238", "type":"measurement", "unit":"ppm", "value":[6.22, 1.02]}' '{"isotope:"Ra", "type":"measurement", "unit":"Bq", "value":[531.3, 5.4]}' '{"isotope:"Th-232", "type":"measurement", "unit":"Bq", "value":[29.4, 0.7]}' '{"isotope:"Th-232", "type":"measurement", "unit":"ppm", "value":[7.24, 0.17]}' '{"isotope:"K-40", "type":"measurement", "unit":"Bq", "value":[402.5, 2.4]}' '{"isotope:"K-40", "type":"measurement", "unit":"pct", "value":[1.3, 0.008]}' --measurement_institution "SDSMT" --measurement_practitioner_name "Juergen Reichenbacher" --measurement_practitioner_contact ""

python python_mongo_toolkit.py insert --sample_name "" --sample_description "DUNE Ross - #4 Winze" --datasource_reference "" --datasource_input_name "" --datasource_input_contact "" --datasource_input_date "2020-06-04" --grouping "" --measurement_results '{"isotope:"U-238", "type":"measurement", "unit":"bq", "value":[148.4, 22.2]}' '{"isotope:"U-238", "type":"measurement", "unit":"ppm", "value":[12.02, 1.8]}' '{"isotope:"Ra", "type":"measurement", "unit":"Bq", "value":[266.4, 2.9]}' '{"isotope:"Th-232", "type":"measurement", "unit":"Bq", "value":[48.4, 0.9]}' '{"isotope:"Th-232", "type":"measurement", "unit":"ppm", "value":[11.9, 0.23]}' '{"isotope:"K-40", "type":"measurement", "unit":"Bq", "value":[1624.4, 6.5]}' '{"isotope:"K-40", "type":"measurement", "unit":"pct", "value":[5.247, 0.021]}' --measurement_institution "SDSMT" --measurement_practitioner_name "Juergen Reichenbacher" --measurement_practitioner_contact ""


# LANCASTER
python python_mongo_toolkit.py insert --sample_name "" --sample_description "APA Wire Assay" --datasource_reference "" --datasource_input_name "" --datasource_input_contact "" --datasource_input_date "2019-12-13" --grouping "" --measurement_results '{"isotope": "U", "type":"measurement", "unit":"mBq", "value":[3000]}' '{"isotope":"Th", "type":"measurement", "unit":"mBq", "value":[100]}' '{"isotope":"K-40", "type":"measurement", "unit":"mBq", "value":[45]}' --measurement_institution "University College London" --measurement_practitioner_name "Dave Waters" --measurement_practitioner_contact ""


### EXAMPLES ###
#python_mongo_toolkit.py insert --sample_name elise --sample_description lsfibvadk --datasource_reference beiajlkn --datasource_input_name christian --datasource_input_contact nlahen --datasource_input_date 2020-09-13

#python python_mongo_toolkit.py insert --sample_name elise --sample_description lsfibvadk --datasource_reference beiajlkn --datasource_input_name christian --datasource_input_contact nlahen --datasource_input_date 2020-09-09 2019-3-20

#python python_mongo_toolkit.py insert --sample_name elise --sample_description lsfibvadk --datasource_reference beiajlkn --datasource_input_name christian --datasource_input_contact nlahen --datasource_input_date 2020-09-09 2019-3-20 --measurement_results '{"isotope":"K", "type":"measurement", "unit":"kg", "value":[10]}' '{"isotope":"Co", "type":"range", "unit":"t", "value":[0.1, "4.0"]}'





