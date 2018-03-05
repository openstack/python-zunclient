#
# Copyright 2013 OpenStack LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import collections
import six

from zunclient.common import cliutils
from zunclient.common import utils
from zunclient import exceptions as exc
from zunclient.tests.unit import utils as test_utils


class CommonFiltersTest(test_utils.BaseTestCase):
    def test_limit(self):
        result = utils.common_filters(limit=42)
        self.assertEqual(['limit=42'], result)

    def test_limit_0(self):
        result = utils.common_filters(limit=0)
        self.assertEqual(['limit=0'], result)

    def test_limit_negative_number(self):
        result = utils.common_filters(limit=-2)
        self.assertEqual(['limit=-2'], result)

    def test_other(self):
        for key in ('marker', 'sort_key', 'sort_dir'):
            result = utils.common_filters(**{key: 'test'})
            self.assertEqual(['%s=test' % key], result)


class SplitAndDeserializeTest(test_utils.BaseTestCase):

    def test_split_and_deserialize(self):
        ret = utils.split_and_deserialize('str=foo')
        self.assertEqual(('str', 'foo'), ret)

        ret = utils.split_and_deserialize('int=1')
        self.assertEqual(('int', 1), ret)

        ret = utils.split_and_deserialize('bool=false')
        self.assertEqual(('bool', False), ret)

        ret = utils.split_and_deserialize('list=[1, "foo", 2]')
        self.assertEqual(('list', [1, "foo", 2]), ret)

        ret = utils.split_and_deserialize('dict={"foo": 1}')
        self.assertEqual(('dict', {"foo": 1}), ret)

        ret = utils.split_and_deserialize('str_int="1"')
        self.assertEqual(('str_int', "1"), ret)

    def test_split_and_deserialize_fail(self):
        self.assertRaises(exc.CommandError,
                          utils.split_and_deserialize, 'foo:bar')


class ArgsArrayToPatchTest(test_utils.BaseTestCase):

    def test_args_array_to_patch(self):
        my_args = {
            'attributes': ['str=foo', 'int=1', 'bool=true',
                           'list=[1, 2, 3]', 'dict={"foo": "bar"}'],
        }
        patch = utils.args_array_to_patch(my_args['attributes'])
        self.assertEqual([{'str': 'foo'},
                          {'int': 1},
                          {'bool': True},
                          {'list': [1, 2, 3]},
                          {'dict': {"foo": "bar"}}], patch)


class FormatArgsTest(test_utils.BaseTestCase):

    def test_format_args_none(self):
        self.assertEqual({}, utils.format_args(None))

    def test_format_args(self):
        l = utils.format_args([
            'K1=V1,K2=V2,'
            'K3=V3,K4=V4,'
            'K5=V5'])
        self.assertEqual({'K1': 'V1',
                          'K2': 'V2',
                          'K3': 'V3',
                          'K4': 'V4',
                          'K5': 'V5'
                          }, l)

    def test_format_args_semicolon(self):
        l = utils.format_args([
            'K1=V1;K2=V2;'
            'K3=V3;K4=V4;'
            'K5=V5'])
        self.assertEqual({'K1': 'V1',
                          'K2': 'V2',
                          'K3': 'V3',
                          'K4': 'V4',
                          'K5': 'V5'
                          }, l)

    def test_format_args_mix_commas_semicolon(self):
        l = utils.format_args([
            'K1=V1,K2=V2,'
            'K3=V3;K4=V4,'
            'K5=V5'])
        self.assertEqual({'K1': 'V1',
                          'K2': 'V2',
                          'K3': 'V3',
                          'K4': 'V4',
                          'K5': 'V5'
                          }, l)

    def test_format_args_split(self):
        l = utils.format_args([
            'K1=V1,'
            'K2=V22222222222222222222222222222'
            '222222222222222222222222222,'
            'K3=3.3.3.3'])
        self.assertEqual({'K1': 'V1',
                          'K2': 'V22222222222222222222222222222'
                          '222222222222222222222222222',
                          'K3': '3.3.3.3'}, l)

    def test_format_args_multiple(self):
        l = utils.format_args([
            'K1=V1',
            'K2=V22222222222222222222222222222'
            '222222222222222222222222222',
            'K3=3.3.3.3'])
        self.assertEqual({'K1': 'V1',
                          'K2': 'V22222222222222222222222222222'
                          '222222222222222222222222222',
                          'K3': '3.3.3.3'}, l)

    def test_format_args_multiple_colon_values(self):
        l = utils.format_args([
            'K1=V1',
            'K2=V2,V22,V222,V2222',
            'K3=3.3.3.3'])
        self.assertEqual({'K1': 'V1',
                          'K2': 'V2,V22,V222,V2222',
                          'K3': '3.3.3.3'}, l)

    def test_format_args_parse_comma_false(self):
        l = utils.format_args(
            ['K1=V1,K2=2.2.2.2,K=V'],
            parse_comma=False)
        self.assertEqual({'K1': 'V1,K2=2.2.2.2,K=V'}, l)

    def test_format_args_multiple_values_per_args(self):
        l = utils.format_args([
            'K1=V1',
            'K1=V2'])
        self.assertIn('K1', l)
        self.assertIn('V1', l['K1'])
        self.assertIn('V2', l['K1'])

    def test_format_args_bad_arg(self):
        args = ['K1=V1,K22.2.2.2']
        ex = self.assertRaises(exc.CommandError,
                               utils.format_args, args)
        self.assertEqual('arguments must be a list of KEY=VALUE '
                         'not K22.2.2.2', str(ex))

    def test_format_multiple_bad_args(self):
        args = ['K1=V1', 'K22.2.2.2']
        ex = self.assertRaises(exc.CommandError,
                               utils.format_args, args)
        self.assertEqual('arguments must be a list of KEY=VALUE '
                         'not K22.2.2.2', str(ex))


