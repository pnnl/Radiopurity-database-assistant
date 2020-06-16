from flask import Flask, request, render_template
from python_mongo_toolkit import search, add_to_query, insert

app = Flask(__name__)

@app.route('/search', methods=['GET','POST'])
def search_endpoint():
    if request.form.get("append_button") == "do_and":
        existing_q_str, num_q_lines, final_q_lines_list, results = do_q_append(request.form, "AND")

    elif request.form.get("append_button") == "do_or":
        existing_q_str, num_q_lines, final_q_lines_list, results = do_q_append(request.form, "OR")

    elif request.method == "POST":
        final_q_str = parse_existing_q(request.form)
        final_q_lines_list = []
        if final_q_str != '':
            final_q_lines_list = final_q_str.split('\n')
        results = perform_search(final_q_lines_list)
        existing_q_str = ''
        num_q_lines = 0

    else:
        existing_q_str = ''
        num_q_lines = 0
        final_q_lines_list = []
        results = []

    return render_template('search.html', existing_query=existing_q_str, num_q_lines=num_q_lines, final_q=final_q_lines_list, results=results)

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
@app.route('/edit', methods=['GET','POST'])
def edit_endpoint():
    return None



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
    print('\nFORM:::::', form)
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



if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)



