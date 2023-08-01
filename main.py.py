import time
from umqttsimple import MQTTClient
from hcsr04 import HCSR04
from time import sleep
import ubinascii
import machine
import micropython
import network
import esp
from machine import Pin
import dht

esp.osdebug(None)
import gc
gc.collect()

ssid = 'DESKTOP-I2S0M9H 9142'
password = '12345678'
mqtt_server = 'test.mosquitto.org'

client_id = ubinascii.hexlify(machine.unique_id())

topic_pub_temp = b'esp/dht/temperature'
topic_pub_dis = b'esp/dht/distance'

last_message = 0
message_interval = 5
counter = 0

station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(ssid, password)

while not station.isconnected():
    pass

print('Connection successful')

sensor = dht.DHT22(Pin(14))
sensor1 = HCSR04(trigger_pin=5, echo_pin=18, echo_timeout_us=10000)


def connect_mqtt():
    global client_id, mqtt_server
    client = MQTTClient(client_id, mqtt_server)
    client.connect()
    print('Connected to %s MQTT broker' % mqtt_server)
    return client


def restart_and_reconnect():
    print('Failed to connect to MQTT broker. Reconnecting...')
    time.sleep(10)
    machine.reset()


def read_sensor():
    try:
        sensor.measure()
        temp = int(sensor.temperature())
        hum = int(sensor.humidity())
        if isinstance(temp, (int, float)) and isinstance(hum, (int, float)):
            return temp
        else:
            return None
    except OSError as e:
        return None


try:
    client = connect_mqtt()
except OSError as e:
    restart_and_reconnect()

while True:
    try:
        if (time.time() - last_message) > message_interval:
            temp = read_sensor()
            distance = int(sensor1.distance_cm())
            print(temp)
            print(distance)
            if temp is not None and distance is not None:
                if temp < 40 and distance < 30:
                    availability = b'Coke is available'
                else:
                    availability = b'Coke is not available'

                print(availability)

                client.publish(b'esp/coke/availability', availability)
                client.publish(topic_pub_temp, str(temp).encode())
                client.publish(topic_pub_dis, str(distance).encode())
                last_message = time.time()
                counter += 1
    except OSError as e:
        restart_and_reconnect()
