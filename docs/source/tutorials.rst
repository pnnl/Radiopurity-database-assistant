*********
Tutorials
*********

.. _user-interface-tutorial:

Using the user interface
========================

Search
------

Insert
------

Update
------


.. _api-tutorial:

Using the API
=============

Add to query
------------

Search
------

Insert
------

Update
------


.. _dunetoolkit-commandline-tutorial:

Using the python toolkit on the command line
============================================

Create a query
--------------
.. code::

    (env) $ python python_mongo_toolkit.py add_query_term --field grouping --compare contains --val Majorana
    QUERY STRING: grouping contains Majorana
    QUERY DICT:   {'grouping': {'$regex': re.compile('^.*Majorana.*$', re.IGNORECASE)}}

Add to an existing query
------------------------
.. code::

    (env) $ python python_mongo_toolkit.py add_query_term --field measurement.technique --compare eq --val NAA --mode AND --q "grouping contains Majorana"
    QUERY STRING: grouping contains Majorana\nAND\nmeasurement.technique equals NAA
    QUERY DICT:   {'$and': [{'grouping': {'$regex': re.compile('^.*Majorana.*$', re.IGNORECASE)}}, {'measurement.technique': {'$regex': re.compile('^NAA$', re.IGNORECASE)}}]}

Search using a query
--------------------
.. code::

    (env) $ python python_mongo_toolkit.py search --q "{'$and': [{'grouping': {'$regex': re.compile('^.*Majorana.*$', re.IGNORECASE)}}, {'measurement.technique': {'$regex': re.compile('^NAA$', re.IGNORECASE)}}]}"
    [{'_id': '5f1a05bc9aa72b9b0aaedfe4', 'specification': '3.00', 'grouping': 'DUNE', 'type': 'assay', 'sample': {'name': 'Rock Sample 1', 'description': 'DUNE Ross - #6 Winze', 'source': 'DUNE Ross - #6 Winze', 'id': 'Sample 1', 'owner': {'name': 'Juergen Reichenbacher', 'contact': 'Juergen.Reichenbacher@sdsmt.edu'}}, 'measurement': {'description': '', 'requestor': {'name': '', 'contact': ''}, 'practitioner': {'name': 'Juergen Reichenbacher', 'contact': 'Juergen.Reichenbacher@sdsmt.edu'}, 'technique': 'Ge Counter', 'institution': 'SDSM&T', 'date': [], 'results': [{'isotope': 'U-238', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [35.6, 5.0]}, {'isotope': 'Ra-226', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [66.0, 0.8]}, {'isotope': 'Th-232', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [48.9, 0.4]}, {'isotope': 'K-40', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [435.3, 1.7]}]}, 'data_source': {'reference': '', 'input': {'notes': '', 'date': [datetime.datetime(2020, 7, 23, 0, 0)], 'name': 'Sylvia Munson', 'contact': ''}}, '_version': 1}, {'_id': '5f1f43beed24042684c51145', 'specification': '3.00', 'grouping': 'DUNE', 'type': 'assay', 'sample': {'name': 'Rock Sample 3', 'description': 'DUNE Ross - Test Blast Site', 'source': 'DUNE Ross - Test Blast Site', 'id': '', 'owner': {'name': 'Juergen Reichenbacher', 'contact': 'Juergen.Reichenbacher@sdsmt.edu'}}, 'measurement': {'description': '', 'requestor': {'name': '', 'contact': ''}, 'practitioner': {'name': 'Juergen Reichenbacher', 'contact': 'Juergen.Reichenbacher@sdsmt.edu'}, 'technique': 'Ge Counter', 'institution': 'SDSM&T', 'date': [], 'results': [{'isotope': 'U-238', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [63.0, 7.8]}, {'isotope': 'Ra-226', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [146.0, 1.5]}, {'isotope': 'Th-232', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [19.6, 0.4]}, {'isotope': 'K-40', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [376.3, 2.3]}]}, 'data_source': {'reference': '', 'input': {'notes': '', 'date': [datetime.datetime(2020, 7, 27, 0, 0)], 'name': 'Sylvia Munson', 'contact': ''}}, '_version': 1}]

