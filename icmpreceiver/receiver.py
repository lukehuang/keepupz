#!/usr/bin/python3

import janus
import socket
import asyncio
import threading
from os import environ
from struct import unpack
from datetime import datetime

from zabbix_helppers import (
    ZabbixAlreadyExistsException,
    ZabbixHelpper
)


_CONSUMERS = int(environ.get('CONSUMER_TASKS'))
# _ZBX_BGAN_KEY = environ.get('ZBX_BGAN_KEY')
# _ZBX_BGAN_ITEM = environ.get('ZBX_BGAN_ITEM')
_ZBX_BGAN_TEMPLATE = environ.get('ZBX_BGAN_TEMPLATE')
_ZBX_BGAN_HOSTGROUP = environ.get('ZBX_BGAN_HOSTGROUP')


async def produce(q):
    c = 0
    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    s.setsockopt(socket.SOL_IP, socket.IP_HDRINCL, 1)
    while True:
        c += 1
        received = True
        data, addr = s.recvfrom(1058)
        addr = addr[0]
        header = data[20:28]
        type, *_ = unpack('bbHHh', header)

        received_time = datetime.now()

        # 8 is icmp echo request
        if 8 == type:
            work_queue_item = {
                "received_addr": addr,
                "received_datetime": received_time
            }
            q.async_q.put_nowait(work_queue_item)
            # q.async_q.join()
            print("producer sequence: %s" % c)
            await asyncio.sleep(0)


def consume(name, q):
    zbxHelpper = ZabbixHelpper(
        group_name=_ZBX_BGAN_HOSTGROUP,
        template_name=_ZBX_BGAN_TEMPLATE
    )
    c = 0
    while True:
        val = q.sync_q.get()
        q.sync_q.task_done()
        c += 1
        print("consumer %s processed :%s" % (str(name), str(c)))
        # print('consumer gotten val: ' + str(val))
        # print(name, str(val))
        ip_addr = val['received_addr']
        try:
            rtrn = zbxHelpper.createHost(
                ip_addr.replace('.', '_'),
                ip_addr
            )
            print(rtrn)
        except ZabbixAlreadyExistsException as e:
            pass
            # print(e)


def run_receiver_forever():
    loop = asyncio.new_event_loop()
    q = janus.Queue(loop=loop)

    loop.create_task(produce(q))

    for x in range(_CONSUMERS):
        t = threading.Thread(
            target=consume,
            args=(str(x), q)
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
