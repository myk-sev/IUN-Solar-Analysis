from openocr import OpenOCR
from pathlib import Path
from os import getcwd
import pandas as pd
import onnxruntime as ort

def process_screenshots(archive_path):
    """"Utilize OpenOCR vision model to extract solar irradiance, longitude, and latitude from SPARKvue screenshots.

    [args]
        archive_path: disc location of the screenshots. *must be a path object*

    [output]
        pd.DataFrame: solar irradiance, longitude, and latitude linked to file name
        failures: images from which a data point could not be read

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
            "SolarIrradiance":0,
            "Longitude":0,
            "Latitude":0
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
                        results["SolarIrradiance"] = float(transcription[l_index:r_index])
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
                            results[name] = float(transcription[l_index:r_index])
                        except Exception as e:
                            print("Results:", results)
                            print("Transcription:", transcription)
                            for d2 in r_obj:
                                print("\t", d2)
                    elif not transcription.isalpha(): #scenario where degree sign is missing
                        try:
                            results[name] = float(transcription[l_index:r_index])
                        except Exception as e:
                            print("Results:", results)
                            print("Transcription:", transcription)
                            for d2 in r_obj:
                                print("\t", d2)

        ### Missed Data Tracking ###
        for data_type in results:
            if not results[data_type]: # default value for results is 0
                failures.append(img_path.name)
        else:
            data.append(results)

    return pd.DataFrame(data), failures




if __name__ == "__main__":
    month = "February"
    archive_path = Path(getcwd()) / "Screenshots" / month
    df, failures = process_screenshots(archive_path)
    print(df.head())
    print(failures)

    first_img = df.iloc[0]['File'][:-4]
    last_img = df.iloc[-1]['File'][:-4]
    output_file_name = f"{month}.csv"
    df.to_csv("Data/" + output_file_name)