led_irr = LED0 # pin attached to LED that indicates irrigation need
fan_pin = D19.PWM # pin attached to fan module
servomotor_pin = D23.PWM # pin attached to servomotor module
soil_pin = A7 # pin attached to soil module (it is the D39 on pinmap)
button_pin = D5 # pin of button to tag dataset

t_acq = 2000 # measurement every t_acq milliseconds
t_pub_zdm = 5 # publish every t_acq*t_pub_mast seconds
t_pub_ub = 15 # publish every t_acq*t_pub_ub seconds

### CHANGES THESE PARAMETERS

WIFI_SSID = ""
WIFI_PW = ""

threshold_temp = 30 # if temp > threshold then activate fan
threshold_soil = 2500 # if soil > threshold then activate servo

end_angle = 180 # end angle of servomotor

# weights = [random(1,10)/random(1,10) for i in range(36)] #36 weights
weights = [-0.065, 0.231, -0.042, -0.272, -0.01, -0.039, 
0.271, 0.482, 0.341, -0.113, 0.396, 0.216, 
0.321, -0.137, -0.307, -0.035, -0.207, 0.461, 
0.265, 0.321, 0.006, -0.139, 0.259, -0.449,
-0.103, -0.436, 0.22, -0.019, 0.272, -0.224,
0.263, -0.348, -0.383, -0.36, 0.303, 0.016]

