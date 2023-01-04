# Python Imports
import glob
import math
import os
import sys
import threading
import time
import tkinter
import tkinter as tk
from tkinter import filedialog, messagebox

# Package Imports
import cv2
import numpy as np
import PIL.Image
import PIL.ImageTk
import serial

# Viewer Imports
import splash
from frame_rate_calc import FrameRateCalc

# Constants
UI_HIDE_DELAY = 3000  # time, in ms, after which bottom bar will disappear
DELAY = 15  # time, in ms, to wait before calling "update" function
DIAGONAL = False  # Sets method for image sizing
MOCK_SERIAL = True  # Sets whether to use the mock serial port.
# Set to False if using the scope with the inclinometer


class Viewer:

    def __init__(self):
        self.window = tk.Tk()

        # Display Splash Screen
        self.window.withdraw()
        splash_screen = splash.Splash(self.window)

        self.window.title("ReadyView")  # sets window title
        self.window.minsize(700, 600)  # sets minimum dimensions of the window

        splash_screen.update_message("Loading settings...")
        self.resolution_strings = []
        self.resolutions = []
        self.DO_TEMP = False
        self.load_settings()

        splash_screen.update_message("Loading camera...")
        # Gets list of available camera indices and default to first option
        self.options = MyVideoCapture.returnCameraIndexes()
        self.camera_index = tkinter.StringVar()
        self.camera_index.set(str(self.options[0]))
        # ToDo: rite code to recognize change in camera_index selection,
        #       close existing video connection, and open a new one

        # open video source
        self.vid = MyVideoCapture(int(self.camera_index.get()))

        # Change camera resolution as needed
        self.vid.set_camera_image_size(self.resolutions[0][0],
                                       self.resolutions[0][1])

        self.raw_image_width, self.raw_image_height = \
            self.vid.get_camera_image_size()
        self.window.geometry("{}x{}".format(self.raw_image_width,
                                            self.raw_image_height))
        self.alpha = 1  # Image scalar

        splash_screen.update_message("Preparing interface...")
        # set up image label
        self.image_label = tk.Label(self.window)
        self.image_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # set up bottom bar
        self.bottom_bar = tk.Frame(self.window)
        self.bottom_bar.place(relx=0.5, rely=1, anchor=tk.S)
        self.bottom_bar.columnconfigure(0, weight=1)
        self.bottom_bar.columnconfigure(1, weight=1)
        self.bottom_bar.columnconfigure(2, weight=1)
        self.bottom_bar.columnconfigure(3, weight=1)
        self.bottom_bar.columnconfigure(4, weight=1)
        self.bottom_bar.columnconfigure(5, weight=1)

        # set up video source dropdown
        self.frame1 = tk.Frame(self.bottom_bar)
        self.frame1.grid(column=0, row=0)
        tk.Label(self.frame1, text='Select a Video Source Index:') \
            .pack(side="top")
        self.dropdown = tkinter.OptionMenu(self.frame1, self.camera_index,
                                           *self.options,
                                           command=self.camera_change_cmd)
        self.dropdown.pack(side="bottom")

        # set up resolution dropdown
        self.resolution_string_choice = tk.StringVar()
        self.resolution_string_choice.set(self.resolution_strings[0])
        self.frame_resolution = tk.Frame(self.bottom_bar)
        self.frame_resolution.grid(column=1, row=0)
        tk.Label(self.frame_resolution, text="Camera Resolution:")\
            .pack(side="top")
        self.resolution_dropdown = tkinter.OptionMenu(
            self.frame_resolution, self.resolution_string_choice,
            *self.resolution_strings, command=self.resolution_change_cmd)
        self.resolution_dropdown.pack(side="bottom")

        # set up snapshot button
        self.snapshot_button = tk.Button(self.bottom_bar,
                                         text='Take Snapshot',
                                         command=self.take_snapshot)
        self.snapshot_button.grid(column=2, row=0)
        self.directory_name = None
        self.snapshot = False

        # set up temperature slider
        # adjusting the slider changes the global temperature_variable so
        # color temp can be adjusted
        self.frame2 = tk.Frame(self.bottom_bar)
        self.frame2.grid(column=3, row=0)
        tk.Label(self.frame2, text='Adjust Color Temperature:') \
            .pack(side="top")
        self.temp_variable = tkinter.IntVar()
        self.slider = tk.Scale(self.frame2, from_=2000, to=10000,
                               orient='horizontal', resolution=500,
                               variable=self.temp_variable)
        self.slider.set(6500)
        self.slider.pack(side="bottom")

        # set up Freeze Rotation button
        self.freeze_rot_button = tk.Button(self.bottom_bar,
                                           text='FREEZE ROTATION',
                                           command=self.freeze_rotation_cmd,
                                           state=tk.DISABLED)
        self.freeze_rot_button.grid(column=4, row=0)

        # set up resize checkbox
        self.frame_btns = tk.Frame(self.bottom_bar)
        self.frame_btns.grid(column=5, row=0)
        self.resize_select = tk.BooleanVar()
        self.resize_select.set(True)
        self.resize_checkbtn = tk.Checkbutton(self.frame_btns,
                                              text="Resize",
                                              variable=self.resize_select,
                                              onvalue=True,
                                              offvalue=False)
        self.resize_checkbtn.pack(side="top")
        self.run_select = tk.BooleanVar()
        self.run_select.set(True)
        self.run_checkbtn =  tk.Checkbutton(self.frame_btns,
                                            text="Run",
                                            variable=self.run_select,
                                            onvalue=True,
                                            offvalue=False)
        self.run_checkbtn.pack(side="bottom")

        # Bind mouse motion to showing UI
        self.window.bind("<Motion>", self.mouse_motion)

        # Bind the "Configure" event to a method so that when the window size
        #  changes, the image size can be changed.
        self.window.bind("<Configure>", self.on_resize)

        self.fps = FrameRateCalc()

        splash_screen.update_message("Finding inclinometer...")
        # Check for inclinometer
        if MOCK_SERIAL:
            ports = MockSerialPort.find_available_ports()
        else:
            ports = SerialPort.find_available_ports()
        self.ser = None
        self.use_gyro = False
        if len(ports) > 0:
            gyro_port = ports[0]
            if MOCK_SERIAL:
                self.ser = MockSerialPort(gyro_port)
            else:
                self.ser = SerialPort(gyro_port)
            self.use_gyro = True
            self.freeze_rot_button.configure(state=tk.ACTIVE)
        self.freeze_rotation = False
        self.rotation_baseline = 0

        splash_screen.destroy()
        self.window.deiconify()
        self.update_id = None  # Variable to hold handle number of update call

        # Remove UI elements after specified period of time
        self.hide_function_id = self.bottom_bar.after(UI_HIDE_DELAY,
                                                      self.hide_bottom_bar)

        self.update()  # called over and over to update image
        self.window.mainloop()

    def load_settings(self):
        with open("resources/settings.txt", 'r') as in_file:
            lines = in_file.readlines()
        for line in lines:
            if line.find('MOCK_SERIAL') >= 0:
                splits = line.strip(" \n").split('=')
                global MOCK_SERIAL
                if splits[1].upper() == "TRUE":
                    MOCK_SERIAL = True
                else:
                    MOCK_SERIAL = False
            elif line.find('DIAGONAL') >= 0:
                splits = line.strip(" \n").split('=')
                global DIAGONAL
                if splits[1].upper() == "TRUE":
                    DIAGONAL = True
                else:
                    DIAGONAL = False
            elif line.find('TEMPERATURE') >= 0:
                splits = line.strip(" \n").split('=')
                if splits[1].upper() == "TRUE":
                    self.DO_TEMP = True
                else:
                    self.DO_TEMP = False
            elif line.find('x') >= 0:
                x, y = line.strip(" \n").split('x')
                self.resolutions.append((int(x), int(y)))
                self.resolution_strings.append(line.strip(" \n"))

    def take_snapshot(self):
        if self.directory_name is None or self.directory_name == "":
            self.directory_name = filedialog.askdirectory()
        if self.directory_name is None or self.directory_name == "":
            messagebox.showerror("Problem Saving Snapshot",
                                 "No directory selected, "
                                 "so no snapshot saved.")
        else:
            self.snapshot = True

    def freeze_rotation_cmd(self):
        if self.freeze_rotation is True:
            self.freeze_rot_button['text'] = "FREEZE ROTATION"
            self.freeze_rotation = False
        else:
            self.freeze_rot_button['text'] = "UNFREEZE ROTATION"
            self.rotation_baseline = self.ser.get_angle()
            self.freeze_rotation = True

    def hide_bottom_bar(self):
        self.bottom_bar.place_forget()

    def mouse_motion(self, event):
        self.bottom_bar.after_cancel(self.hide_function_id)
        self.bottom_bar.place(relx=0.5, rely=1, anchor=tk.S)
        self.hide_function_id = self.bottom_bar.after(UI_HIDE_DELAY,
                                                      self.hide_bottom_bar)

    def update(self):
        # Obtain raw frame from camera
        if self.run_select.get() is False:
            self.window.after(DELAY, self.update)
            return
        ret, frame = self.vid.get_frame()
        if ret:
            if self.DO_TEMP:
                temp_variable_to_send = self.temp_variable.get()
            else:
                temp_variable_to_send = None
            ser_to_send = None
            if self.freeze_rotation:
                ser_to_send = self.ser
            if self.snapshot:
                # if the snapshot button has been pressed, send the foldername
                #   to the thread to save an image
                dir_name = self.directory_name
                self.snapshot = False
            else:
                dir_name = None
            if self.resize_select.get():
                alpha_to_send = self.alpha
            else:
                alpha_to_send = 1.0
            thread = threading.Thread(target=MyVideoCapture.frame_worker,
                                      args=(self.image_label,
                                            frame,
                                            self.raw_image_width,
                                            self.raw_image_height,
                                            alpha_to_send,
                                            temp_variable_to_send,
                                            ser_to_send,
                                            self.rotation_baseline,
                                            dir_name
                                            ))
            thread.daemon = True  # Will cause thread to end when GUI ends
            thread.start()
            if self.fps.add_frame():
                print(self.fps.get_fps())
        self.window.after(DELAY, self.update)

    def on_resize(self, event):
        if DIAGONAL is False:
            alpha_x = self.window.winfo_width() / self.raw_image_width
            alpha_y = self.window.winfo_height() / self.raw_image_height
            self.alpha = min(alpha_x, alpha_y)
        else:
            # sets the width to the length of the diagonal so there is nothing
            # being cut off
            self.alpha = math.sqrt(
                self.window.winfo_width() ** 2
                + self.window.winfo_width() ** 2) / self.raw_image_height

    def resolution_change_cmd(self, event):
        warning_label = tk.Label(self.window,
                                 text="Hold for resolution change",
                                 font=("Arial", 24))
        warning_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.window.update()
        current_resolution = self.vid.get_camera_image_size()
        new_resolution_string = self.resolution_string_choice.get()
        x, y = new_resolution_string.split('x')
        x, y = int(x), int(y)
        while True:
            self.vid.__del__()
            self.vid = MyVideoCapture(int(self.camera_index.get()))
            self.vid.set_camera_image_size(x, y)
            updated_resolution = self.vid.get_camera_image_size()
            if updated_resolution[0] != x or updated_resolution[1] != y:
                warning_label.configure(text="{}x{} unavailable.  Returning to {}x{}"
                                        .format(x, y, current_resolution[0],
                                                current_resolution[1]))
                self.window.update()
                x = current_resolution[0]
                y = current_resolution[1]
                self.resolution_string_choice.set("{}x{}".format(x, y))
            else:
                break
        # self.alpha = 1.0
        self.raw_image_width, self.raw_image_height = \
            self.vid.get_camera_image_size()
        warning_label.place_forget()

    def camera_change_cmd(self, event):
        warning_label = tk.Label(self.window,
                                 text="Hold for camera change",
                                 font=("Arial", 24))
        warning_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.window.update()
        self.vid.__del__()
        self.resolution_string_choice.set("{}x{}".format(640, 480))
        self.vid = MyVideoCapture(int(self.camera_index.get()))
        self.vid.set_camera_image_size(640, 480)
        self.raw_image_width, self.raw_image_height = \
            self.vid.get_camera_image_size()
        warning_label.place_forget()


