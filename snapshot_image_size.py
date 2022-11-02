import cv2

print("Starting connection...")
vid = cv2.VideoCapture(0)
print("End connection...")

# Get Initial Image Size
width = vid.get(cv2.CAP_PROP_FRAME_WIDTH)
height = vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
print("Image Size: {}x{}".format(width, height))

# Set Image Size
vid.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

# Get Updated Image Size
width = vid.get(cv2.CAP_PROP_FRAME_WIDTH)
height = vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
print("Image Size: {}x{}".format(width, height))

# Get and save Snapshot
ret, frame = vid.read()
cv2.imwrite("snap.png", frame)

print("Done")


