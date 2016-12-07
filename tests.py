#!/bin/python

from zabbix_helpers import (
    ZabbixAlreadyExistsException,
    ZabbixParameterException,
    ZabbixNotFoundException,
    ZabbixAPIException,
    ZabbixHelpper,
    ZabbixSender,
    ZabbixPacket,
    ZabbixAPI
)

import unittest
import mock


class ZabbixHelperTest(unittest.TestCase):
    def test_initialization_bad_server(self):
        with self.assertRaises(ZabbixParameterException):
            ZabbixHelpper(
                zbx_addr='0.0.0.0'
            )

    @mock.patch("zabbix_helpers.ZabbixAPI")
    def test_getHostGroupId(self, mocked_zabbix_api):
        mocked_login = mock.Mock()
        mocked_zabbix_api.login.return_value = mocked_login

        mocked_hostgroup_get = mock.Mock()
        mocked_hostgroup_get.return_value = [{'groupid': '1'}]
        mocked_zabbix_api.hostgroup.get.return_value = mocked_hostgroup_get

        z = ZabbixHelpper(zbx_addr='0.0.0.0')
        id = z._getHostgroupId('hostgroup_name')
        self.assertEqual(
            id,
            1
        )

        mocked_zabbix_api.hostgroup.get.assert_called_with(
            'hostgroup_name'
        )


if __name__ == '__main__':
    unittest.main()
