import cv2

# 1. Define your rectangle coordinates
# (x, y) coordinates for the top-left and bottom-right corners
top_left = (160, 75)      # Edit these to move the box
bottom_right = (540, 400)  # Edit these to resize the box

# Color in BGR (Blue, Green, Red) -> (0, 255, 0) is Green
color = (0, 255, 0)
thickness = 3

cap = cv2.VideoCapture(0)

# Standard Pi Resolution
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("Displaying rectangle overlay... Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 2. Draw the rectangle on the current frame
    cv2.rectangle(frame, top_left, bottom_right, color, thickness)

    # 3. Optional: Add a label or corner coordinates text
    cv2.putText(frame, f"ROI: {top_left} to {bottom_right}", (top_left[0], top_left[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # 4. Display the frame
    cv2.imshow('Rectangle Overlay', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
