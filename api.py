from flask import Flask, request, render_template
from python_mongo_toolkit import search, add_to_query, insert, search_by_id, update
import pprint

app = Flask(__name__)

@app.route('/search', methods=['GET','POST'])
def search_endpoint():
    if request.form.get("append_button") == "do_and":
        existing_q_str, num_q_lines, final_q_lines_list, results = do_q_append(request.form, "AND")
        results_str = [ str(r) for r in results ]

    elif request.form.get("append_button") == "do_or":
        existing_q_str, num_q_lines, final_q_lines_list, results = do_q_append(request.form, "OR")
        results_str = [ str(r) for r in results ]

    elif request.method == "POST":
        final_q_str = parse_existing_q(request.form)
        final_q_lines_list = []
        if final_q_str != '':
            final_q_lines_list = final_q_str.split('\n')
        results = perform_search(final_q_lines_list)
        results_str = [ str(r) for r in results ]
        #results = [ pprint.pformat(r).split('\n') for r in results ]
        existing_q_str = ''
        num_q_lines = 0

    else:
        existing_q_str = ''
        num_q_lines = 0
        final_q_lines_list = []
        results = []
        results_str = []

    return render_template('search.html', existing_query=existing_q_str, num_q_lines=num_q_lines, final_q=final_q_lines_list, results_str=results_str, results_dict=results)

@app.route('/insert', methods=['GET','POST'])
def insert_endpoint():
    if request.method == "POST":
        new_doc_id = perform_insert(request.form)
        if new_doc_id is None:
            new_doc_id = "ERROR: record not inserted because of an incorrect formatting issue"
    else:
        new_doc_id = ""
    return render_template('insert.html', new_doc_id=new_doc_id)

#TODO: create insert front-end
@app.route('/update', methods=['GET','POST'])
def update_endpoint():
    if request.method == "GET":
        return render_template('update.html', doc_data=False, message="")

    elif request.form.get("submit_button") == "find_doc":
        doc_id = request.form.get('doc_id', '')
        doc = search_by_id(doc_id)
        print('DOC:::',doc)

        if doc is None:
            return render_template('update.html', doc_data=False, message="No document was found with the ID you provided.")
        
        for i in range(len(doc['measurement']['results'])):
            num_vals = len(doc['measurement']['results'][i]['value'])
            if num_vals == 0:
                doc['measurement']['results'][i]['value'] = []
            if num_vals < 2:
                doc['measurement']['results'][i]['value'].append('')
            if num_vals < 3:
                doc['measurement']['results'][i]['value'].append('')
            

        return render_template('update.html', doc_data=True, doc_id=doc['_id'], \
                grouping=doc['grouping'], \
                sample_name=doc['sample']['name'], \
                sample_description=doc['sample']['description'], \
                sample_source=doc['sample']['source'], \
                sample_id=doc['sample']['id'], \
                sample_owner_name=doc['sample']['owner']['name'], \
                sample_owner_contact=doc['sample']['owner']['contact'], \
                datasource_reference=doc['data_source']['reference'], \
                datasource_input_name=doc['data_source']['input']['name'], \
                datasource_input_contact=doc['data_source']['input']['contact'], \
                datasource_input_date=' '.join(doc['data_source']['input']['date']), \
                datasource_input_notes=doc['data_source']['input']['notes'], \
                measurement_practitioner_name=doc['measurement']['practitioner']['name'], \
                measurement_practitioner_contact=doc['measurement']['practitioner']['contact'], \
                measurement_technique=doc['measurement']['technique'], \
                measurement_institution=doc['measurement']['institution'], \
                measurement_date=' '.join(doc['measurement']['date']), \
                measurement_description=doc['measurement']['description'], \
                measurement_requestor_name=doc['measurement']['requestor']['name'], \
                measurement_requestor_contact=doc['measurement']['requestor']['contact'], \
                measurement_results=doc['measurement']['results']
            ) 

    elif request.form.get("submit_button") == "update_doc":
        doc_id, update_pairs, meas_remove_indices, meas_add_eles = parse_update(request.form)
        update_success = perform_update(doc_id, update_pairs, meas_remove_indices, meas_add_eles)
        if update_success:
            message = "success...?"
        else:
            message = "Encountered an error while trying to update doc."
        return render_template('update.html', doc_data=False, message=message)
    return None


