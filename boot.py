from network import LoRa
import ubinascii
import machine
import os
import pycom

 
# Configure  UART bus 
# Pin P3 on Expansion board to TX1 on the Arduino Uno
# Pin P4 on Expansion board to RX1 on the Arduino Uno
uart1 = machine.UART(1, baudrate=9600)
pycom.heartbeat(False)
machine.main("main.py")

# Initial boot of the lora settings on the device to retrieve the DevEUI and AppEUI for The Things Network end device registration.
lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868)
print("DevEUI: %s" % (ubinascii.hexlify(lora.mac()).decode('ascii')))
print("AppEUI: %s" % (ubinascii.hexlify(machine.unique_id())))
print('==========Starting main.py for the GY-521 Node==========\n')



