import cv2
import nxbt
import time
import sys
import pytesseract
import numpy as np
from PIL import Image
import os
from skimage.metrics import structural_similarity as ssim

#Varibles
Shiny = False
EncounterType = ""
Game = ""
camera_config = None
FirstPass = False

#Macros
ReturnHome = """
HOME 0.5s
2.0s
"""

EnterGameBDSP = """
A 0.5s
30.0s
A 0.5s
5.0s
A 0.5s
15.0s
"""

StillEncounterStart = """
L_STICK@+000+100 2.0s
5.0s
A 0.5s
5.0s
A 0.5s
"""

ExitGame = """
HOME 0.25s
2.0s
X 0.5s
2.0s
A 0.5s
"""

#Camera Intial Setup
def find_available_camera():
#Automatically find the first available camera device
    for i in range(15):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"Found video device at /dev/video{i}")
            return cap, i
        cap.release()
    raise Exception("No video devices found")

def setup_camera(cap, device_index):
 #Try different camera settings until we get a valid video feed
    # List of video formats to try (common ones for Raspberry Pi)
    fourcc_formats = [
        cv2.VideoWriter_fourcc(*'RGB3'),
        cv2.VideoWriter_fourcc(*'MJPG'),
        cv2.VideoWriter_fourcc(*'YUYV'),
        cv2.VideoWriter_fourcc(*'BGR8'),
    ]

    # List of resolutions to try (highest first)
    resolutions = [
        (1920, 1080),
        (1280, 720),
        (640, 480),
    ]
    
    # List of frame rates to try
    frame_rates = [30, 25,20 , 15]
    for fmt in fourcc_formats:
        cap.set(cv2.CAP_PROP_FOURCC, fmt)
        print(f"Trying video format: {fmt}")
    
        for res in resolutions:
            width, height = res
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            for fps in frame_rates:
                cap.set(cv2.CAP_PROP_FPS, fps)
                
                # Give camera time to adjust settings
                time.sleep(2)
                
                # Try capturing frames for a short period
                start_time = time.time()
                success_count = 0
                
                while time.time() - start_time < 3:  # Capture for 2 seconds
                    ret, frame = cap.read()
                    if not ret:
                        continue
                        
                    # Check if the frame has valid content (not empty or black)
                    if cv2.countNonZero(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)) > 0:
                        success_count += 1
                        
                if success_count > 0:
                    print(f"Successfully configured camera with settings:")
                    print(f"- Format: {fmt}")
                    print(f"- Resolution: {width}x{height}")
                    print(f"- FPS: {fps}")
                    return cap
            
    # If all settings fail, clean up and raise error
    cap.release()
    cv2.destroyAllWindows()
    raise Exception("Failed to configure camera - no valid video feed detected")

def get_camera_config():
    global camera_config
    if not camera_config:
        cap, device_index = find_available_camera()
        cap = setup_camera(cap, device_index)
        # Store successful configuration
        camera_config = {
            'device': device_index,
            'format': int(cap.get(cv2.CAP_PROP_FOURCC)),
            'resolution': (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), 
                          int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))),
            'fps': cap.get(cv2.CAP_PROP_FPS)
        }
        cap.release()
        cv2.destroyAllWindows()
    return camera_config

def get_camera_with_config(config):
    """Open camera using stored configuration"""
    cap = cv2.VideoCapture(config['device'])
    if not cap.isOpened():
        raise Exception("Failed to open video device")
    
    # Set stored settings
    cap.set(cv2.CAP_PROP_FOURCC, config['format'])
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config['resolution'][0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config['resolution'][1])
    cap.set(cv2.CAP_PROP_FPS, config['fps'])
    
    # Give camera time to apply settings
    time.sleep(2)
    
    return cap

def get_frame():
    config = get_camera_config()
    cap = get_camera_with_config(config)
    ret, frame = cap.read()
    cap.release()
    cv2.destroyAllWindows()
    if ret:
        return frame
    return false
# Start the NXBT service
nx = nxbt.Nxbt()

# Create a Pro Controller and wait for it to connect
controller_index = nx.create_controller(nxbt.PRO_CONTROLLER)

nx.wait_for_connection(controller_index)
print("Connected")

nx.macro(controller_index, ReturnHome)
nx.clear_macros(controller_index)

