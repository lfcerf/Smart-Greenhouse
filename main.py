# Smart Greenhouse
# Created by 
# - Luigi F. Cerfeda - Head of Sales at Zerynth
# - Stefano Torneo - Software Developer at Zerynth

######## IMPORT LIBRARIES ########

import streams
import adc # analog to digital converter
import config # configuration file, where there are the parameters to modify
import pwm # PWM library, to operate the fan
from servo import servo # library to use servomotor
from bosch.bme280 import bme280 # library for digital weather sensor (attached to board)
from rohm.bh1750fvi import bh1750fvi # library for ambient light (present into board)
from bsp.drivers import wifi
import json
from zdm import zdm  # Zerynth Device Manager
from genann import genann # library for AI

######## END IMPORT LIBRARIES ######## 

### UTILITY FUNCTIONS

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
        wifi_status = True
    except Exception as e:
        print("No Wifi connection")
        wifi_status = False
    try:
        if (device == None):
            # Create a ZDM Device
            device = zdm.Device(jobs_dict=my_jobs)
        # Connect the device to the ZDM
        device.connect()
    except Exception as e:
        print("No ZDM Connection")
    

def check_connection():
    global wifi_status
    wifi_status = interface.is_linked()
    return wifi_status

def pub_data_ZDM():
    global device
    tag = "ZDM"
    payload = {"temperature": temp, "humidity": hum, "pressure": pres, 'soil': soil, 'light': light, 'irrigation_status': servo_status, "fan_status": fan_status, "tag_dataset": tag_dataset}
    try: 
        device.publish(payload, tag)
        print("--------------------------------------------------------")
        print('------------- published data with tag ZDM --------------')
        print("--------------------------------------------------------")
    except Exception as e:
        print(e)


def pub_data_Ubidots():
    global device
    tag_ubi = "UBIDOTS"
    payload_ubi = {'soil': soil, 'servo_status': servo_status}
    try:
        device.publish(payload_ubi, tag_ubi)
        print("--------------------------------------------------------")
        print('------------- published data with tag UBIDOTS ----------')
        print("--------------------------------------------------------")
    except Exception as e:
        print(e)

### END UTILITY FUNCTIONS

######## SETUP


# create a stream linked to the default serial port
streams.serial() 

pinMode(config.led_irr, OUTPUT) # configure the irrigation LED
pinMode(config.fan_pin, OUTPUT) # configure the fan module
pinMode(config.button_pin, INPUT_PULLUP) # configure the button to tag dataset

MyServo = servo.Servo(config.servomotor_pin) # configure the servomotor module
MyServo.attach()

try:
    # Setup weather sensor 
    print("start weather sensor...")
    weather = bme280.BME280(I2C1) #SDA1 -> D21; SCL1 -> D22
    print("Ready!")
    print("--------------------------------------------------------")
except Exception as e:
    print("Error: ",e)

try:
    # Setup ambient light sensor 
    print("start ambient light sensor...")
    light_sensor = bh1750fvi.BH1750FVI(I2C0)
    print("Ready!")
    print("--------------------------------------------------------")
except Exception as e:
    print("Error: ",e)

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
    
    cont_pub_zdm = 0
    cont_pub_ub = 0
    
    while True:
        
        try:
            temp, hum, pres = weather.get_values()
            
            if temp > config.threshold_temp:
                fan_status = 1
                pwm.write(config.fan_pin, 2, 1) # turn on the fan
            else:
                fan_status = 0
                pwm.write(config.fan_pin,0,0) # turn off the fan
                
            print("--------------------------------------------------------")
            print("Temperature:", temp, "C")
            print("Humidity:", hum, "%")
            print("Pressure:", pres, "hPa")
            print("Fan Status", fan_status)
            print("--------------------------------------------------------")
        except Exception as e:
            print("weather sensor err", e)
        
        try:
            soil = adc.read(config.soil_pin) # soil moisture
            light = light_sensor.get_value() # ambient light
        except Exception as e:
            print("light sensor err", e)
            
        if soil > config.threshold_soil:
            servo_status = 1
            digitalWrite(config.led_irr, HIGH)
            MyServo.moveToDegree(config.end_angle)

        else:
            servo_status = 0
            digitalWrite(config.led_irr, LOW)
            MyServo.moveToDegree(0)
        
        print("--------------------------------------------------------")
        print("Soil Humidity:", soil)
        print("Light:", light)
        print("Servo Status", servo_status)
        print("--------------------------------------------------------")
        
            
        tag_dataset = digitalRead(config.button_pin)
        print("--------------------------------------------------------")
        print("Dataset Tag: ", tag_dataset)
        print("--------------------------------------------------------")
        
        # NEURAL NETWORK
            
        '''input_set =  [soil, temp, light, hum, pres] # define the inputs
            
        input_set = [k*1.0 for k in input_set] # ann.run() wants float
    
        print("Input set", input_set)
            
        # run the network
        out = ann.run(input_set)
        print("Result ANN",out)
        
        if out[0] > 0.45:
            servo_status = 1
            digitalWrite(config.led_irr, HIGH)
            MyServo.moveToDegree(config.end_angle)
        else:
            servo_status = 0
            digitalWrite(config.led_irr, LOW)
            MyServo.moveToDegree(0)'''
            
        # publish data on ZDM
        if cont_pub_zdm >= config.t_pub_zdm:
            # check status of wifi connection
            if (not check_connection()):
                connect_wifi_zdm() # if no wifi connection then try to connect
            
            # check again status connection and if ok then publish data
            if wifi_status == 1:
    
                try:
                    pub_data_ZDM()
                except Exception as e:
                    print("pub data ZDM error: ", e)
                    
                cont_pub_zdm = 0
        else:
            cont_pub_zdm += 1
        
        # publish data on Ubidots
        if cont_pub_ub >= config.t_pub_ub:
            # check status of wifi connection
            if (not check_connection()):
                connect_wifi_zdm() # if no wifi connection then try to connect
            
            # check again status connection and if ok then publish data
            if wifi_status == 1:
    
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
