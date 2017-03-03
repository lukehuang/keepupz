#!/usr/bin/python3
import time
import janus
import socket
import asyncio
import ipaddress
import threading
from os import environ
from struct import unpack
from datetime import datetime

from zabbix_helpers import (
    ZabbixAlreadyExistsException,
    ZabbixHelpper
)


_ZBX_TEMPLATE = environ.get('ZBX_TEMPLATE')
_ZBX_HOSTGROUP = environ.get('ZBX_HOSTGROUP')
_ZBX_ALLOWED_NETWORKS = environ.get('ZBX_ALLOWED_NETWORKS').split(',')
_ZBX_WAIT_AFTER_CREATE_HOST = environ.get('ZBX_WAIT_AFTER_CREATE_HOST') or 3

_CONSUMERS = int(environ.get('CONSUMER_TASKS'))


async def produce(q):
    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    s.setsockopt(socket.SOL_IP, socket.IP_HDRINCL, 1)
    while True:
        data, addr = s.recvfrom(1058)
        addr = addr[0]

        ip_addr = ipaddress.ip_address(addr)
        ip_networks = [ipaddress.ip_network(x) for x in _ZBX_ALLOWED_NETWORKS]

        if [network for network in ip_networks if ip_addr in network]:
            header = data[20:28]
            type, *_ = unpack('bbHHh', header)

            # 8 is icmp echo request
            if 8 == type:
                q.async_q.put_nowait((addr, datetime.now()))
                await asyncio.sleep(0)
        else:
            print("Skipping: %s" % addr)


def consume(name, q):
    zbxHelpper = ZabbixHelpper(
        group_name=_ZBX_HOSTGROUP,
        template_name=_ZBX_TEMPLATE
    )
    while True:
        ip_addr, arrived_datetime = q.sync_q.get()
        q.sync_q.task_done()
        host_name = ""
        first_ping = True
        print("[consume] consumer %s processed :%s" % (str(name), ip_addr))
        try:
            host_name = ip_addr.replace('.', '_')
        except Exception as e:
            print("[consume] error on hostname %s ---> skipping next!: %s" % (
                ip_addr, e))
            continue
        try:
            rtrn = zbxHelpper.createHost(
                ip_addr.replace('.', '_'),
                ip_addr
            )
            print("[consume] Host created: %s" % rtrn)
        except ZabbixAlreadyExistsException as e:
            first_ping = False
            print("[consume] %s" % e)
        except Exception as e:
            print("[consume] %s ---> skipping next!" % e)
            continue
        else:
            try:
                time.sleep(_ZBX_WAIT_AFTER_CREATE_HOST)
                # send initial data to zabbix handle the first data
                # situation, so we can send a trap on autosignin using
                # zabbix
                zbxHelpper.send_host_availability(
                    host_name,
                    arrived_datetime,
                    0
                )
                print("[consume] * Initial Availability ZERO on zabbix")
            except Exception as e:
                print("[consume] send_host_availability ZERO %s"
                      " ---> skipping next!" % e)
                continue

        if not first_ping:
            try:
                zbxHelpper.send_host_availability(
                    host_name,
                    arrived_datetime
                )
            except Exception as e:
                print("[consume] #### UNKNOW EXCEPTION"
                      " in send_host_availability")
                print("[consume] %s" % host_name)
                print("[consume] %s" % e)
            else:
                print("[consume] * host %s is available on Zabbix" % host_name)


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
