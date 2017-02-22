#!/usr/bin/python3
import time
import socket
import asyncio
from sys import exit
from os import environ
from struct import unpack
from datetime import datetime
from pyzabbix import (ZabbixAPI, ZabbixAPIException)
from ZabbixSender import (ZabbixSender, ZabbixPacket)

_ZBX_SERVER = environ.get('ZBX_SERVER')
_ZBX_USERNAME = environ.get('ZBX_USERNAME')
_ZBX_PASSWORD = environ.get('ZBX_PASSWORD')
_ZBX_SENDER_KEY = environ.get('ZBX_SENDER_KEY')
_ZBX_SERVER_TIMEOUT = environ.get('ZBX_SERVER_TIMEOUT')


class ZabbixNotFoundException(Exception):
    pass


class ZabbixAlreadyExistsException(Exception):
    pass


class ZabbixParameterException(Exception):
    pass


class ZabbixHelpper(object):
    def __init__(
        self,
        group_name=None,
        template_name=None,
        zbx_addr=_ZBX_SERVER,
        zbx_username=_ZBX_USERNAME,
        zbx_password=_ZBX_PASSWORD,
        srv_timeout=None
    ):
        self.group_name = group_name
        self.template_name = template_name
        self.srv_timeout = int(srv_timeout or _ZBX_SERVER_TIMEOUT)
        self.zbx_addr = zbx_addr
        self.zbx_username = zbx_username
        self.zbx_password = zbx_password
        self.zapi = None
        self._connect_to_zabbix()
        self._connect_to_zabbix_sender()

    def _connect_to_zabbix(self):
        try:
            self.zapi = ZabbixAPI(
                server="http://%s" % self.zbx_addr,
                timeout=self.srv_timeout
            )
            self.zapi.login(
                self.zbx_username,
                self.zbx_password
            )
        except Exception as e:
            msg = 'Error _connect_to_zabbix %s'
            print(msg % e)

    def _connect_to_zabbix_sender(self):
        try:
            self.zbx_sender = ZabbixSender(self.zbx_addr, 10051)
        except Exception as e:
            raise ZabbixParameterException(
                "Error ZabbixSender - Check ZBX_SERVER."
            ) from e

    def _do_request(self, method, *args, **kwargs):
        while 1:
            try:
                return getattr(
                    self.zapi,
                    method
                ).dummy(
                    *args,
                    **kwargs
                )
            except ZabbixAPIException as e:
                raise e
            except:
                print("Error connecting to Zabbix Server. Retrying in 3secs!")
                time.sleep(3)
                self._connect_to_zabbix()

    # Get Zabbix group ID by hostgroup name
    def _getHostgroupId(self, hostgroup_name):
        hostgroups = self._do_request(
            'hostgroup.get',
            filter={'name': hostgroup_name}
        )
        if not hostgroups:
            raise ZabbixNotFoundException("Hostgroup not found")
        return int(hostgroups[0]['groupid'])

    # Get Zabbix template ID by template name
    def _getTemplateId(self, template_name):
        templates = self._do_request(
            'template.get',
            filter={'name': template_name}
        )
        if not templates:
            raise ZabbixNotFoundException("Template not found")
        return int(templates[0]['templateid'])

    def createHost(self, host_name, ip, group_name=None, template_name=None):
        """ Create one host in the Zabbix server

        Raises ZabbixNotFound exceptions from:
            _getTemplateId
            _getHostgroupId

        Raises ZabbixAlreadyExistsException on atempt to create an existent
        host (by hostname)


        Usage example:

        zbxHelpper = ZabbixHelpper()
        try:
            id = zbxHelpper.createHost(
                'my_host',
                '10.10.10.10',
                'my_grp',
                'my_template'
            )
            print(id)
        except ZabbixAlreadyExistsException as e:
            print(e.message)

        or setting default group_name and template_name on class initialization

        zbxHelpper = ZabbixHelpper(
            group_name='my_grp',
            template_name="my_template"
        )
        try:
            id = zbxHelpper.createHost(
                'my_host',
                '10.10.10.10'
            )
            print(id)
        except ZabbixAlreadyExistsException as e:
            print(e.message)


        """
        if not group_name:
            if self.group_name:
                group_name = self.group_name
            else:
                raise ZabbixParameterException(
                    "No group_name given as parameter or"
                    "on class initialization"
                )
        if not template_name:
            if self.template_name:
                template_name = self.template_name
            else:
                raise ZabbixParameterException(
                    "No template_name given as parameter or"
                    "on class initialization"
                )

        template_id = self._getTemplateId(template_name)
        host_group_id = self._getHostgroupId(group_name)

        groups = [{'groupid': host_group_id}]
        templates = [{'templateid': template_id}]
        interfaces = [{
            'ip': ip,
            'useip': 1,
            "dns": "",
            "main": 1,
            "type": 1,
            "port": "10050"
        }]
        inventory = {
            "notes": "my notes",
            "tag": "BGAN",
            "installer_name": "Netvision"
        }

        try:
            call_rtrn = self._do_request(
                'host.create',
                groups=groups,
                host=host_name,
                inventory_mode="1",
                inventory=inventory,
                templates=templates,
                interfaces=interfaces
            )
            return call_rtrn
        except ZabbixAPIException as exc:
            if str(exc).startswith("('Error -32602:"):
                ex_msg = '\tHost %s already exists' % host_name
                raise ZabbixAlreadyExistsException(ex_msg) from exc

    def send_host_availability(self, host_name, arrived_datetime):
        """ Create availability of one host in Zabbix

         The third parameter on package.add ()1 is the default value for
         positive availability.
        """
        packet = ZabbixPacket()
        packet.add(
            host_name,
            _ZBX_SENDER_KEY,
            1,
            datetime.timestamp(arrived_datetime)
        )
        self.zbx_sender.send(packet)
