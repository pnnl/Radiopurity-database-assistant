# DUNE database assistant

### database user interface (UI)
The goal of the database UI is to make interactions with the database more intuitive and easier 
for the user. While the python toolkit (information in the next section) provides a different way 
to access the database, it can often be easier to visualize search results as a table and to be 
guided through the insertion and update processes with buttons, dropdown menus, and text entry 
fields.  
There are three different pages available to users for database interaction, along with a "home" 
page. The user must login to the site in order to use the different pages, and there are two 
different types of permissions a user can have: read only (only the search page is available) and 
edit ability (the search, insert, and update pages are all available).  
Below is a summary of each page:
* `/` The home page. This page contains links to each of the below pages.
* `/search` Allows the user to assemble queies and use them to search the database. Search results 
are displayed at the bottom of the page, along with a count of the number of records found that 
match the query. A small summary of each record's information is provided in the list of search 
results, and the user can click on an individual element in the list to reveal all of the record's 
information. There is no option to export or download the search results from the UI, so in order 
to get those results the user must use the python toolkit (described below).
* `/insert` Provides a form that the user can fill out in order to create a new record in the 
database. This form enforces the required record schema upon the user in order to maintain data 
quality in the database. For example, if the user does not provide a valid isotope name in the 
measurement results section, the "insert" button remains disabled. Each field provides a 
description for what type of value the user should enter. Where possible, dropdown menus help the 
user to know what values they can enter for a given field. To insert a document once all desired 
fields are filled, the user can press the "insert" button. The database ID of the newly-inserted 
record is displayed on the resulting page if the insert was successful; otherwise, an error 
message is displayed describing why the record could not be inserted successfully.
* `/update` To update a record, the user must provide the record's database ID, which can be found 
by using the search page. After entering a valid ID, the user is presented with a page similar to 
the insert page, displaying all the possible fields along with the record's current values for 
each field. With the text entry boxes and dropdown menus, the user can add a new value or invoke no 
changes by leaving the box empty (or selecting the same dropdown option as the current value). The 
user can remove a value alltogether (therefore leaving the field with an empty value) by checking 
the "remove" box. Measurement result objects can be removed entirely by clicking the "remove" 
button below a result object. New measurement result objects can be added by clicking the "add" button 
below the measurement results section (this will display a new empty measurement results set of 
fields). When the fields are filled out to the user's desire, the user can click the "update" 
button. If the update is successful, the resulting page displays the new updated record's database 
ID. Otherwise, an error message is displayed describing why the record could not be updated 
successully.

