import greengrasssdk
import platform
import time
import json
import urllib
import urllib2

client = greengrasssdk.client('iot-data')

ds = False
ws = False
os = False
fs = False
sname = ''
obname = ''
fname = '2'


def function_handler(event, context):
    global ds
    global ws
    global os
    global fs
    global sname
    global obname
    global fname

    state = event['state']
    if state == 'Sensor':
        di = event['ds']
        we = event['ws']
        if (di == 'o'):
            ds = True
        if (we == 'o'):
            ws = True

        if ds:
            if ws:
                name = event['name']
                pp = event['pp']
                if pp == 'pick':
                    values = {'af120_idx': fname}
                    data = urllib.urlencode(values)
                    if (name == 'zapagatty'):
                        name = 'product1_pick_json.do'
                        url = 'http://61.253.199.32/' + name
                        req = urllib2.Request(url, data)
                        response = urllib2.urlopen(req)
                        client.publish(topic='a/b', payload=name)
                    elif (name == 'lottesand'):
                        name = 'product2_pick_json.do'
                        url = 'http://61.253.199.32/' + name
                        req = urllib2.Request(url, data)
                        response = urllib2.urlopen(req)
                        client.publish(topic='a/b', payload=name)
                    elif (name == 'orangejuice'):
                        name = 'product3_pick_json.do'
                        url = 'http://61.253.199.32/' + name
                        req = urllib2.Request(url, data)
                        response = urllib2.urlopen(req)
                        client.publish(topic='a/b', payload=name)
                    elif (name == 'postick'):
                        name = 'product4_pick_json.do'
                        url = 'http://61.253.199.32/' + name
                        req = urllib2.Request(url, data)
                        response = urllib2.urlopen(req)
                        client.publish(topic='a/b', payload=name)
                elif pp == "put":
                    values = {'af120_idx': fname}
                    data = urllib.urlencode(values)
                    if (name == 'zapagatty'):
                        name = 'product1_put_json.do'
                        url = 'http://61.253.199.32/' + name
                        req = urllib2.Request(url, data)
                        response = urllib2.urlopen(req)
                        client.publish(topic='a/b', payload=name)
                    elif (name == 'lottesand'):
                        name = 'product2_put_json.do'
                        url = 'http://61.253.199.32/' + name
                        req = urllib2.Request(url, data)
                        response = urllib2.urlopen(req)
                        client.publish(topic='a/b', payload=name)
                    elif (name == 'orangejuice'):
                        name = 'product3_put_json.do'
                        url = 'http://61.253.199.32/' + name
                        req = urllib2.Request(url, data)
                        response = urllib2.urlopen(req)
                        client.publish(topic='a/b', payload=name)
                    elif (name == 'postick'):
                        name = 'product4_put_json.do'
                        url = 'http://61.253.199.32/' + name
                        req = urllib2.Request(url, data)
                        response = urllib2.urlopen(req)
                        client.publish(topic='a/b', payload=name)
                ds = False
                ws = False
        else:
            if ws and (not os):
                sname = event['name']
            elif ws and os:
                name = event['name']
                if name == obname:
                    values = {'af120_idx': fname}
                    data = urllib.urlencode(values)
                    if (name == 'zapagatty'):
                        name = 'product1_put_json.do'
                        url = 'http://61.253.199.32/' + name
                        req = urllib2.Request(url, data)
                        response = urllib2.urlopen(req)
                        client.publish(topic='a/b', payload=name)
                    elif (name == 'lottesand'):
                        name = 'product2_put_json.do'
                        url = 'http://61.253.199.32/' + name
                        req = urllib2.Request(url, data)
                        response = urllib2.urlopen(req)
                        client.publish(topic='a/b', payload=name)
                    elif (name == 'orangejuice'):
                        name = 'product3_put_json.do'
                        url = 'http://61.253.199.32/' + name
                        req = urllib2.Request(url, data)
                        response = urllib2.urlopen(req)
                        client.publish(topic='a/b', payload=name)
                    elif (name == 'postick'):
                        name = 'product4_put_json.do'
                        url = 'http://61.253.199.32/' + name
                        req = urllib2.Request(url, data)
                        response = urllib2.urlopen(req)
                        client.publish(topic='a/b', payload=name)
                    os = False
                    ws = False
                    obname = ''
                else:
                    os = False
                    sname = name

    elif state == 'Object':
        if ws:
            name = event['name']
            if name == sname:
                values = {'af120_idx': fname}
                data = urllib.urlencode(values)
                if (name == 'zapagatty'):
                    name = 'product1_pick_json.do'
                    url = 'http://61.253.199.32/' + name
                    req = urllib2.Request(url, data)
                    response = urllib2.urlopen(req)
                    client.publish(topic='a/b', payload=name)
                elif (name == 'lottesand'):
                    name = 'product2_pick_json.do'
                    url = 'http://61.253.199.32/' + name
                    req = urllib2.Request(url, data)
                    response = urllib2.urlopen(req)
                    client.publish(topic='a/b', payload=name)
                elif (name == 'orangejuice'):
                    name = 'product3_pick_json.do'
                    url = 'http://61.253.199.32/' + name
                    req = urllib2.Request(url, data)
                    response = urllib2.urlopen(req)
                    client.publish(topic='a/b', payload=name)
                elif (name == 'postick'):
                    name = 'product4_pick_json.do'
                    url = 'http://61.253.199.32/' + name
                    req = urllib2.Request(url, data)
                    response = urllib2.urlopen(req)
                    client.publish(topic='a/b', payload=name)

            ws = False
            sname = ''
        else:
            os = True
            obname = event['name']

    elif state == 'Face':
        x = event['name']
        if x == '2':
            values = {'af120_idx': x}
            data = urllib.urlencode(values)
            name = 'product2_pick_json.do'
            url = 'http://61.253.199.32/' + name
            req = urllib2.Request(url, data)
            response = urllib2.urlopen(req)
            client.publish(topic='a/b', payload=name)

    return