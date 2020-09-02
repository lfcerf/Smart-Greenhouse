# Smart Greenhouse
# Created by 
# - Luigi F. Cerfeda - Head of Sales at Zerynth
# - Stefano Torneo - Software Developer at Zerynth

######## IMPORT LIBRARIES ########

import streams
import mcu # to use low level microcontroller functionalities
import adc # analog to digital converter

import config # configuration file, where there are the parameters to modify

import pwm # PWM library, to operate the fan

from servo import servo # library to use servomotor

from bosch.bme280 import bme280 # library for digital weather sensor (attached to board)
from stm.hts221 import hts221 # library for digital internal weather sensor (present into board)

from rohm.bh1750fvi import bh1750fvi # library for ambient light (present into board)

from bsp.drivers import wifi

import json
from zdm import zdm  # Zerynth Device Manager

from genann import genann # library for AI

######## END IMPORT LIBRARIES ######## 

### UTILITY FUNCTIONS
def servomotor_on():
    
    print("Servo ON")
    MyServo.attach()
    
    print("Servo controlled in degrees")
    sleep(100)
    MyServo.moveToDegree(0)
    sleep(1000)
    MyServo.moveToDegree(config.end_angle)
    
def servomotor_off():
    print("servo OFF")
    MyServo.detach()

interface = None
device = None
wifi_status = False
tag_dataset = 0

def connect_wifi_zdm():
    global wifi_status, device
    try:
        print("Connecting to wifi...")
        # Connect to wifi
        interface.link(config.WIFI_SSID, interface.WIFI_WPA2, config.WIFI_PW)
        if (device == None):
            # Create a ZDM Device
            device = zdm.Device(jobs_dict=my_jobs)
        # Connect the device to the ZDM
        device.connect()
        wifi_status = True
    except Exception as e:
        print("No Wifi connection")
        wifi_status = False
    
def check_connection():
    global wifi_status
    wifi_status = interface.is_linked()
    return wifi_status

def pub_data_MAST():
    global device
    print('------ publish data MAST ------')
    print('    External temperature     :', ext_temp)
    print('    External humidity        :', ext_hum)
    print('    Internal temperature     :', int_temp)
    print('    Internal humidity        :', int_hum)
    print('    Internal pressure        :', int_pres)
    print('    Soil                     :', soil)
    print('    Light                    :', light)
    print('    Irrigation status        :', irrigation_status)
    print('    Fan status               :', fan_status)
    print('    Dataset tag              :', tag_dataset)
    print('-------------------------------')
    tag = "MAST"
    payload = {'external_temp': ext_temp, 'external_humidity': ext_hum, 'internal_temp': int_temp, 'internal_humidity': int_hum, 'internal_pressure': int_pres, 'soil': soil, 'light': light, 'irrigation_status': irrigation_status, "fan_status": fan_status, "tag_dataset": tag_dataset}
    device.publish(payload, tag)

def pub_data_Ubidots():
    global device
    print('------ publish data UBIDOTS ------')
    print('    Soil                     :', soil)
    print('    Irrigation status        :', irrigation_status)
    print('-------------------------------')
    tag_ubi = "UBIDOTS"
    payload_ubi = {'soil': soil, 'irrigation_status': irrigation_status}
    device.publish(payload_ubi, tag_ubi)

### END UTILITY FUNCTIONS

######## SETUP

# create a stream linked to the default serial port
streams.serial() 

pinMode(config.led_irr, OUTPUT) # configure the irrigation LED
pinMode(config.fan_pin, OUTPUT) # configure the fan module
MyServo = servo.Servo(config.servomotor_pin) # configure the servomotor module
pinMode(config.light_led, OUTPUT) # configure the light LED
pinMode(config.button_pin, INPUT_PULLUP) # configure the button to tag dataset

try:
    # Setup weather sensor 
    print("start weather sensor...")
    weather_int = bme280.BME280(I2C1) #SDA1 -> D21; SCL1 -> D22
    weather_ext = hts221.HTS221(I2C0, D2)
    print("Ready!")
    print("--------------------------------------------------------")
except Exception as e:
    print("Error: ",e)
    mcu.reset()

try:
    # Setup ambient light sensor 
    print("start ambient light sensor...")
    light_sensor = bh1750fvi.BH1750FVI(I2C0)
    print("Ready!")
    print("--------------------------------------------------------")
except Exception as e:
    print("Error: ",e)
    mcu.reset()
    
######## END SETUP

######## ARTIFICIAL INTELLIGENCE

# create an ANN object
ann = genann.ANN()

