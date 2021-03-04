
.. _query-class-developer-docs:

***********
Query class
***********
.. currentmodule:: dunetoolkit.query_class.Query

.. autoclass:: dunetoolkit.query_class.Query


instantiation
=============
.. autofunction:: __init__
.. autofunction:: _load_synonyms

load query from string
======================
.. autofunction:: _load_from_str
.. autofunction:: _get_field_from_str
.. autofunction:: _get_comparison_from_str
.. autofunction:: _get_value_from_str

add query term
==============
.. autofunction:: add_query_term
.. autofunction:: _add_query_term_all
.. autofunction:: _add_query_term_nonall

convert to pymongo query
========================
.. autofunction:: to_query_language
.. autofunction:: _convert_append_str_to_q_operator

functions to create pymongo query terms for basic types: the "all" query, date comparisons, str comparisons, number comparisons
-------------------------------------------------------------------------------------------------------------------------------
.. autofunction:: _assemble_qterm_all
.. autofunction:: _assemble_qterm_date
.. autofunction:: _assemble_qterm_str
.. autofunction:: _assemble_qterm_num

helper functions for curating measurement results terms into valid pymongo query terms
--------------------------------------------------------------------------------------
.. autofunction:: _consolidate_measurement_results
.. autofunction:: _assemble_qterm_meas_results
.. autofunction:: _get_valid_meas_types
.. autofunction:: _get_meas_value_variations
.. autofunction:: _assemble_meas_result_terms

convert to human-readable string
================================
.. autofunction:: to_string
.. autofunction:: _comparison_to_human
.. autofunction:: _value_to_human

validation
==========
.. autofunction:: _validate_term
.. autofunction:: _validate_field_name
.. autofunction:: _validate_comparison
.. autofunction:: _validate_value
.. autofunction:: _validate_append_mode
.. autofunction:: _validate_term_against_other_terms




