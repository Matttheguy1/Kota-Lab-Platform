import time
import math
import cv2
import numpy as np
from simple_pid import PID
import localization as loc
import pigpio

# Initialize pigpio
pi = pigpio.pi()

# Servo Constants:
x_servo_pin = 18
y_servo_pin = 17


# Function that sets the servo to a given position
def set_servo_position(gpio_pin, position, min_pulse=500, max_pulse=2500):
    position = max(-1.0, min(1.0, position))
    pulse_width = min_pulse + (position + 1) * (max_pulse - min_pulse) / 2
    pi.set_servo_pulsewidth(gpio_pin, pulse_width)


# PID Constants:
kyP = 0.0155
kyI = 0.0
kyD = 0.0

kxP = 0.0155
kxI = 0.0
kxD = 0.00

# PID Controllers:
pid_x = PID(kxP, kxI, kxD, setpoint=0, output_limits=(-1, 1))
pid_y = PID(kyP, kyI, kyD, setpoint=0, output_limits=(-1, 1))


def adjust_servo(x, y):
    set_servo_position(x_servo_pin, pid_x(x))
    set_servo_position(y_servo_pin, -1 * pid_y(y))


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
# Trajectory display window
# ─────────────────────────────────────────────

# Canvas size in pixels
CANVAS_W = 600
CANVAS_H = 600
PADDING  = 50   # space around the coordinate area

# Colors (BGR)
C_BG          = (15,  15,  15)
C_GRID_MINOR  = (40,  40,  40)
C_GRID_MAJOR  = (70,  70,  70)
C_AXIS        = (110, 110, 110)
C_LABEL       = (130, 130, 130)
C_TRAJ        = (80,  80,  200)   # blue  — full trajectory
C_TRAJ_DONE   = (60,  160,  60)   # green — completed portion
C_WAYPOINT    = (100, 100, 180)   # waypoint dots
C_TARGET      = (0,   210, 170)   # teal crosshair — current target
C_DROPLET     = (50,   60, 240)   # red-orange — droplet
C_POINT       = (0,   210, 170)   # single-point marker
C_TEXT        = (210, 210, 210)
C_BORDER      = (180, 180, 180)


def _coord_to_canvas(cx, cy):
    """Map (-100,100) coordinate space to canvas pixel position."""
    usable_w = CANVAS_W - 2 * PADDING
    usable_h = CANVAS_H - 2 * PADDING
    px = int(PADDING + (cx + 100) / 200.0 * usable_w)
    py = int(PADDING + (100 - cy) / 200.0 * usable_h)   # flip y
    return (px, py)


def draw_coordinate_canvas():
    """Create a fresh canvas with grid, axes, and labels."""
    canvas = np.full((CANVAS_H, CANVAS_W, 3), C_BG, dtype=np.uint8)
    font   = cv2.FONT_HERSHEY_SIMPLEX

    # Grid lines every 10 units
    for v in range(-100, 101, 10):
        # vertical
        px, _ = _coord_to_canvas(v, 0)
        if v == 0:
            color, thick = C_AXIS, 1
        elif v % 50 == 0:
            color, thick = C_GRID_MAJOR, 1
        else:
            color, thick = C_GRID_MINOR, 1
        cv2.line(canvas, (px, PADDING), (px, CANVAS_H - PADDING), color, thick)

        # horizontal
        _, py = _coord_to_canvas(0, v)
        if v == 0:
            color, thick = C_AXIS, 1
        elif v % 50 == 0:
            color, thick = C_GRID_MAJOR, 1
        else:
            color, thick = C_GRID_MINOR, 1
        cv2.line(canvas, (PADDING, py), (CANVAS_W - PADDING, py), color, thick)

    # Axis tick labels every 50 units
    ox, oy = _coord_to_canvas(0, 0)
    for v in range(-100, 101, 50):
        if v == 0:
            continue
        px, _ = _coord_to_canvas(v, 0)
        cv2.putText(canvas, str(v), (px - 10, oy + 18), font, 0.33, C_LABEL, 1)
        _, py = _coord_to_canvas(0, v)
        cv2.putText(canvas, str(v), (ox + 5,  py + 4),  font, 0.33, C_LABEL, 1)

    # Origin and axis end labels
    cv2.putText(canvas, "0",  (ox + 4,  oy + 18), font, 0.33, C_LABEL, 1)
    cv2.putText(canvas, "+X", (CANVAS_W - PADDING + 3, oy + 4), font, 0.36, C_AXIS, 1)
    cv2.putText(canvas, "+Y", (ox + 4, PADDING - 6),            font, 0.36, C_AXIS, 1)

    # Border
    cv2.rectangle(canvas, (PADDING, PADDING),
                  (CANVAS_W - PADDING, CANVAS_H - PADDING), C_BORDER, 1)

    return canvas


