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


# Function that sets the servo to a given position
def set_servo_position(gpio_pin, position, min_pulse=500, max_pulse=2500):
    # Ensure position is within range
    position = max(-1.0, min(1.0, position))
    # Convert position to pulse width
    pulse_width = min_pulse + (position + 1) * (max_pulse - min_pulse) / 2
    # Set servo position
    pi.set_servo_pulsewidth(gpio_pin, pulse_width)


# PID Constants:
kyP = 0.001
kyI = 0.0
kyD = 0.0

kxP = 0.001
kxI = 0.0
kxD = 0.00

# PID Controllers:
pid_x = PID(kxP, kxI, kxD, setpoint=0, output_limits=(-1, 1))
pid_y = PID(kyP, kyI, kyD, setpoint=0, output_limits=(-1, 1))


# Moves the motor according to the instructions given by the PID, and the current position
def adjust_servo(x, y):
    set_servo_position(x_servo_pin, pid_x(x))
    # Has to be -1 because it is reversed
    set_servo_position(y_servo_pin, pid_y(y))


def generate_line_trajectory(start_x, start_y, end_x, end_y, num_points=50):
    """
    Generate waypoints along a straight line between two points.
    
    Args:
        start_x, start_y: Starting coordinates (-100 to 100)
        end_x, end_y: Ending coordinates (-100 to 100)
        num_points: Number of waypoints to generate
    
    Returns:
        List of (x, y) tuples in coordinate space
    """
    x_points = np.linspace(start_x, end_x, num_points)
    y_points = np.linspace(start_y, end_y, num_points)
    return list(zip(x_points, y_points))


def generate_arc_trajectory(center_x, center_y, radius, start_angle, end_angle, num_points=50):
    """
    Generate waypoints along an arc.
    
    Args:
        center_x, center_y: Center of the arc (-100 to 100)
        radius: Radius of the arc in coordinate units
        start_angle: Starting angle in degrees (0 = right, 90 = up)
        end_angle: Ending angle in degrees
        num_points: Number of waypoints to generate
    
    Returns:
        List of (x, y) tuples in coordinate space
    """
    # Convert angles to radians
    start_rad = math.radians(start_angle)
    end_rad = math.radians(end_angle)
    
    # Generate angles
    angles = np.linspace(start_rad, end_rad, num_points)
    
    # Calculate points along the arc
    trajectory = []
    for angle in angles:
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        # Clamp to valid range
        x = max(-100, min(100, x))
        y = max(-100, min(100, y))
        trajectory.append((x, y))
    
    return trajectory


