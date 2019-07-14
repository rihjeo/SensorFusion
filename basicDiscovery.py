# /*
# * Copyright 2010-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# *
# * Licensed under the Apache License, Version 2.0 (the "License").
# * You may not use this file except in compliance with the License.
# * A copy of the License is located at
# *
# *  http://aws.amazon.com/apache2.0
# *
# * or in the "license" file accompanying this file. This file is distributed
# * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# * express or implied. See the License for the specific language governing
# * permissions and limitations under the License.
# */


import os
import sys
import serial
import time
import uuid
import RPi.GPIO as GPIO
import json
import logging
import argparse
import numpy
from AWSIoTPythonSDK.core.greengrass.discovery.providers import DiscoveryInfoProvider
from AWSIoTPythonSDK.core.protocol.connection.cores import ProgressiveBackOffCore
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from AWSIoTPythonSDK.exception.AWSIoTExceptions import DiscoveryInvalidRequestException


EMULATE_HX711 = False

if not EMULATE_HX711:
    from hx711 import HX711
else:
    from emulated_hx711 import HX711

hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")
hx.set_reference_unit(270)

hx.reset()

hx.tare()

hx1 = HX711(13, 19)
hx1.set_reading_format("MSB", "MSB")
hx1.set_reference_unit(270)

hx1.reset()

hx1.tare()

# hx2 = HX711(26, 20)
# hx2.set_reading_format("MSB", "MSB")
# hx2.set_reference_unit(270)

# hx2.reset()

# hx2.tare()

GPIO.setmode(GPIO.BCM)

trig = 2
echo = 3

trig1 = 17
echo1 = 27

# trig2 = 23
# echo2 = 24

GPIO.setup(trig, GPIO.OUT)
GPIO.setup(echo, GPIO.IN)

GPIO.setup(trig1, GPIO.OUT)
GPIO.setup(echo1, GPIO.IN)

# GPIO.setup(trig2, GPIO.OUT)
# GPIO.setup(echo2, GPIO.IN)

AllowedActions = ['both', 'publish', 'subscribe']


# General message notification callback
def customOnMessage(message):
    print('Received message on topic %s: %s\n' % (message.topic, message.payload))


MAX_DISCOVERY_RETRIES = 10
GROUP_CA_PATH = "./groupCA/"

# Read in command-line parameters
parser = argparse.ArgumentParser()
parser.add_argument("-e", "--endpoint", action="store", required=True, dest="host", help="Your AWS IoT custom endpoint")
parser.add_argument("-r", "--rootCA", action="store", required=True, dest="rootCAPath", help="Root CA file path")
parser.add_argument("-c", "--cert", action="store", dest="certificatePath", help="Certificate file path")
parser.add_argument("-k", "--key", action="store", dest="privateKeyPath", help="Private key file path")
parser.add_argument("-n", "--thingName", action="store", dest="thingName", default="Bot", help="Targeted thing name")
parser.add_argument("-t", "--topic", action="store", dest="topic", default="sdk/test/Python", help="Targeted topic")
parser.add_argument("-m", "--mode", action="store", dest="mode", default="both",
                    help="Operation modes: %s" % str(AllowedActions))
parser.add_argument("-M", "--message", action="store", dest="message", default="Hello World!",
                    help="Message to publish")

args = parser.parse_args()
host = args.host
rootCAPath = args.rootCAPath
certificatePath = args.certificatePath
privateKeyPath = args.privateKeyPath
clientId = args.thingName
thingName = args.thingName
topic = args.topic

if args.mode not in AllowedActions:
    parser.error("Unknown --mode option %s. Must be one of %s" % (args.mode, str(AllowedActions)))
    exit(2)

if not args.certificatePath or not args.privateKeyPath:
    parser.error("Missing credentials for authentication.")
    exit(2)

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Progressive back off core
backOffCore = ProgressiveBackOffCore()

# Discover GGCs
discoveryInfoProvider = DiscoveryInfoProvider()
discoveryInfoProvider.configureEndpoint(host)
discoveryInfoProvider.configureCredentials(rootCAPath, certificatePath, privateKeyPath)
discoveryInfoProvider.configureTimeout(10)  # 10 sec

