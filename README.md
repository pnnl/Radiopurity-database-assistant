# radiopurity.org
This is the code for the SNOLAB Radiopurity instance, which is hosted at SNOLAB. It is available to anyone with a SNOLAB account, but part of the goal of the HPGE site is to allow experiment administrators to keep their experiment assays private, until they release them. Assays are hidden (not searchable) based on whether their "grouping" field is one of the (currently pre-determined) private groupings. In order to include a private experiment's assays in your search, you must enter the experiment's credentials in the /add_experiment_credentials page. You can then "log out" of a given private experiment by visiting the /remove_experiment_credentials page. To make an experiment's assay no longer private, you can enter experiment credentials to the /make_public page.

### General Requirements
* Python >= 3.7
* A conda or virtualenv environment with the contents of requirements.txt installed
* A JSON config file that provides database information to help the code connect to MongoDB. The config file should have the following fields:
    * `mongodb_host` a string that provides the host name to use when connecting to MongoDB
    * `mongodb_port` an int that provides the port to use when connecting to MongoDB
    * `database` a string that provides the name of the MongoDB database where the necessary collections can be accessed
    * `secret_key` (only for the UI) a string to use for the user interface in order to initialize sessions
    * `salt` (only for the UI) a string to use for hashing passwords when users log into the user interface
* Environment variables `DUNE_API_CONFIG_NAME` and `TOOLKIT_CONFIG_NAME` set to the absolute paths of the toolkit config file and the user interface config file, respectively
* MongoDB installed and running on a machine (or in a Docker container) that you have access to via the values for “mongodb_host” and “mongodb_port” in the app config JSON file 
    * Within the database (specified in the config file), a collection named "assays" must have a text index on the fields "grouping," "sample.name," "sample.description," "sample.source," "sample.id," "measurement.technique," "measurement.description," "data_source.reference," and "data_source.input.notes" so that they can be properly searched. For help creating a text index, see the [setup docs](docs/source/setup.rst)

### Tests
There are a set of pytests for the dunetoolkit package (in "tests") and a set for the user interface (in "user_interface/local_tests"). The user interface tests can only be run in a local environment, as the basic authentication is only set up in the SNOLAB environment (that is why they are called "local_tests"). In order to run the user interface tests, ensure that a test app config is created in the "local_tests" directory and that the DUNE_API_CONFIG_NAME environment variable is set. Then run the pytests from the user_interface/local_tests directory. 
To run the dunetoolkit tests, simply run `pytest` from within the "tests" directory.

### User Interface (UI)
#### Running the UI (command line)
* clone the repository
* activate the virtual environment
* `cd` into the repository directory
* make sure the `DUNE_APII_CONFiG_NAME` environment variable is set
* execute the run script `./run.sh`
* access the UI in your browser using the port number listed on the console.

#### Running the UI and database with Docker compose
* Clone the repository and `cd` into it.
* Build the cluster by running `docker-compose build`. This uses the `docker-compose.yml` file in the top level of the cloned repository.
* Start the cluster by running `docker-compose up`.
* Navigate the browser to localhost:5000/ and you should see the launch page.

#### Running the UI with Docker
* Clone the repository and `cd` into it.
* Create the docker image by running the bash script `create_image.sh` that is included in the repository. Alternatively, run the command `docker build --file ./Dockerfile -t dune_image .` from the top-level directory of the cloned repository. The `-t dune_image` flag names the image "dune_image" for ease of use.
* Run the docker container by running the bash script `run_docker.sh` that is included in the repository. Alternatively, execute the following command: `docker run -d --expose 27017 -p 5000:5000 -p 27017:27017 dune_image`. The `-p` arguments connect ports 5000 (for the user interface) and 27017 (for MongoDB) on the docker container to ports 5000 and 27017 on the host, so that the host can access the processes running on those ports via HTTP.
* Navigate the browser to localhost:5000/ and you should see the launch page.

