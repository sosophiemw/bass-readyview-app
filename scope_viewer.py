# Python Imports
import tkinter
import tkinter as tk

# Package Imports
import cv2

# Viewer Imports
import splash

# Constants
UI_HIDE_DELAY = 3000  # time, in ms, after which bottom bar will disappear


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

        splash_screen.destroy()
        self.window.deiconify()

        self.window.mainloop()

    def take_snapshot(self):
        # ToDo:  Code take_snapshot command function
        pass

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


if __name__ == '__main__':
    Viewer()