Insert a full document into the database
----------------------------------------
.. code::

    (env) $ python python_mongo_toolkit.py insert --sample_name "example name" --sample_description "this is an example entry" --data_reference test --data_input_name "Testing Person" --data_input_contact testing.person@gmail.com --data_input_date 05-27-2020 --data_input_notes "these would be testing notes" --grouping Testing --sample_source "test central" --sample_id testing123 --sample_owner_name "Test Owner" --sample_owner_contact testowner@test.edu --measurement_results '{"type":"measurement", "unit":"ppb", "isotope":"Th-236", "value":[13.2, 1.1]}' --measurement_practitioner_name "Practitioner Person" --measurement_practitioner_contact practitioner@practitioner.com --measurement_technique ABC --measurement_institution "The Test Center" --measurement_date 05-15-2020 --measurement_description "the measurement is a test" --measurement_requestor_name "Requesting Person" --measurement_requestor_contact requestor01@req.com
    NEW DOC ID: 603eae79eaffa3fc80478027

The document in the database would look like:

.. code::

    { 
        "grouping" : "Testing", 
        "sample" : { 
            "name" : "example name", 
            "description" : "this is an example entry", 
            "source" : "test central", 
            "id" : "testing123", 
            "owner" : { 
                "name" : "Test Owner", 
                "contact" : "testowner@test.edu" 
            }
        }, 
        "measurement" : { 
            "description" : "the measurement is a test", 
            "requestor" : { 
                "name" : "Requesting Person", 
                "contact" : "requestor01@req.com" 
            }, 
            "practitioner" : { 
                "name" : "Practitioner Person", 
                "contact" : "practitioner@practitioner.com" 
            }, 
            "technique" : "ABC", 
            "institution" : "The Test Center", 
            "date" : [ ISODate("2020-05-15T00:00:00Z") ], 
            "results" : [ 
                { 
                    "type" : "measurement", 
                    "unit" : "ppb", 
                    "isotope" : "Th-236", 
                    "value" : [ 13.2, 1.1 ] 
                } 
            ] 
        }, 
        "data_source" : { 
            "reference" : "test", 
            "input" : { 
                "notes" : "these would be testing notes", 
                "date" : [ ISODate("2020-05-27T00:00:00Z") ], 
                "name" : "Testing Person", 
                "contact" : "testing.person@gmail.com" 
            } 
        } 
    }

Insert a partial document into the database
-------------------------------------------
.. code::

    (env) $ python python_mongo_toolkit.py insert --sample_name "example name" --sample_description "this is an example entry" --data_reference test --data_input_name "Testing Person" --data_input_contact testing.person@gmail.com --data_input_date 05-27-2020 --grouping Testing --measurement_results '{"type":"measurement", "unit":"ppb", "isotope":"Th-236", "value":[13.2, 1.1]}' '{"type":"limit", "unit":"ppb", "isotope":"K-40", "value":[10.0, 1.03]}'
    NEW DOC ID: 603ea098ee219f6de37738c5

The document in the database would look like:
.. code::

    { 
        "grouping" : "Testing", 
        "sample" : { 
            "name" : "example name", 
            "description" : "this is an example entry", 
            "source" : "", 
            "id" : "", 
            "owner" : { 
                "name" : "", 
                "contact" : "" 
            } 
        }, 
        "measurement" : { 
            "description" : "", 
            "requestor" : { 
                "name" : "", 
                "contact" : "" 
            }, 
            "practitioner" : { 
                "name" : "", 
                "contact" : "" 
            }, 
            "technique" : "", 
            "institution" : "", 
            "date" : [ ], 
            "results" : [ 
                { 
                    "type" : "measurement", 
                    "unit" : "ppb", 
                    "isotope" : "Th-236", 
                    "value" : [ 13.2, 1.1 ] 
                },
                { 
                    "type" : "limit", 
                    "unit" : "ppb", 
                    "isotope" : "K-40", 
                    "value" : [ 10, 1.03 ] 
                } 
            ]
        }, 
        "data_source" : { 
            "reference" : "test", 
            "input" : { 
                "notes" : "", 
                "date" : [ ISODate("2020-05-27T00:00:00Z") ], 
                "name" : "Testing Person", 
                "contact" : "testing.person@gmail.com" 
            } 
        }
    }

