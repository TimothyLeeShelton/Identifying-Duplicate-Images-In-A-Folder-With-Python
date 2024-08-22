# Import necessary libraries
import os  # For operating system related operations like file and directory handling
import threading  # For running multiple tasks concurrently
import time  # For timing operations and adding delays
import shutil  # For high-level file operations like copying
import hashlib  # For generating file hashes
from collections import defaultdict  # For creating dictionaries with default values
import concurrent.futures  # For parallel execution of tasks
import threading  # For creating and managing threads

# Import third-party libraries
import tkinter as tk  # For creating graphical user interfaces
import send2trash  # For safely deleting files by moving them to the recycle bin
from tkinter import ttk  # For themed Tkinter widgets
import cv2  # For handling video files
import imagehash  # For generating perceptual hashes of images
from PIL import Image, ImageTk  # For image processing and display in Tkinter

# Global variables
running = True  # Controls the overall execution of the script
folder_path = r"C:\Users\..."  # The folder to search for duplicates (replace with actual path)

# Function to calculate a hash (unique identifier) for a file
def get_file_hash(file_path):
    try:
        with open(file_path, "rb") as f:  # Open the file in binary mode
            file_hash = hashlib.md5()  # Create a new MD5 hash object
            chunk = f.read(8192)  # Read the file in chunks of 8192 bytes
            while chunk:
                file_hash.update(chunk)  # Update the hash with each chunk
                chunk = f.read(8192)
        return file_hash.hexdigest()  # Return the final hash as a hexadecimal string
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")  # Print any errors that occur
    return None  # Return None if there was an error

# Function to process a chunk of files
def process_file_chunk(file_chunk):
    local_hash_dict = defaultdict(list)  # Create a dictionary to store file hashes and paths
    for file_path in file_chunk:
        if not running:  # Check if the script should still be running
            return None
        file_hash = get_file_hash(file_path)  # Get the hash of the current file
        if file_hash:
            local_hash_dict[file_hash].append(file_path)  # Add the file path to the list for this hash
    return local_hash_dict  # Return the dictionary of hashes and file paths

# Function to find duplicate files in a folder
def find_duplicates(folder_path):
    global running
    hash_dict = defaultdict(list)  # Create a dictionary to store all file hashes and paths
    
    all_files = []
    for root, dirs, files in os.walk(folder_path):  # Walk through all directories and files
        all_files.extend([os.path.join(root, file) for file in files])  # Add full file paths to the list
    
    total_files = len(all_files)
    print(f"Total files to analyze: {total_files}")
    
    num_threads = os.cpu_count() or 1  # Determine the number of CPU cores available
    chunk_size = max(1, total_files // num_threads)  # Calculate the size of each chunk of files
    
    analyzed_files = 0
    start_time = time.time()  # Record the start time
    
    # Use a ThreadPoolExecutor to process file chunks in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_to_chunk = {executor.submit(process_file_chunk, all_files[i:i+chunk_size]): i 
                           for i in range(0, len(all_files), chunk_size)}
        
        for future in concurrent.futures.as_completed(future_to_chunk):
            if not running:
                return None, None
            chunk_result = future.result()
            if chunk_result:
                for file_hash, file_list in chunk_result.items():
                    hash_dict[file_hash].extend(file_list)  # Combine results from all chunks
            
            analyzed_files += chunk_size
            current_time = time.time()
            elapsed_time = current_time - start_time
            percentage = (analyzed_files / total_files) * 100
            
            # Calculate and display progress information
            if analyzed_files > 10:
                estimated_total_time = elapsed_time / (analyzed_files / total_files)
                estimated_remaining_time = estimated_total_time - elapsed_time
                time_remaining_str = f", Estimated time remaining: {estimated_remaining_time:.2f} seconds"
            else:
                time_remaining_str = ""
            
            print(f"Analyzed approximately {analyzed_files} out of {total_files} files ({percentage:.2f}%){time_remaining_str}")
    
    duplicates = {k: v for k, v in hash_dict.items() if len(v) > 1}  # Filter out non-duplicates
    return duplicates, hash_dict

