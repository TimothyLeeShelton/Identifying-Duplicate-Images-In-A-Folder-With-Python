# Duplicate File Organizer

This Python script identifies duplicate images and videos within a specified folder and all it's subfolders.

## Features

- Analyzes a range of filetypes (.png, .jpg, .jpeg, .gif, .bmp, .mp4, .avi, .mov, .wmv)
- Identifies duplicate files using image hashing techniques
- Organizes files into separate folders for non-duplicates and duplicate sets. Duplicate image pairs go into their own file, so the user can choose which to delete.
- Provides progress updates and estimated completion time
- Implements a timeout mechanism to prevent excessively long runs
- Verifies file integrity during the moving process
- Removes empty folders after organization

## Requirements

- Python 3.x
- Required libraries: 
  - os
  - imagehash
  - PIL (Python Imaging Library)
  - cv2 (OpenCV)
  - collections
  - threading
  - time
  - shutil
  - hashlib

## Usage

1. Install the required libraries:
   ```
   pip install imagehash Pillow opencv-python
   ```

2. Replace the `folder_path` variable in the script with the path to the folder you want to organize:
   ```python
   folder_path = r"C:\Path\To\Your\Folder"
   ```

3. Run the script:
   ```
   python duplicate_file_organizer.py
   ```

4. The script will analyze the files, provide progress updates, and organize them into the following structure:
   - NonDuplicateImages: Contains all non-duplicate files
   - DuplicateImageSets: Contains folders (Set_1, Set_2, etc.) with groups of duplicate files

## Important Notes

- The script has a built-in timeout of 100 minutes (6000 seconds) to prevent excessively long runs.
- Always keep a backup of your original folder before running this script.
- Verify that all files have been correctly organized before deleting any original files.
- The script uses image hashing, which may occasionally identify visually similar (but not identical) images as duplicates.

## Customization

- You can adjust the timeout duration by modifying the `time.sleep(6000)` value in the `timeout_function()`.
- To include additional file types, add them to the file extension checks in the `get_file_hash()` function.

## Limitations

- The script currently only analyzes the first frame of video files. For more comprehensive video comparison, you could implement a more advanced video hashing technique.
- Very large folders with numerous files require significant processing time.

## Disclaimer

This script modifies your file system. Use it at your own risk and always ensure you have backups of important data before running it.