Update a document in the database
---------------------------------
.. code::

    (env) $ python python_mongo_toolkit.py update --doc_id 603ea098ee219f6de37738c5 --update_pairs '{"grouping":"", "measurement.institution":"Testing Corp"}' --new_meas_objects '{"type":"limit", "unit":"ppb", "isotope":"K-40", "value":[1.0]}' '{"type":"measurement", "unit":"ppm", "isotope":"U-238", "value":[27, 0.1, 0.3]}' --meas_remove_indices 1
    UPDATED DOC ID: 603ea72b52787ed26f843df3

The document in the database would look like:

.. code::

    { 
        "grouping" : "", 
        "sample" : { 
            "name" : "example name", 
            "description" : "this is an example entry", 
            "source" : "", 
            "id" : "", 
            "owner" : { 
                "name" : "", 
                "contact" : "" 
            }
        }, 
        "measurement" : { 
            "description" : "", 
            "requestor" : { 
                "name" : "", 
                "contact" : "" 
            }, 
            "practitioner" : { 
                "name" : "",
                "contact" : ""
            }, 
            "technique" : "", 
            "institution" : "Testing Corp", 
            "date" : [ ],
            "results" : [ 
                { 
                    "type" : "measurement", 
                    "unit" : "ppb", 
                    "isotope" : "Th-236", 
                    "value" : [ 13.2, 1.1 ] 
                }, 
                {
                    "type" : "limit", 
                    "unit" : "ppb", 
                    "isotope" : "K-40", 
                    "value" : [ 1 ] 
                }, 
                { 
                    "type" : "measurement", 
                    "unit" : "ppm", 
                    "isotope" : "U-238", 
                    "value" : [ 27, 0.1, 0.3 ] 
                } 
            ] 
        }, 
        "data_source" : { 
            "reference" : "test", 
            "input" : { 
                "notes" : "", 
                "date" : [ ISODate("2020-05-27T00:00:00Z") ], 
                "name" : "Testing Person", 
                "contact" : "testing.person@gmail.com" 
            } 
        }
    }

Remove a document from the database
-----------------------------------
.. code::

    (env) $ python python_mongo_toolkit.py update --doc_id 603ea72b52787ed26f843df3 --remove_doc
    REMOVED.


.. _dunetoolkit-script-tutorial:

Using the python toolkit code in a python script
================================================

Query class
-----------
For a reference of what methods the Query class has, see :ref:`query-class-user-docs`. 


Create a query from scratch
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block::
    :linenos:

    from dunetoolkit import Query
    
    query_object = Query()
    query_object.add_query_term("grouping", "contains", "Majorana")
    print('QUERY DICT:',query_object.to_query_language())
    print('QUERY STRING:',query_object.to_string())

.. code-block::

    QUERY DICT: {'grouping': {'$regex': re.compile('^.*Majorana.*$', re.IGNORECASE)}}
    QUERY STRING: grouping contains Majorana


Create a query from an existing query string
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block::
    :linenos:

    from dunetoolkit import Query

    start_query = "grouping contains Majorana"
    query_object = Query(start_query)
    print('QUERY DICT:',query_object.to_query_language())
    print('QUERY STRING:',query_object.to_string())

.. code-block::

    QUERY DICT: {'grouping': {'$regex': re.compile('^.*Majorana.*$', re.IGNORECASE)}}
    QUERY STRING: grouping contains Majorana

Add to query
^^^^^^^^^^^^

.. code-block::
    :linenos:

    from dunetoolkit import Query

    query_object = Query("grouping contains Majorana")
    print('QUERY DICT:',query_object.to_query_language())
    print('QUERY STRING:',query_object.to_string())

    query_object.add_query_term("all", "contains", "copper", append_type="AND")
    print('QUERY DICT:',query_object.to_query_language())
    print('QUERY STRING:',query_object.to_string())
    
    query_object.add_query_term("all", "contains", "potassium", append_type="OR")
    print('QUERY DICT:',query_object.to_query_language())
    print('QUERY STRING:',query_object.to_string())

.. code-block::

    QUERY DICT: {'grouping': {'$regex': re.compile('^.*Majorana.*$', re.IGNORECASE)}}
    QUERY STRING: grouping contains Majorana
    QUERY DICT: {'$and': [{'grouping': {'$regex': re.compile('^.*Majorana.*$', re.IGNORECASE)}}, {'$text': {'$search': 'Copper Cu'}}]}
    QUERY STRING: grouping contains Majorana
    AND
    all contains ["Copper", "Cu"]
    QUERY DICT: {'$and': [{'grouping': {'$regex': re.compile('^.*Majorana.*$', re.IGNORECASE)}}, {'$text': {'$search': 'Copper Cu Potassium K'}}]}
    QUERY STRING: grouping contains Majorana
    AND
    all contains ["Copper", "Cu", "Potassium", "K"]


