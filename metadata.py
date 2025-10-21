from importlib.metadata import metadata

import pandas as pd
from pathlib import Path
from PIL import Image
from lxml import etree
import os

def extract_metadata(folder_path:Path) -> pd.DataFrame:
    all_metadata = []
    for img_path in folder_path.glob("*.png"): #look through each file in the image directory
        img_metadata = {
            "filename": img_path.name,
        }

        with Image.open(img_path) as img:
            # Extract XMP metadata if present
            xmp_data = img.info.get("XML:com.adobe.xmp")
            if xmp_data:
                root = etree.fromstring(xmp_data.encode("utf-8"))

                for elem in root.xpath("//*"):
                    if elem.text and elem.text.strip():
                        # Use namespace:tag format if available
                        if elem.prefix:
                            key = f"{elem.prefix}:{elem.tag.split('}')[-1]}"
                        else:
                            key = elem.tag.split('}')[-1]
                        img_metadata[key] = elem.text.strip()

                    # Include other PNG text metadata
            for key, value in img.info.items():
                if key != "XML:com.adobe.xmp":
                    img_metadata[key] = value

        all_metadata.append(img_metadata)

    return pd.DataFrame(all_metadata)

if __name__ == "__main__":
    main_dir = Path(os.getcwd()) / "Screenshots"
    sub_dirs = [main_dir / folder for folder in os.listdir(main_dir) if os.path.isdir(main_dir / folder)] #check that each result is indeed a directory
    output_csv = Path(os.getcwd()) / "metadata.csv"

    monthly_metadata = [extract_metadata(folder) for folder in sub_dirs]
    metadata_df = pd.concat(monthly_metadata, ignore_index=True)

    # Output clean up
    metadata_df = metadata_df.rename(columns={"photoshop:DateCreated": "timestamp"})
    metadata_df = metadata_df[["filename","timestamp"]]

    metadata_df.to_csv("metadata.csv")