class CliUtilsTest(test_utils.BaseTestCase):

    def test_keys_and_vals_to_strs(self):
        dict_in = {six.u('a'): six.u('1'),
                   six.u('b'): {six.u('x'): 1,
                                'y': six.u('2'),
                                six.u('z'): six.u('3')},
                   'c': 7}

        dict_exp = collections.OrderedDict([
            ('a', '1'),
            ('b', collections.OrderedDict([
                ('x', 1),
                ('y', '2'),
                ('z', '3')])),
            ('c', 7)])

        dict_out = cliutils.keys_and_vals_to_strs(dict_in)
        dict_act = collections.OrderedDict([
            ('a', dict_out['a']),
            ('b', collections.OrderedDict(sorted(dict_out['b'].items()))),
            ('c', dict_out['c'])])

        self.assertEqual(six.text_type(dict_exp), six.text_type(dict_act))


class ParseNetsTest(test_utils.BaseTestCase):

    def test_no_nets(self):
        nets = []
        result = utils.parse_nets(nets)
        self.assertEqual([], result)

    def test_nets_with_network(self):
        nets = [' network = 1234567 , v4-fixed-ip = 172.17.0.3 ']
        result = utils.parse_nets(nets)
        self.assertEqual([{'network': '1234567', 'v4-fixed-ip': '172.17.0.3'}],
                         result)

    def test_nets_with_port(self):
        nets = ['port=1234567, v6-fixed-ip=2001:db8::2']
        result = utils.parse_nets(nets)
        self.assertEqual([{'port': '1234567', 'v6-fixed-ip': '2001:db8::2'}],
                         result)

    def test_nets_with_only_ip(self):
        nets = ['v4-fixed-ip = 172.17.0.3']
        self.assertRaises(exc.CommandError,
                          utils.parse_nets, nets)

    def test_nets_with_both_network_port(self):
        nets = ['port=1234567, network=2345678, v4-fixed-ip=172.17.0.3']
        self.assertRaises(exc.CommandError,
                          utils.parse_nets, nets)

    def test_nets_with_invalid_ip(self):
        nets = ['network=1234567, v4-fixed-ip=23.555.567,789']
        self.assertRaises(exc.CommandError,
                          utils.parse_nets, nets)


class ParseCommandTest(test_utils.BaseTestCase):

    def test_no_command(self):
        command = []
        result = utils.parse_command(command)
        self.assertEqual('', result)

    def test_command_ls(self):
        command = ['ls', '-al']
        result = utils.parse_command(command)
        self.assertEqual('"ls" "-al"', result)

    def test_command_echo_hello(self):
        command = ['sh', '-c', 'echo hello']
        result = utils.parse_command(command)
        self.assertEqual('"sh" "-c" "echo hello"', result)
