import numpy as np

# Maps the temperature variables to how RGB channels should be adjusted
KELVIN_TABLE = {
    2000: (255, 137, 18), 
    2500: (255, 161, 72), 
    3000: (255, 180, 107), 
    3500: (255, 196, 137), 
    4000: (255, 209, 163), 
    4500: (255, 219, 186), 
    5000: (255, 228, 206), 
    5500: (255, 236, 224), 
    6000: (255, 243, 239), 
    6500: (255, 249, 253), 
    7000: (245, 243, 255), 
    7500: (235, 238, 255), 
    8000: (227, 233, 255), 
    8500: (220, 229, 255), 
    9000: (214, 225, 255), 
    9500: (208, 222, 255), 
    10000: (204, 219, 255)}


def adjust_color_temperature(frame,  temp_variable):
    frame = frame.astype(np.float64)
    weight_array_temp = np.array([1, 1, 1]) / 255
    temp_array = np.array(KELVIN_TABLE[temp_variable])
    weight_array_temp[0] *= temp_array[2]
    weight_array_temp[1] *= temp_array[1]
    weight_array_temp[2] *= temp_array[0]

    mod_weight_array = (255 * weight_array_temp) / (np.max(frame))
    frame[:, :, 0] *= mod_weight_array[0]
    frame[:, :, 1] *= mod_weight_array[1]
    frame[:, :, 2] *= mod_weight_array[2]
    return frame
