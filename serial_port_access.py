import time
import serial

ser = serial.Serial(port='COM4', baudrate=115200, bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
ser.write("[1D100\r".encode('utf-8'))
# ser.open()
while True:
    # time.sleep(0.1)
    # s = ser.read(1)
    # hex_string = s.hex()
    # dec = int(hex_string, 16)
    # if dec < 128:
    #     ascii = chr(dec)
    # else:
    #     ascii = ""
    # print("Hex {} / Decimal {} / Char {}".format(hex_string, dec, ascii))

    s = ser.readline()
    print(s)