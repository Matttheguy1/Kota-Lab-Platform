import numpy as np
import cv2
from picamera2 import Picamera2

#Experimentally determine later
transformation_factor = 1/2.5
# Initialize the PiCamera2 object
picam2 = Picamera2()
picam2.start()


def localize():

    while True:
        # Capture a frame from the camera
        frame = picam2.capture_array()

        # Convert the frame to the HSV color space
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Define the range of red color in HSV
        lower_red = np.array([0, 100, 100])
        upper_red = np.array([10, 255, 255])

        # Create a mask for the red color
        mask = cv2.inRange(hsv_frame, lower_red, upper_red)

        # Find contours in the mask
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Iterate through the contours and find the largest one
        for contour in contours:
            if cv2.contourArea(contour) > 100:
                # Get the coordinates of the center of the contour
                M = cv2.moments(contour)
                if M['m00'] != 0:
                    cx = int(M['m10'] / M['m00'])
                    cy = int(M['m01'] / M['m00'])
                    print(f"Red circle found at ({cx}, {cy})")

        # Display the frame with the detected circle (optional)
        cv2.imshow('Red Circle Detection', frame)

        # Press 'q' to exit the loop
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        transformed_x, transformed_y = cx*transformation_factor, cy*transformation_factor

        return transformed_x, transformed_y

picam2.stop()
cv2.destroyAllWindows()