class MyVideoCapture:

    @staticmethod
    def returnCameraIndexes():
        # Returns potential video sources
        # checks the first 10 indices
        index = 0
        arr = []
        i = 10

        cap = cv2.VideoCapture()

        while i > 0:
            if cap.open(index, cv2.CAP_DSHOW):
                arr.append(index)
                cap.release()
            index += 1
            i -= 1
        return arr

    def __init__(self, video_source=0):
        # Open the video source
        self.vid_source = video_source
        self.vid = cv2.VideoCapture(self.vid_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)

    def __del__(self):
        # Release the video source when the object is destroyed
        if self.vid.isOpened():
            self.vid.release()

    def get_frame(self):
        ret = None
        frame = None
        if self.vid.isOpened():
            ret, frame = self.vid.read()
        return ret, frame

    def get_camera_image_size(self):
        image_width = round(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH))
        image_height = round(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return image_width, image_height

    def set_camera_image_size(self, width: int, height: int):
        self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    @staticmethod
    def frame_worker(image_label, frame, raw_image_width, raw_image_height,
                     alpha=1, temp_variable=None, serial_port=None,
                     rotation_baseline=None, snapshot_dir_name=None):
        from scope_adjust_color_temperature import adjust_color_temperature
        if temp_variable is not None:
            frame = adjust_color_temperature(frame, temp_variable)
        # Convert BGR, obtained by OpenCV, to RGB which is what Pillow expects
        frame = np.flip(frame, axis=2)
        image = PIL.Image.fromarray(frame.astype(np.uint8))
        if snapshot_dir_name is not None:
            timestr = time.strftime("%Y%m%d-%H%M%S")
            filename = "{}.png".format(timestr)
            path_file_name = os.path.join(snapshot_dir_name, filename)
            image.save(path_file_name)
        # ToDo:  Where should snapshot be?
        #  Before or after sizing/rotation/color?
        if not (0.98 <= alpha <= 1.02):
            new_x = round(raw_image_width * alpha)
            new_y = round(raw_image_height * alpha)
            image = image.resize((new_x, new_y))
        if serial_port is not None:
            try:
                rotation_variable = serial_port.get_angle()
            except RuntimeError:
                return
            image = image.rotate(rotation_variable - rotation_baseline,
                                 PIL.Image.NEAREST)
        tk_image = PIL.ImageTk.PhotoImage(image)
        image_label.configure(image=tk_image)
        image_label.image = tk_image


class SerialPort:

    @staticmethod
    def find_available_ports():
        """ Lists serial port names

            :raises EnvironmentError:
                On unsupported or unknown platforms
            :returns:
                A list of the serial ports available on the system
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith(
                'cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in ports:
            try:
                ser = serial.Serial(port, baudrate=115200,
                                    bytesize=serial.EIGHTBITS,
                                    parity=serial.PARITY_NONE,
                                    stopbits=serial.STOPBITS_ONE,
                                    write_timeout=5, timeout=1)
                ser.write("[1D100\r".encode('utf-8'))
                ser.write("[N?\r".encode('utf-8'))
                for x in range(5):
                    s = ser.readline()
                    data_string = s.decode("utf-8")
                    data = data_string.split(",")
                    if data[0] == '>Unit Number:1\r\r\n':
                        result.append(port)
                ser.close()
            except (OSError, serial.SerialException):
                pass

        return result

    def __init__(self, port_id):
        self.ser = serial.Serial(port=port_id, baudrate=115200,
                                 bytesize=serial.EIGHTBITS,
                                 parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_ONE)
        self.ser.write("[1D100\r".encode('utf-8'))

    def get_angle(self):
        # flushes input so only most recent data is displayed
        self.ser.flushInput()
        s = self.ser.readline()  # reads new input
        data_string = s.decode("utf-8")
        data = data_string.split(",")
        if len(data) > 5:
            return int(float(data[len(data) - 2]))
        else:
            raise RuntimeError("Problem with inclinometer")


class MockSerialPort:

    @staticmethod
    def find_available_ports():
        return [-44]

    def __init__(self, port_id):
        if port_id != -44:
            raise AttributeError("Not consistently using Mock")
        self.active = False
        self.start_time = None
        self.up_direction = True

    def get_angle(self):
        if self.active is False:
            self.active = True
            self.start_time = time.monotonic()
        time_elapsed = time.monotonic() - self.start_time
        if time_elapsed > 45:
            time_elapsed = 0
            self.start_time = time.monotonic()
        angle = round(time_elapsed) * 2
        return angle


if __name__ == '__main__':
    Viewer()
