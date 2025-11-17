from openocr import OpenOCR
from pathlib import Path
from os import getcwd
import pandas as pd
import onnxruntime as ort
from typing import Dict, Optional

SCREENSHOT_FOLDER = Path(getcwd()) / "screenshots"
OUTPUT_FOLDER = Path(getcwd()) / "data"

def process_screenshots(archive_path: Path) -> pd.DataFrame:
    """"Utilize OpenOCR vision model to extract solar irradiance, longitude, and latitude from SPARKvue screenshots.

    :param archive_path: disc location of the screenshots
    :return: the data gathered for each image split into two categories: success & failure
    """
    data = []
    failures = []

    onnx_engine = OpenOCR(backend="onnx", device="cpu") #initialize vision model
    options = ort.SessionOptions()
    options.log_severity_level = 3

    for img_path in archive_path.glob("*.png") : #retrieves the paths to all screenshots
        detections, elapsed = onnx_engine(str(img_path))  # OpenOCR's backend does not handle Path object. Convert to a string first
        r_obj = eval(detections[0][detections[0].index("\t") + 1:])  # OpenOCR's result is a list of results encoded as a list with a label

        results = {
            "filename": img_path.name,
            "measurement": -1,
            "longitude": -1,
            "latitude": -1
        }

        for detection in r_obj:
            transcription = detection["transcription"]
            transcription = transcription.replace("_", "") # spaces are occasionally interpreted as underscores
            transcription = transcription.replace(" ", "") # reduces the number of possibilities that need to be tested

            ### Irradiance Processing ###
            for unit_variation in ("W/m2", "W/m²"):
                if unit_variation in transcription and transcription != unit_variation:
                    l_index = 0
                    r_index = transcription.rindex(unit_variation)
                    for name_variation in ("SolarIrradiance", 'Solarlrradiance'):
                        if name_variation in transcription:
                            l_index = transcription.index(name_variation) + len(name_variation)
                    try:
                        results["measurement"] = float(transcription[l_index:r_index])
                    except Exception as e:
                        print("Results:", results)
                        print("Transcription:", transcription)
                        for d2 in r_obj:
                            print("\t", d2)

            ### Location Processing ###
            for name in ("Latitude", "Longitude"):
                l_index = 0
                r_index = len(transcription)
                if name in transcription:
                    l_index = transcription.index(name) + len(name)
                    if "°" in transcription:
                        r_index = transcription.rindex("°")
                        try:
                            results[name.lower()] = float(transcription[l_index:r_index])
                        except Exception as e:
                            print("Results:", results)
                            print("Transcription:", transcription)
                            for d2 in r_obj:
                                print("\t", d2)
                    elif not transcription.isalpha(): #scenario where degree sign is missing
                        try:
                            results[name.lower()] = float(transcription[l_index:r_index])
                        except Exception as e:
                            print("Results:", results)
                            print("Transcription:", transcription)
                            for d2 in r_obj:
                                print("\t", d2)

        # last ditch effort to find match in the event coordinate and label detection were split
        if results["latitude"] == -1:
            for detection in r_obj:
                transcription = detection["transcription"]
                if transcription.startswith("42."):
                    transcription = transcription.replace("°", "")
                    results["latitude"] = float(transcription)

        if results["longitude"] == -1:
            for detection in r_obj:
                transcription = detection["transcription"]
                if transcription.startswith("-87."):
                    transcription = transcription.replace("°", "")
                    results["longitude"] = float(transcription)

        ### Missed Data Tracking ###
        for data_type in results:
            if results[data_type] == -1: # default value for results is -1
                results["detection"] = detections[0][detections[0].index("\t") + 1:]
                failures.append(results)
                break
        else:
            data.append(results)

    return pd.DataFrame(data), pd.DataFrame(failures)

def get_detection_for_image(image_path: Path) -> list[dict]:
    """Extract detection data for a single image file.
    
    :param image_path: location of image file to process
    :return: output from the model constructed into a workable object
    """
    onnx_engine = OpenOCR(backend="onnx", device="cpu")
    options = ort.SessionOptions()
    options.log_severity_level = 3

    detections, _ = onnx_engine(str(image_path))
    r_obj = eval(detections[0][detections[0].index("\t") + 1:])
        
    return r_obj

if __name__ == "__main__":
    month = "September"
    archive_path = SCREENSHOT_FOLDER / month
    data, failures = process_screenshots(archive_path)
    print("Failures:", failures["filename"])

    data_output_location = OUTPUT_FOLDER / f"{month}.csv"
    failure_record_location = OUTPUT_FOLDER / f"{month}_failures.csv"
    data.to_csv(data_output_location)
    failures.to_csv(failure_record_location)
