import cv2
import numpy as np


# ── Grid drawing ──────────────────────────────────────────────────────────────

def draw_grid(image):
    """
    Draw a coordinate grid on the image in the (-100, 100) space with interval 10.
    Assumes image is 720x480.
    """
    h, w = image.shape[:2]
    font      = cv2.FONT_HERSHEY_SIMPLEX
    col_minor = (50, 50, 50)      # dark grey for minor grid lines
    col_major = (90, 90, 90)      # slightly brighter for every 50-unit line
    col_axis  = (130, 130, 130)   # brightest for the zero axes
    col_label = (100, 100, 100)   # muted label text

    for v in range(-100, 101, 10):
        # ── Vertical lines (x = v) ────────────────────────────────────────────
        px, _ = coordinates_to_pixels(v, 0)
        px = int(px)
        if v == 0:
            color, thickness = col_axis, 1
        elif v % 50 == 0:
            color, thickness = col_major, 1
        else:
            color, thickness = col_minor, 1
        cv2.line(image, (px, 0), (px, h), color, thickness)

        # Label every 50 units on the x-axis (skip 0 to avoid clutter)
        if v % 50 == 0 and v != 0:
            _, oy = coordinates_to_pixels(0, 0)
            label_y = min(int(oy) + 14, h - 4)
            cv2.putText(image, str(v), (px + 2, label_y), font, 0.32, col_label, 1)

        # ── Horizontal lines (y = v) ──────────────────────────────────────────
        _, py = coordinates_to_pixels(0, v)
        py = int(py)
        if v == 0:
            color, thickness = col_axis, 1
        elif v % 50 == 0:
            color, thickness = col_major, 1
        else:
            color, thickness = col_minor, 1
        cv2.line(image, (0, py), (w, py), color, thickness)

        # Label every 50 units on the y-axis
        if v % 50 == 0 and v != 0:
            ox, _ = coordinates_to_pixels(0, 0)
            cv2.putText(image, str(v), (int(ox) + 3, py - 3), font, 0.32, col_label, 1)

    # Origin label
    ox, oy = coordinates_to_pixels(0, 0)
    cv2.putText(image, "0", (int(ox) + 3, int(oy) - 3), font, 0.32, col_label, 1)

    return image


# ── Centroid detection ────────────────────────────────────────────────────────

def find_centroid(image):
    # Draw grid onto the frame first (behind everything else)
    image = draw_grid(image)

    # Convert to HSV color space
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # ── Green color range ─────────────────────────────────────────────────────
    # Green sits roughly 40-80 in hue; two sub-ranges cover yellow-green → cyan-green
    lower_green1 = np.array([35,  80, 50])
    upper_green1 = np.array([85, 255, 255])
    # Wider catch-all (softer saturation floor for pale greens)
    lower_green2 = np.array([36,  40, 40])
    upper_green2 = np.array([84, 255, 255])

    mask1 = cv2.inRange(hsv, lower_green1, upper_green1)
    mask2 = cv2.inRange(hsv, lower_green2, upper_green2)
    mask  = cv2.bitwise_or(mask1, mask2)

    # Clean up the mask
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None, image

    # Find the largest contour (assuming it's the droplet)
    largest_contour = max(contours, key=cv2.contourArea)

    # Calculate centroid using moments
    M = cv2.moments(largest_contour)
    if M["m00"] == 0:
        return None, image

    cx = int(M["m10"] / M["m00"])
    cy = int(M["m01"] / M["m00"])

    # ── Normalized coordinates for the label ─────────────────────────────────
    norm_x, norm_y = pixels_to_coordinates(cx, cy)

    # ── Draw contour and centroid ─────────────────────────────────────────────
    cv2.drawContours(image, [largest_contour], -1, (0, 255, 0), 2)
    cv2.circle(image,      (cx, cy),            5, (0, 255, 0), -1)

    # ── Live coordinate label attached to the droplet ─────────────────────────
    label      = f"({norm_x:+.1f}, {norm_y:+.1f})"
    font       = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.48
    thickness  = 1
    pad        = 4

    (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, thickness)

    # Position the label just above the centroid; shift left if it would clip the right edge
    label_x = cx + 10
    label_y = cy - 10
    img_h, img_w = image.shape[:2]
    if label_x + text_w + pad > img_w:
        label_x = cx - text_w - 10
    if label_y - text_h - pad < 0:
        label_y = cy + text_h + 10

    # Semi-transparent background pill
    bg_x1 = label_x - pad
    bg_y1 = label_y - text_h - pad
    bg_x2 = label_x + text_w + pad
    bg_y2 = label_y + baseline + pad

    # Clamp to image bounds
    bg_x1, bg_y1 = max(0, bg_x1), max(0, bg_y1)
    bg_x2, bg_y2 = min(img_w, bg_x2), min(img_h, bg_y2)

    roi = image[bg_y1:bg_y2, bg_x1:bg_x2]
    if roi.size > 0:
        dark_overlay = np.zeros_like(roi)
        image[bg_y1:bg_y2, bg_x1:bg_x2] = cv2.addWeighted(roi, 0.35, dark_overlay, 0.65, 0)

    cv2.putText(image, label, (label_x, label_y), font, font_scale, (0, 255, 0), thickness)

    return (cx, cy), image


# ── Error calculation ─────────────────────────────────────────────────────────

def find_error(x_desired, y_desired, centroid):
    """Returns pixel-space error between desired position and detected centroid."""
    cx = centroid[0]
    cy = centroid[1]
    x_error = cx - x_desired
    y_error = cy - y_desired
    return x_error, y_error


# ── Coordinate transforms ─────────────────────────────────────────────────────

def pixels_to_coordinates(x_pixels, y_pixels):
    """
    Convert pixel coordinates (0-720, 0-480) to normalized space (-100, 100).
    Center of image (360, 240) maps to (0, 0).
    """
    x = ((x_pixels - 360) / 360) * 100
    y = ((y_pixels - 240) / 240) * 100
    return (x, y)


def coordinates_to_pixels(x_coordinate, y_coordinate):
    """
    Convert normalized coordinates (-100, 100) to pixel space (0-720, 0-480).
    """
    x_pixel = ((x_coordinate + 100) / 200) * 720
    y_pixel = ((y_coordinate + 100) / 200) * 480
    return (x_pixel, y_pixel)