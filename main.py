import time
import math
import cv2
from gpiozero import Servo
import numpy as np
from simple_pid import PID
import localization as loc
import pigpio

pi = pigpio.pi()

# Servo Constants:
x_servo_pin = 18
y_servo_pin = 17

# Set up the servo on GPIO pin 18
# y_servo = Servo(17)
# x_servo = Servo(18)



# Define the pulse width range for the servo,
#Deprecated because we switched from pigpio to gpiozero
min_PW = 1000  # Minimum pulse width in microseconds
max_PW = 2000  # Maximum pulse width in microseconds


# # Function that sets the position of the x servo with (-1,1) as the range
# def set_x_position(value):
#     # Sets servo to given value
#     x_servo.value = value

# # Function that sets the position of the y servo with (-1,1) as the range
# def set_y_position(value):
#     # Sets servo to given value
#     y_servo.value = value


def set_servo_position(gpio_pin, position, min_pulse=500, max_pulse=2500):
# Ensure position is within range
    position = max(-1.0, min(1.0, position))
    # Convert position to pulse width
    pulse_width = min_pulse + (position + 1) * (max_pulse - min_pulse) / 2
    # Set servo position
    pi.set_servo_pulsewidth(gpio_pin, pulse_width)

# Function that zeroes the servo
# def zero_servo():
#     set_y_position(0.1)
#     set_x_position(0.1)


# PID
# Set to 0 everything except p for now, current full P control is working.
kyP = 0.05
kyI = 0.0
kyD = 0.0

kxP = 0.05
kxI = 0.0
kxD = 0.00


pid_x = PID(kxP, kxI, kxD, setpoint=0, output_limits=(-1, 1))
pid_y = PID(kyP, kyI, kyD, setpoint=0, output_limits=(-1, 1))


#Moves the motor according to the instructions given by the PID, and the current position
def adjust_servo(x, y):
    set_servo_position(x_servo_pin, pid_x(x))
    # Has to be -1 because it is reversed
    set_servo_position(y_servo_pin,-1*pid_y(y))


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
            print(f"Droplet centroid at: {centroid}")
            print(f"Droplet error: {x_error, y_error}")
            if abs(x_error) > 10 and abs(y_error) > 10:
                print("Droplet centered!")
                adjust_servo(centroid[0],centroid[1])
                break
            adjust_servo(centroid[0],centroid[1])

        cv2.imshow('Red Droplet Detection', annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