def draw_trajectory_on_canvas(canvas, trajectory, current_idx=0, droplet_coord=None, target_coord=None):
    """
    Draw the trajectory, current target, and droplet onto the canvas.

    Args:
        canvas        : base canvas from draw_coordinate_canvas()
        trajectory    : list of (x, y) in [-100, 100]
        current_idx   : index of the waypoint currently being tracked
        droplet_coord : (norm_x, norm_y) or None
        target_coord  : (norm_x, norm_y) or None
    """
    font = cv2.FONT_HERSHEY_SIMPLEX

    if len(trajectory) == 1:
        # ── Single point mode ─────────────────────────────────────────────────
        px, py = _coord_to_canvas(trajectory[0][0], trajectory[0][1])
        cv2.circle(canvas, (px, py), 10, C_POINT,  1)
        cv2.circle(canvas, (px, py),  4, C_POINT, -1)
        h = 12
        cv2.line(canvas, (px - h, py), (px + h, py), C_POINT, 1)
        cv2.line(canvas, (px, py - h), (px, py + h), C_POINT, 1)
        lbl = f"({trajectory[0][0]:+.1f}, {trajectory[0][1]:+.1f})"
        cv2.putText(canvas, lbl, (px + 14, py - 6), font, 0.4, C_TEXT, 1)

    else:
        # ── Multi-point trajectory ────────────────────────────────────────────
        pts = [_coord_to_canvas(x, y) for x, y in trajectory]

        # Tiny waypoint dots
        for pt in pts:
            cv2.circle(canvas, pt, 2, C_WAYPOINT, -1)

        # Upcoming portion (blue)
        if current_idx < len(pts) - 1:
            todo = np.array(pts[current_idx:], dtype=np.int32)
            cv2.polylines(canvas, [todo], False, C_TRAJ, 2)

        # Completed portion (green)
        if current_idx > 0:
            done = np.array(pts[:current_idx + 1], dtype=np.int32)
            cv2.polylines(canvas, [done], False, C_TRAJ_DONE, 2)

        # Start marker
        cv2.circle(canvas, pts[0],  5, C_TRAJ,      -1)
        cv2.putText(canvas, "START", (pts[0][0] + 7,  pts[0][1] - 5),  font, 0.35, C_TRAJ,      1)

        # End marker
        cv2.circle(canvas, pts[-1], 5, C_TRAJ_DONE, -1)
        cv2.putText(canvas, "END",   (pts[-1][0] + 7, pts[-1][1] - 5), font, 0.35, C_TRAJ_DONE, 1)

        # Waypoint progress counter
        wp_str = f"WP {current_idx + 1} / {len(trajectory)}"
        cv2.putText(canvas, wp_str, (PADDING + 4, PADDING - 10), font, 0.42, C_TEXT, 1)

    # ── Current target crosshair ──────────────────────────────────────────────
    if target_coord is not None:
        tx, ty = _coord_to_canvas(target_coord[0], target_coord[1])
        h = 9
        cv2.line(canvas, (tx - h, ty), (tx + h, ty), C_TARGET, 1)
        cv2.line(canvas, (tx, ty - h), (tx, ty + h), C_TARGET, 1)
        cv2.circle(canvas, (tx, ty), 5, C_TARGET, 1)

    # ── Droplet position ──────────────────────────────────────────────────────
    if droplet_coord is not None:
        dx, dy = _coord_to_canvas(droplet_coord[0], droplet_coord[1])
        cv2.circle(canvas, (dx, dy),  7, C_DROPLET, -1)
        cv2.circle(canvas, (dx, dy), 10, C_DROPLET,  1)
        lbl = f"({droplet_coord[0]:+.1f}, {droplet_coord[1]:+.1f})"
        cv2.putText(canvas, lbl, (dx + 13, dy - 6), font, 0.38, C_DROPLET, 1)

    return canvas


# ─────────────────────────────────────────────
# Trajectory follower
# ─────────────────────────────────────────────

