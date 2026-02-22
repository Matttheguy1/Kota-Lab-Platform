import cv2
import numpy as np

# ── The "Search Zone" boundaries (in normalized units) ────────────────────────
SEARCH_X_MIN, SEARCH_X_MAX = -50, 50
SEARCH_Y_MIN, SEARCH_Y_MAX = -75, 75

def draw_grid(image):
    """Draws the full -100 to 100 grid with the search zone highlighted."""
    h, w = image.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    col_minor, col_major, col_axis = (40, 40, 40), (70, 70, 70), (100, 100, 100)

    for v in range(-100, 101, 10):
        # Vertical lines
        px, _ = coordinates_to_pixels(v, 0)
        px = int(px)
        color = col_axis if v == 0 else (col_major if v % 50 == 0 else col_minor)
        cv2.line(image, (px, 0), (px, h), color, 1)

        # Horizontal lines
        _, py = coordinates_to_pixels(0, v)
        py = int(py)
        color = col_axis if v == 0 else (col_major if v % 50 == 0 else col_minor)
        cv2.line(image, (0, py), (w, py), color, 1)
    
    # Visual cue: Draw the "Active Search Zone" box in a subtle red/orange
    x1, y1 = coordinates_to_pixels(SEARCH_X_MIN, SEARCH_Y_MAX)
    x2, y2 = coordinates_to_pixels(SEARCH_X_MAX, SEARCH_Y_MIN)
    cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 200), 1, cv2.LINE_AA)
    cv2.putText(image, "SEARCH ZONE (RED ONLY)", (int(x1)+5, int(y1)-8), font, 0.35, (0, 0, 200), 1)
    
    return image

def find_centroid(image):
    # 1. Draw Grid
    image = draw_grid(image)
    h, w = image.shape[:2]

    # 2. ROI Mask (Restrict search to +-50, +-75)
    mask_roi = np.zeros((h, w), dtype=np.uint8)
    x1, y1 = coordinates_to_pixels(SEARCH_X_MIN, SEARCH_Y_MAX)
    x2, y2 = coordinates_to_pixels(SEARCH_X_MAX, SEARCH_Y_MIN)
    cv2.rectangle(mask_roi, (int(x1), int(y1)), (int(x2), int(y2)), 255, -1)

    # 3. Process HSV for RED
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Red Range 1 (0-10 degrees)
    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])
    # Red Range 2 (160-180 degrees)
    lower_red2 = np.array([160, 120, 70])
    upper_red2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    color_mask = cv2.bitwise_or(mask1, mask2)
    
    # Combine with ROI Mask
    final_mask = cv2.bitwise_and(color_mask, mask_roi)

    # 4. Cleanup and Centroid Detection
    kernel = np.ones((5, 5), np.uint8)
    final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_OPEN, kernel)
    contours, _ = cv2.findContours(final_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None, image

    largest_contour = max(contours, key=cv2.contourArea)
    M = cv2.moments(largest_contour)
    if M["m00"] == 0: return None, image

    cx, cy = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
    norm_x, norm_y = pixels_to_coordinates(cx, cy)

    # Feedback Visualization (Now in RED)
    cv2.drawContours(image, [largest_contour], -1, (0, 0, 255), 2)
    cv2.circle(image, (cx, cy), 5, (0, 0, 255), -1)
    cv2.putText(image, f"({norm_x:+.1f}, {norm_y:+.1f})", (cx+10, cy-10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (50, 50, 255), 1)

    return (cx, cy), image

# ── Keep standard coordinate transforms ───────────────────────────────────────

def find_error(x_desired, y_desired, centroid):
    return centroid[0] - x_desired, centroid[1] - y_desired

def pixels_to_coordinates(x_pixels, y_pixels):
    x = ((x_pixels - 360) / 360) * 100
    y = ((240 - y_pixels) / 240) * 100 # Adjusted for typical cartesian up = positive
    return (x, y)

def coordinates_to_pixels(x_coordinate, y_coordinate):
    x_pixel = ((x_coordinate + 100) / 200) * 720
    y_pixel = ((100 - y_coordinate) / 200) * 480
    return (x_pixel, y_pixel)