# Function to calculate the MD5 checksum of a file
def get_file_checksum(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):  # Read the file in 4KB chunks
            hash_md5.update(chunk)
    return hash_md5.hexdigest()  # Return the hexadecimal representation of the hash

# Function to stop the script after a certain time
def timeout_function():
    global running
    time.sleep(6000)  # Wait for 100 minutes
    running = False
    print("Script execution timed out after 100 minutes")

# Function to safely move a file and verify its integrity
def safe_move(src, dst):
    if not os.path.exists(src):
        print(f"Warning: Source file does not exist: {src}")
        return False

    src_checksum = get_file_checksum(src)  # Get the checksum of the source file
    shutil.copy2(src, dst)  # Copy the file to the destination
    dst_checksum = get_file_checksum(dst)  # Get the checksum of the copied file

    if src_checksum == dst_checksum:
        os.remove(src)  # If checksums match, delete the original file
        return True
    else:
        os.remove(dst)  # If checksums don't match, delete the copy and report an error
        print(f"Error: File integrity check failed for {src}")
        return False

# Function to organize files into duplicate and non-duplicate folders
def organize_files(folder_path, duplicate_groups, hash_dict):
    non_duplicate_folder = os.path.join(folder_path, "NonDuplicateImages")
    duplicate_sets_folder = os.path.join(folder_path, "DuplicateImageSets")
    
    os.makedirs(non_duplicate_folder, exist_ok=True)  # Create folder for non-duplicates
    os.makedirs(duplicate_sets_folder, exist_ok=True)  # Create folder for duplicates
    
    total_files = sum(len(file_list) for file_list in hash_dict.values())
    processed_files = 0
    start_time = time.time()

    print(f"\nOrganizing {total_files} files...")

    # Move non-duplicate files
    for hash_value, file_list in hash_dict.items():
        if len(file_list) == 1:  # If there's only one file with this hash, it's not a duplicate
            file_path = file_list[0]
            file_name = os.path.basename(file_path)
            base_name, extension = os.path.splitext(file_name)
            
            # Handle filename conflicts
            counter = 1
            new_file_name = file_name
            while os.path.exists(os.path.join(non_duplicate_folder, new_file_name)):
                new_file_name = f"{base_name}_{counter}{extension}"
                counter += 1
            
            if safe_move(file_path, os.path.join(non_duplicate_folder, new_file_name)):
                processed_files += 1
            else:
                print(f"Failed to move file: {file_path}")

            # Update progress every 10 files
            if processed_files % 10 == 0:
                update_progress(processed_files, total_files, start_time)
    
    # Move duplicate files
    for hash_value, file_list in duplicate_groups.items():
        for file_path in file_list:
            file_name, file_ext = os.path.splitext(os.path.basename(file_path))
            
            # Handle filename conflicts
            counter = 1
            new_file_name = f"{file_name}{file_ext}"
            while os.path.exists(os.path.join(duplicate_sets_folder, new_file_name)):
                new_file_name = f"{file_name}_{counter}{file_ext}"
                counter += 1
            
            if safe_move(file_path, os.path.join(duplicate_sets_folder, new_file_name)):
                processed_files += 1
            else:
                print(f"Failed to move file: {file_path}")

            # Update progress every 10 files
            if processed_files % 10 == 0:
                update_progress(processed_files, total_files, start_time)

    # Final progress update
    update_progress(processed_files, total_files, start_time)
    print("\nFile organization completed.")

# Function to update and display progress information
def update_progress(processed_files, total_files, start_time):
    current_time = time.time()
    elapsed_time = current_time - start_time
    percentage = (processed_files / total_files) * 100
    
    if processed_files > 10:
        estimated_total_time = elapsed_time / (processed_files / total_files)
        estimated_remaining_time = estimated_total_time - elapsed_time
        time_remaining_str = f", Estimated time remaining: {estimated_remaining_time:.2f} seconds"
    else:
        time_remaining_str = ""
    
    print(f"Organized {processed_files} out of {total_files} files ({percentage:.2f}%){time_remaining_str}")

# Function to remove empty folders recursively
def remove_empty_folders(path):
    for root, dirs, files in os.walk(path, topdown=False):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if not os.listdir(dir_path):  # Check if the directory is empty
                try:
                    os.rmdir(dir_path)
                    print(f"Removed empty folder: {dir_path}")
                except OSError as e:
                    print(f"Error removing empty folder {dir_path}: {e}")                

