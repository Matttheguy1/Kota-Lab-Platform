import cv2
import numpy as np

def find_centroid(image):

    # Convert to HSV color space
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Define range for red color
    # Red wraps around in HSV, so we need two masks
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])

    # Create masks for red regions
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)

    # Clean up the mask
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
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

    # Draw the centroid on the image (for visualization)
    cv2.circle(image, (cx, cy), 5, (0, 255, 0), -1)
    cv2.drawContours(image, [largest_contour], -1, (0, 255, 0), 2)

    return (cx, cy), image


# Function that determines and returns the x and y error
def find_error(x_desired, y_desired, centroid):
    cx = centroid[0]
    cy = centroid[1]
    x_error = cx - x_desired
    y_error = cy - y_desired
    return x_error, y_error
