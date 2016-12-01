#!/usr/bin/python3
import socket
import asyncio
from os import environ
from struct import unpack
from datetime import datetime
from pyzabbix import ZabbixAPI
from pyzabbix import ZabbixAPIException

q = asyncio.Queue()
_CONSUMERS = int(environ.get('RECEIVER_TASKS'))
_ZBX_SERVER = environ.get('ZBX_SERVER')
_ZBX_USERNAME = environ.get('ZBX_USERNAME')
_ZBX_PASSWORD = environ.get('ZBX_PASSWORD')
_ZBX_BGAN_TEMPLATE = environ.get('ZBX_BGAN_TEMPLATE')
_ZBX_BGAN_HOSTGROUP = environ.get('ZBX_BGAN_HOSTGROUP')
_ZBX_BGAN_ITEM = environ.get('ZBX_BGAN_ITEM')
_ZBX_BGAN_KEY = environ.get('ZBX_BGAN_KEY')


class ZabbixNotFoundException(Exception):
    def __init__(self, message):
        self.message = message


class ZabbixAlreadyExistsException(Exception):
    def __init__(self, message):
        self.message = message


class ZabbixHelpper(object):
    def __init__(self):
        self.zapi = ZabbixAPI(_ZBX_SERVER)
        self.zapi.login(
            _ZBX_USERNAME,
            _ZBX_PASSWORD
        )

    # Get Zabbix group ID by hostgroup name
    def _getHostgroupId(self, hostgroup_name):
        hostgroups = self.zapi.hostgroup.get(
            filter={'name': hostgroup_name}
        )
        if not hostgroups:
            raise ZabbixNotFoundException("Hostgroup not found")
        return int(hostgroups[0]['groupid'])

    # Get Zabbix template ID by template name
    def _getTemplateId(self, template_name):
        templates = self.zapi.template.get(
            filter={'name': template_name}
        )
        if not templates:
            raise ZabbixNotFoundException("Template not found")
        return int(templates[0]['templateid'])

    def createHost(self, host_name, ip, group_name, template_name):
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

        """
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

        try:
            call_rtrn = self.zapi.host.create(
                groups=groups,
                host=host_name,
                inventory_mode=1,
                templates=templates,
                interfaces=interfaces
            )
            return call_rtrn
        except ZabbixAPIException as exc:
            if str(exc).startswith("('Error -32602:"):
                ex_msg = 'Host %s already exists' % host_name
                raise ZabbixAlreadyExistsException(ex_msg) from exc


async def produce():
    # c = 0
    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    s.setsockopt(socket.SOL_IP, socket.IP_HDRINCL, 1)
    while True:
        received = True
        data, addr = s.recvfrom(1058)
        addr = addr[0]
        header = data[20:28]
        type, *_ = unpack('bbHHh', header)

        received_time = datetime.now()

        # 8 is icmp echo request
        if 8 == type:
            # c += 1
            # print(c)
            work_queue_item = {
                "received_addr": addr,
                "received_datetime": received_time
            }
            await q.put(work_queue_item)
            await asyncio.sleep(0)


async def consume(name):
    c = 0
    while True:
        c += 1
        value = await q.get()
        print(c, name, value)

loop = asyncio.get_event_loop()
loop.create_task(produce())
for x in range(_CONSUMERS):
    loop.create_task(consume(str(x)))
try:
    loop.run_forever()
except:
    asyncio.Future.cancel()
    loop.stop()
    loop.close()