# Function to create and manage the GUI for comparing duplicate images
def compare_duplicates_gui(duplicate_groups):
    shown_images = set()  # Set to keep track of images that have been displayed

    # Function to load the next pair of duplicate images
    def load_next_pair():
        nonlocal current_pair_index
        while current_pair_index < len(image_pairs):
            pair = image_pairs[current_pair_index]
            try:
                # Print whether each image in the pair has been shown before
                print("Loading new image pair:")
                for img_path in pair:
                    img_name = os.path.basename(img_path)
                    print(f"{img_name}: {'True' if img_name in shown_images else 'False'}")
                
                display_images(pair[0], pair[1])  # Display the images
                
                # Add the filenames to the shown_images set
                shown_images.add(os.path.basename(pair[0]))
                shown_images.add(os.path.basename(pair[1]))
                
                current_pair_index += 1
                return
            except Exception as e:
                print(f"Error displaying pair {current_pair_index}: {str(e)}")
                current_pair_index += 1
        print("No more image pairs to compare.")
        root.quit()  # Close the GUI when all pairs have been shown

    # Function to get the file size in MB
    def get_file_size(file_path):
        size_bytes = os.path.getsize(file_path)
        size_mb = round(size_bytes / (1024 * 1024), 2)
        return f"{size_mb} MB"

    # Function to display images or video thumbnails
    def display_images(img1_path, img2_path):
        def process_file(file_path, img_label, name_label, delete_button):
            file_name = os.path.basename(file_path)
            file_size = get_file_size(file_path)
            name_label.config(text=f"{file_name}\nSize: {file_size}")
            delete_button.config(text=f"Delete file: {file_name}")

            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                # Handle image files
                img = Image.open(file_path)
                img.thumbnail((400, 400))  # Resize the image
                photo = ImageTk.PhotoImage(img)
                img_label.config(image=photo)
                img_label.image = photo
            elif file_path.lower().endswith(('.mp4', '.avi', '.mov', '.wmv')):
                # Handle video files
                video = cv2.VideoCapture(file_path)
                ret, frame = video.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame)
                    img.thumbnail((400, 400))  # Resize the frame
                    photo = ImageTk.PhotoImage(img)
                    img_label.config(image=photo)
                    img_label.image = photo
                else:
                    img_label.config(image='')
                    img_label.image = None
                    print(f"Unable to read video file: {file_path}")
                video.release()
            else:
                img_label.config(image='')
                img_label.image = None
                print(f"Unsupported file type: {file_path}")

        # Process and display both images
        for file_path, img_label, name_label, delete_button in [
            (img1_path, img1_label, img1_name_label, delete1_button),
            (img2_path, img2_label, img2_name_label, delete2_button)
        ]:
            process_file(file_path, img_label, name_label, delete_button)

    # Function to skip the current pair of images
    def skip():
        load_next_pair()
     
    def delete_image(img_path):
        try:
            send2trash.send2trash(img_path)
            print(f"Moved to Recycle Bin: {img_path}")
            # Remove the deleted file from the current pair
            current_pair = image_pairs[current_pair_index - 1]
            current_pair.remove(img_path)
            if len(current_pair) == 1:
                # If only one image left in the pair, move to the next pair
                load_next_pair()
            else:
                # If both images were deleted, move to the next pair
                load_next_pair()
        except Exception as e:
            print(f"Error moving {img_path} to Recycle Bin: {e}")

    # Function to handle closing the GUI window
    def on_closing():
        root.quit()

    # Convert duplicate_groups to a list of pairs
    image_pairs = [group for group in duplicate_groups.values() if len(group) > 1]

    if not image_pairs:
        print("No duplicate pairs found.")
        return

    current_pair_index = 0

    # Create main window
    root = tk.Tk()
    root.title("Duplicate Image Comparison")

    # Create and pack widgets
    frame = ttk.Frame(root, padding="10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    skip_button = ttk.Button(frame, text="Skip", command=skip)
    skip_button.grid(row=0, column=1, pady=10)

    img1_label = ttk.Label(frame)
    img1_label.grid(row=2, column=0, padx=10)

    img2_label = ttk.Label(frame)
    img2_label.grid(row=2, column=2, padx=10)

    img1_name_label = ttk.Label(frame, text="")
    img1_name_label.grid(row=3, column=0)

    img2_name_label = ttk.Label(frame, text="")
    img2_name_label.grid(row=3, column=2)

    delete1_button = ttk.Button(frame, text="", command=lambda: delete_image(image_pairs[current_pair_index-1][0]))
    delete1_button.grid(row=1, column=0)

    delete2_button = ttk.Button(frame, text="", command=lambda: delete_image(image_pairs[current_pair_index-1][1]))
    delete2_button.grid(row=1, column=2)

    # Load first pair of images
    load_next_pair()

    # Set up the closing protocol
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Start GUI event loop
    root.mainloop()

# Function to update the file paths of duplicates after reorganization
def update_duplicate_paths(duplicate_groups, folder_path):
    duplicate_sets_folder = os.path.join(folder_path, "DuplicateImageSets")
    updated_groups = {}
    
    for hash_value, file_list in duplicate_groups.items():
        updated_list = []
        for file_path in file_list:
            file_name = os.path.basename(file_path)
            new_path = os.path.join(duplicate_sets_folder, file_name)
            if os.path.exists(new_path):
                updated_list.append(new_path)
            else:
                print(f"Warning: File not found at expected location: {new_path}")
        
        if updated_list:
            updated_groups[hash_value] = updated_list
    
    return updated_groups

# Function to run the GUI in a separate thread
def run_gui_in_thread(duplicate_groups):
    gui_thread = threading.Thread(target=compare_duplicates_gui, args=(duplicate_groups,))
    gui_thread.start()
    return gui_thread

# Create and start the timeout thread
timeout_thread = threading.Thread(target=timeout_function)
timeout_thread.start()

try:
    start_time = time.time()  # Record the start time of the script
    duplicate_groups, hash_dict = find_duplicates(folder_path)  # Find duplicate files
    
    if duplicate_groups is not None and hash_dict is not None:
        # Calculate and display summary statistics
        total_files = sum([len(files) for r, d, files in os.walk(folder_path)])
        total_duplicates = sum(len(file_list) for file_list in duplicate_groups.values()) - len(duplicate_groups)
        duplicate_percentage = (total_duplicates / total_files) * 100

        print(f"\nSummary:")
        print(f"Total files analyzed: {total_files}")
        print(f"Total duplicate copies found: {total_duplicates}")
        print(f"Percentage of files that are duplicates: {duplicate_percentage:.2f}%\n")

        print("Organizing files...")
        organize_files(folder_path, duplicate_groups, hash_dict)  # Organize files into duplicate and non-duplicate folders
        print("File organization completed.")
        
        print("\nRemoving empty folders...")
        remove_empty_folders(folder_path)  # Remove any empty folders left after organization
        print("Empty folder removal completed.")
        
        print(f"Duplicate groups variable looks like: {duplicate_groups}")
        
        end_time = time.time()
        print(f"Script completed in {end_time - start_time:.2f} seconds")

        print("Updating duplicate file paths...")
        duplicate_groups = update_duplicate_paths(duplicate_groups, folder_path)  # Update file paths after reorganization
        print("File paths updated.")

        # Prompt user to launch GUI
        launch_gui = input("Do you want to launch the duplicate comparison GUI? (y/n): ").lower().strip()
        if launch_gui == 'y':
            gui_thread = run_gui_in_thread(duplicate_groups)  # Run GUI in a separate thread
            print("GUI launched. You can continue using the console.")
            print("The program will exit when you close the GUI window.")
            gui_thread.join()  # Wait for GUI thread to finish
        else:
            print("GUI not launched. Script execution complete.")
    else:
        print("Script execution was interrupted")
except Exception as e:
    print(f"An error occurred: {str(e)}")
finally:
    running = False  # Stop the script execution
    timeout_thread.join()  # Wait for the timeout thread to finish

print("\nIMPORTANT: Please verify that all files have been correctly organized before deleting any original files.")
print("It's recommended to keep a backup of the original folder until you've confirmed the results.")
