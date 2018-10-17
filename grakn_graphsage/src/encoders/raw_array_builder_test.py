import unittest

import grakn

import grakn_graphsage.src.encoders.raw_array_building as builders
import grakn_graphsage.src.neighbourhood.traversal as trv
import grakn_graphsage.src.neighbourhood.traversal_mocks as mock
import grakn_graphsage.src.neighbourhood.executor as ex

import numpy as np
client = grakn.Grakn(uri="localhost:48555")
session = client.session(keyspace="test_schema")


# def expected_output():
#     """
#
#     :return: A list of length 3, each element is a dict. Each dict holds arrays for the different properties we need.
#     """
#
#     # 'role_direction', np.int), ('role_type', np.int), ('thing_type', np.int), ('data_type', np.int),
#     #          ('neighbour_value_long', np.int), ('neighbour_value_double', np.float), ('neighbour_value_boolean', np.bool),
#     #          ('neighbour_value_date', np.datetime64), ('neighbour_value_string', np.str)])
#
#     full_shape = (1, 2, 2)
#
#     o = {'role_type': np.full(full_shape[:1], np.nan, np.int)}


class TestNeighbourTraversalFromEntity(unittest.TestCase):

    def setUp(self):
        self._tx = session.transaction(grakn.TxType.WRITE)
        self._neighbourhood_sizes = (3, 2)
        self._concept_info_with_neighbourhood = mock.mock_traversal_output()

        self._concept_infos_with_neighbourhoods = trv.concepts_with_neighbourhoods_to_neighbour_roles(
            [self._concept_info_with_neighbourhood, self._concept_info_with_neighbourhood])

        thing_type_labels = ['name', 'person', '@has-name', 'employment', 'company']

        # TODO Only required while we have a bug on roles as variables in Graql
        role_type_labels = ['employee', 'employer', '@has-name-value', '@has-name-owner']

        self._n_starting_concepts = len(self._concept_infos_with_neighbourhoods)

        self._builder = builders.RawArrayBuilder(thing_type_labels, role_type_labels, self._neighbourhood_sizes,
                                                 self._n_starting_concepts)

        self._expected_dims = [self._n_starting_concepts] + list(self._neighbourhood_sizes) + [1]
        
    def tearDown(self):
        self._tx.close()

    def _check_dims(self, arrays):
        # We expect dimensions:
        # (2, 3, 2, 1)
        # (2, 2, 1)
        # (2, 1)
        exp = [[self._expected_dims[0]] + list(self._expected_dims[i+1:]) for i in range(len(self._expected_dims)-1)]
        for i in range(len(self._expected_dims) - 1):
            with self.subTest(exp[i]):
                self.assertEqual(arrays[i]['neighbour_type'].shape, tuple(exp[i]))

    def test_build_raw_arrays(self):

        depthwise_arrays = self._builder.build_raw_arrays(self._concept_infos_with_neighbourhoods)
        self._check_dims(depthwise_arrays)

    def test_initialised_array_sizes(self):

        initialised_arrays = self._builder._initialise_arrays()
        self._check_dims(initialised_arrays)

    def test__determine_values_to_put_with_entity(self):
        role_label = 'employer'
        role_direction = ex.TARGET_PLAYS
        neighbour_type_label = 'company'
        neighbour_data_type = None
        neighbour_value = None
        values_dict = self._builder._determine_values_to_put(role_label, role_direction, neighbour_type_label,
                                                             neighbour_data_type, neighbour_value)
        expected_result = {"role_type": 1,
                           'role_direction': role_direction,
                           'neighbour_type': 4
                           }
        self.assertEqual(values_dict, expected_result)

    def test__determine_values_to_put_with_string_attribute(self):
        role_label = '@has-name-value'
        role_direction = ex.NEIGHBOUR_PLAYS
        neighbour_type_label = 'name'
        neighbour_data_type = 'string'
        neighbour_value = 'Person\'s Name'
        values_dict = self._builder._determine_values_to_put(role_label, role_direction, neighbour_type_label,
                                                             neighbour_data_type, neighbour_value)
        expected_result = {"role_type": 2,
                           'role_direction': role_direction,
                           'neighbour_type': 0,
                           'neighbour_data_type': 8,
                           'neighbour_value_string': neighbour_value}
        self.assertEqual(expected_result, values_dict)