@app.route('/', methods=['GET', 'POST'])
def reference_page():
    '''
    example_data_dict = {
        "grouping" : "<string> experiment name or similar", 
        "specification" : "<string> MADF specification version (current is 3)", 
        "type" : "<string> document type (always assay)", 
        "sample" : { 
            "name" : "<string> concise description", 
            "description" : "<string> detailed description", 
            "source" : "<string> where the sample came from", 
            "id" : "<string> identification number", 
            "owner" : {
                "name" : "<string> name of who owns the sample", 
                "contact" : "<string> email or telephone of who owns the sample"
            } 
        }, 
        "measurement" : {
            "description" : "<string> detailed description",
            "technique" : "<string> technique name",
            "institution" : "<string> institution name",
            "requestor" : {
                "name" : "<string> name of who coordinated the measurement",
                "contact" : "<string> email or telephone of who coordinated the measurement"
            },
            "practitioner" : {
                "name" : "<string> name of who did the measurement",
                "contact" : "<string> email or telephone of who did the measurement"
            },
            "results" : [
                {
                    "isotope" : "<string> isotope name, usually in the format symbol-mass number",
                    "type" : "<string> the type of measurement (one of 'measurement' 'limit' or 'range')",
                    "unit" : "<string> unit for measurement (one of 'pct', 'g/g', 'ppm', 'ppb', 'ppt', 'ppq', 'g', 'mg', 'ug','ng', 'pg', 'Bq','mBq','uBq','nBq', 'pBq', 'g/kg','g/cm','g/m', 'g/cm2', 'g/m2', 'g/cm3', 'g/m3', 'mg/kg', 'mg/cm', 'mg/m', 'mg/cm2', 'mg/m2', 'mg/cm3', 'mg/m3', 'ug/kg', 'ug/cm', 'ug/m', 'ug/cm2', 'ug/m2', 'ug/cm3', 'ug/m3', 'ng/kg', 'ng/cm', 'ng/m', 'ng/cm2', 'ng/m2', 'ng/cm3', 'ng/m3', 'pg/kg', 'pg/cm', 'pg/m', 'pg/cm2',  'pg/m2', 'pg/cm3', 'pg/m3', 'Bq/kg', 'Bq/cm', 'Bq/m',  'Bq/cm2', 'Bq/m2', 'Bq/cm3', 'Bq/m3',  'mBq/kg', 'mBq/cm', 'mBq/m', 'mBq/cm2', 'mBq/m2', 'mBq/cm3', 'mBq/m3', 'uBq/kg', 'uBq/cm', 'uBq/m', 'uBq/cm2', 'uBq/m2', 'uBq/cm3', 'uBq/m3', 'nBq/kg', 'nBq/cm', 'nBq/m', 'nBq/cm2', 'nBq/m2', 'nBq/cm3', 'nBq/m3', 'pBq/kg', 'pBq/cm', 'pBq/m', 'pBq/cm2', 'pBq/m2', 'pBq/cm3', 'pBq/m3')",
                    "value" : [
                        "<float> if type is 'measurement' this is the central value. If type is 'limit' this is the upper limit. If type is 'range' this is the lower bound",
                        "<float> if type is 'measurement' this is the symmetric error. If type is 'limit' this is the confidence level. If type is 'range' this is upper bound",
                        "<float> if type is 'measurement' this is the asymmetric error. If type is 'limit' no value necessary. If type is 'range' this is the confidence level"
                    ]
                }
            ],
            "date" : [
                "<string> if only one date string, this is the date of measurement. If two date strings, this is the start of the date range for the measurement",
                "<string> if present, this is the end of the date range for the measurement"
            ]
        },
        "data_source" : {
            "reference" : "<string> where the data came from",
            "input" : {
                "name" : "<string> name of who entered the data",
                "contact" : "<string> email or telephone of who entered the data",
                "notes" : "<string> input simplifications, assumptions",
                "date" : [
                    "<string> if only one date string, this is the date of data input. If two date strings, this is the start of the date range for the data input",
                    "<string> if present, this is the end of the date range for the measurement"
                ]
            }
        }
    }
    #dict_lines = pprint.pformat(example_data_dict).split('\n')
    num_indents = 1
    for d_ch in json.dumps(example_data_dict):
        if d_ch in ['{', '[']:
            

    for a in dict_lines:
        print(a)
    '''
    return render_template('test.html')    


def do_q_append(form, append_mode):
    existing_q = parse_existing_q(form)
    existing_q += "\n"+append_mode
    q_lines = existing_q.count('\n')
    return existing_q, q_lines, [], []

