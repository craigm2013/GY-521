from network import LoRa
import socket
import time
import ubinascii
import struct
import machine
import os
import pycom


# Function for joining the LoPy4 to the gateway by Over The Air Activation and node functionalities
def OTAA():
    print("OOTA Mode")

    # Creates a lora object, initialises in LoRaWAN mode set to join the European cluster
    lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)

    # create an OTAA authentication parameters, change them to the provided credentials
    app_eui = ubinascii.unhexlify('240ac4c73cf40000')                   # AppEUI (known as the JoinEUI) global application ID, identifies the join server
    app_key = ubinascii.unhexlify('1F864A3048A8F9AF80E60A2DEBFE4508')   # AppKey - encryption key for messages, should be kept secret in implementations
    dev_eui = ubinascii.unhexlify('70b3d5499cdc2fd8')                   # DevEUI - identifier for the device, converted from the 48bit MAC address, inputted in the 

    # Attempts to complete the OOTA transaction, authorising with the previously inputted parameters for the end device.
    lora.join(activation=LoRa.OTAA, auth=(dev_eui, app_eui, app_key), timeout=0)

    # wait until the module has joined the network
    while not lora.has_joined():
        time.sleep(2.5)
        print('Not yet joined...')

    print('Joined')
    # create a LoRa socket
    s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

    # set the LoRaWAN data rate
    s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)

    # make the socket blocking
    # (waits for the data to be sent and for the 2 receive windows to expire)
    s.setblocking(True)

    # Send some placeholder data, this will allow the console to show that the end device is live and will start sending data
    s.send(bytes([0x01, 0x02, 0x03]))
    
    # make the socket non-blocking
    # (because if there's no data received it will block forever...)
    s.setblocking(False)

    # file Payload will be the string that is written to the SD card readings file
    # counter will maintain whether we've read 10 environmental readings
    filePayload = "GY-521 | 70b3d5499cdc2fd8 Sensor Readings"
    counter = 0
    # Proceeds to start the loop from which the Arduino-LoPy will operate continously from
    while True:
        # make the socket blocking
        # (waits for the data to be sent and for the 2 receive windows to expire)
        s.setblocking(True)
        
        # Receieve the values from the readUnoData() function
        payload = readUnoData()

        # If the payload is "n" this means a null reading so we only forward it to the gateway if we have a full reading
        if(payload != "n"):
            if(counter < 11):
                  filePayload = filePayload + "\n" + payload  # String that will accumulate the data readings for writing to the SD card
          
            counter = counter + 1
            
            
            payload = formatPayload(payload)    # Function that will format the payload into strictly numerical values
            print(ubinascii.hexlify(payload))   # Prints the payload locally as hex that TTN console will receieve
            s.send(payload)                     # Transmits the payload over LoRaWAn to the gateway
            
            # If statement that will execute the function responsible to writing the entries to the SD card
            if(counter == 10):
                WriteToSD(filePayload)  
                filePayload = ""         # Clears filePayload    
        else:
            print("idle")   
            time.sleep(4)

        
        # make the socket non-blocking
        # (because if there's no data received it will block forever...)
        s.setblocking(False)

        # Sleeps for 1 second, the Arduino is on a 60 second cycle
        time.sleep(1)

# Function for reading in a reading sent by the Arduino TX, receieved in the LoPy's RX port
def readUnoData():
    # Sets the value from the RX port and explicitly converts it into a string
    x = uart1.readline()
    y = str(x)
    # Start from 2nd character, until from the length of the string -5, cuts off \n at the start and end
    y = y[2:len(y)-5]
    # If it's an empty reading (the arduino still hasn't read recently enough) y will be "n"
    # So we only format the reading if we have values then
    if(y != "n"):
        # This will send the string to the WriteData function which will write it to the on board SD card storage
        return y

    # Else the empty reading was formatted as "n" and we won't forward this to the gateway
    else:
        return("n")

# Function for extracting strictly numerical values from the string
# passed by the Arduino so we can minimise the payload amount, increasing efficiency
def formatPayload(fullReading):
    # Pointer value to keep track how far we are along the string
    pointer = 0
    # Empty array for hosting the reading values
    readings = ""

    # While loop we stay in until pointer equals the length of the reading.
    while pointer < len(fullReading):
        # Element for readings array]
        value = ""
        for c in fullReading:
            if(c == "-"):           # Check whether the value is negative
                value = value + c
            if(c.isdigit()):        # Check whether we are reading a digit
                value = value + c
            if(c == "]"):           # Check when we reach the end of the value
                value = value + c   # Unlike the MLX90393, that stores decimal values
                readings += value   # which can determine where the value ends, we must maintain ] in the payload for the GY-521
                #print(value)       # For error checking
                value = ""
            pointer = pointer + 1   # For every character, we increment until we get to the full length of the reading
    # Returns the values as one big long string
    return readings


# Function to initiate the storage of readings to an SD card, must disconnect RX TX connections to function
def WriteToSD(fileReading):
    pycom.rgbled(0x7f0000)  # Sets RGB Led to red, indicating to disconnect wires.
    time.sleep(10)          # 10 second pause before promptly flashing
    for x in range(5):
        pycom.rgbled(0x0) 
        time.sleep(0.5)
        pycom.rgbled(0x7f0000)  
        time.sleep(0.5)
    for x in range(10):
        pycom.rgbled(0x0) 
        time.sleep(0.25)
        pycom.rgbled(0x7f0000)  
        time.sleep(0.25)     
    
    pycom.rgbled(0x0)  # Turns off LED
    # Try catch so the LoPy doesn't crash if the Arduino hasn't been disconnected
    try:
        sd = machine.SD()
        os.mount(sd, "/sd")
        file = open("/sd/Readings.txt", "w")
        file.write(fileReading)
        file.close()
    except:
        print("SD Card not written to")

    time.sleep(5)

    pycom.rgbled(0xff00) 
    time.sleep(10)
    for x in range(5):
        pycom.rgbled(0x0) 
        time.sleep(0.5)
        pycom.rgbled(0xff00)  
        time.sleep(0.5)
    pycom.rgbled(0x0) # Turns off LED

# Starts the OOTA function and loop
OTAA()
