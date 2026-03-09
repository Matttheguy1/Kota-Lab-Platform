import cv2
import numpy as np
import matplotlib.pyplot as plt
import time

# Parameters
DURATION  = 10   # seconds
TIME_STEP = 0.1  # seconds

# Storage
positions  = []
velocities = []
timestamps = []

# Initialize webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 30)

# Red color range in HSV (unchanged)
lower_red1 = np.array([0,  120, 70])
upper_red1 = np.array([10, 255, 255])
lower_red2 = np.array([170, 120, 70])
upper_red2 = np.array([180, 255, 255])

print("Starting red circle tracking for 10 seconds...")
print("Press 'q' to quit early")

start_time  = time.time()
prev_pos    = None
prev_time   = None
frame_count = 0

while True:
    current_time = time.time() - start_time
    if current_time >= DURATION:
        break

    ret, frame = cap.read()
    if not ret:
        break

    if frame_count % int(30 * TIME_STEP) == 0:
        hsv   = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask  = cv2.bitwise_or(mask1, mask2)

        kernel = np.ones((5, 5), np.uint8)
        mask   = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel)
        mask   = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            largest = max(contours, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(largest)

            if radius > 10:
                current_pos = np.array([x, y])
                positions.append(current_pos.copy())
                timestamps.append(current_time)

                if prev_pos is not None and prev_time is not None:
                    dt    = current_time - prev_time
                    speed = np.linalg.norm(current_pos - prev_pos) / dt if dt > 0 else 0.0
                else:
                    speed = 0.0

                velocities.append(speed)
                prev_pos  = current_pos
                prev_time = current_time

                cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 0), 2)
                cv2.circle(frame, (int(x), int(y)), 5, (0, 0, 255), -1)
                cv2.putText(frame, f"Vel: {speed:.1f} px/s",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    time_left = DURATION - current_time
    cv2.putText(frame, f"Time: {time_left:.1f}s",
                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.imshow('Red Circle Tracking', frame)
    frame_count += 1

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print(f"Tracking complete! Collected {len(positions)} data points")

# ── Plot ──────────────────────────────────────────────────────────────────────
if positions and velocities:
    positions  = np.array(positions)
    velocities = np.array(velocities)
    timestamps = np.array(timestamps)

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Droplet Velocity Analysis', fontsize=14, fontweight='bold')

    # Position vs Time
    axes[0, 0].plot(timestamps, positions[:, 0], 'b-', label='X position', linewidth=2)
    axes[0, 0].plot(timestamps, positions[:, 1], 'r-', label='Y position', linewidth=2)
    axes[0, 0].set_xlabel('Time (s)')
    axes[0, 0].set_ylabel('Position (pixels)')
    axes[0, 0].set_title('Position vs Time')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # Velocity vs Time
    axes[0, 1].plot(timestamps, velocities, color='royalblue', linewidth=2)
    axes[0, 1].fill_between(timestamps, velocities, alpha=0.15, color='royalblue')
    axes[0, 1].set_xlabel('Time (s)')
    axes[0, 1].set_ylabel('Velocity (px/s)')
    axes[0, 1].set_title('Velocity vs Time')
    axes[0, 1].grid(True, alpha=0.3)

    # Trajectory
    axes[1, 0].plot(positions[:, 0], positions[:, 1], 'b-', linewidth=2)
    axes[1, 0].plot(positions[0, 0],  positions[0, 1],  'go', markersize=10, label='Start')
    axes[1, 0].plot(positions[-1, 0], positions[-1, 1], 'ro', markersize=10, label='End')
    axes[1, 0].set_xlabel('X Position (pixels)')
    axes[1, 0].set_ylabel('Y Position (pixels)')
    axes[1, 0].set_title('Trajectory')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].invert_yaxis()

    # Velocity histogram
    axes[1, 1].hist(velocities, bins=20, color='royalblue', alpha=0.75, edgecolor='white')
    axes[1, 1].set_xlabel('Velocity (px/s)')
    axes[1, 1].set_ylabel('Frequency')
    axes[1, 1].set_title('Velocity Distribution')
    axes[1, 1].grid(True, alpha=0.3)

    stats = (f"Mean: {velocities.mean():.1f} px/s\n"
             f"Max:  {velocities.max():.1f} px/s\n"
             f"Min:  {velocities.min():.1f} px/s")
    axes[1, 1].text(0.97, 0.97, stats, transform=axes[1, 1].transAxes,
                    verticalalignment='top', horizontalalignment='right',
                    fontsize=9, fontfamily='monospace',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

    plt.tight_layout()
    plt.savefig('tracking_results.png', dpi=150, bbox_inches='tight')
    print("Graph saved as 'tracking_results.png'")
    plt.show()
else:
    print("No data collected. Make sure a red circle was visible during tracking.")