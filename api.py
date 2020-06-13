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
    results = ['this would be one result. Helo it is elise and i am here to speak to you aboutsomething vrty important. chris is watching a thing about seth rogana nd nathan for you. funny guys!', 'looks like joseph gordon levitt is also in there. and another guy, i actually dont know who he is which is too bad. its some sort of scene where nathan is fiving them group therapy. it is called nathan for you gets awkward with the night begore featuring seth rogan. hmm. i dont knwo what that would be like.', 'every time youre near baby i get kinda crazyin my head for yo i dont know what to do and oh baby i get kinda shaky when they mention you i just lose my cool my friends tell me something has come over me and i think i know what it is i think im imn love boy i think that im in love with you', 'laefjd asijjsdghdk jlo    jaliwej lkasdjflkasjelawihighlaugmrsnkamfndbajhviubrhakljjfhthifjieaegnighdihtransifweoair;ljgrneluvd s aefhjfhsslieine fjsalaeibuyatrjnihafd iaen aidjaie d']

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



