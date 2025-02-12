import time
import math
import cv2
import pigpio
import numpy as np
from simple_pid import PID
import localization as loc

# Servo Constants:

x_servo_zero = 0.5
y_servo_zero = 0.5
transformation_factor = 1/5

# x_servo_pin = 1-20
# y_servo_pin = 1-20

# x_servo = Servo(x_servo_pin)
# y_servo = Servo(y_servo_pin)


# Function that zeroes the servo
def zero_servo():
    pass
    # x_servo.value = x_servo_zero
    # y_servo.value = y_servo_zero


# This is for angles, later change this to work off distances provides, then platform angles
def set_servos_pos(x_pos, y_pos):
    pass
    # x_servo.value = x_pos
    # y_servo.value = y_pos


# PID
kyP = 0.1
kyI = 0.1
kyD = 0.05

kxP = 0.1
kxI = 0.1
kxD = 0.05


pid_x = PID(kxP, kxI, kxD, setpoint=0, output_limits=(-1, 1))
pid_y = PID(kyP, kyI, kyD, setpoint=0, output_limits=(-1, 1))




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

        centroid, annotated_frame = loc.find_centroid(frame)

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
