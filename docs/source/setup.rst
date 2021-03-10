*****
Setup
*****


General requirements
====================
* MongoDB `installed and running <https://docs.mongodb.com/manual/installation/>`_ on a machine that you have access to via the values for "mongodb_host" and "mongodb_port" in your app config JSON file
* Python >= 3.6
* A conda or virtualenv environment with the contents of requirements.txt installed
    * `virtualenv venv -p python3.6`
    * `source venv/bin/activate`
    * `pip install -r requirements.txt`


Running the user interface
==========================
Requirements
------------
* A JSON file (preferrably in the "user_interface" directory) containing one JSON object with the following keys and values types: "mongodb_host" (a string with the IP or name of the machine where MongoDB is running), "mongodb_port" (an integer that corresponds to the port that MongoDB is listening on), "database" (the name of the MongoDB database to use for the back-end of the app), "secret_key" (a string that is used to initiate sessions for users; set the value to whatever you perfer), and "salt" (a string that is used with encryption to make password hashes unpredictable).
    * Note: If you are running the app in a Docker container and using the MongoDB instance that is running on the host, you must use "host.docker.internal" as the value for "mongodb_host".
    * Note: If you are running the app in a Docker container, make sure the value you use for "mongodb_port" is mapped to the host when you run the container.
* An `environment variable <https://www.schrodinger.com/kb/1842>`_ named ``DUNE_API_CONFIG_NAME`` whose value is the path to the app config json file
* If you want to host the documentation along with the user interface, create a directory called "docs" in the user_interface/static directory. Then create a `symbolic link <https://www.freecodecamp.org/news/symlink-tutorial-in-linux-how-to-create-and-remove-a-symbolic-link/>`_ from the sphinx docs build to the newly created docs directory by running a command like this: ``ln -s dune/docs/build/html docs`` (this will keep the code in "docs" up to date with the code in "dune/docs/build/html" if it gets rebuilt). Then when you run the user interface, access the docs in your browser at: `HOSTNAME:PORT/static/docs/html/index.html`. 

Instructions
------------
1. Clone the repository
2. Activate the virtual environment
3. ``cd`` into the "user_interface" directory
4. Run ``./run.sh``
5. Navigate the browser to `localhost:5000/` and you should see the search page

For examples on using the user interface, see :ref:`user-interface-tutorial`.


Running the API
===============
Not sure if this will be a thing.

For examples on using the API, see :ref:`api-tutorial`.


Using the python toolkit on the command line
============================================
1. Clone the repository
2. Activate the virtual environment
3. To get help on how to run the script, run ``python python_mongo_toolkit.py -h``
4. There are three main commands, each with specific subcommands, that can be used:
    * ``search`` Search for an assay in the database. The following arguments can be used with the this command:
        * ``--q``: the query (a python dictionary) to use for the search **must be surrounded by double quotes**
    * ``add_query_term`` Adds a new query term to an existing query. The following arguments pertain to this command:
        * ``--field`` (string) the field to compare the value of
        * ``--compare`` (string) comparison operator to use to compare actual field value to given value (most be one of: "eq", "contains", "notcontains", "gt", "gte", "lt", "lte")
        * ``--val`` (string, int, or float) the value to compare against
        * ``--mode`` (string) optional argument to define append mode. (valid values are "AND" and "OR")
        * ``--q`` (string) existing human readable query string to add a new term to. If not present, creates a new query. **must be surrounded by double quotes**
    * ``insert`` Inserts a new assay into the database. The following arguments pertain to this command:
        * ``--sample_name`` (string) (required) concise sample description
        * ``--sample_description`` (required) (string) detailed sample description
        * ``--data_reference`` (string) (required) where the data came from
        * ``--data_inpu_name`` (string) (required) name of the person/people who performed data input
        * ``--data_input_contact`` (string) (required) email of the person/people who performed data input
        * ``--data_input_date`` (series of strings) (required) series of date strings for dates of input
        * ``--data_input_notes`` (string) input simplifications, assumptions
        * ``--grouping`` (string) experiment name or similar
        * ``--sample_source`` (string) where the sample came from
        * ``--sample_id`` (string) identification number
        * ``--sample_owner_name`` (string) name of who owns the sample
        * ``--sample_owner_contact`` (string) email of who owns the sample
        * ``--measurement_results`` (series of dicts) series of measurement dictionaries (each must have the following fields: "type", "unit", "value", "isotope") **must be surrounded with single quotes, and use double quotes within dict**
        * ``--measurement_practitioner_name`` (string) name of who did the measurement
        * ``--measurement_practitioner_contact`` (string) email of who did the measurement
        * ``--measurement_technique`` (string) technique name
        * ``--measurement_institution`` (string) institution name
        * ``--measurement_date`` (series of strings) series of date strings for dates of measurement
        * ``--measurement_description`` (string) detailed description
        * ``--measurement_requestor_name`` (string) name of who coordinated the measurement
        * ``--measurement_requestor_contact`` (string) email of who coordinated the measurement
    * ``update`` Updates an existing assay in the database. The following arguments pertain to this command:
        * ``--doc_id`` (string) the MongoDB id of the document in the database to update
        * ``--remove_doc`` if present, remove the entire document from the database
        * ``--update_pairs`` (dict) a dict of the fields to update and the corresponding values to update them with. **Must be surrounded with single quotes, and use double quotes within dict**
        * ``--new_meas_objects`` (series of dicts) series of measurement results dictionaries to add to the document. **Must be surrounded with single quotes, and use double quotes within dict**
        * ``--meas_remove_indices`` (series of ints) series of indices (zero-indexed) corresponding to the document measurement result object to remove

For examples on using the python toolkit on the command line, see :ref:`dunetoolkit-commandline-tutorial`.


Using the python toolkit code in a python script
================================================
1. Clone the repository
2. Ensure all requirements from requirements.txt are installed
3. ``cd`` into the dunetoolkit directory and run ``python setup.py install``
4. In the desired python script, import the dunetoolkit package like ``import dunetoolkit``
5. Use any of the available features in your code (for assistance with this, see the documentation on "Toolkit Functions")

For examples on using the python toolkit in a python script, see :ref:`dunetoolkit-script-tutorial`.