### python toolkit
The python toolkit was created to provide ease of database use for users. The database used for 
this application is [MongoDB](https://docs.mongodb.com/manual/), though with the help of the 
python toolkit, a user need not know how to query a Mongo database. The toolkit provides four 
functions to aid the user to insert records into the database, update records, and assemble 
and execute queries. A user can explore the options available to them via the toolkit by 
executing the following command: `python python_mongo_toolkit.py -h`. This command will print 
a listing of the four available functions and what they do.  
Users can get more information about each function and the arguments that can be passed to it 
by executing the following command: `python python_mongo_toolkit.py <function_name> -h` where 
`<function_name>` is the name of one of the four functions. Each function has a set of required 
and optional arguments. If the user does not properly specify an argument, the toolkit will 
return an error and provide assistance on whether the user left out a required argument, 
misspelled an argument, or provided a value in an improper format.  
Below are concise descriptions of the four main functions and what they do:
* `add_query_term` This function was created to help the user assemble a query without needing to 
know the MongoDB query language. To use it, the user executes `python python_mongo_toolkit.py 
add_query_term` with the essential elements of a query term: the `field` name to query on, the 
`compare` operator, and the `value` to compare against. This function will assemble a query 
term in the MongoDB query language based on what the user specified in the arguments. If an 
existing query (`q`) is passed to this function, the new query term is added to it using the 
user-specified `mode` ("AND" or "OR) and the updated existing query is returned. Otherwise, the 
new query term is returned as the entire query. In this way, the user can assemble a query by 
adding terms where a field is compared to a value and the query that gets returned can be directly 
used to query the database.
* `search` Takes in a properly-formatted MongoDB query and returns the results as a list of python 
[dictionaries](https://www.w3schools.com/python/python_dictionaries.asp). Since the user is 
not expected to know the MongoDB query language, they are expected to use the `add_query_term` 
function to create an accurate query. Any query that is returned from the `add_query_term` 
function can be passed as an argument to the `search` function and expected to work correctly. 
The argument passed to this function must be a python dictionary surrounded by single quotes 
(`'`). The string values inside of the dictionary must be surrounded by double quotes (`"`), 
otherwise, the function will return an error.
* `insert` Is used to create a new record in the database. There are a set of valid fields that 
each record can have, and a subset of those fields are required to be present. Those required 
values are: `sample_name`, `sample_description`, `data_reference`, `data_input_name`, 
`data_input_contact`, and `data_input_date`. The other fields are optional. The 
`measurement_results` field can take any number of space-separated python dictionaries, each with 
the following fields: `isotope`, `type`, `unit`, `value`. If an argument is not properly 
formatted, the function will return an error describing how to fix the formatting issue. The goal 
of this function is not only to help users insert records into the database, but also to enforce 
a schema where all records have the same data format.
* `update` is used to change the existing values of the specified fields for an existing record 
in the database. The user must enter the database ID of the desired record, which they can get 
by searching for the desired record with the `search` function. The `remove_doc` argument can be 
added to specify that the user would like to delete the entire document from the database. 
Otherwise, the user can specify any number of `update_pairs`, each of which are a python 
dictionary where the key is the field name to update and the value is the new value to update (or 
add, if the field does not already have a value for this record) the field with. The user adds new 
measurement results to the record by passing any number of python dictionaries with the 
`new_meas_objects` field (each dictionary must have the `isotope`, `type`, `unit`, `value` 
fields). If the user wants to remove an entire measurement, they would use the original record to 
identify the index (in the measurements.results list) of the measurement they wish to remove. 
Users can specify any number of measurement indices to remove. When a record is updated in the 
database, it is given a new database ID, and the old version of the record is moved to an "old 
versions" database. Thus, information is never lost when it is deleted or updated, however users 
do not currently have access to the "old versions" database.

### requirements
* python >= 3.6
* conda or virtualenv environment with the contents of requirements.txt installed
    * `virtualenv venv -p python3.6`
    * `source venv/bin/activate`
    * `pip install -r requirements.txt`

### running the UI
* clone the repository
* `cd` into the repository directory
* create the virtualenvironment (see the requirements section above)
* activate the virtual environment
* be sure you are connected to the database (use port forwarding)
* run `python api.py` with the appropriate database selection arguments (run `python api.py -h` 
for a listing of all available arguments and what they do)
* access the UI in your browser using the port number listed on the console.

### copyright disclaimer
This material was prepared as an account of work sponsored by an agency of the United States Government.  Neither the United States Government nor the United States Department of Energy, nor Battelle, nor any of their employees, nor any jurisdiction or organization that has cooperated in the development of these materials, makes any warranty, express or implied, or assumes any legal liability or responsibility for the accuracy, completeness, or usefulness or any information, apparatus, product, software, or process disclosed, or represents that its use would not infringe privately owned rights.\
Reference herein to any specific commercial product, process, or service by trade name, trademark, manufacturer, or otherwise does not necessarily constitute or imply its endorsement, recommendation, or favoring by the United States Government or any agency thereof, or Battelle Memorial Institute. The views and opinions of authors expressed herein do not necessarily state or reflect those of the United States Government or any agency thereof.\
PACIFIC NORTHWEST NATIONAL LABORATORY\
operated by\
BATTELLE\
for the\
UNITED STATES DEPARTMENT OF ENERGY\
under Contract DE-AC05-76RL01830

