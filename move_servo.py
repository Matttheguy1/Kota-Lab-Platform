#Just like how the name suggests, this code moves the servo motor to a specific angle.
# It uses the pigpio library to control the GPIO pins of a Raspberry Pi, using user input to set the desired angle for the servo motor. The code also includes a function to set the servo position based on the desired angle, and it ensures that the angle is within a specified range. The code is designed to be run on a Raspberry Pi with a connected servo motor.
import pigpio

# Define GPIO pins for the servos
SERVO_1_PIN = 17
SERVO_2_PIN = 18

# Pulse width range for typical servos
MIN_PULSE_WIDTH = 500   # microseconds
MAX_PULSE_WIDTH = 2500  # microseconds

# Function to convert angle (0-180) to pulse width
def angle_to_pulse(angle):
    angle = max(0, min(180, angle))  # Clamp angle to 0-180
    return int(MIN_PULSE_WIDTH + (angle / 180.0) * (MAX_PULSE_WIDTH - MIN_PULSE_WIDTH))

def main():
    pi = pigpio.pi()
    if not pi.connected:
        print("Could not connect to pigpio daemon.")
        return

    try:
        while True:
            try:
                angle1 = int(input("Enter angle for Servo 1 (0-180): "))
                angle2 = int(input("Enter angle for Servo 2 (0-180): "))
            except ValueError:
                print("Invalid input. Please enter integers between 0 and 180.")
                continue

            pulse1 = angle_to_pulse(angle1)
            pulse2 = angle_to_pulse(angle2)

            pi.set_servo_pulsewidth(SERVO_1_PIN, pulse1)
            pi.set_servo_pulsewidth(SERVO_2_PIN, pulse2)

            print(f"Moved Servo 1 to {angle1}°, pulse width: {pulse1}μs")
            print(f"Moved Servo 2 to {angle2}°, pulse width: {pulse2}μs")

    except KeyboardInterrupt:
        print("\nExiting...")

    finally:
        # Stop servo pulses
        pi.set_servo_pulsewidth(SERVO_1_PIN, 0)
        pi.set_servo_pulsewidth(SERVO_2_PIN, 0)
        pi.stop()

if __name__ == "__main__":
    main()
