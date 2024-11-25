import cv2


# Load face detection classifier
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Start video
video_capture = cv2.VideoCapture(0)

while True:
    # Get frame
    ret, frame = video_capture.read()

    # Use grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Look for faces in grayscale
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )

    # Draw rectangle
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        print("xcoord:", (x+w)/2, "ycoord:", ((y+h)/2))

    # Display image
    cv2.imshow('Face Tracking', frame)

    # Exit condition
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


# Release video capture and close windows
video_capture.release()
cv2.destroyAllWindows()


