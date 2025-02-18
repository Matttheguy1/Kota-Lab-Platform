import cv2 as cv
import localization as loc

cap = cv.VideoCapture(0)
while True:
    ret, frame = cap.read()
    centroid, annotated_frame = loc.find_centroid(frame)
    cv.imshow('frame', annotated_frame)
    print(centroid[0], centroid[1])
    if cv.waitKey(1) & 0xFF == ord('q'):
        break



cap.release()
cv.destroyAllWindows()
