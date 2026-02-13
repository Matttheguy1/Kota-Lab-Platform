\import cv2
import numpy as np
import matplotlib.pyplot as plt
from collections import deque
import time

# Parameters
DURATION = 10  # seconds
TIME_STEP = 0.1  # seconds
FPS = int(1 / TIME_STEP)

# Storage for position and velocity data
positions = []
velocities = []
timestamps = []

# Initialize webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 30)

# Define red color range in HSV
lower_red1 = np.array([0, 120, 70])
upper_red1 = np.array([10, 255, 255])
lower_red2 = np.array([170, 120, 70])
upper_red2 = np.array([180, 255, 255])

print("Starting red circle tracking for 10 seconds...")
print("Press 'q' to quit early")

start_time = time.time()
prev_pos = None
prev_time = None
frame_count = 0

while True:
    current_time = time.time() - start_time
    
    # Check if duration exceeded
    if current_time >= DURATION:
        break
    
    ret, frame = cap.read()
    if not ret:
        break
    
    # Sample at TIME_STEP intervals
    if frame_count % int(30 * TIME_STEP) == 0:
        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Create masks for red color (red wraps around in HSV)
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = cv2.bitwise_or(mask1, mask2)
        
        # Morphological operations to reduce noise
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Find largest contour (assumed to be the red circle)
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Get minimum enclosing circle
            ((x, y), radius) = cv2.minEnclosingCircle(largest_contour)
            
            if radius > 10:  # Minimum radius threshold
                # Store position
                current_pos = np.array([x, y])
                positions.append(current_pos)
                timestamps.append(current_time)
                
                # Calculate velocity
                if prev_pos is not None and prev_time is not None:
                    dt = current_time - prev_time
                    if dt > 0:
                        displacement = current_pos - prev_pos
                        velocity = displacement / dt
                        velocity_magnitude = np.linalg.norm(velocity)
                        velocities.append(velocity_magnitude)
                    else:
                        velocities.append(0)
                else:
                    velocities.append(0)
                
                prev_pos = current_pos
                prev_time = current_time
                
                # Draw circle and center
                cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 0), 2)
                cv2.circle(frame, (int(x), int(y)), 5, (0, 0, 255), -1)
                
                # Display velocity
                if velocities:
                    cv2.putText(frame, f"Vel: {velocities[-1]:.1f} px/s", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Display time remaining
    time_left = DURATION - current_time
    cv2.putText(frame, f"Time: {time_left:.1f}s", 
               (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Show frame
    cv2.imshow('Red Circle Tracking', frame)
    
    frame_count += 1
    
    # Break on 'q' press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()

print(f"Tracking complete! Collected {len(positions)} data points")

# Plot the data
if positions and velocities:
    positions = np.array(positions)
    velocities = np.array(velocities)
    timestamps = np.array(timestamps)
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Position vs Time (X and Y)
    axes[0, 0].plot(timestamps, positions[:, 0], 'b-', label='X position', linewidth=2)
    axes[0, 0].plot(timestamps, positions[:, 1], 'r-', label='Y position', linewidth=2)
    axes[0, 0].set_xlabel('Time (s)')
    axes[0, 0].set_ylabel('Position (pixels)')
    axes[0, 0].set_title('Position vs Time')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # Velocity vs Time
    axes[0, 1].plot(timestamps, velocities, 'g-', linewidth=2)
    axes[0, 1].set_xlabel('Time (s)')
    axes[0, 1].set_ylabel('Velocity (pixels/s)')
    axes[0, 1].set_title('Velocity vs Time')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Trajectory (X vs Y)
    axes[1, 0].plot(positions[:, 0], positions[:, 1], 'b-', linewidth=2)
    axes[1, 0].plot(positions[0, 0], positions[0, 1], 'go', markersize=10, label='Start')
    axes[1, 0].plot(positions[-1, 0], positions[-1, 1], 'ro', markersize=10, label='End')
    axes[1, 0].set_xlabel('X Position (pixels)')
    axes[1, 0].set_ylabel('Y Position (pixels)')
    axes[1, 0].set_title('Trajectory')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].invert_yaxis()  # Invert Y to match screen coordinates
    
    # Velocity histogram
    axes[1, 1].hist(velocities, bins=20, color='green', alpha=0.7, edgecolor='black')
    axes[1, 1].set_xlabel('Velocity (pixels/s)')
    axes[1, 1].set_ylabel('Frequency')
    axes[1, 1].set_title('Velocity Distribution')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('tracking_results.png', dpi=150, bbox_inches='tight')
    print("Graph saved as 'tracking_results.png'")
    plt.show()
else:
    print("No data collected. Make sure a red circle was visible during tracking.")