while Shiny == False:
    while Game == "":
        try:
            config = get_camera_config()
            cap = get_camera_with_config(config)
            ret, frame = cap.read()
            if ret:
                # Calculate text region based on current resolution
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                
                # Define percentages for the text region (based on original 1920x1080)
                top_pct = 150 / 1080
                bottom_pct = 300 / 1080
                left_pct = 100 / 1920
                right_pct = 700 / 1920
                
                # Calculate actual pixel values based on current resolution
                text_region_top = int(height * top_pct)
                text_region_bottom = int(height * bottom_pct)
                text_region_left = int(width * left_pct)
                text_region_right = int(width * right_pct)
                
                text_region = frame[text_region_top:text_region_bottom, 
                                text_region_left:text_region_right]
                gray = cv2.cvtColor(text_region, cv2.COLOR_BGR2GRAY)
                # Apply thresholding to enhance text visibility
                thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
                # Perform OCR using pytesseract
                text = pytesseract.image_to_string(thresh)
                if "Brilliant Diamond" in text:
                    Game = "BDSP"
                    if not FirstPass:
                        print(Game)
                else:
                    if not FirstPass:
                        print("Text above pulsing image:", text)

                cap.release()
                cv2.destroyAllWindows()
        except Exception as e:
            print(f"Error re-initializing camera: {e}")
        
        
    if Game == "BDSP":
        nx.macro(controller_index, EnterGameBDSP)
        nx.clear_macros(controller_index)
    while EncounterType == "":
        #Still Encounter aka game resets needed
        if not os.path.exists("Still_Encounter.png"):
            try:
                frame = get_frame()
                cv2.imwrite("Still_Encounter.png", frame)
            except Exception as e:
                print(f"Error re-initializing camera: {e}")
        #Compair the images to determine encounter type
        reference_image = cv2.imread("Still_Encounter.png")
        gray_reference = cv2.cvtColor(reference_image, cv2.COLOR_BGR2GRAY)
        try:
            frame = get_frame()
            gray_current = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        except Exception as e:
            print(f"Error re-initializing camera: {e}")

        # Calculate similarity using SSIM (Structural Similarity Index)
        similarity_index = ssim(gray_reference, gray_current, multichannel=False)
            
        if similarity_index > 0.9:  # Adjust threshold as needed
            if not FirstPass:
                print("Still encounter Detected")
            EncounterType = "Still"
            time.sleep(0.1)  # Small delay between checks
        else:
            nx.press_buttons(controller_index, [nxbt.Buttons.A], down=1.0)
    if EncounterType == "Still":
        nx.macro(controller_index, StillEncounterStart)
        nx.clear_macros(controller_index)
        time.sleep(11)
        try:
            config = get_camera_config()
            cap = get_camera_with_config(config)

            # Initialize variables for frame comparison
            frames = []
            similarity_indexes = []
            start_time = time.time()

            while time.time() - start_time < 7:
                ret, frame = cap.read()
                if ret:
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

                    # Define percentages for the top-right region
                    top_pct = 50 / height
                    bottom_pct = 125 / height
                    left_pct = 1400 / width
                    right_pct = 1750 / width

                    # Calculate actual pixel values based on current resolution
                    text_region_top = int(height * top_pct)
                    text_region_bottom = int(height * bottom_pct)
                    text_region_left = int(width * left_pct)
                    text_region_right = int(width * right_pct)

                    text_region = frame[text_region_top:text_region_bottom, text_region_left:text_region_right]
                    
                    # Convert cropped image text to string using OCR
                    gray = cv2.cvtColor(text_region, cv2.COLOR_BGR2GRAY)
                    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
                    text = pytesseract.image_to_string(thresh).strip().replace(" ", "")
                    
                    # Store frames for comparison
                    frames.append(frame)

            if not FirstPass:
                print("Pokemon:", text)
            if not os.path.exists("Pokemon"):
                        os.makedirs("Pokemon")
            reference_image_path = os.path.join("Pokemon", text + ".png")

             # Save the first frame as a reference image
            if not os.path.exists(reference_image_path):
                cv2.imwrite(reference_image_path, frame)
                print(f"Reference image saved to: {reference_image_path}")

            if os.path.exists(reference_image_path):
                reference_image = cv2.imread(reference_image_path)
                if reference_image is not None:
                    for frame in frames:
                        similarity_index = ssim(reference_image, frame, multichannel=True, channel_axis=2)
                        similarity_indexes.append(similarity_index)

                    # Find the closest match (highest similarity index)
                    max_similarity = max(similarity_indexes) if similarity_indexes else 0
                    print(f"Closest Match: {max_similarity * 100:.2f}%")
                    if max_similarity > 0.9:
                        print("Not Shiny")
                        EncounterType = ""
                        Game = ""
                        FirstPass = True

                        # Used to save images
                        if not os.path.exists("Not Shiny"):
                            os.makedirs("Not Shiny")
                        #Used to track encounters
                        if not os.path.exists("Shiny"):
                                os.makedirs("Shiny")
                            
                        # Use the frame with highest similarity for saving
                        best_frame_index = similarity_indexes.index(max_similarity)
                        best_frame = frames[best_frame_index]

                        # Determine the encounter count
                        file_path_txt = os.path.join("Shiny", text + ".txt")
                        if os.path.exists(file_path_txt):
                            with open(file_path_txt, "r") as f:
                                current_count = int(f.readline().split(": ")[1])
                            encounters = current_count + 1
                        else:
                            encounters = 1

                        file_path = os.path.join("Not Shiny", f"{text}_{encounters}.png")
                        if not os.path.exists(file_path):
                            cv2.imwrite(file_path, best_frame)

                        with open(os.path.join("Shiny", text + ".txt"), "w") as f:
                            f.write(f"Encounters: {encounters}")
                        
                        time.sleep(0.1)  # Small delay between checks
                        nx.macro(controller_index, ExitGame)
                        nx.clear_macros(controller_index)
                    else:
                        Shiny = True
                        print(f"Closeness: {similarity_index * 100:.2f}%")
                        print("\033[38;2;255;215;0mShiny Spotted!\033[0m")
                cap.release()
                cv2.destroyAllWindows()
                
        except Exception as e:
            print(f"Error re-initializing camera: {e}")

cap.release()
cv2.destroyAllWindows()

# Stop the controller and NXBT service
nx.remove_controller(controller_index)
sys.exit()
