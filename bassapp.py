import threading
import time
import tkinter as tk
from tkinter import filedialog
import imageio

from cv2 import cv2
import numpy as np
import pyvirtualcam

CAMERA_ON = False
WHITE_BALANCE_ON = False
WHITE_BALANCE_SET = False
SNAPSHOT = False
GUI_ON = True
DIRECTORY_NAME=None
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

def toggle_camera():
    global CAMERA_ON
    CAMERA_ON = not CAMERA_ON
    if TOGGLE_CAMERA_BUTTON['text'] == 'Turn Camera ON':
        TOGGLE_CAMERA_BUTTON.config(text='Turn Camera OFF')
    else:
        TOGGLE_CAMERA_BUTTON.config(text='Turn Camera ON')

def take_snapshot():
    global SNAPSHOT
    global DIRECTORY_NAME
    if DIRECTORY_NAME==None:
        DIRECTORY_NAME=filedialog.askdirectory()
    SNAPSHOT = True;
    

def toggle_white_balance():
    global WHITE_BALANCE_ON
    WHITE_BALANCE_ON = not WHITE_BALANCE_ON
    if WHITE_BALANCE_BUTTON['text'] == 'Turn Color Correction ON':
        WHITE_BALANCE_BUTTON.config(text='Turn Color Correction OFF')
    else:
        WHITE_BALANCE_BUTTON.config(text='Turn Color Correction ON')


def set_white_balance():
    global WHITE_BALANCE_SET
    WHITE_BALANCE_SET = True
    WHITE_BALANCE_BUTTON.config(state='normal')

def stop_gui():
    global GUI_ON
    GUI_ON = False
    r.destroy()

def returnCameraIndexes():
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

def calc_weights(pixel_array):

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


def get_frame(weight_array, camera_start, cap=None):
    global KELVIN_TABLE
    global WHITE_BALANCE_SET
    global SNAPSHOT
    # open camera
    if camera_start:
        cap = cv2.VideoCapture(int(variable.get()),cv2.CAP_DSHOW)
        cap.set(3, 640)
        cap.set(4, 480)
        camera_start = False

    # grab frame
    ret, frame = cap.read()
    if frame is None:
        print("no frame")
        return None

    frame=frame.astype(np.float64)

    if WHITE_BALANCE_SET:
        weight_array = calc_weights(frame)
        WHITE_BALANCE_SET = False

    if WHITE_BALANCE_ON:
        weight_array_temp=weight_array/255
        temp_array=np.array(KELVIN_TABLE[int(temp_variable.get())])
        weight_array_temp[0]*=temp_array[2]
        weight_array_temp[1]*=temp_array[1]
        weight_array_temp[2]*=temp_array[0]
        # if SCALE:
        max_weight = np.max(weight_array)
        mod_weight_array = (255 * weight_array_temp)/(np.max(frame) * max_weight)
        frame[:, :640, 0] *= mod_weight_array[0]
        frame[:, :640, 1] *= mod_weight_array[1]
        frame[:, :640, 2] *= mod_weight_array[2]
        # else:
        #     frame[:, :640, 0] *= weight_array_temp[0]
        #     frame[:, :640, 1] *= weight_array_temp[1]
        #     frame[:, :640, 2] *= weight_array_temp[2]
        # if CAP:
        #     frame = np.where(frame > 255, 255, frame)

    if SNAPSHOT:
        timestr = time.strftime("%Y%m%d-%H%M%S")
        print(timestr)
        cv2.imwrite(DIRECTORY_NAME+'/'+timestr+'.png', frame)
        SNAPSHOT = False

    # fix the color orientation (BRG -> RGB)
    frame = np.flip(frame, axis=2)
    return frame, weight_array, camera_start, cap


def run_camera():
    with pyvirtualcam.Camera(width=640, height=480, fps=120, backend='obs',print_fps=True) as cam:
        weight_array = np.array([1, 1, 1])
        # flag to represent if the camera is being started
        camera_start = True
        cap = None

        while True:
            if not GUI_ON:
                cap.release()
                break
            if CAMERA_ON:
                result = get_frame(weight_array, camera_start, cap=cap)
                if result is None:  # Check to see if you got a frame...if not, jump to the beginning of the loop and try again
                    continue
                frame, weight_array, camera_start, cap = result
                # flippedframe=np.fliplr(frame.astype(np.uint8))
                # send the frame to the virtual camera object
                cam.send(frame.astype(np.uint8))

            if not CAMERA_ON and not camera_start:
                # im = imageio.imread('placeholder.png')
                # cam.send(im)
                cap.release()
                # cv2.destroyAllWindows()
                camera_start = True


T1 = threading.Thread(target=run_camera)
T1.start()

r = tk.Tk()
r.title('KeyScope Camera Controls')

LABEL=tk.Label(r, text='Select a Video Source Index:')
TEMP_LABEL=tk.Label(r, text='Adjust Color Temperature:')
WHITE_BALANCE_BUTTON = tk.Button(
    r, text='Turn Color Correction ON', command=toggle_white_balance, state="disabled")
SET_WHITE_BALANCE_BUTTON = tk.Button(
    r, text='Set White Balance', command=set_white_balance)
TOGGLE_CAMERA_BUTTON = tk.Button(
    r, text='Turn Camera ON', command=toggle_camera)
TAKE_SNAPSHOT = tk.Button(
    r, text='Take Snapshot', command=take_snapshot)
r.protocol("WM_DELETE_WINDOW", stop_gui)

OPTIONS=returnCameraIndexes()
variable=tk.StringVar()
variable.set(OPTIONS[0])
DROPDOWN = tk.OptionMenu(r,variable,*OPTIONS)

temp_variable=tk.IntVar()
slider=tk.Scale(r,from_=2000, to=10000, orient='horizontal',resolution=500,variable=temp_variable)
slider.set(6500)

LABEL.pack()
DROPDOWN.pack()
TOGGLE_CAMERA_BUTTON.pack()
SET_WHITE_BALANCE_BUTTON.pack()
WHITE_BALANCE_BUTTON.pack()
TEMP_LABEL.pack()
slider.pack()
TAKE_SNAPSHOT.pack()

print("before mainloop")
r.mainloop()
print("mainloop")
T1.join()
print("finished")