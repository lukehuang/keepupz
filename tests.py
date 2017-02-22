#!/bin/python

from zabbix_helpers import (
    ZabbixParameterException,
    ZabbixNotFoundException,
    ZabbixHelpper,
    ZabbixPacket,
)

from datetime import datetime
import unittest
import mock


class ZabbixHelperTest(unittest.TestCase):
    def test_initialization_bad_server(self):
        with self.assertRaises(ZabbixParameterException):
            ZabbixHelpper(
                zbx_addr='10.23.76.98',
                srv_timeout=1
            )

    @mock.patch("zabbix_helpers.ZabbixAPI")
    def test_getHostGroupId(self, mocked_zabbix_api):
        z = ZabbixHelpper(
            zbx_addr='10.23.76.98',
            srv_timeout=1
        )
        z._do_request = mock.Mock()
        z._do_request.return_value = [{'groupid': 10}]
        id = z._getHostgroupId('asd')
        self.assertEqual(
            id,
            10
        )

        z._do_request.assert_called_with(
            'hostgroup.get',
            filter={'name': 'asd'}
        )

    @mock.patch("zabbix_helpers.ZabbixAPI")
    def test_getHostGroupId_wrong_hostgroup_name(self, mocked_zabbix_api):
        z = ZabbixHelpper(
            zbx_addr='10.23.76.98',
            srv_timeout=1
        )
        z._do_request = mock.Mock()
        z._do_request.return_value = []
        with self.assertRaises(ZabbixNotFoundException):
            z._getHostgroupId('asd')

    @mock.patch("zabbix_helpers.ZabbixAPI")
    def test_getTemplateId(self, mocked_zabbix_api):
        z = ZabbixHelpper(
            zbx_addr='10.23.76.98',
            srv_timeout=1
        )
        z._do_request = mock.Mock()
        z._do_request.return_value = [{'templateid': 20}]
        id = z._getTemplateId('asd')
        self.assertEqual(
            id,
            20
        )

        z._do_request.assert_called_with(
            'template.get',
            filter={'name': 'asd'}
        )

    @mock.patch("zabbix_helpers.ZabbixAPI")
    def test_getTemplateId_wrong_template_name(self, mocked_zabbix_api):
        z = ZabbixHelpper(
            zbx_addr='10.23.76.98',
            srv_timeout=1
        )

        z._do_request = mock.Mock()
        z._do_request.return_value = []
        with self.assertRaises(ZabbixNotFoundException):
            z._getTemplateId('asd')

    @mock.patch("zabbix_helpers.ZabbixAPI")
    def test_createHost(self, mocked_zabbix_api):
        z = ZabbixHelpper(
            zbx_addr='10.23.76.98',
            srv_timeout=1
        )

        z._getTemplateId = mock.Mock()
        z._getHostgroupId = mock.Mock()

        z._getTemplateId.return_value = 22
        z._getHostgroupId.return_value = 22

        z._do_request = mock.Mock()
        z._do_request.return_value = 20
        id = z.createHost(
            "host_name",
            "10.0.0.10",
            group_name="grp_name",
            template_name="tpl_name"
        )
        self.assertEqual(
            id,
            20
        )

        z._do_request.assert_called_with(
            'host.create',
            groups=[{'groupid': 22}],
            host='host_name',
            interfaces=[{
                'ip': '10.0.0.10',
                'main': 1,
                'port': '10050',
                'dns': '',
                'useip': 1,
                'type': 1
            }],
            inventory={
                'tag': 'BGAN',
                'notes': 'my notes',
                'installer_name': 'Netvision'
            },
            inventory_mode='1',
            templates=[{'templateid': 22}]
        )

    @mock.patch.object(ZabbixPacket, "add")
    @mock.patch("zabbix_helpers.ZabbixSender")
    @mock.patch("zabbix_helpers.ZabbixAPI")
    def test_send_host_availability(
        self,
        mocked_zabbix_api,
        mocked_zabbix_sender,
        mocked_zabbix_packet
    ):

        z = ZabbixHelpper(
            zbx_addr='10.23.76.98',
            srv_timeout=1
        )

        arrived_time = datetime.now()
        z.send_host_availability('host_name', arrived_time)

        z.zbx_sender.send.assert_called()
        mocked_zabbix_packet.assert_called()


if __name__ == '__main__':
    unittest.main()
