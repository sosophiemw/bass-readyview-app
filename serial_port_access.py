import time
import serial

ser = serial.Serial(port='COM4', baudrate=115200, bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
ser.write("[1D100\r".encode('utf-8'))

# For continuous access
while True:
    s = ser.readline()
    print(s)

# Analyze a string
# s = ser.readline()
# print(s)
# data_string = s.decode("utf-8")
# print(data_string)
# data = data_string.split(",")
# print(data)
