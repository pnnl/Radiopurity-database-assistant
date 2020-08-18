from pymongo import MongoClient
from python_mongo_toolkit import add_to_query, search, insert, update_with_versions, convert_date_to_str

def _get_user(user, db_name):
    client = MongoClient('localhost', 27017)
    coll = client[db_name]['users']

    find_user_q = {'user_mode':{'$eq':user}}
    find_user_resp = coll.find(find_user_q)
    find_user_resp = list(find_user_resp)
    if len(find_user_resp) <= 0:
        user_obj = None
    else:
        user_obj = find_user_resp[0]
    return user_obj

def _add_user(user, encrypted_pw, db_name):
    client = MongoClient('localhost', 27017)
    coll = client[db_name]['users']

    db_new_user = {'user_mode':user, 'password_hashed':encrypted_pw}
    insert_resp = coll.insert_one(db_new_user)
    return insert_resp

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

            # implement search for "all" fields, aka the string fields that might have the same type of value in them
            if field == 'all':
                fields_for_all = ['grouping', 'sample.name', 'sample.description', 'sample.source', \
                                  'sample.id', 'measurement.technique', 'measurement.description', \
                                  'data_source.reference', 'data_source.input.notes']
                curr_q, error_msg = add_to_query(fields_for_all[0], comparison, value, existing_q=curr_q, append_mode='AND')
                if error_msg != '':
                    return [], error_msg
                for all_field in fields_for_all[1:]:
                    curr_q, error_msg = add_to_query(all_field, comparison, value, existing_q=curr_q, append_mode='OR')
                    if error_msg != '':
                        return [], error_msg

                continue

            curr_q, error_msg = add_to_query(field, comparison, value, existing_q=curr_q, append_mode=append_mode)
            if error_msg != '':
                return [], error_msg

    print('QUERY:::::',curr_q)

    # query for results
    results = search(curr_q)

    # convert datetime objects to strings for UI display
    for i in range(len(results)):
        for j in range(len(results[i]['measurement']['date'])):
            results[i]['measurement']['date'][j] = convert_date_to_str(results[i]['measurement']['date'][j])
        for j in range(len(results[i]['data_source']['input']['date'])):
            results[i]['data_source']['input']['date'][j] = convert_date_to_str(results[i]['data_source']['input']['date'][j])

    return results, ''


def perform_insert(form):
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
        meas_ele = {'isotope':form.get('measurement.results.isotope'+str(i), ''),
            'type':form.get('measurement.results.type'+str(i), ''),
            'unit':form.get('measurement.results.unit'+str(i), ''),
            'value': vals
        }

        # add to measurements list
        meas_results.append(meas_ele)
        i += 1

    # properly format dates
    data_input_date = form.get('data_source.input.date','')
    if data_input_date == '':
        data_input_date = []
    else:
        data_input_date = data_input_date.split(' ')
        for i in range(len(data_input_date)):
            data_input_date[i] = data_input_date[i].strip()
    measurement_date = form.get('measurement.date','')
    if measurement_date == '':
        measurement_date = []
    else:
        measurement_date = measurement_date.split(' ')
        for i in range(len(measurement_date)):
            measurement_date[i] = measurement_date[i].strip()

    new_doc_id, error_msg = insert(sample_name=form.get('sample.name',''), \
        sample_description=form.get('sample.description',''), \
        data_reference=form.get('data_source.reference',''), \
        data_input_name=form.get('data_source.input.name',''), \
        data_input_contact=form.get('data_source.input.contact',''), \
        data_input_date=data_input_date, \
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
        measurement_date=measurement_date, \
        measurement_description=form.get('measurement.description',''), \
        measurement_requestor_name=form.get('measurement.requestor.name',''), \
        measurement_requestor_contact=form.get('measurement.requestor.contact',''), \
        data_input_notes=form.get('data_source.input.notes','')
    )
    
    return new_doc_id, error_msg


def parse_update(form):
    remove_meas_indices = []
    update_pairs = {}
    add_eles = []

    doc_id = form.get('current_doc_id')
    remove_doc = form.get("remove.doc", "") == "remove"

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
    non_meas_result_fields = ["grouping", "sample.name", "sample.description", "sample.source", "sample.id", "sample.owner.name", "sample.owner.contact", "measurement.practitioner.name", "measurement.practitioner.contact", "measurement.technique","measurement.institution", "measurement.date", "measurement.description", "measurement.requestor.name", "measurement.requestor.contact", "data_source.reference", "data_source.input.name", "data_source.input.contact", "data_source.input.date", "data_source.input.notes"]
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

    return doc_id, remove_doc, update_pairs, remove_meas_indices, add_eles


def perform_update(doc_id, remove_doc, update_pairs, meas_remove_indices, meas_add_eles):
    new_doc_id, error_msg = update_with_versions(doc_id, remove_doc, update_pairs, meas_add_eles, meas_remove_indices)
    return new_doc_id, error_msg


