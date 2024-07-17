import string
import easyocr

reader = easyocr.Reader(['en'], gpu=True)

# Mapping dictionaries for character conversion
dict_char_to_int = {'I': '1',
                    'J': '3',
                    'A': '4',
                    'G': '6',
                    'S': '5'}

dict_int_to_char = {'1': 'I',
                    '3': 'J',
                    '4': 'A',
                    '6': 'G',
                    '5': 'S'}

weird_chars = ['0', '1', '5', '4', ]

def validate_plate(plate):
    accepted = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K',
                  'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W',
                    'X', 'Y', 'Z']


    if len(plate)<4:
        return False 
    
    for char in plate:
        if char not in accepted:
            return False 

    return True

def get_car(license_plate, vehicle_track_ids):
    x1, y1, x2, y2,score, class_id = license_plate
    foundIt= False
    for j in range(len(vehicle_track_ids)):
        xcar1, ycar1, xcar2, ycar2, car_id = vehicle_track_ids[j]

        if x1> xcar1 and y1> ycar1 and x2<xcar2 and y2<ycar2:
            car_indx = j
            foundIt = True
            break
    if foundIt:
        return vehicle_track_ids[car_indx]

    return -1, -1, -1 ,-1 ,-1 


def read_license_plate(plate_crop):
    detections = reader.readtext(plate_crop)

    for detection in detections:
        bbox, text, score = detection

        text = text.upper().replace(' ', '')
        text = text.replace('-', '')
        
        text = text.replace('O', '0')

        #logic to return an array of possible number plates: 
        if validate_plate(text):
            possibilities = get_diff_licensePlates(text)
            # print('PLATE::::   ' + text)
            return text, score 
    return None, None

    # return None, None

def get_diff_licensePlates(plate):
    """"
    Returns possible combinations of the license plates we have found. 
    It is so that we are sure of the OCR 
    """
    combinations = []
    combinations.append(plate)     
    def combs(plate, filteredTill):
        for char in plate:
            place = plate.index(char)
            if place > filteredTill:
                if char in dict_char_to_int:
                    new_plate = plate.replace(char, dict_char_to_int[char])
                    combinations.append(new_plate)
                    combs(plate=new_plate, filteredTill=place)
                
                if char in dict_int_to_char:
                    new_plate = plate.replace(char, dict_int_to_char[char])
                    combinations.append(new_plate)
                    combs(plate=new_plate, filteredTill=place)
    
    return combinations
    