# set the layers: 5 inputs, 1 output, 1 hidden layer of 5 neurons
ann.create(5, 1, 1, 5)
weights = config.weights
print(weights)
# set the weights
ann.set_weights(weights)

######## END ARTIFICIAL INTELLIGENCE

##### JOBS

def job_update_weights(obj, arg):
    global weights
    # print(arg)
    weights = arg["weights"] # {"weights": [-1.777,-5.734,-6.029,-4.460,-3.261,-3.172,2.444,-6.581,5.826] }
    print("weights ->",weights)
    ann.set_weights(weights)
    return 'weights received'

# you can call job_update_weights method using rpc
my_jobs = {
    'job_update_weights': job_update_weights,
}

#### END JOBS

### CONNECT

print("Init wifi...")
wifi.init()
# Create a Wifi interface
interface = wifi.interface()
# Connect to wifi and zdm
connect_wifi_zdm()
    
### END CONNECT

### Main loop


try:
    
    cont_pub_mast = 0
    cont_pub_ub = 0
    
    while True:
        
        try:
            ext_temp, ext_hum = weather_ext.get_temp_humidity()
            print("--------------------------------------------------------")
            print("EXTERNAL VALUES")
            print("Temperature:", ext_temp, "C")
            print("Humidity:", ext_hum, "%")
                
            int_temp, int_hum, int_pres = weather_int.get_values()
            print("--------------------------------------------------------")
            print("INTERNAL VALUES")
            print("Temperature:", int_temp, "C")
            print("Humidity:", int_hum, "%")
            print("Pressure:", int_pres, "hPa")
                
            if int_temp > config.threshold_temp:
                fan_status = 1
                pwm.write(config.fan_pin, 2, 1) # turn on the fan
            else:
                fan_status = 0
                pwm.write(config.fan_pin,0,0) # turn off the fan
            print("fan_status", fan_status)
                
            print("--------------------------------------------------------")
        except Exception as e:
            print("weather sensor err", e)
                
        tag_dataset = digitalRead(config.button_pin)
        print("tag_dataset: ", tag_dataset)
        
        # Acquisition of data from sensors
        soil = adc.read(config.soil_pin) # soil moisture
        light = light_sensor.get_value() # ambient light
        
        if soil > config.threshold_soil:
            irrigation_status = 1
            digitalWrite(config.led_irr, HIGH)
            servomotor_on()
        else:
             irrigation_status = 0
             digitalWrite(config.led_irr, LOW)
             servomotor_off()
        
        if (light > config.threshold_light):
            digitalWrite(config.light_led, HIGH)  # turn the LED ON by setting the voltage HIGH
        else:
            digitalWrite(config.light_led, LOW)   # turn the LED OFF by setting the voltage LOW
        
        # NEURAL NETWORK
            
        '''input_set =  [soil, ext_temp, light, ext_hum, int_pres] # define the inputs
            
        input_set = [k*1.0 for k in input_set] # ann.run() wants float
    
        print("Input set", input_set)
            
        # run the network
        out = ann.run(input_set)
        print("Result ANN",out)
        
        if out[0] > 0.45:
            irrigation_status = 1
            digitalWrite(config.led_irr, HIGH)
        else:
            irrigation_status = 0
            digitalWrite(config.led_irr, LOW)'''
            
        print("--------------------------------------------------------")
        print("Soil Humidity:", soil)
        print("Light:", light)
        print("irrigation_status", irrigation_status)
        print("--------------------------------------------------------")
        
        # publish data on ZDM
        if (cont_pub_mast >= config.t_pub_mast):
            # check status of wifi connection
            if (not check_connection()):
                connect_wifi_zdm() # if no wifi connection then try to connect
            
            # check again status connection and if ok then publish data
            if (wifi_status == 1):
    
                try:
                    pub_data_MAST()
                except Exception as e:
                    print("pub data MAST error: ", e)
                    
                cont_pub_mast = 0
        else:
            cont_pub_mast += 1
        
        # publish data on Ubidots
        if (cont_pub_ub >= config.t_pub_ub):
            # check status of wifi connection
            if (not check_connection()):
                connect_wifi_zdm() # if no wifi connection then try to connect
            
            # check again status connection and if ok then publish data
            if (wifi_status == 1):
    
                try:
                    pub_data_Ubidots()
                except Exception as e:
                    print("pub data Ubidots error: ", e)
                    
                cont_pub_ub = 0
        else:
            cont_pub_ub += 1
        
        sleep(config.t_acq)
        
except Exception as e:
    print("main loop error: ",e)