Search
------

Search with existing text query
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block::
    :linenos:

    from dunetoolkit import search

    results = search("grouping contains DUNE")
    print('RESULTS:',results)

.. code-block::

    RESULTS: [{'_id': '5f1a05bc9aa72b9b0aaedfe4', 'specification': '3.00', 'grouping': 'DUNE', 'type': 'assay', 'sample': {'name': 'Rock Sample 1', 'description': 'DUNE Ross - #6 Winze', 'source': 'DUNE Ross - #6 Winze', 'id': 'Sample 1', 'owner': {'name': 'Juergen Reichenbacher', 'contact': 'Juergen.Reichenbacher@sdsmt.edu'}}, 'measurement': {'description': '', 'requestor': {'name': '', 'contact': ''}, 'practitioner': {'name': 'Juergen Reichenbacher', 'contact': 'Juergen.Reichenbacher@sdsmt.edu'}, 'technique': 'Ge Counter', 'institution': 'SDSM&T', 'date': [], 'results': [{'isotope': 'U-238', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [35.6, 5.0]}, {'isotope': 'Ra-226', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [66.0, 0.8]}, {'isotope': 'Th-232', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [48.9, 0.4]}, {'isotope': 'K-40', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [435.3, 1.7]}]}, 'data_source': {'reference': '', 'input': {'notes': '', 'date': [datetime.datetime(2020, 7, 23, 0, 0)], 'name': 'Sylvia Munson', 'contact': ''}}, '_version': 1}, {'_id': '5f1f43beed24042684c51145', 'specification': '3.00', 'grouping': 'DUNE', 'type': 'assay', 'sample': {'name': 'Rock Sample 3', 'description': 'DUNE Ross - Test Blast Site', 'source': 'DUNE Ross - Test Blast Site', 'id': '', 'owner': {'name': 'Juergen Reichenbacher', 'contact': 'Juergen.Reichenbacher@sdsmt.edu'}}, 'measurement': {'description': '', 'requestor': {'name': '', 'contact': ''}, 'practitioner': {'name': 'Juergen Reichenbacher', 'contact': 'Juergen.Reichenbacher@sdsmt.edu'}, 'technique': 'Ge Counter', 'institution': 'SDSM&T', 'date': [], 'results': [{'isotope': 'U-238', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [63.0, 7.8]}, {'isotope': 'Ra-226', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [146.0, 1.5]}, {'isotope': 'Th-232', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [19.6, 0.4]}, {'isotope': 'K-40', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [376.3, 2.3]}]}, 'data_source': {'reference': '', 'input': {'notes': '', 'date': [datetime.datetime(2020, 7, 27, 0, 0)], 'name': 'Sylvia Munson', 'contact': ''}}, '_version': 1}, {'_id': '5f1f466bed24042684c51146', 'specification': '3.00', 'grouping': 'DUNE', 'type': 'assay', 'sample': {'name': 'Rock Sample 2', 'description': "DUNE Ross - Governor's Corner", 'source': "DUNE Ross - Governor's Corner", 'id': '', 'owner': {'name': 'Juergen Reichenbacher', 'contact': 'Juergen.Reichenbacher@sdsmt.edu'}}, 'measurement': {'description': '', 'requestor': {'name': '', 'contact': ''}, 'practitioner': {'name': 'Juergen Reichenbacher', 'contact': 'Juergen.Reichenbacher@sdsmt.edu'}, 'technique': 'Ge Counter', 'institution': 'SDSM&T', 'date': [], 'results': [{'isotope': 'U-238', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [24.4, 6.9]}, {'isotope': 'Ra-226', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [79.1, 1.1]}, {'isotope': 'Th-232', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [20.5, 0.4]}, {'isotope': 'K-40', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [420.6, 2.4]}]}, 'data_source': {'reference': '', 'input': {'notes': '', 'date': [datetime.datetime(2020, 7, 27, 0, 0)], 'name': 'Sylvia Munson', 'contact': ''}}, '_version': 2, '_parent_id': '5f1f40cbed24042684c51144'}, ...]


