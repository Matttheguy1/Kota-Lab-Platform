import time
import math
import cv2
import pigpio
import numpy as np
from simple_pid import PID
import localization as loc

pi = pigpio.pi()

# Set up the servo on GPIO pin 18
y_servo = 17
x_servo = 18

# Define the pulse width range for the servo
min_PW = 1000  # Minimum pulse width in microseconds
max_PW = 2000  # Maximum pulse width in microseconds


# Function that sets the position of the x servo with (-1,1) as the range
def set_x_position(value):
    # Convert the input value (-1 to 1) to pulse width
    pulse_width = ((value + 1) / 2) * (max_PW - min_PW) + min_PW
    pi.set_servo_pulsewidth(x_servo, pulse_width)

# Function that sets the position of the y servo with (-1,1) as the range
def set_y_position(value):
    # Convert the input value (-1 to 1) to pulse width
    pulse_width = ((value + 1) / 2) * (max_PW - min_PW) + min_PW
    pi.set_servo_pulsewidth(y_servo, pulse_width)

# Function that zeroes the servo
def zero_servo():
    set_y_position(0.1)
    set_x_position(0.1)


# PID
kyP = 0.1
kyI = 0.1
kyD = 0.05

kxP = 0.1
kxI = 0.1
kxD = 0.05


pid_x = PID(kxP, kxI, kxD, setpoint=0, output_limits=(-1, 1))
pid_y = PID(kyP, kyI, kyD, setpoint=0, output_limits=(-1, 1))


#Moves the motor according to the instructions given by the PID, and the current position
def adjust_servo(x, y):
    set_x_position(pid_x(x))
    set_y_position(pid_y(y))
    time.sleep(0.05)




def main():

    # Start video capture
    cap = cv2.VideoCapture(0)
    # Get the desired coordinates as integers
    req_x = int(input("Enter x coordinate"))
    req_y = int(input("Enter y coordinate"))

    # Set the PID setpoints based on input
    pid_x.setpoint = req_x
    pid_y.setpoint = req_y

    # Loop that constantly updates vision and setpoints
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        centroid, annotated_frame = loc.find_centroid(frame)

        if centroid is not None:
            x_error, y_error = loc.find_error(req_x, req_y, centroid)
            set_x_position(pid_x(x_error))
            set_y_position(pid_y(y_error))
            print(f"Droplet centroid at: {centroid}")
            print(f"Droplet error: {x_error, y_error}")

        cv2.imshow('Red Droplet Detection', annotated_frame)
        adjust_servo(centroid[0], centroid[1])

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
