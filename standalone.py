import tkinter
import cv2
import PIL.Image, PIL.ImageTk
import numpy as np

WEIGHT_ARRAY=[0,0,0]
WHITE_BALANCE_ON = False
WHITE_BALANCE_SET = False
SNAPSHOT = False
GUI_ON = True
DIRECTORY_NAME=None
TEMP_VARIABLE=None
variable=None
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
        global variable
        self.window = window
        self.window.title(window_title)
        self.OPTIONS=self.returnCameraIndexes()
        variable=tkinter.StringVar()
        variable.set(self.OPTIONS[0])
        self.DROPDOWN = tkinter.OptionMenu(window,variable,*self.OPTIONS)
        self.video_source =video_source

        #open video source
        self.vid = MyVideoCapture(video_source)

        self.canvas=tkinter.Canvas(window,width=self.vid.width, height=self.vid.height)
        self.canvas.pack()

        self.LABEL=tkinter.Label(window, text='Select a Video Source Index:')
        self.TEMP_LABEL=tkinter.Label(window, text='Adjust Color Temperature:')
        self.WHITE_BALANCE_BUTTON = tkinter.Button(
            window, text='Turn Color Correction ON', command=self.toggle_white_balance, state="disabled")
        self.SET_WHITE_BALANCE_BUTTON = tkinter.Button(
            window, text='Set White Balance', command=self.set_white_balance)

        

        TEMP_VARIABLE=tkinter.IntVar()
        self.slider=tkinter.Scale(window,from_=2000, to=10000, orient='horizontal',resolution=500,variable=TEMP_VARIABLE)
        self.slider.set(6500)

        self.LABEL.pack()
        self.DROPDOWN.pack()
        self.SET_WHITE_BALANCE_BUTTON.pack()
        self.WHITE_BALANCE_BUTTON.pack()
        self.TEMP_LABEL.pack()
        self.slider.pack()

        self.delay = 15
        self.update()

        self.window.mainloop()
    def toggle_white_balance(self):
        global WHITE_BALANCE_ON
        WHITE_BALANCE_ON = not WHITE_BALANCE_ON
        if self.WHITE_BALANCE_BUTTON['text'] == 'Turn Color Correction ON':
            self.WHITE_BALANCE_BUTTON.config(text='Turn Color Correction OFF')
        else:
            self.WHITE_BALANCE_BUTTON.config(text='Turn Color Correction ON')
    def set_white_balance(self):
        global WHITE_BALANCE_SET
        WHITE_BALANCE_SET = True
        self.WHITE_BALANCE_BUTTON.config(state='normal')

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
    
    def update(self):
        #Get a frame from the video source
        ret, frame=self.vid.get_frame()

        if ret:
            self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(frame.astype(np.uint8)))
            self.canvas.create_image(0, 0, image = self.photo, anchor = tkinter.NW)
        
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
    
    def calc_weights(self, pixel_array):

        blue_average = np.mean(pixel_array[:, :, 0])
        red_average = np.mean(pixel_array[:, :, 1])
        green_average = np.mean(pixel_array[:, :, 2])

        overall_average = (red_average + green_average + blue_average) / 3
        if overall_average > 170:
            constant = 200
        else:
            constant = 128

        weight_array_val = constant * np.array([(1 / blue_average), (1 / red_average), (1 / green_average)])
        return weight_array_val

    def get_frame(self):
        global WHITE_BALANCE_SET;
        global WHITE_BALANCE_ON;
        global KELVIN_TABLE;
        global WEIGHT_ARRAY;
        global TEMP_VARIABLE;
        global variable;

        if(int(variable.get())!=self.vid_source):
            self.vid_source=int(variable.get())
            self.vid = cv2.VideoCapture(int(variable.get()),cv2.CAP_DSHOW)
            if not self.vid.isOpened():
                raise ValueError("Unable to open video source", int(variable.get()))

            # Get video source width and height
            self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
            self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
        
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            if ret:
                # Return a boolean success flag and the current frame converted to BGR
                frame=frame.astype(np.float64);
                if WHITE_BALANCE_SET:
                    WEIGHT_ARRAY = self.calc_weights(frame)
                    WHITE_BALANCE_SET = False
                    print(WEIGHT_ARRAY)
                if WHITE_BALANCE_ON:
                    weight_array_temp=WEIGHT_ARRAY/255
                    temp_array=np.array(KELVIN_TABLE[TEMP_VARIABLE.get()]) #int(temp_variable.get())
                    weight_array_temp[0]*=temp_array[2]
                    weight_array_temp[1]*=temp_array[1]
                    weight_array_temp[2]*=temp_array[0]
                    # if SCALE:
                    max_weight = np.max(WEIGHT_ARRAY)
                    mod_weight_array = (255 * weight_array_temp)/(np.max(frame) * max_weight)
                    frame[:, :640, 0] *= mod_weight_array[0]
                    frame[:, :640, 1] *= mod_weight_array[1]
                    frame[:, :640, 2] *= mod_weight_array[2]
                frame = np.flip(frame, axis=2)
                return (ret, frame);
            else:
                return (ret, None)
        else:
            return (ret, None)    
        

# Create a window and pass it to the Application object
App(tkinter.Tk(), "Tkinter and OpenCV")