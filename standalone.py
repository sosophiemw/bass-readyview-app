import tkinter
from tkinter import filedialog
import time
import cv2
import PIL.Image, PIL.ImageTk
import numpy as np

import splash
UI_HIDE_DELAY=3000;
SNAPSHOT = False
GUI_ON = True
DIRECTORY_NAME=None
TEMP_VARIABLE=None
CAMERA_INDEX=None
KELVIN_TABLE = {
    2000: (255,137,18),
    2500: (255,161,72),
    3000: (255,180,107),
    3500: (255,196,137),
    4000: (255,209,163),
    4500: (255,219,186),
    5000: (255,228,206),
    5500: (255,236,224),
    6000: (255,243,239),
    6500: (255,249,253),
    7000: (245,243,255),
    7500: (235,238,255),
    8000: (227,233,255),
    8500: (220,229,255),
    9000: (214,225,255),
    9500: (208,222,255),
    10000: (204,219,255)}

class App:
    def __init__(self, window, window_title, video_source=0):
        global TEMP_VARIABLE
        global CAMERA_INDEX
        global UI_HIDE_DELAY

        self.window = window

        # Display Splash Screen
        self.window.withdraw()
        splash_screen = splash.Splash(self.window)

        self.window.title(window_title)
        self.window.minsize(700,600)
        self.OPTIONS=self.returnCameraIndexes()
        CAMERA_INDEX=tkinter.StringVar()
        CAMERA_INDEX.set(self.OPTIONS[0])
        self.video_source =video_source

        #open video source
        self.vid = MyVideoCapture(video_source)

        #set up canvas
        self.canvas=ResizingImageCanvas(window)
        self.canvas.grid(column=0, row=0, rowspan=1,sticky="news")
        window.columnconfigure(0, weight=1)
        window.rowconfigure(0, weight=1)
        #set up video source dropdown
        self.bottom_bar=tkinter.Frame(window)
        self.bottom_bar.grid(column=0,row=1, sticky='ew')
        self.bottom_bar.columnconfigure(0, weight=1)
        self.bottom_bar.columnconfigure(1, weight=1)
        self.bottom_bar.columnconfigure(2, weight=1)

        self.frame1=tkinter.Frame(self.bottom_bar)
        self.frame1.grid(column=0,row=0)
        self.LABEL=tkinter.Label(self.frame1, text='Select a Video Source Index:')
        self.LABEL.pack(side="top")
        self.DROPDOWN = tkinter.OptionMenu(self.frame1,CAMERA_INDEX,*self.OPTIONS)
        self.DROPDOWN.pack(side="bottom")
        #set up snapshot buttom
        self.SNAPSHOT_BUTTON=tkinter.Button(self.bottom_bar, text='Take Snapshot', command=self.take_snapshot);
        self.SNAPSHOT_BUTTON.grid(column=1,row=0)
        #set up temperature slider
        self.frame2=tkinter.Frame(self.bottom_bar)
        self.frame2.grid(column=2,row=0)
        self.TEMP_LABEL=tkinter.Label(self.frame2, text='Adjust Color Temperature:')
        TEMP_VARIABLE=tkinter.IntVar()
        self.slider=tkinter.Scale(self.frame2,from_=2000, to=10000, orient='horizontal',resolution=500,variable=TEMP_VARIABLE)
        self.slider.set(6500)
        self.TEMP_LABEL.pack(side="top")
        self.slider.pack(side="bottom")
        # Remove UI elements after 3 seconds
        self.hide_function_id = self.bottom_bar.after(UI_HIDE_DELAY, self.hide_bottom_bar)

        # Bind mouse motion to showing UI
        self.window.bind("<Motion>", self.mouse_motion)

        self.delay = 15
        splash_screen.destroy()
        self.window.deiconify()
        
        self.update()
        self.window.mainloop()
    
    def hide_bottom_bar(self):
        self.bottom_bar.grid_forget()
    
    def mouse_motion(self, event):
        global UI_HIDE_DELAY
        self.bottom_bar.after_cancel(self.hide_function_id)
        self.bottom_bar.grid(column=0,row=1, sticky='ew')
        self.bottom_bar.columnconfigure(0, weight=1)
        self.bottom_bar.columnconfigure(1, weight=1)
        self.bottom_bar.columnconfigure(2, weight=1)
        self.hide_function_id = self.bottom_bar.after(UI_HIDE_DELAY, self.hide_bottom_bar)

    def returnCameraIndexes(self):
        # checks the first 10 indexes.
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

    def take_snapshot(self):
        global SNAPSHOT
        global DIRECTORY_NAME
        if DIRECTORY_NAME==None:
            DIRECTORY_NAME=filedialog.askdirectory()
        SNAPSHOT = True;

    def update(self):
        #Get a frame from the video source
        ret, frame=self.vid.get_frame()
        if ret:
            self.image=PIL.Image.fromarray(frame.astype(np.uint8))
            self.canvas.setImage(self.image)
        self.window.after(self.delay,self.update)

