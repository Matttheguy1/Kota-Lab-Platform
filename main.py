import time
import math
import cv2
import numpy as np
import matplotlib.pyplot as plt
from simple_pid import PID
import localization as loc
import pigpio

# Initialize pigpio
pi = pigpio.pi()

# Servo Constants:
x_servo_pin = 17
y_servo_pin = 18

def set_servo_position(gpio_pin, position, min_pulse=500, max_pulse=2500):
    position = max(-1.0, min(1.0, position))
    pulse_width = min_pulse + (position + 1) * (max_pulse - min_pulse) / 2
    pi.set_servo_pulsewidth(gpio_pin, pulse_width)

# PID Constants:
#Top Servo 7 DOF
#kyP, kyI, kyD = 0.002, 0.0, 0.00015
#Top Servo 2 DOF
kyP, kyI, kyD = 0.001, 0.00, 0.0

#Bottom servo 7 DOF
#kxP, kxI, kxD = 0.002, 0.0, 0.00015
#Bottom servo 2 DOF (0.001 P value is good)
kxP, kxI, kxD = 0.001, 0.00, 0.000

# PID Controllers:
pid_x = PID(kxP, kxI, kxD, setpoint=0, output_limits=(-0.15, 0.15))
pid_y = PID(kyP, kyI, kyD, setpoint=0, output_limits=(-0.15, 0.15))

def adjust_servo(x, y):
    set_servo_position(x_servo_pin,1* pid_x(x))
    set_servo_position(y_servo_pin,1 * pid_y(y))

# ─────────────────────────────────────────────
# Trajectory generators
# ─────────────────────────────────────────────

def generate_line_trajectory(start_x, start_y, end_x, end_y, num_points=50):
    x_points = np.linspace(start_x, end_x, num_points)
    y_points = np.linspace(start_y, end_y, num_points)
    return list(zip(x_points, y_points))

def generate_arc_trajectory(center_x, center_y, radius, start_angle, end_angle, num_points=50):
    start_rad = math.radians(start_angle)
    end_rad   = math.radians(end_angle)
    angles    = np.linspace(start_rad, end_rad, num_points)
    trajectory = []
    for angle in angles:
        x = max(-100, min(100, center_x + radius * math.cos(angle)))
        y = max(-100, min(100, center_y + radius * math.sin(angle)))
        trajectory.append((x, y))
    return trajectory

# ─────────────────────────────────────────────
# Trajectory display window logic
# ─────────────────────────────────────────────

CANVAS_W, CANVAS_H, PADDING = 600, 600, 50
C_BG, C_GRID_MINOR, C_GRID_MAJOR = (15, 15, 15), (40, 40, 40), (70, 70, 70)
C_AXIS, C_LABEL, C_TRAJ, C_TRAJ_DONE = (110, 110, 110), (130, 130, 130), (80, 80, 200), (60, 160, 60)
C_WAYPOINT, C_TARGET, C_DROPLET, C_POINT = (100, 100, 180), (0, 210, 170), (50, 60, 240), (0, 210, 170)
C_TEXT, C_BORDER = (210, 210, 210), (180, 180, 180)

def _coord_to_canvas(cx, cy):
    usable_w = CANVAS_W - 2 * PADDING
    usable_h = CANVAS_H - 2 * PADDING
    px = int(PADDING + (cx + 100) / 200.0 * usable_w)
    py = int(PADDING + (100 - cy) / 200.0 * usable_h)
    return (px, py)

