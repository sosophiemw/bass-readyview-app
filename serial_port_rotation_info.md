# Accessing Inclinometer via Serial Port

## Intro
Version 5 of the laparoscope has a "TILT-05" Dual-Axis Inclinometer made by
CTi (<https://ctisensors.com/products/tilt-05-oem-inclinometer/>).  It is 
accessed through a serial port.  Here are instructions for accessing the
serial port and interpreting the data.

The following instructions are based on a Windows 10 operating system.

## Installation
### USB Connection
The laparoscope is connected to the computer via USB.  When first connected, 
the operating system will detect a "CP2102N USB to UART Bridge Controller".
The correct drivers for this controller may or may not be installed 
automatically.  How to detect if this was done will be described below.


### `pyserial`
The package `pyserial` is used to access the serial port.
* <https://pypi.org/project/pyserial/>
* <https://pyserial.readthedocs.io/en/latest/>

Install `pyserial` in the virtual environment.

### Verify Serial Port Accessibility
1. Make sure the virtual environment is active and that `pyserial` is 
  installed.
2. Make sure that the laparoscope is NOT connected to the computer.
3. At a command prompt, enter the following command:  
   `python -m serial.tools.list_ports`
4. Make note of the ports shown.  (Note: on my system, `COM1` is displayed.)
5. Connect the laparoscope to the computer via USB.
6. At a command prompt, re-enter `python -m serial.tools.list_ports`.
7. If a new port is displayed, that is the port for the laparoscope.  If a new
   port is not displayed, an updated driver for the USB to UART Bridge 
   Controller needs to be installed.  Install the driver as described below
   and then repeat steps 2 through 6 again.

Note: On my system, the driver needed to be installed.  And, once installed,
a `COM4` port was shown for the inclinometer.

### USB to UART Bridge Controller Driver
If the inclinometer serial port is not detected, an updated driver for the 
USB to UART Bridge Controller may need to be installed.
1. Visit <https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers?tab=downloads>
2. Download the appropriate ZIP file.  For Windows 10 or 11, download the
   `CP210x Universal Windows Driver` file.  
3. Unzip the file.  The driver can be manually installed by following the
   "Manual Install" instructions in the 
   "CP210x_Universal_Windows_Driver_ReleaseNotes.txt" file.  

## Usage
The file `serial_port_access.py` demonstrates how the inclinometer data can
be accessed.  Detailed information on commands sent to the inclinometer and
returned information can be found on the data sheet which can be downloaded
from the CTi website references in the Introduction above.  

First, an instance of the `serial.Serial` class is created for communication
with the serial port.  The value of the `port` named parameter should be the
name of the port determined in step 7 of "Verify Serial Port Accessibility"
above.  

Second, a command to modify the data rate is sent using the `.write()` method.
The value of 100 Hz is taken from earlier code and may be open for 
optimization.

The `.readline()` method is then used to get the next set of readings from the
inclinometer.  How buffering of data access vs data rate vs the speed of the code
to process and display images has not been examined and should be before 
production to ensure that the latest inclinometer data is being used in
conjunction with the most recent image.

## Data
The `.readline()` method returns a bytes object.  When converted into a string
using `.decode("utf-8"), a string is obtained in the following format:

`$CSTLT,Axn,Ayn,Azn,alpha_x,alpha_y,T*CC\r\n`

The values of interest appear to be `alpha_x` and `alpha_y`.  

`alpha_x` is the pitch of the laparoscope from horizontal.

`alpha_y` is the roll from when the molded arrow is on top of the laparoscope
when horizontal.  How `alpha_y` changes is a function of the `alpha_x` pitch.   

If the laparoscope is held horizontal to the ground with the "arrow" on top, 
the `alpha_x` pitch will read at 0 and the `alpha_y` roll will read at 0.  
If the laparoscope is rotated so it remains horizontal to the floor, but the 
arrow now points to the right, pitch remains at 0 and roll is at -90 (it goes 
to positive 90 with a roll to the left).

Next, if the laparoscope is returned to the starting position (0 pitch, 0 roll),
and it is tilted upwards, keeping the arrow on top, the `alpha_x` pitch will increase
until it reaches 90 when the laparoscope is  perpendicular to the ground.
However, in this orientation, if the laparoscope is rotated so that the arrow 
moves around the axis, the `alpha_y` roll value will not change.

If the pitch is set at 45 deg, then a 90 degree rotation of the arrow yields
a change in the roll of 45.  If pitch is at 60 deg, then the 90 deg rotation
yields a roll of about 30.  

On the surface, it would appear that the actual rotation around the axis would
be determined by:

actual_rotation = 90 * `alpha_y` / (90-`alpha_x`)

Note that this is only looking at values between 0 and 90.  We will need to
examine more closely what happens with negative values.  And, when rotation is
done past 90 deg, the measured values decrease again.  So, the formula above 
is just a starting point.

## Suggested Path Forward

Assume that the laparoscope will be used horizontally, and write the code to 
stabilize an image using the `alpha_y` without any correction.