retryCount = MAX_DISCOVERY_RETRIES
discovered = False
groupCA = None
coreInfo = None
while retryCount != 0:
    try:
        discoveryInfo = discoveryInfoProvider.discover(thingName)
        caList = discoveryInfo.getAllCas()
        coreList = discoveryInfo.getAllCores()

        # We only pick the first ca and core info
        groupId, ca = caList[1]
        coreInfo = coreList[1]
        print("Discovered GGC: %s from Group: %s" % (coreInfo.coreThingArn, groupId))

        print("Now we persist the connectivity/identity information...")
        groupCA = GROUP_CA_PATH + groupId + "_CA_" + str(uuid.uuid4()) + ".crt"
        if not os.path.exists(GROUP_CA_PATH):
            os.makedirs(GROUP_CA_PATH)
        groupCAFile = open(groupCA, "w")
        groupCAFile.write(ca)
        groupCAFile.close()

        discovered = True
        print("Now proceed to the connecting flow...")
        break
    except DiscoveryInvalidRequestException as e:
        print("Invalid discovery request detected!")
        print("Type: %s" % str(type(e)))
        print("Error message: %s" % e.message)
        print("Stopping...")
        break
    except BaseException as e:
        print("Error in discovery!")
        print("Type: %s" % str(type(e)))
        print("Error message: %s" % e.message)
        retryCount -= 1
        print("\n%d/%d retries left\n" % (retryCount, MAX_DISCOVERY_RETRIES))
        print("Backing off...\n")
        backOffCore.backOff()

if not discovered:
    print("Discovery failed after %d retries. Exiting...\n" % (MAX_DISCOVERY_RETRIES))
    sys.exit(-1)

# Iterate through all connection options for the core and use the first successful one
myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
myAWSIoTMQTTClient.configureCredentials(groupCA, privateKeyPath, certificatePath)
myAWSIoTMQTTClient.onMessage = customOnMessage

connected = False
for connectivityInfo in coreInfo.connectivityInfoList:
    currentHost = connectivityInfo.host
    currentPort = connectivityInfo.port
    print("Trying to connect to core at %s:%d" % (currentHost, currentPort))
    myAWSIoTMQTTClient.configureEndpoint(currentHost, currentPort)
    try:
        myAWSIoTMQTTClient.connect()
        connected = True
        break
    except BaseException as e:
        print("Error in connect!")
        print("Type: %s" % str(type(e)))
        print("Error message: %s" % e.message)

if not connected:
    print("Cannot connect to core %s. Exiting..." % coreInfo.coreThingArn)
    sys.exit(-2)

# Successfully connected to the corclient.publish(topic='a/b', payload='Weight')e
if args.mode == 'both' or args.mode == 'subscribe':
    myAWSIoTMQTTClient.subscribe(topic, 0, None)
time.sleep(2)

dtemp = 0
wtemp = 0
dav = 0
dtav = 0
daver = []


dtemp1 = 0
wtemp1 = 0
dav1 = 0
dtav1 = 0
daver1 = []

count = 0
count1 = 0
threshold = 5