def follow_trajectory(cap, trajectory, tolerance=10, max_time_per_point=30):
    for idx, (target_x, target_y) in enumerate(trajectory):
        print(f"\n--- Waypoint {idx + 1}/{len(trajectory)} ---")
        print(f"Target: ({target_x:.1f}, {target_y:.1f})")

        target_x_px, target_y_px = loc.coordinates_to_pixels(target_x, target_y)
        pid_x.setpoint = target_x_px
        pid_y.setpoint = target_y_px

        start_time    = time.time()
        settled_count = 0
        required_settled_frames = 10

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame")
                break

            centroid, _ = loc.find_centroid(frame)
            droplet_norm = None

            if centroid is not None:
                x_error, y_error = loc.find_error(target_x_px, target_y_px, centroid)
                norm_x, norm_y   = loc.pixels_to_coordinates(centroid[0], centroid[1])
                droplet_norm     = (norm_x, norm_y)

                print(f"Current: ({norm_x:.1f}, {norm_y:.1f}), Error: ({x_error:.1f}, {y_error:.1f})")

                if abs(x_error) < tolerance and abs(y_error) < tolerance:
                    settled_count += 1
                    if settled_count >= required_settled_frames:
                        print(f"Waypoint {idx + 1} reached!")
                        break
                else:
                    settled_count = 0

                adjust_servo(centroid[0], centroid[1])
            else:
                print("Droplet not detected")

            # ── Draw and show trajectory window ───────────────────────────────
            canvas = draw_coordinate_canvas()
            canvas = draw_trajectory_on_canvas(
                canvas,
                trajectory    = trajectory,
                current_idx   = idx,
                droplet_coord = droplet_norm,
                target_coord  = (target_x, target_y),
            )
            cv2.imshow('Trajectory', canvas)

            if time.time() - start_time > max_time_per_point:
                print(f"Timeout at waypoint {idx + 1}, moving to next")
                break

            if cv2.waitKey(1) & 0xFF == ord('q'):
                return False

        time.sleep(0.1)

    return True


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

def main():
    cap = cv2.VideoCapture(0)

    set_servo_position(x_servo_pin, 0.1)
    set_servo_position(y_servo_pin, 0.1)

    print("\n=== Droplet Trajectory Control ===")
    print("1. Single point")
    print("2. Line trajectory")
    print("3. Arc trajectory")

    choice = input("Select mode (1/2/3): ")

    if choice == "1":
        req_x = int(input("Enter x coordinate (-100 to 100): "))
        req_y = int(input("Enter y coordinate (-100 to 100): "))
        if req_x < -100 or req_x > 100 or req_y < -100 or req_y > 100:
            print("Coordinates out of range.")
            return
        trajectory = [(req_x, req_y)]

    elif choice == "2":
        print("\n--- Line Trajectory ---")
        start_x    = int(input("Enter start x (-100 to 100): "))
        start_y    = int(input("Enter start y (-100 to 100): "))
        end_x      = int(input("Enter end x   (-100 to 100): "))
        end_y      = int(input("Enter end y   (-100 to 100): "))
        num_points = int(input("Number of waypoints (default 50): ") or "50")
        if any(c < -100 or c > 100 for c in [start_x, start_y, end_x, end_y]):
            print("Coordinates out of range.")
            return
        trajectory = generate_line_trajectory(start_x, start_y, end_x, end_y, num_points)
        print(f"Generated {len(trajectory)} waypoints along line")

    elif choice == "3":
        print("\n--- Arc Trajectory ---")
        center_x    = int(input("Enter center x (-100 to 100): "))
        center_y    = int(input("Enter center y (-100 to 100): "))
        radius      = float(input("Enter radius (coordinate units): "))
        start_angle = float(input("Enter start angle (degrees, 0=right, 90=up): "))
        end_angle   = float(input("Enter end angle (degrees): "))
        num_points  = int(input("Number of waypoints (default 50): ") or "50")
        if center_x < -100 or center_x > 100 or center_y < -100 or center_y > 100:
            print("Center coordinates out of range.")
            return
        trajectory = generate_arc_trajectory(center_x, center_y, radius, start_angle, end_angle, num_points)
        print(f"Generated {len(trajectory)} waypoints along arc")

    else:
        print("Invalid choice.")
        return

    # Static preview before starting
    preview = draw_coordinate_canvas()
    preview = draw_trajectory_on_canvas(preview, trajectory)
    cv2.imshow('Trajectory', preview)
    print("\nTrajectory preview shown. Press any key to start...")
    cv2.waitKey(0)

    print("Starting trajectory...")
    time.sleep(1)

    success = follow_trajectory(cap, trajectory)

    if success:
        print("\n✓ Trajectory completed successfully!")
    else:
        print("\n✗ Trajectory interrupted")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()