Search with existing dict query
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block::
    :linenos:

    from dunetoolkit import search
    import re

    results = search({'grouping': {'$regex': re.compile('^.*Dune.*$', re.IGNORECASE)}})
    print('RESULTS:',results)

.. code-block::

    RESULTS: [{'_id': '5f1a05bc9aa72b9b0aaedfe4', 'specification': '3.00', 'grouping': 'DUNE', 'type': 'assay', 'sample': {'name': 'Rock Sample 1', 'description': 'DUNE Ross - #6 Winze', 'source': 'DUNE Ross - #6 Winze', 'id': 'Sample 1', 'owner': {'name': 'Juergen Reichenbacher', 'contact': 'Juergen.Reichenbacher@sdsmt.edu'}}, 'measurement': {'description': '', 'requestor': {'name': '', 'contact': ''}, 'practitioner': {'name': 'Juergen Reichenbacher', 'contact': 'Juergen.Reichenbacher@sdsmt.edu'}, 'technique': 'Ge Counter', 'institution': 'SDSM&T', 'date': [], 'results': [{'isotope': 'U-238', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [35.6, 5.0]}, {'isotope': 'Ra-226', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [66.0, 0.8]}, {'isotope': 'Th-232', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [48.9, 0.4]}, {'isotope': 'K-40', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [435.3, 1.7]}]}, 'data_source': {'reference': '', 'input': {'notes': '', 'date': [datetime.datetime(2020, 7, 23, 0, 0)], 'name': 'Sylvia Munson', 'contact': ''}}, '_version': 1}, {'_id': '5f1f43beed24042684c51145', 'specification': '3.00', 'grouping': 'DUNE', 'type': 'assay', 'sample': {'name': 'Rock Sample 3', 'description': 'DUNE Ross - Test Blast Site', 'source': 'DUNE Ross - Test Blast Site', 'id': '', 'owner': {'name': 'Juergen Reichenbacher', 'contact': 'Juergen.Reichenbacher@sdsmt.edu'}}, 'measurement': {'description': '', 'requestor': {'name': '', 'contact': ''}, 'practitioner': {'name': 'Juergen Reichenbacher', 'contact': 'Juergen.Reichenbacher@sdsmt.edu'}, 'technique': 'Ge Counter', 'institution': 'SDSM&T', 'date': [], 'results': [{'isotope': 'U-238', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [63.0, 7.8]}, {'isotope': 'Ra-226', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [146.0, 1.5]}, {'isotope': 'Th-232', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [19.6, 0.4]}, {'isotope': 'K-40', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [376.3, 2.3]}]}, 'data_source': {'reference': '', 'input': {'notes': '', 'date': [datetime.datetime(2020, 7, 27, 0, 0)], 'name': 'Sylvia Munson', 'contact': ''}}, '_version': 1}, {'_id': '5f1f466bed24042684c51146', 'specification': '3.00', 'grouping': 'DUNE', 'type': 'assay', 'sample': {'name': 'Rock Sample 2', 'description': "DUNE Ross - Governor's Corner", 'source': "DUNE Ross - Governor's Corner", 'id': '', 'owner': {'name': 'Juergen Reichenbacher', 'contact': 'Juergen.Reichenbacher@sdsmt.edu'}}, 'measurement': {'description': '', 'requestor': {'name': '', 'contact': ''}, 'practitioner': {'name': 'Juergen Reichenbacher', 'contact': 'Juergen.Reichenbacher@sdsmt.edu'}, 'technique': 'Ge Counter', 'institution': 'SDSM&T', 'date': [], 'results': [{'isotope': 'U-238', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [24.4, 6.9]}, {'isotope': 'Ra-226', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [79.1, 1.1]}, {'isotope': 'Th-232', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [20.5, 0.4]}, {'isotope': 'K-40', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [420.6, 2.4]}]}, 'data_source': {'reference': '', 'input': {'notes': '', 'date': [datetime.datetime(2020, 7, 27, 0, 0)], 'name': 'Sylvia Munson', 'contact': ''}}, '_version': 2, '_parent_id': '5f1f40cbed24042684c51144'}, ...]


Search with query from Query object
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block::
    :linenos:

    from dunetoolkit import Query, search

    query_object = Query()
    query_object.add_query_term("grouping", "contains", "DUNE")
    results = search(query_object.to_query_language())
    print('RESULTS:',results)

