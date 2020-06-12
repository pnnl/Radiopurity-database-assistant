from flask import Flask, request, render_template
from python_mongo_toolkit import search, add_to_query, insert

app = Flask(__name__)

@app.route('/', methods=['GET','POST'])
def get_from_assembled_query():
    final_q = request.form.get('existing_query', '').strip() + '\n'
    final_q += request.form.get('query_field', '').strip() +' '\
        + request.form.get('comparison_operator', '').strip() +' '\
        + request.form.get('query_value', '').strip()
    #print(final_q)
    actual_q = parse_query
    print(actual_q)
    return render_template('index.html', existing_query='', num_q_lines=1)

@app.route('/append_and', methods=['GET','POST'])
def do_append_and():
    existing_q = request.form.get('existing_query', '').strip() + '\n'
    existing_q += request.form.get('query_field', '').strip() +' '\
        + request.form.get('comparison_operator', '').strip() +' '\
        + request.form.get('query_value', '').strip() + '\n'
    existing_q += "AND\n"
    q_lines = existing_q.count('\n')
    return render_template('index.html', existing_query=existing_q, num_q_lines=q_lines)

@app.route('/append_or', methods=['GET','POST'])
def do_append_or():
    existing_q = request.form.get('existing_query', '').strip() + '\n'
    existing_q += request.form.get('query_field', '').strip() +' '\
        + request.form.get('comparison_operator', '').strip() +' '\
        + request.form.get('query_value', '').strip() + '\n'
    existing_q += "OR\n"
    q_lines = existing_q.count('\n')
    return render_template('index.html', existing_query=existing_q, num_q_lines=q_lines)

def parse_query(q_str):
    query = {} #TODO: figure out how to append stuff (and, or) to query
    lines = [ l.strip() for l in q_str.split('\n') ]
    
    for i in range(0, len(lines)-1, 2):
        # parse query
        line = lines[i].split(' ')
        field = line[0]
        comparison = line[1]
        value = ' '.join(line[2:])
        try:
            value = float(value)
            if comparison in ['eq', 'lt', 'lte', 'gt', 'gte']:
                comparison = '$' + comparison
                q = {field:{comparison:val}}
        except:
            if comparison == 'contains':
                search_val = {'$regex':'.*'+val+'.*'}
            elif comparison == 'eq':
                search_val = {'$regex':val}
            elif comparison == 'notcontains':
                match_pattern = re.compile(val)
                search_val = {"$not":match_pattern}
            else:
                # not doing anything with <, <=, >, >= 
                search_val = None
            q = {field:search_val}

        # handle and/or
        if lines[i+1] == 'OR' or lines[i-1] == 'OR':
            if '$or' not in query.keys():
                query['$or'] = []
            query['$or'].append(lines[i])
            #TODO: do something
            if line == 'OR':
                query['$or'] = []  # {$or: [{expires: {$gte: new Date()}}, {expires: null}]}
            elif line == 'AND':
                pass


            if field in query.keys():
                query[field][comparison] = val
            else:
                query[field] = {comparison:val}

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)


