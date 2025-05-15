import cv2
import numpy as np

def find_centroid(image):

    # Convert to HSV color space
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Define the range for red color in HSV
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])

    # Create mask for blue regions
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

# Function that transforms pixel coordinates to a coordinate with domain (-100,100) and range (-100,100)
def pixels_to_coordinates(x_pixels,y_pixels):
    x = ((x_pixels-360)/360) * 100
    y = ((y_pixels-240)/240) * 100
    coordinates = (x,y)
    return coordinates

# Function that transforms coordinates with domain (-100,100) and range (-100,100) to pixel coordinates domain (0,720) and range (0,480)
def coordinates_to_pixels(x_coordinate,y_coordinate):
    x_pixel = ((x_coordinate + 100) / 200) * 720  # Scale x from [-100,100] to [0,720]
    y_pixel = ((y_coordinate + 100) / 200) * 480  # Scale y from [-100,100] to [0,480]
    pixel_coordinates = (x_pixel,y_pixel)
    return pixel_coordinates

