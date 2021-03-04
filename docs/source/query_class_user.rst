
.. _query-class-user-docs:

***********
Query class
***********
.. currentmodule:: dunetoolkit.query_class.Query


.. py:class:: Query(query_str=None)

   This class enables the database toolkit to form complicated queries that will return expectable results.

   :param query_str: If provided, this string will be parsed and loaded into the Query class, where it can then be added to, converted to human-readable format, or converted to the pymongo query language.
   :type query_str: str, optional


.. py:method:: dunetoolkit.query_class.Query.add_query_term(field, comparison, value, append_type='', include_synonyms=True)
      
   Add a new query term to the query that the Query object is keeping track of. If one or more query terms have already been loaded into the Query object, this term is added, according to the append_type, to the set of existing terms. The order in which query terms are added to the Query object matters. It impacts how the "and" and "or" append types apply to the terms and how certain terms are consolidated together, if necessary.

   :param field: The field whose value to compare.
   :type field: str
   :param comparison: The comparison to use to compare the field's value against the specified value.
   :type comparison: str
   :param value: The value to compare against.
   :type value: str, int, or float
   :param append_type: The append mode to use for this query term. Must be one of "AND" or "OR" or "". If append_type is an empty string, this is the first/only term in the Query object.
   :type append_type: str, optional
   :param include_synonyms: Whether or not to include the value's synonyms in the query term or to only search for the value itself.
   :type include_synonyms: bool, optionali


.. py:method:: dunetoolkit.query_class.Query.to_query_language()

   Convert the query terms that have been added to the Query object, via object instantiation and/or using add_query_term(), into valid pymongo query language. The dictionary that is returned from this function can be directly fed to the search() function.

   :rtype: dict. The query dict in pymongo query language.


.. py:method:: dunetoolkit.query_class.Query.to_string()

   Convert the query terms that have been added to the Query object, via object instantiation and/or using add_query_term(), into human-readable and python print-friendly format.

   :rtype: str. The query in human-readable format.