#### Available Pages
The user interface provides an easy way to interact with the database. The user can search, insert, and update assays as well as assay requests.
* `/about` provides info about the Radiopurity database, data sources, and help with using the UI.
* `/login` allows a user to log in with the general read-only credentials or the general read/edit credentials.
* `/simple_search` is a simple search interface where the user enters a keyword (or keywords) to search for in any field of any assay in the database.
Search results are displayed at the bottom of the page, along with a count of the number of records found that 
match the query. A small summary of each record's information is provided in the list of search 
results, and the user can click on an individual element in the list to reveal all of the record's 
information.
* `/search` allows the user to assemble more complicated queries and use them to search the database. 
In contrast to the simple search page, which searches all fields for the keyword(s), this page allows 
the user to define specific fields, comparisons, and values to search for. Using this page, the user 
can also create multi-term queries, where they add as many field-comparison-value sets to the query 
as desired.
* `/add_experiment_credentials` "log in" to an experiment so that when you execute a search, this 
experiment's results can be in the results. A user can be "logged in" to multiple experiments at once.
* `/remove_experiment_credentials` "log out" of an experiment so that when you execute a search, this 
experiment's results are no longer searchable by you.
* `/make_public` release an experiment's results to everyone else using the HPGE site. Credentials 
will no longer be needed to include results for the experiment in a search.
* `/edit/insert` provides a form that the user can fill out in order to create a new assay record in the 
database. This form enforces the required record schema upon the user in order to maintain data 
quality in the database. Each field provides a 
description for what type of value the user should enter. To insert a document once all desired 
fields are filled, the user can press the "insert" button. The database ID of the newly-inserted 
record is displayed on the resulting page if the insert was successful; otherwise, an error 
message is displayed describing why the record could not be inserted successfully.
* `/edit/update` to update a record, the user must provide the record's database ID, which can be found 
by using the search page. After entering a valid ID, the user is presented with a page similar to 
the insert page, displaying all the possible fields along with the record's current values for 
each field. The user can remove a value altogether by checking 
the "remove" box. Measurement result objects can be removed entirely by clicking the "remove" 
button below a result object. New measurement result objects can be added by clicking the "add" button 
below the measurement results section. To insert the updated document into the database, the user can click the "update" 
button. If the update is successful, the resulting page displays the new updated record's database 
ID. Otherwise, an error message is displayed describing why the record could not be updated 
successfully.

#### Private experiment credentials
To make an experiment private, a developer with access to the MongoDB instance must add credentials to the database. The MongoDB collection where credentials are stored is called "users". 
A set of credentials for a private experiment has two fields: `experiment_name` and `password_hashed`. For a non-admin, the `experiment_name` should map to the experiment assays' "grouping" field. 
Each private experiment should also have a set of admin credentials, where the `experiment_name` for the admin should be the same as the non-admin but ending with "\_ADMIN". The admin credentials are used to make an experiment public.
The password for each experiment and admin is decided with the help of Silvia, and then hashed and stored. You'll need to use the same hashing method as we use in the `/add_experiment_credentials` page so it can be decrypted properly. To do this we use the python Scrypt package (See how in the `_log_in_experiment` function in the frontend_helpers.py file).

### Python Toolkit
The python toolkit was created to provide ease of database use. With the help of the 
python toolkit, a user need not know how to query a MongoDB database. 
Users can explore the options available in the toolkit by 
running `python python_mongo_toolkit.py -h` which will list the available functions and what they do.  

Users can get more information about each function and the arguments that can be passed to it 
by executing `python python_mongo_toolkit.py <function_name> -h` where 
`<function_name>` is the name of one of the main functions. Each function has a set of required 
and optional arguments. 

Below are concise descriptions of the main functions and what they do:
* `add_query_term` was created to help the user assemble a query without needing to 
know the MongoDB query language. To use it, run  `python python_mongo_toolkit.py 
add_query_term` with the essential elements of a query term: the `field` name to query on, the 
`compare` operator, and the `value` to compare against. The query dict that is returned can be used to query the database.
* `search` takes in a properly-formatted MongoDB query and returns the results as a list of python 
dictionaries. Since the user is 
not expected to know the MongoDB query language, they are expected to use the `add_query_term` 
function to create an accurate query. The `q` argument passed to this function must be a python dictionary surrounded by single quotes 
(`'`). The string values inside of the dictionary must be surrounded by double quotes (`"`).
* `insert` is used to create a new record in the database. The goal 
of this function is not only to help users insert records into the database, but also to enforce 
a schema where all records have the same data format.
* `update` is used to change the existing values of the specified fields for an existing record 
in the database. When a record is updated, it is given a new database ID, and the old version of the record is moved to an "old 
versions" collection. Thus, information is never lost when it is deleted or updated, however users 
do not have access to the "old versions" collection.

### Copyright Disclaimer
This material was prepared as an account of work sponsored by an agency of the United States Government.  Neither the United States Government nor the United States Department of Energy, nor Battelle, nor any of their employees, nor any jurisdiction or organization that has cooperated in the development of these materials, makes any warranty, express or implied, or assumes any legal liability or responsibility for the accuracy, completeness, or usefulness or any information, apparatus, product, software, or process disclosed, or represents that its use would not infringe privately owned rights.\
Reference herein to any specific commercial product, process, or service by trade name, trademark, manufacturer, or otherwise does not necessarily constitute or imply its endorsement, recommendation, or favoring by the United States Government or any agency thereof, or Battelle Memorial Institute. The views and opinions of authors expressed herein do not necessarily state or reflect those of the United States Government or any agency thereof.\
PACIFIC NORTHWEST NATIONAL LABORATORY\
operated by\
BATTELLE\
for the\
UNITED STATES DEPARTMENT OF ENERGY\
under Contract DE-AC05-76RL01830

