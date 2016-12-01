#!/usr/bin/python3
import socket
import asyncio
from os import environ
from struct import unpack
from datetime import datetime

q = asyncio.Queue()
_CONSUMERS = int(environ.get('RECEIVER_TASKS'))
_ZBX_SERVER = environ.get('ZBX_SERVER')
_ZBX_USERNAME = environ.get('ZBX_USERNAME')
_ZBX_PASSWORD = environ.get('ZBX_PASSWORD')
_ZBX_BGAN_TEMPLATE = environ.get('ZBX_BGAN_TEMPLATE')
_ZBX_BGAN_HOSTGROUP = environ.get('ZBX_BGAN_HOSTGROUP')
_ZBX_BGAN_ITEM = environ.get('ZBX_BGAN_ITEM')
_ZBX_BGAN_KEY = environ.get('ZBX_BGAN_KEY')


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
