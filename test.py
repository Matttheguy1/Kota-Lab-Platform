import time
import math
import cv2
from gpiozero import Servo
import numpy as np
from simple_pid import PID


# Servo Constants:

x_servo_zero = 0.5
y_servo_zero = 0.5

transformation_factor = 1/5

x_servo_pin = 1-20
y_servo_pin = 1-20

x_servo = Servo(x_servo_pin)
y_servo = Servo(y_servo_pin)


# Function that zeroes the servo
def zero_servo():
    x_servo.value = x_servo_zero
    y_servo.value = y_servo_zero


# This is for angles, later change this to work off distances provides, then platform angles
def set_servos_pos(x_pos, y_pos):
    x_servo.value = x_pos
    y_servo.value = y_pos


# PID
kxP = 0.1
kxI = 0.1
kxD = 0.05

kyP = 0.1
kyI = 0.1
kyD = 0.05

pid_x = PID(kxP, kxI, kxD, setpoint=0, output_limits=(-1, 1))
pid_y = PID(kyP, kyI, kyD, setpoint=0, output_limits=(-1, 1))


# Finds the centroid of the droplet
def find_centroid(image):

    # Convert to HSV color space
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Define range for red color
    # Red wraps around in HSV, so we need two masks
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])

    # Create masks for red regions
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)

    # Clean up the mask
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None, image

    # Find the largest contour (assuming it's the droplet)
    largest_contour = max(contours, key=cv2.contourArea)

    # Calculate centroid using moments
    M = cv2.moments(largest_contour)
    if M["m00"] == 0:
        return None, image

    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])

    # Draw the centroid on the image (for visualization)
    cv2.circle(image, (cx, cy), 5, (0, 255, 0), -1)
    cv2.drawContours(image, [largest_contour], -1, (0, 255, 0), 2)

    return (cx, cy), image


# Function that determines and returns the x and y error
def find_error(x_desired, y_desired, centroid):
    cx = centroid[0]
    cy = centroid[1]
    x_error = cx - x_desired
    y_error = cy - y_desired
    return x_error, y_error


# Example usage
def main():

    # Start video capture
    cap = cv2.VideoCapture(0)
    # Get the desired coordinates as integers
    req_x = int(input("Enter x coordinate"))
    req_y = int(input("Enter y coordinate"))
    pid_x.setpoint = req_x
    pid_y.setpoint = req_y

    # Loop that constantly updates vision and data
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        centroid, annotated_frame = find_centroid(frame)

        if centroid is not None:
            x_error, y_error = find_error(req_x, req_y, centroid)
            print(f"Droplet centroid at: {centroid}")
            print(f"Droplet error: {x_error, y_error}")

        cv2.imshow('Red Droplet Detection', annotated_frame)
        # x_servo.value = pid_x(centroid[0])
        # y_servo.value = pid_y(centroid[1])

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