.. code-block::

    RESULTS: [{'_id': '5f1a05bc9aa72b9b0aaedfe4', 'specification': '3.00', 'grouping': 'DUNE', 'type': 'assay', 'sample': {'name': 'Rock Sample 1', 'description': 'DUNE Ross - #6 Winze', 'source': 'DUNE Ross - #6 Winze', 'id': 'Sample 1', 'owner': {'name': 'Juergen Reichenbacher', 'contact': 'Juergen.Reichenbacher@sdsmt.edu'}}, 'measurement': {'description': '', 'requestor': {'name': '', 'contact': ''}, 'practitioner': {'name': 'Juergen Reichenbacher', 'contact': 'Juergen.Reichenbacher@sdsmt.edu'}, 'technique': 'Ge Counter', 'institution': 'SDSM&T', 'date': [], 'results': [{'isotope': 'U-238', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [35.6, 5.0]}, {'isotope': 'Ra-226', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [66.0, 0.8]}, {'isotope': 'Th-232', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [48.9, 0.4]}, {'isotope': 'K-40', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [435.3, 1.7]}]}, 'data_source': {'reference': '', 'input': {'notes': '', 'date': [datetime.datetime(2020, 7, 23, 0, 0)], 'name': 'Sylvia Munson', 'contact': ''}}, '_version': 1}, {'_id': '5f1f43beed24042684c51145', 'specification': '3.00', 'grouping': 'DUNE', 'type': 'assay', 'sample': {'name': 'Rock Sample 3', 'description': 'DUNE Ross - Test Blast Site', 'source': 'DUNE Ross - Test Blast Site', 'id': '', 'owner': {'name': 'Juergen Reichenbacher', 'contact': 'Juergen.Reichenbacher@sdsmt.edu'}}, 'measurement': {'description': '', 'requestor': {'name': '', 'contact': ''}, 'practitioner': {'name': 'Juergen Reichenbacher', 'contact': 'Juergen.Reichenbacher@sdsmt.edu'}, 'technique': 'Ge Counter', 'institution': 'SDSM&T', 'date': [], 'results': [{'isotope': 'U-238', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [63.0, 7.8]}, {'isotope': 'Ra-226', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [146.0, 1.5]}, {'isotope': 'Th-232', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [19.6, 0.4]}, {'isotope': 'K-40', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [376.3, 2.3]}]}, 'data_source': {'reference': '', 'input': {'notes': '', 'date': [datetime.datetime(2020, 7, 27, 0, 0)], 'name': 'Sylvia Munson', 'contact': ''}}, '_version': 1}, {'_id': '5f1f466bed24042684c51146', 'specification': '3.00', 'grouping': 'DUNE', 'type': 'assay', 'sample': {'name': 'Rock Sample 2', 'description': "DUNE Ross - Governor's Corner", 'source': "DUNE Ross - Governor's Corner", 'id': '', 'owner': {'name': 'Juergen Reichenbacher', 'contact': 'Juergen.Reichenbacher@sdsmt.edu'}}, 'measurement': {'description': '', 'requestor': {'name': '', 'contact': ''}, 'practitioner': {'name': 'Juergen Reichenbacher', 'contact': 'Juergen.Reichenbacher@sdsmt.edu'}, 'technique': 'Ge Counter', 'institution': 'SDSM&T', 'date': [], 'results': [{'isotope': 'U-238', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [24.4, 6.9]}, {'isotope': 'Ra-226', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [79.1, 1.1]}, {'isotope': 'Th-232', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [20.5, 0.4]}, {'isotope': 'K-40', 'type': 'measurement', 'unit': 'Bq/kg', 'value': [420.6, 2.4]}]}, 'data_source': {'reference': '', 'input': {'notes': '', 'date': [datetime.datetime(2020, 7, 27, 0, 0)], 'name': 'Sylvia Munson', 'contact': ''}}, '_version': 2, '_parent_id': '5f1f40cbed24042684c51144'}, ...]


Insert
------