def parse_existing_q(form_obj):
    existing_q = form_obj.get('existing_query', '').strip() + '\n'
    existing_q += form_obj.get('query_field', '').strip() +' '\
        + form_obj.get('comparison_operator', '').strip() +' '\
        + form_obj.get('query_value', '').strip()
    existing_q = existing_q.strip()
    return existing_q

def perform_search(q_lines):
    # assemble query
    curr_q = {}
    append_mode = 'AND'
    for q_line in q_lines:
        q_line = q_line.strip()
        if q_line == '':
            continue
        elif q_line == 'AND' or q_line == 'OR':
            append_mode = q_line
        else:
            line_eles = q_line.split(' ')
            field = line_eles[0]
            comparison = line_eles[1]
            value = ' '.join(line_eles[2:])
            curr_q = add_to_query(field, comparison, value, existing_q=curr_q, append_mode=append_mode)

    # query for results
    results = search(curr_q)

    return results


def perform_insert(form):
#    print('\nFORM:::::', form)
    meas_results = []
    i = 1
    form_keys = list(form.to_dict().keys())
    while True:
        # check if there are no more measurement elements
        if 'measurement.results.isotope'+str(i) not in form_keys:
            break

        # format values
        vals = []
        for val_key in ['measurement.results.valueA'+str(i), 'measurement.results.valueB'+str(i), 'measurement.results.valueC'+str(i)]:
            if form.get(val_key).strip() != '':
                # currently not enforcing any missing value rules
                vals.append(float(form.get(val_key).strip()))

        # create measurement element
        meas_ele = {'isotope':request.form.get('measurement.results.isotope'+str(i), ''),
            'type':request.form.get('measurement.results.type'+str(i), ''),
            'unit':request.form.get('measurement.results.unit'+str(i), ''),
            'value': vals
        }

        # add to measurements list
        meas_results.append(meas_ele)
        i += 1

    new_doc_id = insert(sample_name=form.get('sample.name',''), \
        sample_description=form.get('sample.description',''), \
        datasource_reference=form.get('datasource.reference',''), \
        datasource_input_name=form.get('datasource.input.name',''), \
        datasource_input_contact=form.get('datasource.input.contact',''), \
        datasource_input_date=form.get('datasource.input.date','').split(' '), \
        grouping=form.get('grouping',''), \
        sample_source=form.get('sample.source',''), \
        sample_id=form.get('sample.id',''), \
        sample_owner_name=form.get('sample.owner.name',''), \
        sample_owner_contact=form.get('sample.owner.contact',''), \
        measurement_results=meas_results, \
        measurement_practitioner_name=form.get('measurement.practitioner.name',''), \
        measurement_practitioner_contact=form.get('measurement.practitioner.contact',''), \
        measurement_technique=form.get('measurement.technique',''), \
        measurement_institution=form.get('measurement.institution',''), \
        measurement_date=form.get('measurement.date','').split(' '), \
        measurement_description=form.get('measurement.description',''), \
        measurement_requestor_name=form.get('measurement.requestor.name',''), \
        measurement_requestor_contact=form.get('measurement.requestor.contact',''), \
        datasource_input_notes=form.get('datasource.input.notes','')
    )
    
    return new_doc_id


