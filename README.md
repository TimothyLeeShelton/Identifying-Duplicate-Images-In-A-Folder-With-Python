# Summary

This Python script identifies and organizes duplicate images and videos within a specified folder and all its subfolders. It includes a graphical user interface (GUI) for comparing and managing duplicates.

## Warnings: 
- Please note: This was a hobby project, please don't trust it with anything you can't afford to delete.
- It will traverse all sub-folders of the primary file, and will re-organize every image/video into either a "Duplicates" folder or a "Non-Duplicates" folder.
- Items you choose to delete through the GUI will be moved to your computer's Recycle Bin.

## Setup for Beginners

If you're new to Python and haven't used the command prompt before, follow these step-by-step instructions to get started:

1. Install Python:
   - Visit the official Python website: https://www.python.org/downloads/
   - Download the latest version of Python for Windows
   - Run the installer. Important: Check the box that says "Add Python to PATH" before installing
   - Click "Install Now"

2. Install Required Libraries:
   - After Python is installed, open the Start menu and type "cmd"
   - Click on "Command Prompt" to open it
   - In the command prompt window, type the following command and press Enter:
     ```
     pip install imagehash Pillow opencv-python send2trash
     ```
   - Wait for the installations to complete

## Usage

1. Download the Script:
   - Download the `duplicate_file_organizer.py` file to your computer

2. Edit the Folder Path:
   - Right-click on the `duplicate_file_organizer.py` file and select "Edit" or "Open with" and choose a text editor like Notepad
   - Find the line that says: `folder_path = r"C:\Path\To\Your\Folder"`
   - Replace `C:\Path\To\Your\Folder` with the path to the folder you want to organize
   - For example, if your images are in a folder called "My Pictures" on your Desktop, it might look like this:
     `folder_path = r"C:\Users\YourUsername\Desktop\My Pictures"`
   - Save the file and close the text editor

3. Run the Script:
   - Open File Explorer and navigate to where you saved the `duplicate_file_organizer.py` file
   - In the File Explorer address bar, type "cmd" and press Enter. This will open a command prompt in that folder
   - In the command prompt, type the following and press Enter:
     ```
     python duplicate_file_organizer.py
     ```
   - The script will start running. You'll see progress updates in the command prompt window

4. Using the GUI:
   - After the script finishes organizing files, it will ask if you want to launch the GUI
   - Type 'y' and press Enter to launch the GUI
   - The GUI will show you pairs of duplicate files. You can:
     - Click "Skip" to move to the next pair
     - Click "Delete file: [filename]" to move that file to the Recycle Bin
   - When you're done, close the GUI window, and close the command prompt window.

5. Check Results:
   - Open the folder you specified in step 2
   - You'll see two new folders:
     - "NonDuplicateImages": Contains all unique files
     - "DuplicateImageSets": Contains all the files that were part of duplicate image sets, and any remaining skipped sets of duplicate files.

## Features
- Analyzes a range of filetypes (.png, .jpg, .jpeg, .gif, .bmp, .mp4, .avi, .mov, .wmv)
- Identifies duplicate files using image hashing techniques
- Organizes files into separate folders for non-duplicates and duplicate sets
- Provides progress updates and estimated completion time
- Implements a timeout mechanism to prevent excessively long runs
- Verifies file integrity during the moving process
- Removes empty folders after organization
- GUI for comparing and deleting duplicate files
- Handles both image and video files in the comparison GUI

## Requirements
- Python 3.x
- Required libraries: 
  - os
  - threading
  - time
  - shutil
  - hashlib
  - collections
  - tkinter
  - send2trash
  - cv2 (OpenCV)
  - imagehash
  - PIL (Python Imaging Library)

## Important Notes
- The script has a built-in timeout of 100 minutes (6000 seconds) to prevent excessively long runs.
- Always keep a backup of your original folder before running this script.
- Verify that all files have been correctly organized before deleting any original files.
- The script defaults to only surfacing exact identical images as duplicates. If you want to find similar images, see the note in customization section.
- Files deleted through the GUI are moved to the Recycle Bin, not permanently deleted.

## Customization
- You can adjust the timeout duration by modifying the `time.sleep(6000)` value in the `timeout_function()`.
- To include additional file types, add them to the file extension checks in the `get_file_hash()` function.
- It currently uses a hashing algorithm that identifies exact duplicates. If you want it to match more loosely on similar photos, you can comment out the existing hash function, and un-comment the one that is currently commented out.

## Limitations
- The script currently only analyzes the first frame of video files for comparison.
- Very large folders with numerous files may require significant processing time.

## Disclaimer
This script modifies your file system. Use it at your own risk and always ensure you have backups of important data before running it.
