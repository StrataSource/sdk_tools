# Script for converting original VGUI captions into the .kv3 format used by Panorama. (V1.00)
# Credit goes to gemini/copilot for any regex in this script (it scares me).
# Extra credit goes to Sirenstorm for putting up with my bombardment of questions :P
# - Rip Rip Rip

import sys
import os
import pathlib
import re

# check if input file was provided before doing anything else
if len(sys.argv) != 2:
    print("Usage: python convert_captions_to_panorama.py <input_file>")
    sys.exit(1)

# captions input file (should be UTF-16 since thats what the old VGUI captions use)
inputFile = sys.argv[1]
inputFileName = pathlib.Path(inputFile).stem

# set working directory to where the script was ran from
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

# read the provided file and store lines in a list
with open(inputFile, "r", encoding = "utf-16") as file:
    lines = file.readlines()

# detect language of captions
try:
    fileLanguage = re.search(r'"Language"\s+"([^"]+)', lines[2]).group(1)
    print(f"\n=== Detected caption language: {fileLanguage}")
except Exception as e:
    print(f"=== Error detecting caption language, defaulting to 'english' ({e})")
    fileLanguage = "english"

# update header to match what panorama wants
try:
    print("\n=== Updating file header to match Panorama format...")
    fileHeader = [
        "{\n",
        "	format_version = 0\n",
        f"	language = \"{fileLanguage}\"\n",
        "	tokens = {\n",
        ""]
    lines[:5] = fileHeader
except Exception as e:
    print(f"Error updating file header! {e}")

# iterate through the rest of the lines and update accordingly
try:
    print("\n=== Updating caption lines to match Panorama format:")
    for x in range(5, len(lines) - 1):
        
        print(f"- Updating caption line {x}...")

        # get caption line
        caption = lines[x].strip()
        
        # match the first quoted string as the token, and everything inside the second set of quotes as the value
        match = re.search(r'^"([^"]+)"\s+"(.*)"$', caption)

        if match:   # if its a valid caption in the original format ("token" "value")
            captionToken = match.group(1)
            captionValue = match.group(2)
            
            # === escape any backslashes in the caption token
            captionToken = captionToken.replace("\\", "\\\\")

            # replace colour tags (`<clr:250,231,181>` becomes <font color=\"rgb(250,231,181)\">\)
            captionValue = re.sub(r'<clr:(\d+),(\d+),(\d+)>', r'<font color=\"rgb(\1,\2,\3)\">', captionValue)

            # replace generic caption codes:   <B> --> <b>   <I> --> <i>   <cr> --> <br>
            captionValue = captionValue.replace("<B>", "<b>").replace("<I>", "<i>").replace("<cr>", "<br>")

            # fix closing <b> tags to be </b> instead of <b> and same for <i>
            captionValue = re.sub(r'<b>(.*?)<b>', r'<b>\1</b>', captionValue)   # <B>
            captionValue = re.sub(r'<i>(.*?)<i>', r'<i>\1</i>', captionValue)   # <I>

            # === update the line in the file
            lines[x] = f"		\"{captionToken}\" = \"{captionValue}\"\n"
        else:
            continue
        
except Exception as e:
    print(f"Error updating caption lines! {e}")

# write updated lines back to file (UTF-8 since thats what panorama uses)
try:
    print("\n=== Writing updated captions to file...")

    with open(f"{inputFileName}.kv3", "w", encoding = "utf-8") as file:
        file.writelines(lines)

    print(f"\n=== Successfully converted captions! Output file: {inputFileName}.kv3\n")

except Exception as e:
    print(f"Error writing captions! {e}")