class ResizingImageCanvas(tkinter.Canvas):
    """
    This class inherits from tkinter.Canvas and provides some additional
    functionality so that the canvas will resize the image it contains in
    response to a change in size of the canvas.
    """

    def __init__(self, parent):
        tkinter.Canvas.__init__(self, parent, background="red")

        # Create an image object on the canvas
        self.photo_id = self.create_image(0,0, anchor=tkinter.CENTER)
        self.alpha=1

        self.resize=1

        # Bind the "Configure" event to a method so that when the canvas size
        #  changes, the image size can be changed.
        self.bind("<Configure>", self.on_resize)

    def setImage(self,image):
        self.image_width=image.size[0]
        self.image_height=image.size[1]
        resized_image=image.resize([int(self.image_width*self.alpha),int(self.image_height*self.alpha)])
        self.photo = PIL.ImageTk.PhotoImage(image = resized_image)
        self.itemconfigure(self.photo_id, image=self.photo)
        

    def on_resize(self, event): 
        if(self.resize==1):
            alpha_x = event.width / self.image_width
            alpha_y = event.height / self.image_height
            self.alpha = min(alpha_x, alpha_y)
            self.config(width=self.image_width*self.alpha, height=self.image_height*self.alpha)
            self.moveto(self.photo_id,(self.winfo_width()-self.image_width*self.alpha)/2,(self.winfo_height()-self.image_height*self.alpha)/2)
            self.resize=0
        else:
           self.resize=1
        
class MyVideoCapture:
    def __init__(self, video_source=0):
        # Open the video source
        self.vid_source=video_source
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)

        # Get video source width and height
        self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

        # Release the video source when the object is destroyed
    def __del__(self):
         if self.vid.isOpened():
            self.vid.release()

    def get_frame(self):
        global KELVIN_TABLE;
        global TEMP_VARIABLE;
        global CAMERA_INDEX;
        global SNAPSHOT;

        if(int(CAMERA_INDEX.get())!=self.vid_source):
            self.vid_source=int(CAMERA_INDEX.get())
            self.vid = cv2.VideoCapture(int(CAMERA_INDEX.get()),cv2.CAP_DSHOW)
            if not self.vid.isOpened():
                raise ValueError("Unable to open video source", int(CAMERA_INDEX.get()))

            # Get video source width and height
            self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
            self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
        
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            if ret:
                # Return a boolean success flag and the current frame converted to BGR
                frame=frame.astype(np.float64);
                weight_array_temp=np.array([1, 1, 1])/255
                temp_array=np.array(KELVIN_TABLE[TEMP_VARIABLE.get()]) #int(temp_variable.get())
                weight_array_temp[0]*=temp_array[2]
                weight_array_temp[1]*=temp_array[1]
                weight_array_temp[2]*=temp_array[0]
                
                mod_weight_array = (255 * weight_array_temp)/(np.max(frame))
                frame[:, :640, 0] *= mod_weight_array[0]
                frame[:, :640, 1] *= mod_weight_array[1]
                frame[:, :640, 2] *= mod_weight_array[2]

                if SNAPSHOT:
                    timestr = time.strftime("%Y%m%d-%H%M%S")
                    print(timestr)
                    cv2.imwrite(DIRECTORY_NAME+'/'+timestr+'.png', frame)
                    SNAPSHOT = False


                frame = np.flip(frame, axis=2)
                return (ret, frame);
            else:
                return (ret, None)
        else:
            return (ret, None)    
        

# Create a window and pass it to the Application object
App(tkinter.Tk(), "ReadyView")