from flask import Flask, request, render_template
from python_mongo_toolkit import search, add_to_query, insert

app = Flask(__name__)

@app.route('/', methods=['GET','POST'])
def get_from_assembled_query():
    final_q = parse_existing_q(request.form)

    q_lines = []
    if final_q != '':
        q_lines = final_q.split('\n')

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
    print('FINAL_Q:',curr_q)

    # QUERY FOR RESULTS
    results = ['one', 'two', 'three', 'four']

    return render_template('index.html', existing_query='', num_q_lines=1, final_q=q_lines, results=results)

@app.route('/append_and', methods=['GET','POST'])
def do_append_and():
    existing_q = parse_existing_q(request.form)
    existing_q += "\nAND"
    q_lines = existing_q.count('\n')
    return render_template('index.html', existing_query=existing_q, num_q_lines=q_lines, final_q=[], results=[])

@app.route('/append_or', methods=['GET','POST'])
def do_append_or():
    existing_q = parse_existing_q(request.form)
    existing_q += "\nOR"
    q_lines = existing_q.count('\n')
    return render_template('index.html', existing_query=existing_q, num_q_lines=q_lines, final_q=[], results=[])

def parse_existing_q(form_obj):
    existing_q = form_obj.get('existing_query', '').strip() + '\n'
    existing_q += form_obj.get('query_field', '').strip() +' '\
        + form_obj.get('comparison_operator', '').strip() +' '\
        + form_obj.get('query_value', '').strip()
    existing_q = existing_q.strip()
    return existing_q

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)