def parse_update(form):
#    print(form)

    remove_meas_indices = []
    update_pairs = {}
    add_eles = []

    doc_id = form.get('current_doc_id')

    # gather updates for current measurement results objects
    num_measurement_results = 0
    while True:
        # check if this is the last of the existing measurement results objects
        if form.get("measurement.results.isotope"+str(num_measurement_results+1)) is None:
            break
        num_measurement_results += 1

        # check if entire object is to be removed
        if form.get('remove.measurement.results'+str(num_measurement_results)) is not None:
            remove_meas_indices.append(num_measurement_results - 1)

        for field in ["isotope", "type", "unit"]:
            # get form values
            curr_val = form.get('current.measurement.results.'+field+str(num_measurement_results), '')
            val = form.get('measurement.results.'+field+str(num_measurement_results), '')
            do_remove = form.get('remove.measurement.results.'+field+str(num_measurement_results), '') != ''

            # remove field's value by updating it with an empty string value. Use mongodb list indices, not html element numbers
            if do_remove:
                # add field to the "update values" list with an empty field (we don't want to completely delete the field)
                update_pairs['measurement.results.'+str(num_measurement_results-1)+'.'+field] = ''

            # val not empty means perform some update
            elif val != '':
                if val != curr_val: # dropdowns are pre-selected with the curr_val by default, so same value means no change
                    # add field to the "update values" list
                    update_pairs['measurement.results.'+str(num_measurement_results-1)+'.'+field] = val

        # handle the measurement results values
        curr_A = form.get('current.measurement.results.valueA'+str(num_measurement_results), '')
        curr_B = form.get('current.measurement.results.valueB'+str(num_measurement_results), '')
        curr_C = form.get('current.measurement.results.valueC'+str(num_measurement_results), '')
        vals = [curr_A, curr_B, curr_C]
        val_A = form.get('measurement.results.valueA'+str(num_measurement_results), '')
        val_B = form.get('measurement.results.valueB'+str(num_measurement_results), '')
        val_C = form.get('measurement.results.valueC'+str(num_measurement_results), '')
        if val_A != '':
            vals[0] = val_A
        if val_B != '':
            vals[1] = val_B
        if val_C != '':
            vals[2] = val_C
        if form.get('remove.measurement.results.valueA'+str(num_measurement_results), '') != '':
            vals[0] = None
        if form.get('remove.measurement.results.valueB'+str(num_measurement_results), '') != '':
            vals[1] = None
        if form.get('remove.measurement.results.valueC'+str(num_measurement_results), '') != '':
            vals[2] = None
        if vals[0] == curr_A and vals[1] == curr_B and vals[2] == curr_C:
            # no update
            pass
        else:
            if vals[2] is None or vals[2] == '':
                update = [vals[0], vals[1]]
            else:
                update = [vals[0], vals[1], vals[2]]

            if vals[1] is None or vals[1] == '':
                update = [vals[0]]

            if vals[0] is None or vals[0] == '':
                update = []

            update_pairs['measurement.results.'+str(num_measurement_results-1)+'.value'] = update

    # assemble newly-added measurement results
    num_new_measurement_results = 0
    while True:
        # check if this is the last of the new measurement results objects
        if form.get("new.measurement.results.isotope"+str(num_new_measurement_results+1)) is None:
            break
        num_new_measurement_results += 1
        
        # assemble a new result object
        new_meas_element = {}
        for meas_field in ["measurement.results.isotope", "measurement.results.type", "measurement.results.unit"]:
            new_val = form.get('new.'+meas_field+str(num_new_measurement_results), '')
            new_meas_element[meas_field.split('.')[-1]] = new_val
        new_meas_element["value"] = [form.get('new.measurement.results.valueA'+str(num_new_measurement_results), ''), \
            form.get('new.measurement.results.valueB'+str(num_new_measurement_results), ''), \
            form.get('new.measurement.results.valueC'+str(num_new_measurement_results), '')
        ]
        if new_meas_element["value"][2] == '':
            new_meas_element["value"] = [new_meas_element["value"][0], new_meas_element["value"][1]]
        else:
            new_meas_element["value"] = [new_meas_element["value"][0], new_meas_element["value"][1], new_meas_element["value"][2]]
        if new_meas_element["value"][1] == '':
            new_meas_element["value"] = [new_meas_element["value"][0]]
        if new_meas_element["value"][0] == '':
            new_meas_element["value"] = []

        # add new object to the "new additions" list
        add_eles.append(new_meas_element)

    # go over non-measurement_result fields looking for updates
    non_meas_result_fields = ["grouping", "sample.name", "sample.description", "sample.source", "sample.id", "sample.owner.name", "sample.owner.contact", "measurement.practitioner.name", "measurement.practitioner.contact", "measurement.technique","measurement.institution", "measurement.date", "measurement.description", "measurement.requestor.name", "measurement.requestor.contact", "datasource.reference", "datasource.input.name", "datasource.input.contact", "datasource.input.date", "datasource.input.notes"]
    for field in non_meas_result_fields:
        val = form.get(field, '')
        do_remove = form.get('remove.'+field, '') != ''
    
        if do_remove:
            if 'date' in field:
                update_pairs[field] = []
            else:
                update_pairs[field] = ''
        elif val != '':
            if 'date' in field:
                val = val.split(' ')
            update_pairs[field] = val

    return doc_id, update_pairs, remove_meas_indices, add_eles


def perform_update(doc_id, update_pairs, meas_remove_indices, meas_add_eles):
    successful_update = update(doc_id, update_pairs, meas_add_eles, meas_remove_indices)
    return successful_update

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)