def follow_trajectory(cap, trajectory, tolerance=10, max_time_per_point=30):
    """
    Follow a trajectory of waypoints.
    
    Args:
        cap: Video capture object
        trajectory: List of (x, y) tuples in coordinate space
        tolerance: Distance in pixels to consider a waypoint reached
        max_time_per_point: Maximum seconds to try reaching each waypoint
    """
    for idx, (target_x, target_y) in enumerate(trajectory):
        print(f"\n--- Waypoint {idx + 1}/{len(trajectory)} ---")
        print(f"Target: ({target_x:.1f}, {target_y:.1f})")
        
        # Convert to pixel coordinates
        target_x_px, target_y_px = loc.coordinates_to_pixels(target_x, target_y)
        
        # Update PID setpoints
        pid_x.setpoint = target_x_px
        pid_y.setpoint = target_y_px
        
        # Track time at this waypoint
        start_time = time.time()
        settled_count = 0
        required_settled_frames = 10  # Require stable position for N frames
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("Failed to read frame")
                break
            
            # Find the centroid of the droplet
            centroid, annotated_frame = loc.find_centroid(frame)
            
            if centroid is not None:
                x_error, y_error = loc.find_error(target_x_px, target_y_px, centroid)
                normalized_x, normalized_y = loc.pixels_to_coordinates(centroid[0], centroid[1])
                
                print(f"Current: ({normalized_x:.1f}, {normalized_y:.1f}), Error: ({x_error:.1f}, {y_error:.1f})")
                
                # Check if we've reached the waypoint
                if abs(x_error) < tolerance and abs(y_error) < tolerance:
                    settled_count += 1
                    if settled_count >= required_settled_frames:
                        print(f"Waypoint {idx + 1} reached!")
                        break
                else:
                    settled_count = 0
                
                # Continuously adjust the servo motors based on the error
                adjust_servo(centroid[0], centroid[1])
                
                # Display the annotated frame
                cv2.imshow('Red Droplet Detection', annotated_frame)
                
                # Check for timeout
                if time.time() - start_time > max_time_per_point:
                    print(f"Timeout at waypoint {idx + 1}, moving to next")
                    break
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    return False  # Signal to quit
            
            else:
                print("Droplet not detected")
                cv2.imshow('Red Droplet Detection', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    return False
        
        # Small pause between waypoints
        time.sleep(0.1)
    
    return True  # Completed successfully


# Function that is run on the Pi
def main():
    # Start video capture
    cap = cv2.VideoCapture(0)
    
    # Zero Servos (0 is the neutral position)
    set_servo_position(x_servo_pin, 0)
    set_servo_position(y_servo_pin, 0)
    
    # Choose trajectory type
    print("\n=== Droplet Trajectory Control ===")
    print("1. Single point")
    print("2. Line trajectory")
    print("3. Arc trajectory")
    
    choice = input("Select mode (1/2/3): ")
    
    if choice == "1":
        # Original single point mode
        req_x = int(input("Enter x coordinate (-100 to 100): "))
        req_y = int(input("Enter y coordinate (-100 to 100): "))
        
        if req_x < -100 or req_x > 100 or req_y < -100 or req_y > 100:
            print("Coordinates out of range.")
            return
        
        trajectory = [(req_x, req_y)]
    
    elif choice == "2":
        # Line trajectory mode
        print("\n--- Line Trajectory ---")
        start_x = int(input("Enter start x coordinate (-100 to 100): "))
        start_y = int(input("Enter start y coordinate (-100 to 100): "))
        end_x = int(input("Enter end x coordinate (-100 to 100): "))
        end_y = int(input("Enter end y coordinate (-100 to 100): "))
        num_points = int(input("Enter number of waypoints (default 50): ") or "50")
        
        if any(c < -100 or c > 100 for c in [start_x, start_y, end_x, end_y]):
            print("Coordinates out of range.")
            return
        
        trajectory = generate_line_trajectory(start_x, start_y, end_x, end_y, num_points)
        print(f"Generated {len(trajectory)} waypoints along line")
    
    elif choice == "3":
        # Arc trajectory mode
        print("\n--- Arc Trajectory ---")
        center_x = int(input("Enter center x coordinate (-100 to 100): "))
        center_y = int(input("Enter center y coordinate (-100 to 100): "))
        radius = float(input("Enter radius (in coordinate units): "))
        start_angle = float(input("Enter start angle (degrees, 0=right, 90=up): "))
        end_angle = float(input("Enter end angle (degrees): "))
        num_points = int(input("Enter number of waypoints (default 50): ") or "50")
        
        if center_x < -100 or center_x > 100 or center_y < -100 or center_y > 100:
            print("Center coordinates out of range.")
            return
        
        trajectory = generate_arc_trajectory(center_x, center_y, radius, start_angle, end_angle, num_points)
        print(f"Generated {len(trajectory)} waypoints along arc")
    
    else:
        print("Invalid choice.")
        return
    
    # Follow the trajectory
    print("\nStarting trajectory...")
    time.sleep(1)  # Brief pause before starting
    
    success = follow_trajectory(cap, trajectory)
    
    if success:
        print("\n✓ Trajectory completed successfully!")
    else:
        print("\n✗ Trajectory interrupted")
    
    cap.release()
    cv2.destroyAllWindows()
    pi.stop()


if __name__ == "__main__":
    main()
