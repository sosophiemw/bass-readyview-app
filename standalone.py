import tkinter
from tkinter import filedialog
import time
import cv2
import PIL.Image, PIL.ImageTk
import numpy as np

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

        self.window = window
        self.window.title(window_title)
        self.OPTIONS=self.returnCameraIndexes()
        CAMERA_INDEX=tkinter.StringVar()
        CAMERA_INDEX.set(self.OPTIONS[0])
        self.DROPDOWN = tkinter.OptionMenu(window,CAMERA_INDEX,*self.OPTIONS)
        self.video_source =video_source

        #open video source
        self.vid = MyVideoCapture(video_source)

        self.canvas=tkinter.Canvas(window)
        self.canvas.pack()
        self.photo_id=self.canvas.create_image(0, 0, anchor = tkinter.NW)

        self.LABEL=tkinter.Label(window, text='Select a Video Source Index:')
        self.TEMP_LABEL=tkinter.Label(window, text='Adjust Color Temperature:')

        TEMP_VARIABLE=tkinter.IntVar()
        self.slider=tkinter.Scale(window,from_=2000, to=10000, orient='horizontal',resolution=500,variable=TEMP_VARIABLE)
        self.slider.set(6500)

        self.SNAPSHOT_BUTTON=tkinter.Button(window, text='Take Snapshot', command=self.take_snapshot);

        self.LABEL.pack()
        self.DROPDOWN.pack()
        self.SNAPSHOT_BUTTON.pack()
        self.TEMP_LABEL.pack()
        self.slider.pack()

        self.delay = 15

        self.update()
        self.window.mainloop()

    def returnCameraIndexes(self):
        # checks the first 10 indexes.
        index = 0
        arr = []
        i = 10

        while i > 0:
            cap = cv2.VideoCapture(index,cv2.CAP_DSHOW)
            if cap.read()[0]:
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
            self.resized_image=self.image.resize([int(self.image.size[0]*1.3),int(self.image.size[1]*1.3)])
            self.photo = PIL.ImageTk.PhotoImage(image = self.resized_image)
            self.canvas.config(width=self.resized_image.size[0], height=self.resized_image.size[1])
            self.canvas.itemconfigure(self.photo_id, image=self.photo)
        
        self.window.after(self.delay,self.update)

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