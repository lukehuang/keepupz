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

_ZBX_CONNECT_MAX_RETRY = 10  # max retry connect
_ZBX_CONNECT_WAIT = 3  # secs to wait


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

    def _connect_to_zabbix(self, retry=0):
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
            if retry < _ZBX_CONNECT_MAX_RETRY:
                retry += 1
                print("[_connect_to_zabbix] Error connecting to Zabbix Server."
                      " Retrying in %ssecs!" % _ZBX_CONNECT_WAIT)
                print("[_connect_to_zabbix] %s" % e)
                time.sleep(_ZBX_CONNECT_WAIT)
                self._connect_to_zabbix(retry)
            else:
                raise e

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
            except Exception as e:
                if (
                    "Error -32602: Invalid params., "
                    "Host with the same name"
                ) in str(e):
                    ex_msg = 'Host %s already exists' % \
                        kwargs.get('host', '')
                    raise ZabbixAlreadyExistsException(ex_msg) from e
                else:
                    # so tento reconectar se nao for hostduplicado
                    print("[_do_request] Error connecting to Zabbix Server."
                          " Retrying in %ssecs!" % _ZBX_CONNECT_WAIT)
                    print("[_do_request] %s" % e)
                    time.sleep(_ZBX_CONNECT_WAIT)
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

    def send_host_availability(self, host_name, arrived_datetime,
                               positive_availability=1, retry=0):
        """ Create availability of one host in Zabbix

         The third parameter on package.add ()1 is the default value for
         positive availability.
        """
        packet = ZabbixPacket()
        packet.add(
            host_name,
            _ZBX_SENDER_KEY,
            positive_availability,
            datetime.timestamp(arrived_datetime)
        )
        self.zbx_sender.send(packet)
        processed = 0
        try:
            ret_dct = dict(
                item.split(':') for item in self.zbx_sender.status[
                    'info'].split(";"))
            processed = int(ret_dct['processed'])
        except Exception as e:
            print("[send_host_availability] Error parsing zbx response")
            print("[send_host_availability] %s" % e)

        if processed == 0 and retry < _ZBX_CONNECT_MAX_RETRY:
            print("[send_host_availability] Packet not processed by zbx"
                  " Retrying in %ssecs!" % _ZBX_CONNECT_WAIT)
            time.sleep(_ZBX_CONNECT_WAIT)
            retry += 1
            self.send_host_availability(host_name,
                                        arrived_datetime,
                                        positive_availability,
                                        retry)