def draw_coordinate_canvas():
    canvas = np.full((CANVAS_H, CANVAS_W, 3), C_BG, dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX
    for v in range(-100, 101, 10):
        px, _ = _coord_to_canvas(v, 0)
        color, thick = (C_AXIS, 1) if v == 0 else ((C_GRID_MAJOR, 1) if v % 50 == 0 else (C_GRID_MINOR, 1))
        cv2.line(canvas, (px, PADDING), (px, CANVAS_H - PADDING), color, thick)
        _, py = _coord_to_canvas(0, v)
        cv2.line(canvas, (PADDING, py), (CANVAS_W - PADDING, py), color, thick)
    cv2.rectangle(canvas, (PADDING, PADDING), (CANVAS_W - PADDING, CANVAS_H - PADDING), C_BORDER, 1)
    return canvas

def draw_trajectory_on_canvas(canvas, trajectory, current_idx=0, droplet_coord=None, target_coord=None):
    font = cv2.FONT_HERSHEY_SIMPLEX
    pts = [_coord_to_canvas(x, y) for x, y in trajectory]

    for pt in pts: cv2.circle(canvas, pt, 2, C_WAYPOINT, -1)
    if current_idx < len(pts) - 1:
        cv2.polylines(canvas, [np.array(pts[current_idx:], np.int32)], False, C_TRAJ, 2)
    if current_idx > 0:
        cv2.polylines(canvas, [np.array(pts[:current_idx + 1], np.int32)], False, C_TRAJ_DONE, 2)

    if target_coord:
        tx, ty = _coord_to_canvas(*target_coord)
        cv2.circle(canvas, (tx, ty), 5, C_TARGET, 1)

    if droplet_coord:
        dx, dy = _coord_to_canvas(*droplet_coord)
        cv2.circle(canvas, (dx, dy), 7, C_DROPLET, -1)

    return canvas

# ─────────────────────────────────────────────
# Velocity graph
# ─────────────────────────────────────────────

def show_velocity_graph(timestamps, velocities):
    """Display a velocity vs time graph at the end of a run."""
    if len(timestamps) < 2:
        print("Not enough data to plot velocity graph.")
        return

    timestamps = np.array(timestamps)
    velocities = np.array(velocities)
    t = timestamps - timestamps[0]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('Droplet Velocity Analysis', fontsize=14, fontweight='bold')

    # Velocity vs Time
    axes[0].plot(t, velocities, color='royalblue', linewidth=2)
    axes[0].fill_between(t, velocities, alpha=0.15, color='royalblue')
    axes[0].set_xlabel('Time (s)')
    axes[0].set_ylabel('Velocity (px/s)')
    axes[0].set_title('Velocity vs Time')
    axes[0].grid(True, alpha=0.3)

    # Velocity histogram
    axes[1].hist(velocities, bins=20, color='royalblue', alpha=0.75, edgecolor='white')
    axes[1].set_xlabel('Velocity (px/s)')
    axes[1].set_ylabel('Frequency')
    axes[1].set_title('Velocity Distribution')
    axes[1].grid(True, alpha=0.3)

    stats = (f"Mean: {velocities.mean():.1f} px/s\n"
             f"Max:  {velocities.max():.1f} px/s\n"
             f"Min:  {velocities.min():.1f} px/s")
    axes[1].text(0.97, 0.97, stats, transform=axes[1].transAxes,
                 verticalalignment='top', horizontalalignment='right',
                 fontsize=9, fontfamily='monospace',
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

    plt.tight_layout()
    plt.savefig('velocity_results.png', dpi=150, bbox_inches='tight')
    print("Velocity graph saved as 'velocity_results.png'")
    plt.show()

# ─────────────────────────────────────────────
# Trajectory follower with LIVE FEED
# ─────────────────────────────────────────────

def follow_trajectory(cap, trajectory, tolerance=15, max_time_per_point=30):
    vel_timestamps = []
    vel_values     = []
    prev_centroid  = None
    prev_time      = None

    for idx, (target_x, target_y) in enumerate(trajectory):
        print(f"Tracking Waypoint {idx + 1}/{len(trajectory)}: ({target_x}, {target_y})")

        target_x_px, target_y_px = loc.coordinates_to_pixels(target_x, target_y)
        pid_x.setpoint = target_x_px
        pid_y.setpoint = target_y_px

        start_time    = time.time()
        settled_count = 0

        while True:
            ret, frame = cap.read()
            if not ret: break

            centroid, _ = loc.find_centroid(frame)
            droplet_norm = None
            now = time.time()

            if centroid is not None:
                x_error, y_error = loc.find_error(target_x_px, target_y_px, centroid)
                norm_x, norm_y   = loc.pixels_to_coordinates(centroid[0], centroid[1])
                droplet_norm     = (norm_x, norm_y)

                # Velocity calculation
                if prev_centroid is not None and prev_time is not None:
                    dt = now - prev_time
                    if dt > 0:
                        speed = np.linalg.norm(np.array(centroid) - np.array(prev_centroid)) / dt
                        vel_timestamps.append(now)
                        vel_values.append(speed)

                prev_centroid = centroid
                prev_time     = now

                # Overlay on live feed
                cv2.circle(frame, (int(centroid[0]), int(centroid[1])), 10, (0, 255, 0), 2)
                cv2.drawMarker(frame, (int(target_x_px), int(target_y_px)),
                               (0, 255, 255), cv2.MARKER_CROSS, 20, 2)

                if vel_values:
                    cv2.putText(frame, f"Vel: {vel_values[-1]:.1f} px/s",
                                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)

                if abs(x_error) < tolerance and abs(y_error) < tolerance:
                    settled_count += 1
                    if settled_count >= 10: break
                else:
                    settled_count = 0

                adjust_servo(centroid[0], centroid[1])

            canvas = draw_coordinate_canvas()
            canvas = draw_trajectory_on_canvas(canvas, trajectory, idx, droplet_norm, (target_x, target_y))

            cv2.imshow('Trajectory Map', canvas)
            cv2.imshow('Live Camera Feed', frame)

            if time.time() - start_time > max_time_per_point: break
            if cv2.waitKey(1) & 0xFF == ord('q'):
                show_velocity_graph(vel_timestamps, vel_values)
                return False

    show_velocity_graph(vel_timestamps, vel_values)
    return True

# ─────────────────────────────────────────────
# Main Entry Point with Original Menu
# ─────────────────────────────────────────────

def main():
    cap = cv2.VideoCapture(0)
    set_servo_position(x_servo_pin,-0.1)
    set_servo_position(y_servo_pin,-0.1)

    print("\n=== Droplet Trajectory Control ===")
    print("1. Single point")
    print("2. Line trajectory")
    print("3. Arc trajectory")

    choice = input("Select mode (1/2/3): ")

    if choice == "1":
        req_x = int(input("Enter x (-100 to 100): "))
        req_y = int(input("Enter y (-100 to 100): "))
        trajectory = [(req_x, req_y)]

    elif choice == "2":
        start_x = int(input("Start x: ")); start_y = int(input("Start y: "))
        end_x = int(input("End x: ")); end_y = int(input("End y: "))
        num = int(input("Points (default 50): ") or "50")
        trajectory = generate_line_trajectory(start_x, start_y, end_x, end_y, num)

    elif choice == "3":
        cx = int(input("Center x: ")); cy = int(input("Center y: "))
        r = float(input("Radius: "))
        s_ang = float(input("Start Angle: "))
        e_ang = float(input("End Angle: "))
        num = int(input("Points (default 50): ") or "50")
        trajectory = generate_arc_trajectory(cx, cy, r, s_ang, e_ang, num)
    else:
        print("Invalid choice."); return

    preview = draw_coordinate_canvas()
    preview = draw_trajectory_on_canvas(preview, trajectory)
    cv2.imshow('Trajectory Map', preview)
    print("\nPress any key in the window to start...")
    cv2.waitKey(0)

    success = follow_trajectory(cap, trajectory)
    print("\nDone!" if success else "\nInterrupted.")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
