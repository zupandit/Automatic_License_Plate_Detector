from ultralytics import YOLO
import cv2 as cv
from sort.sort import Sort
import numpy as np
from util import get_car, read_license_plate
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from create_db import Base, LicensePlates, WantedLicensePlates

# Script by Zaid Nissar to automatically detect license plates and run them through a database.
# Credit to Computer Vision Engineer on youtube for some of the code. 
# The use of this code is subject to the license included with it originally. 

# Create an engine and configure session
engine = create_engine('sqlite:///car_plates.db')  # Use the same database URL
Session = sessionmaker(bind=engine)
session = Session()

# Function to check if a license plate exists and if it is wanted
def check_license_plate(plate_text):
    return_text = ''
    # Query the LicensePlates table
    db_search = session.query(LicensePlates).filter(LicensePlates.plate_text == plate_text).first()
    
    if db_search:
        return_text += f'License Plate: {db_search.plate_text}, Owner: {db_search.owner}, Car: {db_search.car}'
        
        # Query the WantedLicensePlates table
        db_search_wanted = session.query(WantedLicensePlates).filter(WantedLicensePlates.plate_id == db_search.plate_id).first()
        
        if db_search_wanted:
           return_text += f'\n Wanted for: {db_search_wanted.crime_text} '
        
    else:
        return_text = 'License plate not found.'

    return return_text
    


# Saves the details of the cars that have already been found 
results = {}

# Object tracker
mot_tracker = Sort()

coco_model = YOLO('yolov8n.pt')
license_plate_detector = YOLO('license_plate_detector.pt')

cap = cv.VideoCapture(0)

frame_num = -1
ret = True

# Vehicle class numbers in COCO dataset
vehicles = [2, 3, 5, 7]

results_found_in_db = {}

while ret:
    frame_num += 1
    ret, frame = cap.read()

    if ret:
        results[frame_num] = {}

        # Detect vehicles
        detections = coco_model(frame)[0]
        detections_boxes = []
        for detection in detections.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = detection
            # Only add boxes of objects we want
            if int(class_id) in vehicles:
                detections_boxes.append([x1, y1, x2, y2, score])
                cv.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        
        # Track vehicles if there are any detections
        if detections_boxes:
            track_ids = mot_tracker.update(np.asarray(detections_boxes))
        else:
            track_ids = np.empty((0, 5))  # Create an empty array for track_ids to avoid errors

        # Detect license plates
        license_plates = license_plate_detector(frame)[0]
        for license_plate in license_plates.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = license_plate

            # Link license plate to car
            xcar1, ycar1, xcar2, ycar2, car_id = get_car(license_plate, track_ids)

            if car_id != -1:
                cropped_plate = frame[int(y1):int(y2), int(x1):int(x2), :]

                # Process plate
                gray = cv.cvtColor(cropped_plate, cv.COLOR_BGR2GRAY)
                _, thresh = cv.threshold(gray, 64, 255, cv.THRESH_BINARY_INV)

                # OCR the plate
                plate_text, plate_text_confidence = read_license_plate(cropped_plate)

                if plate_text is not None:
                    results[frame_num][car_id] = {'car': {'bbox': [xcar1, ycar1, xcar2, ycar2]},
                                                  'license_plate': {'bbox': [x1, y1, x2, y2],
                                                                    'text': plate_text,
                                                                    'bbox_score': score,
                                                                    'text_score': plate_text_confidence}}
                    # Draw the license plate bounding box and text
                    cv.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 2)
                    car_details = check_license_plate(plate_text=plate_text)
                    if car_details != "License plate not found.":
                        if car_id not in results_found_in_db:
                            results_found_in_db[car_id] = car_details
                    
                    if car_id in results_found_in_db:
                        cv.putText(frame, results_found_in_db[car_id], (int(x1), int(y1)-10), cv.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
                    else:
                        cv.putText(frame, car_details, (int(x1), int(y1)-10), cv.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
        cv.imshow('Real-Time Vehicle and License Plate Detection', frame)

        if cv.waitKey(1) & 0xFF == ord('q'):
            break
    else:
        break

cap.release()
cv.destroyAllWindows()
session.close()
