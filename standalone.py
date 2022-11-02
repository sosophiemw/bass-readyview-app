import tkinter
from tkinter import filedialog
import time
import cv2
import PIL.Image, PIL.ImageTk, PIL.ImageDraw, PIL.ImageChops
import numpy as np
import serial
import splash
import math

#DEFINING GLOBAL VARIABLES
UI_HIDE_DELAY=3000; #bottom bar will disappear after three seconds of no mouse movement
SNAPSHOT = False #Only toggles on when the snapshot button has been pressed
GUI_ON = True
DIRECTORY_NAME=None #The name of the folder where the pictures should be shared
TEMP_VARIABLE=None #color temperature variable
ROTATION_VARIABLE=None #degree to rotate the image
FREEZE_ROT=None
ROT_BASELINE=None
CAMERA_INDEX=None #what source the video is being pulled from
KELVIN_TABLE = { #maps the temperature variables to how RGB channels should be adjusted
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
class App: #sets up the user interface
    def __init__(self, window, window_title, video_source=0):
        global TEMP_VARIABLE
        global CAMERA_INDEX
        global UI_HIDE_DELAY
        global ROTATION_VARIABLE

        self.window = window

        # Display Splash Screen
        self.window.withdraw()
        splash_screen = splash.Splash(self.window)

        self.window.title(window_title) #sets window title to ReadyView
        self.window.minsize(700,600) #sets minimum dimensions of the window
        window.columnconfigure(0, weight=1) #The window is split into a grid pattern and having weights of the first row and first column set to 1 means it will take up all space not used by other elements in the grid
        window.rowconfigure(0, weight=1)

        self.OPTIONS=self.returnCameraIndexes() #returns a list of available camera indexes
        CAMERA_INDEX=tkinter.StringVar() 
        CAMERA_INDEX.set(self.OPTIONS[0]) #defaults the camera index to the first option

        #open video source
        self.video_source =video_source
        self.vid = MyVideoCapture(video_source)

        #set up canvas
        self.canvas=ResizingImageCanvas(window)
        self.canvas.configure(bg='#012169')
        self.canvas.grid(column=0, row=0, rowspan=1,sticky="news") #places the canvas in the first row and first column of the window grid

        #set up bottom_bar
        self.bottom_bar=tkinter.Frame(window) 
        self.bottom_bar.grid(column=0,row=1, sticky='ew') #places the bottom_bar frame in the first column and second row of the window grid
        self.bottom_bar.columnconfigure(0, weight=1)
        self.bottom_bar.columnconfigure(1, weight=1)
        self.bottom_bar.columnconfigure(2, weight=1)
        self.bottom_bar.columnconfigure(3, weight=1)

        #set up video source dropdown
        self.frame1=tkinter.Frame(self.bottom_bar) #creates frame inside the bottom bar
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
        self.slider=tkinter.Scale(self.frame2,from_=2000, to=10000, orient='horizontal',resolution=500,variable=TEMP_VARIABLE) #adjusting the slider changes the global temperature_variable so color temp can be adjusted
        self.slider.set(6500)
        self.TEMP_LABEL.pack(side="top")
        self.slider.pack(side="bottom")

        self.FREEZE_ROT_BUTTON=tkinter.Button(self.bottom_bar, text='FREEZE ROTATION', command=self.freeze_rotation);
        self.FREEZE_ROT_BUTTON.grid(column=3,row=0)

        # Remove UI elements after 3 seconds
        self.hide_function_id = self.bottom_bar.after(UI_HIDE_DELAY, self.hide_bottom_bar)

        # Bind mouse motion to showing UI
        self.window.bind("<Motion>", self.mouse_motion)

        self.delay = 15
        splash_screen.destroy()
        self.window.deiconify()
        
        self.update() #called over and over to update image
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

    def returnCameraIndexes(self): #returns potential video sources
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

    def freeze_rotation(self):
        global FREEZE_ROT
        global ROT_BASELINE
        if FREEZE_ROT==True:
            self.FREEZE_ROT_BUTTON['text']=" FREEZE ROTATION"
            FREEZE_ROT=False
        else:
            self.FREEZE_ROT_BUTTON['text']="UNFREEZE ROTATION"

            self.canvas.ser.flushInput() #flushes input so only most recent data is displayed
            s=self.canvas.ser.readline() #reads new input
            data_string = s.decode("utf-8")
            data = data_string.split(",")
            if(len(data)>5):
                ROT_BASELINE=int(float(data[len(data)-2]))
            
            FREEZE_ROT=True


    def update(self): #basic structure: update function gets a frame from the camera using the vid.get_frame method and passes it to the camera.setImage() so that it can be rotated, resized, and displayed on the canvas
        #Get a frame from the video source
        ret, frame=self.vid.get_frame()
        if ret: #if there is an image returned, the canvas element is updated with this new image using the set image function
            self.image=PIL.Image.fromarray(frame.astype(np.uint8))
            self.canvas.setImage(self.image)
        self.window.after(self.delay,self.update)

class ResizingImageCanvas(tkinter.Canvas):
    """
    This class inherits from tkinter.Canvas and provides some additional
    functionality so that the canvas will resize the image it contains in
    response to a change in size of the canvas.
    """

    def __init__(self, parent): #initializes variables for canvas object
        tkinter.Canvas.__init__(self, parent)

        # Create an image object on the canvas
        self.photo_id = self.create_image(0,0, anchor=tkinter.CENTER)
        self.alpha=1

        self.resize=1
        self.rotation_variable=0

        # Bind the "Configure" event to a method so that when the canvas size
        #  changes, the image size can be changed.
        self.bind("<Configure>", self.on_resize)

        self.ser = serial.Serial(port='COM7', baudrate=115200, bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
        self.ser.write("[1D100\r".encode('utf-8'))

    def setImage(self,image):
        global ROTATION_VARIABLE
        global FREEZE_ROT
        self.image_width=image.size[0]
        self.image_height=image.size[1]

        self.ser.flushInput() #flushes input so only most recent data is displayed
        s=self.ser.readline() #reads new input
        data_string = s.decode("utf-8")
        data = data_string.split(",")
        if(len(data)>5):
            self.rotation_variable=int(float(data[len(data)-2]))    
        resized_image=image.resize([int(self.image_width*self.alpha),int(self.image_height*self.alpha)]).rotate(self.rotation_variable-ROT_BASELINE if FREEZE_ROT else 0, PIL.Image.NEAREST, expand = 0)
        height, width = resized_image.size
        self.photo = PIL.ImageTk.PhotoImage(image = resized_image ) #turns the resized_image into the proper form
        self.itemconfigure(self.photo_id, image=self.photo) #sets the photo on the canvas

    def on_resize(self, event): #when the screen size is adjusted, this method should set the width and height od the canvas to an adjusted value
        if(self.resize==1): #There were issues with the screen growing infinitely large so that why there is a weird fix that toggles self.resize on and off
            # alpha_x = event.width / self.image_width
            # alpha_y = event.height / self.image_height
            # self.alpha = max(alpha_x, alpha_y)
            self.alpha=math.sqrt(event.width*event.width + event.height*event.height)/ self.image_height #sets the width to the length of the diagonal so there is nothing being cut off
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

    #gets frame from camera, and tweaks to reflect changes in temperature
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
                #adjust photo to be of the appropriate temperature
                frame=frame.astype(np.float64);
                weight_array_temp=np.array([1, 1, 1])/255
                temp_array=np.array(KELVIN_TABLE[TEMP_VARIABLE.get()]) #uses temperature variable from ui slider to find appropriate values
                weight_array_temp[0]*=temp_array[2]
                weight_array_temp[1]*=temp_array[1]
                weight_array_temp[2]*=temp_array[0]
                
                mod_weight_array = (255 * weight_array_temp)/(np.max(frame))
                frame[:, :640, 0] *= mod_weight_array[0]
                frame[:, :640, 1] *= mod_weight_array[1]
                frame[:, :640, 2] *= mod_weight_array[2]

                if SNAPSHOT: #if the snapshow button has been pressed save the image in the appropriate folder
                    timestr = time.strftime("%Y%m%d-%H%M%S")
                    print(timestr)
                    cv2.imwrite(DIRECTORY_NAME+'/'+timestr+'.png', frame)
                    SNAPSHOT = False #reset snapshot to false


                frame = np.flip(frame, axis=2) #mirror frame
                return (ret, frame);
            else:
                return (ret, None)
        else:
            return (ret, None)    

# Create a window and pass it to the Application object
App(tkinter.Tk(), "ReadyView")