.. code-block::
    :linenos:

    from dunetoolkit import insert, search_by_id

    measurement_results_list = [
        {
            'type':'limit', 
            'unit':'ppb', 
            'isotope':'K-40', 
            'value':[1, 2]
        },
        {
            'type':'measurement', 
            'unit':'ppm', 
            'isotope':'Th-238', 
            'value':[10.7, 3, 0.4]
        }
    ]
    new_doc_id, error_msg = insert('test sample name', \
        'test sample description', \
        'test reference', \
        'Data Inputperson', \
        'input.person@gmail.com', \
        ['2020-05-27'], \
        grouping='test', \
        sample_source='test source', \
        measurement_results=measurement_results_list, \
        measurement_practitioner_name='Practitioner Name', \
        measurement_practitioner_contact='prac@prac.edu', \
        measurement_date=['2020-05-15']
    )
    print('New doc id:',new_doc_id)

    found_doc = search_by_id(str(new_doc_id))
    print('Inserted doc:',found_doc)

.. code-block::

    New doc id: 604016f3ed4f33259bff6c15
    Inserted doc: {'_id': ObjectId('604016f3ed4f33259bff6c15'), 'specification': '3.00', 'grouping': 'test', 'type': 'assay', 'sample': {'name': 'test sample name', 'description': 'test sample description', 'source': 'test source', 'id': '', 'owner': {'name': '', 'contact': ''}}, 'measurement': {'description': '', 'requestor': {'name': '', 'contact': ''}, 'practitioner': {'name': 'Practitioner Name', 'contact': 'prac@prac.edu'}, 'technique': '', 'institution': '', 'date': [datetime.datetime(2020, 5, 15, 0, 0)], 'results': [{'type': 'limit', 'unit': 'ppb', 'isotope': 'K-40', 'value': [1, 2]}, {'type': 'measurement', 'unit': 'ppm', 'isotope': 'Th-238', 'value': [10.7, 3, 0.4]}]}, 'data_source': {'reference': 'test reference', 'input': {'notes': '', 'date': [datetime.datetime(2020, 5, 27, 0, 0)], 'name': 'Data Inputperson', 'contact': 'input.person@gmail.com'}}, '_version': 1}


Update
------
.. code-block::
    :linenos:

    from dunetoolkit import update, search_by_id

    doc_id = '604016f3ed4f33259bff6c15'

    # change the "grouping" value, remove the values for measurement practitioner name and contact, add a value for measurement institution
    updates = {
        'grouping':'DUNE', 
        'measurement.practitioner.name':'', 
        'measurement.practitioner.contact':'', 
        'measurement.institution':'PNNL'
    }
    
    # This new measurement result will be appended to the measurement.results list
    new_measurement_results = [
        {
            'type':'measurement', 
            'unit':'ppm', 
            'isotope':'U-238', 
            'value':[11.1, 0.7]
        }
    ]
    potassium_measurement_result_idx = 0

    updated_doc_id, error_msg = update(doc_id, \
        remove_doc=False, 
        update_pairs=updates, 
        new_meas_objects=new_measurement_results, \
        meas_remove_indices=[potassium_measurement_result_idx]
    )
    print('Updated doc id:',updated_doc_id)

    found_doc = search_by_id(str(updated_doc_id))
    print('Updated doc:',found_doc)

.. code-block::

    Updated doc id: 604019cdae553df33a4d1ed3
    Updated doc: {'_id': ObjectId('604019cdae553df33a4d1ed3'), 'specification': '3.00', 'grouping': 'DUNE', 'type': 'assay', 'sample': {'name': 'test sample name', 'description': 'test sample description', 'source': 'test source', 'id': '', 'owner': {'name': '', 'contact': ''}}, 'measurement': {'description': '', 'requestor': {'name': '', 'contact': ''}, 'practitioner': {'name': '', 'contact': ''}, 'technique': '', 'institution': 'PNNL', 'date': [datetime.datetime(2020, 5, 15, 0, 0)], 'results': [{'type': 'measurement', 'unit': 'ppm', 'isotope': 'Th-238', 'value': [10.7, 3, 0.4]}, {'type': 'measurement', 'unit': 'ppm', 'isotope': 'U-238', 'value': [11.1, 0.7]}]}, 'data_source': {'reference': 'test reference', 'input': {'notes': '', 'date': [datetime.datetime(2020, 5, 27, 0, 0)], 'name': 'Data Inputperson', 'contact': 'input.person@gmail.com'}}, '_version': 2, '_parent_id': '604016f3ed4f33259bff6c15'}