try:
    while True:
        if args.mode == 'both' or args.mode == 'publish':
            GPIO.output(trig, False)
            time.sleep(0.1)

            GPIO.output(trig, True)
            time.sleep(0.00001)
            GPIO.output(trig, False)

            while GPIO.input(echo) == 0:
                pulse_start = time.time()
            while GPIO.input(echo) == 1:
                pulse_end = time.time()

            pulse_duration = pulse_end - pulse_start
            distance = pulse_duration * 17000
            distance = round(distance, 2)

            val = hx.get_weight(1)
            message = {}
            if (count == 0):
                dtemp = distance
                dtav = distance
                wtemp = val
                #wtav = val
                count += 1
            
            if(len(daver) == 3):
                daver.remove(daver[0])
                daver.append(distance)
            elif(len(daver) < 3):
                daver.append(distance)
                
            """if(len(waver) == 10):
                waver.remove(waver[0])
                waver.append(val)
            elif(len(waver) < 10):
                waver.append(val)"""
            
            dav = numpy.mean(daver)
            #wav = numpy.mean(waver)
            
            if dav - dtav < threshold and dav - dtav > -threshold:
                if dav - dtav < 0.5 and dav - dtav > -0.5 and dav - dtemp > 7 and val - wtemp < -20:
                    message['pp'] = "pick"
                    message['state'] = "Sensor"
                    message['name'] = "zapagatty"
                    message['ds'] = "o"
                    message['ws'] = "o"
                    messageJson = json.dumps(message)
                    myAWSIoTMQTTClient.publish(topic, messageJson, 0)
                    if args.mode == 'publish':
                        print('1:Published topic %s: %s\n' % (topic, messageJson))
                    dtemp = dav
                    wtemp = val
                elif dav - dtav < 0.5 and dav - dtav > -0.5 and dav - dtemp < -7 and val - wtemp > 20:
                    message['pp'] = "put"
                    message['state'] = "Sensor"
                    message['name'] = "zapagatty"
                    message['ds'] = "o"
                    message['ws'] = "o"
                    messageJson = json.dumps(message)
                    myAWSIoTMQTTClient.publish(topic, messageJson, 0)
                    if args.mode == 'publish':
                        print('1:Published topic %s: %s\n' % (topic, messageJson))
                    dtemp = dav
                    wtemp = val
                elif dav - dtav < 0.5 and dav - dtav > -0.5 and val - wtemp < -40:
                    message['pp'] = "pick"
                    message['state'] = "Sensor"
                    message['name'] = "zapagatty"
                    message['ds'] = "x"
                    message['ws'] = "o"
                    messageJson = json.dumps(message)
                    myAWSIoTMQTTClient.publish(topic, messageJson, 0)
                    if args.mode == 'publish':
                        print('1:Published topic %s: %s\n' % (topic, messageJson))
                    wtemp = val
                
                elif dav - dtav < 0.5 and dav - dtav > -0.5 and val - wtemp > 40:
                    message['pp'] = "put"
                    message['state'] = "Sensor"
                    message['name'] = "zapagatty"
                    message['ds'] = "x"
                    message['ws'] = "o"
                    messageJson = json.dumps(message)
                    myAWSIoTMQTTClient.publish(topic, messageJson, 0)
                    if args.mode == 'publish':
                        print('1:Published topic %s: %s\n' % (topic, messageJson))
                    wtemp = val



            #wtav = wav
            dtav = dav
            
            hx.power_down()
            hx.power_up()

            GPIO.output(trig1, False)
            time.sleep(0.5)

            GPIO.output(trig1, True)
            time.sleep(0.00001)
            GPIO.output(trig1, False)

            while GPIO.input(echo1) == 0:
                pulse_start1 = time.time()
            while GPIO.input(echo1) == 1:
                pulse_end1 = time.time()

            pulse_duration1 = pulse_end1 - pulse_start1
            distance1 = pulse_duration1 * 17000
            distance1 = round(distance1, 2)

            val1 = hx1.get_weight(1)
            message = {}
            if (count1 == 0):
                dtemp1 = distance1
                dtav1 = distance1
                wtemp1 = val1
                #wtav = val
                count1 += 1
            
            if(len(daver1) == 3):
                daver1.remove(daver1[0])
                daver1.append(distance1)
            elif(len(daver1) < 3):
                daver1.append(distance1)

            dav1 = numpy.mean(daver1)
            #wav = numpy.mean(waver)
            
            if dav1 - dtav1 < threshold and dav1 - dtav1 > -threshold:
                if dav1 - dtav1 < 0.5 and dav1 - dtav1 > -0.5 and dav1 - dtemp1 > 7 and val1 - wtemp1 < -20:
                    message['pp'] = "pick"
                    message['state'] = "Sensor"
                    message['name'] = "lottesand"
                    message['ds'] = "o"
                    message['ws'] = "o"
                    messageJson = json.dumps(message)
                    myAWSIoTMQTTClient.publish(topic, messageJson, 0)
                    if args.mode == 'publish':
                        print('2:Published topic %s: %s\n' % (topic, messageJson))
                    dtemp1 = dav1
                    wtemp1 = val1
                elif dav1 - dtav1 < 0.5 and dav1 - dtav1 > -0.5 and dav1 - dtemp1 < -7 and val1 - wtemp1 > 20:
                    message['pp'] = "put"
                    message['state'] = "Sensor"
                    message['name'] = "lottesand"
                    message['ds'] = "o"
                    message['ws'] = "o"
                    messageJson = json.dumps(message)
                    myAWSIoTMQTTClient.publish(topic, messageJson, 0)
                    if args.mode == 'publish':
                        print('2:Published topic %s: %s\n' % (topic, messageJson))
                    dtemp1 = dav1
                    wtemp1 = val1
                elif dav1 - dtav1 < 0.5 and dav1 - dtav1 > -0.5 and val1 - wtemp1 < -40:
                    message['pp'] = "pick"
                    message['state'] = "Sensor"
                    message['name'] = "lottesand"
                    message['ds'] = "x"
                    message['ws'] = "o"
                    messageJson = json.dumps(message)
                    myAWSIoTMQTTClient.publish(topic, messageJson, 0)
                    if args.mode == 'publish':
                        print('2:Published topic %s: %s\n' % (topic, messageJson))
                    wtemp1 = val1
                elif dav1 - dtav1 < 0.5 and dav1 - dtav1 > -0.5 and val1 - wtemp1 > 40:
                    message['pp'] = "put"
                    message['state'] = "Sensor"
                    message['name'] = "lottesand"
                    message['ds'] = "x"
                    message['ws'] = "o"
                    messageJson = json.dumps(message)
                    myAWSIoTMQTTClient.publish(topic, messageJson, 0)
                    if args.mode == 'publish':
                        print('2:Published topic %s: %s\n' % (topic, messageJson))
                    wtemp1 = val1


            dtav1 = dav1
            hx1.power_down()
            hx1.power_up()

        # time.sleep(0.5)

except KeyboardInterrupt:
    GPIO.cleanup()
