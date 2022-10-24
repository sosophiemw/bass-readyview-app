import time
import serial

ser = serial.Serial(port='COM7', baudrate=115200, bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
ser.write("[1D100\r".encode('utf-8'))

# For continuous access
while(True):
    s = ser.readline()
    data_string = s.decode("utf-8")
    data = data_string.split(",")
    print(data)
    if(len(data)>5):
        print(data[5])
