import cv2
import time
from ultralytics import YOLO

# --- Distance calculation constants
a = 9703.20
b = -0.4911842338691967

# --- Load YOLO model
model = YOLO("models/model.pt")  # Ensure this path is correct

# --- Get user-defined distance threshold
try:
    max_distance = float(input("Enter maximum face distance in cm: "))
except ValueError:
    print("Invalid input. Using default 130cm.")
    max_distance = 130

# --- Initialize webcam with DirectShow backend (fix for Windows)
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    raise RuntimeError("Unable to access webcam")

print("Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame.")
        break

    # Run YOLO face detection
    results = model(frame, conf=0.4, verbose=False)
    detections = results[0].boxes
    annotated = frame.copy()

    if detections is not None:
        for box in detections:
            conf = float(box.conf[0])
            if conf < 0.4:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            area_px = (x2 - x1) * (y2 - y1)
            distance = a * (area_px ** b)

            # Color based on threshold
            color = (0, 255, 0) if distance < max_distance else (0, 0, 255)
            label = f"{distance:.1f}cm"

            # Draw bounding box and distance label
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                annotated,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )

    # Show the annotated frame
    cv2.imshow("YOLO Face Distance", annotated)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- Cleanup
cap.release()
cv2.destroyAllWindows()
