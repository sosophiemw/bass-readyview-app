# Python Imports
import os
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

# Viewer Imports
import splash
from frame_rate_calc import FrameRateCalc

# Constants
UI_HIDE_DELAY = 3000  # time, in ms, after which bottom bar will disappear
DELAY = 15  # time, in ms, to wait before calling "update" function


class Viewer:

    def __init__(self):
        self.window = tk.Tk()

        # Display Splash Screen
        self.window.withdraw()
        splash_screen = splash.Splash(self.window)

        self.window.title("ReadyView")  # sets window title
        self.window.minsize(700, 600)  # sets minimum dimensions of the window

        # Gets list of available camera indices and default to first option
        self.options = MyVideoCapture.returnCameraIndexes()
        camera_index = tkinter.StringVar()
        camera_index.set(str(self.options[0]))
        # ToDo: rite code to recognize change in camera_index selection,
        #       close existing video connection, and open a new one

        # open video source
        self.vid = MyVideoCapture(int(camera_index.get()))

        # ToDo: Add code here to change camera resolution as needed

        self.raw_image_width, self.raw_image_height = \
            self.vid.get_camera_image_size()
        self.window.geometry("{}x{}".format(self.raw_image_width,
                                            self.raw_image_height))
        self.alpha = 1  # Image scalar

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

        # set up video source dropdown
        self.frame1 = tk.Frame(self.bottom_bar)
        self.frame1.grid(column=0, row=0)
        tk.Label(self.frame1, text='Select a Video Source Index:')\
            .pack(side="top")
        self.dropdown = tkinter.OptionMenu(self.frame1, camera_index,
                                           *self.options)
        self.dropdown.pack(side="bottom")

        # set up snapshot button
        self.snapshot_button = tk.Button(self.bottom_bar,
                                         text='Take Snapshot',
                                         command=self.take_snapshot)
        self.snapshot_button.grid(column=1, row=0)
        self.directory_name = None
        self.snapshot = False

        # set up temperature slider
        # adjusting the slider changes the global temperature_variable so
        # color temp can be adjusted
        self.frame2 = tk.Frame(self.bottom_bar)
        self.frame2.grid(column=2, row=0)
        tk.Label(self.frame2, text='Adjust Color Temperature:')\
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
                                           command=self.freeze_rotation)
        self.freeze_rot_button.grid(column=3, row=0)

        # Remove UI elements after specified period of time
        self.hide_function_id = self.bottom_bar.after(UI_HIDE_DELAY,
                                                      self.hide_bottom_bar)

        # Bind mouse motion to showing UI
        self.window.bind("<Motion>", self.mouse_motion)

        # Bind the "Configure" event to a method so that when the window size
        #  changes, the image size can be changed.
        self.window.bind("<Configure>", self.on_resize)

        self.fps = FrameRateCalc()

        splash_screen.destroy()
        self.window.deiconify()

        self.update()  # called over and over to update image
        self.window.mainloop()

    def take_snapshot(self):
        if self.directory_name is None or self.directory_name == "":
            self.directory_name = filedialog.askdirectory()
        if self.directory_name is None or self.directory_name == "":
            messagebox.showerror("Problem Saving Snapshot",
                                 "No directory selected, "
                                 "so no snapshot saved.")
        else:
            self.snapshot = True

    def freeze_rotation(self):
        # ToDo: Code freeze_rotation command function
        pass

    def hide_bottom_bar(self):
        self.bottom_bar.place_forget()

    def mouse_motion(self, event):
        self.bottom_bar.after_cancel(self.hide_function_id)
        self.bottom_bar.place(relx=0.5, rely=1, anchor=tk.S)
        self.hide_function_id = self.bottom_bar.after(UI_HIDE_DELAY,
                                                      self.hide_bottom_bar)

    def update(self):
        # Obtain raw frame from camera
        ret, frame = self.vid.get_frame()
        if ret:
            temp_variable_to_send = self.temp_variable.get()
            rotation_to_send = 0
            if self.snapshot:
                # if the snapshot button has been pressed, send the foldername
                #   to the thread to save an image
                dir_name = self.directory_name
                self.snapshot = False
            else:
                dir_name = None
            thread = threading.Thread(target=MyVideoCapture.frame_worker,
                                      args=(self.image_label,
                                            frame,
                                            self.raw_image_width,
                                            self.raw_image_height,
                                            self.alpha,
                                            temp_variable_to_send,
                                            rotation_to_send,
                                            dir_name
                                            ))
            thread.start()
            if self.fps.add_frame():
                print(self.fps.get_fps())
        self.window.after(DELAY, self.update)

    def on_resize(self, event):
        alpha_x = self.window.winfo_width() / self.raw_image_width
        alpha_y = self.window.winfo_height() / self.raw_image_height
        self.alpha = min(alpha_x, alpha_y)


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

    @staticmethod
    def frame_worker(image_label, frame, raw_image_width, raw_image_height,
                     alpha=1, temp_variable=None, rotation=0,
                     snapshot_dir_name=None):
        from scope_adjust_color_temperature import adjust_color_temperature
        if temp_variable is not None:
            frame = adjust_color_temperature(frame, temp_variable)
        # Convert BGR, obtained by OpenCV, to RGB which is what Pillow expects
        frame = np.flip(frame, axis=2)
        image = PIL.Image.fromarray(frame.astype(np.uint8))
        if not (0.98 <= alpha <= 1.02):
            new_x = round(raw_image_width * alpha)
            new_y = round(raw_image_height * alpha)
            image = image.resize((new_x, new_y))
        if rotation != 0:
            image = image.rotate(rotation, PIL.Image.NEAREST)
        if snapshot_dir_name is not None:
            timestr = time.strftime("%Y%m%d-%H%M%S")
            filename = "{}.png".format(timestr)
            path_file_name = os.path.join(snapshot_dir_name, filename)
            image.save(path_file_name)
        tk_image = PIL.ImageTk.PhotoImage(image)
        image_label.configure(image=tk_image)
        image_label.image = tk_image


if __name__ == '__main__':
    Viewer()
