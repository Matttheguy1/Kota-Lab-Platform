import time
import math
import cv2
from gpiozero import Servo
import numpy as np
from simple_pid import PID
import localization as loc
import pigpio
import csv

# Initialize pigpio
pi = pigpio.pi()

# Servo Constants:
x_servo_pin = 18
y_servo_pin = 17


#Function that sets the servo to a given position
def set_servo_position(gpio_pin, position, min_pulse=500, max_pulse=2500):
# Ensure position is within range
    position = max(-1.0, min(1.0, position))
    # Convert position to pulse width
    pulse_width = min_pulse + (position + 1) * (max_pulse - min_pulse) / 2
    # Set servo position
    pi.set_servo_pulsewidth(gpio_pin, pulse_width)



# PID Constants:
kyP = 0.0155
kyI = 0.0
kyD = 0.0

kxP = 0.0155
kxI = 0.0
kxD = 0.00

#PID Controllers:
pid_x = PID(kxP, kxI, kxD, setpoint=0, output_limits=(-1, 1))
pid_y = PID(kyP, kyI, kyD, setpoint=0, output_limits=(-1, 1))


# Moves the motor according to the instructions given by the PID, and the current position
def adjust_servo(x, y):
    set_servo_position(x_servo_pin, pid_x(x))
    # Has to be -1 because it is reversed
    set_servo_position(y_servo_pin,-1*pid_y(y))

# Function that is run on the Pi
def main():

    # Start video capture
    cap = cv2.VideoCapture(0)
    
    # Zero Servos (0.1 is the neutral position)
    set_servo_position(x_servo_pin, 0.1)
    set_servo_position(y_servo_pin, 0.1)

    # Get the desired x coordinate as an integer
    req_x = int(input("Enter x coordinate (-100 to 100): "))

    # Ensure the coordinates are within the range
    if req_x < -100 or req_x > 100:
        print("X coordinate out of range. Please enter a value between -100 and 100.")
        return
    
    # Get the desired y coordinate as an integer
    req_y = int(input("Enter y coordinate (-100 to 100): "))

    # Ensure the coordinates are within the range
    if req_y < -100 or req_y > 100:
        print("X coordinate out of range. Please enter a value between -100 and 100.")
        return
    #Transform the coordinates to pixel coordinates
    (req_x, req_y) = loc.coordinates_to_pixels(req_x, req_y)

    # Set the PID setpoints based on input
    pid_x.setpoint = req_x
    pid_y.setpoint = req_y

    #Make sure the loop doesn't run forever
    temp_counter = 0
    # Loop that constantly updates vision and setpoints
    while True:
        ret, frame = cap.read()

        # Check if frame is read correctly
        if not ret:
            break
        #Find the centroid of the droplet
        centroid, annotated_frame = loc.find_centroid(frame)
        if centroid is not None:
            x_error, y_error = loc.find_error(req_x, req_y, centroid)
            normalized_x, normalized_y = loc.pixels_to_coordinates(centroid[0], centroid[1])
            print(f"Normalized coordinates: {normalized_x, normalized_y}")
            print(f"Droplet error: {x_error, y_error}")
                    
            if abs(x_error) < 10 and abs(y_error) < 10:
                print("Droplet is centered")
                
            # Continuously adjust the servo motors based on the error
            adjust_servo(centroid[0],centroid[1])

            #Display the annotated frame with the droplet and centroid
            cv2.imshow('Red Droplet Detection', annotated_frame)
            if temp_counter == 1000:
                break
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            temp_counter+=1

        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
