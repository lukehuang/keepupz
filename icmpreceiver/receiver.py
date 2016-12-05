#!/usr/bin/python3

import janus
import socket
import asyncio
import ipaddress
import threading
from os import environ
from struct import unpack
from datetime import datetime

from zabbix_helppers import (
    ZabbixAlreadyExistsException,
    ZabbixHelpper
)


_ZBX_TEMPLATE = environ.get('ZBX_TEMPLATE')
_ZBX_HOSTGROUP = environ.get('ZBX_HOSTGROUP')
_ZBX_ALLOW_NETWORK = environ.get('ZBX_ALLOW_NETWORK')
_CONSUMERS = int(environ.get('CONSUMER_TASKS'))


async def produce(q):
    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    s.setsockopt(socket.SOL_IP, socket.IP_HDRINCL, 1)
    while True:
        data, addr = s.recvfrom(1058)
        addr = addr[0]

        ip_addr = ipaddress.ip_address(addr)
        ip_network = ipaddress.ip_network(_ZBX_ALLOW_NETWORK)

        if ip_addr in ip_network:
            print ("ip %s in %s" % (addr, _ZBX_ALLOW_NETWORK))
            header = data[20:28]
            type, *_ = unpack('bbHHh', header)

            # 8 is icmp echo request
            if 8 == type:
                q.async_q.put_nowait(addr)
                await asyncio.sleep(0)
        else:
            print("Skipping: %s" % addr)


def consume(name, q):
    zbxHelpper = ZabbixHelpper(
        group_name=_ZBX_HOSTGROUP,
        template_name=_ZBX_TEMPLATE
    )
    while True:
        ip_addr = q.sync_q.get()
        q.sync_q.task_done()
        print("consumer %s processed :%s" % (str(name), ip_addr))
        try:
            rtrn = zbxHelpper.createHost(
                ip_addr.replace('.', '_'),
                ip_addr
            )
            print(rtrn)
        except ZabbixAlreadyExistsException as e:
            print(e)


def run_receiver_forever():
    loop = asyncio.new_event_loop()
    q = janus.Queue(loop=loop)

    loop.create_task(produce(q))

    for x in range(_CONSUMERS):
        t = threading.Thread(
            target=consume,
            args=(
                "Thread-%s" % str(x),
                q
            )
        )
        t.start()

    try:
        loop.run_forever()
    except:
        asyncio.Future.cancel()
        loop.stop()
        loop.close()


if __name__ == "__main__":
    run_receiver_forever()
