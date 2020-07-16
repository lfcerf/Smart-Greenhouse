# Smart Greenhouse
# Created by Luigi F. Cerfeda - Head of Sales at Zerynth

######## IMPORT LIBRARIES ########

import streams
import adc # analog to digital converter

import config #file di configurazione, dove ci sono i parametri da modificare

import pwm # lilbreria PWM, per azionare ventola

from bosch.bme280 import bme280 # digital weather sensor

from wireless import wifi
from espressif.esp32net import esp32wifi as wifi_driver

import json
from zdm import zdm  # Zerynth Device Manager

from genann import genann # libreria intelligenza artificiale


######## END IMPORT LIBRARIES ######## 


######## SETUP

# create a stream linked to the default serial port
streams.serial() 

pinMode(config.led_irr,OUTPUT) # irrigation LED
pinMode(config.fan_pin,OUTPUT) # fan module


try:
    # Setup weather sensor 
    print("start weather sensor...")
    weather = bme280.BME280(I2C1) #SDA1 -> D32; SCL1 -> D33
    print("Ready!")
    print("--------------------------------------------------------")
except Exception as e:
    print("Error: ",e)

######## END SETUP

######## ARTIFICIAL INTELLIGENCE

# create an ANN object
ann = genann.ANN()

# set the layers: 2 inputs, 1 output, 1 hidden layer of 2 neurons
ann.create(2,1,1,2)
weights = [-1.777,-5.734,-6.029,-4.460,-3.261,-3.172,2.444,-6.581,5.826]
# set the weights of a pretrained XOR model (https://github.com/codeplea/genann/blob/master/example/xor.ann)
ann.set_weights(weights)

######## END ARTIFICIAL INTELLIGENCE

##### JOBS

def job_update_weights(obj, arg):
    global weights
    # print(arg)
    weights = arg["args"]["weights"] # {"weights": [-1.777,-5.734,-6.029,-4.460,-3.261,-3.172,2.444,-6.581,5.826] }
    print("weights ->",weights)
    ann.set_weights(weights)
    return 'weights received'


# you can call job_update_weights method using rpc
my_jobs = {
    'job_update_weights': job_update_weights,
}

#### END JOBS

### Connect

wifi_driver.auto_init()

for _ in range(3):
    try:
        print("connect wifi")
        # Write here your wifi SSID and password
        wifi.link(config.WIFI_SSID, wifi.WIFI_WPA2, config.WIFI_PW)
        print("connect wifi done")
        break
    except Exception as e:
        print("wifi connect err", e)

try:
    # create a ZDM Device instance with your device id
    device = zdm.Device(config.device_id, jobs_dict=my_jobs)
    # set the device's password (jwt)
    device.set_password(config.password)
    # connect your device to ZDM enabling the device to receive incoming messages
    device.connect()
except Exception as e:
    print("zdm connect err", e)

def pub_data_MAST():
    print('---- publish data MAST ----')
    tag = "MAST"
    payload = {'temp': temp, 'pressure': pres, 'humidity': hum, 'soil':soil, 'light':light, 'irrigation_status': irrigation_status, "fan_status": fan_status}
    device.publish(json.dumps(payload), tag)
    print("--------------------------------------------------------")



def pub_data_Ubidots():
    print('---- publish data UBIDOTS ----')
    tag_ubi = "UBIDOTS"
    payload_ubi = {'soil':soil, 'irrigation_status': irrigation_status}
    device.publish(json.dumps(payload_ubi), tag_ubi)


### Main loop

try:
    while True:
       
        # Acquisizione dati da sensori
        soil = adc.read(config.soil_pin) # soil moisture
        light = adc.read(config.light_pin) # light sensor
        
        if soil<config.soglia_soil:
            irrigation_status = 1
            digitalWrite(config.led_irr, HIGH)
        else:
            irrigation_status = 0
            digitalWrite(config.led_irr, LOW)

        print("--------------------------------------------------------")
        print("Soil Humidity:",soil)
        print("Light:", light)
        print("irrigation_status", irrigation_status)
        print("--------------------------------------------------------")
        
        try:
            temp, hum, pres = weather.get_values()
            print("Temperature:", temp, "C")
            print("Humidity:", hum, "%")
            print("Pressure:", pres, "hPa")
            
            if hum > config.soglia_hum:
                fan_status = 1
                pwm.write(config.fan_pin,2,1)
            else:
                fan_status = 0
                pwm.write(config.fan_pin,0,0)
            print("fan_status", fan_status)
            print("--------------------------------------------------------")
        except Exception as e:
            print("weather sensor err", e)
        
        
        try:
            pub_data_Ubidots()
        except Exception as e:
            print("pub data Ubidots error: ",e)
        
        try:
            pub_data_MAST()
        except Exception as e:
            print("pub data MAST error: ",e)
        
        sleep(1000)
        
except Exception as e:
    print("main loop error: ",e)
