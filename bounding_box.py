import cv2
import numpy as np

def detect_circle_quadrant():
    # Initialize camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame")
            break
        
        # Get frame dimensions
        h, w = frame.shape[:2]
        mid_x, mid_y = w // 2, h // 2
        
        # Draw quadrant lines
        cv2.line(frame, (mid_x, 0), (mid_x, h), (255, 255, 255), 2)
        cv2.line(frame, (0, mid_y), (w, mid_y), (255, 255, 255), 2)
        
        # Add quadrant labels
        cv2.putText(frame, "Q1", (mid_x + 20, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, "Q2", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, "Q3", (20, mid_y + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, "Q4", (mid_x + 20, mid_y + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Convert to grayscale for circle detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (9, 9), 2)
        
        # Detect circles using HoughCircles with stricter parameters
        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=10,  # Increased minimum distance between circles
<<<<<<< HEAD
            param1=200,   # Higher edge detection threshold
            param2=75,    # Much higher accumulator threshold for circle detection
            minRadius=10, # Larger minimum radius
            maxRadius=400
=======
            param1=100,   # Higher edge detection threshold
            param2=25,    # Much higher accumulator threshold for circle detection
            minRadius=20, # Larger minimum radius
            maxRadius=150
>>>>>>> 422d60731831c3b7f6689e516c8e9289e078a24c
        )
        
        # Process detected circles (limit to 2 best circles)
        if circles is not None:
            circles = np.uint16(np.around(circles))
            
            # Limit to maximum 2 circles
            circles_to_process = circles[0, :2] if len(circles[0]) > 4 else circles[0, :]
            
            for circle in circles_to_process:
                cx, cy, r = circle
                
                # Draw the circle
                cv2.circle(frame, (cx, cy), r, (0, 255, 0), 3)
                cv2.circle(frame, (cx, cy), 2, (0, 0, 255), 3)
                
                # Determine quadrant
                if cx >= mid_x and cy < mid_y:
                    quadrant = "Q1"
                elif cx < mid_x and cy < mid_y:
                    quadrant = "Q2"
                elif cx < mid_x and cy >= mid_y:
                    quadrant = "Q3"
                else:
                    quadrant = "Q4"
                print(quadrant)
                # Display quadrant info
                cv2.putText(frame, f"{quadrant}", (cx - 20, cy - r - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Display the frame
        cv2.imshow('Circle Quadrant Detector', frame)

        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    detect_circle_quadrant()
