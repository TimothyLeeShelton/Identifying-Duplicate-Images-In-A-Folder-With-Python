# Standard library imports
import os
import threading
import time
import shutil
import hashlib
from collections import defaultdict
import concurrent.futures
import threading

# Third-party library imports
import tkinter as tk
import send2trash

from tkinter import ttk
import cv2
import imagehash
from PIL import Image, ImageTk


# Local imports

running = True
folder_path = r"C:\Users\..."  # Replace with your folder path

# This filehash approach finds only exact matches.
def get_file_hash(file_path):
    try:
        with open(file_path, "rb") as f:
            file_hash = hashlib.md5()
            chunk = f.read(8192)
            while chunk:
                file_hash.update(chunk)
                chunk = f.read(8192)
        return file_hash.hexdigest()
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
    return None

# The below is an alternative file hash that will find "close" matches. 
# def get_file_hash(file_path):
#     try:
#         if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
#             return imagehash.average_hash(Image.open(file_path))
#         elif file_path.lower().endswith(('.mp4', '.avi', '.mov', '.wmv')):
#             video = cv2.VideoCapture(file_path)
#             ret, frame = video.read()
#             if ret:
#                 return imagehash.average_hash(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
#             else:
#                 print(f"Warning: Unable to read video file: {file_path}")
#     except Exception as e:
#         print(f"Error processing file {file_path}: {str(e)}")
#     return None

def process_file_chunk(file_chunk):
    local_hash_dict = defaultdict(list)
    for file_path in file_chunk:
        if not running:
            return None
        file_hash = get_file_hash(file_path)
        if file_hash:
            local_hash_dict[file_hash].append(file_path)
    return local_hash_dict

def find_duplicates(folder_path):
    global running
    hash_dict = defaultdict(list)
    
    all_files = []
    for root, dirs, files in os.walk(folder_path):
        all_files.extend([os.path.join(root, file) for file in files])
    
    total_files = len(all_files)
    print(f"Total files to analyze: {total_files}")
    
    # Determine the number of threads to use (you can adjust this)
    num_threads = os.cpu_count() or 1
    chunk_size = max(1, total_files // num_threads)
    
    analyzed_files = 0
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_to_chunk = {executor.submit(process_file_chunk, all_files[i:i+chunk_size]): i 
                           for i in range(0, len(all_files), chunk_size)}
        
        for future in concurrent.futures.as_completed(future_to_chunk):
            if not running:
                return None, None
            chunk_result = future.result()
            if chunk_result:
                for file_hash, file_list in chunk_result.items():
                    hash_dict[file_hash].extend(file_list)
            
            analyzed_files += chunk_size
            current_time = time.time()
            elapsed_time = current_time - start_time
            percentage = (analyzed_files / total_files) * 100
            
            if analyzed_files > 10:
                estimated_total_time = elapsed_time / (analyzed_files / total_files)
                estimated_remaining_time = estimated_total_time - elapsed_time
                time_remaining_str = f", Estimated time remaining: {estimated_remaining_time:.2f} seconds"
            else:
                time_remaining_str = ""
            
            print(f"Analyzed approximately {analyzed_files} out of {total_files} files ({percentage:.2f}%){time_remaining_str}")
    
    duplicates = {k: v for k, v in hash_dict.items() if len(v) > 1}
    return duplicates, hash_dict



def get_file_checksum(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def timeout_function():
    global running
    time.sleep(6000)  # Max runtime
    running = False
    print("Script execution timed out after 100 minutes")

def safe_move(src, dst):
    # Check if source file exists
    if not os.path.exists(src):
        print(f"Warning: Source file does not exist: {src}")
        return False

    # Get the checksum of the source file
    src_checksum = get_file_checksum(src)

    # Copy the file
    shutil.copy2(src, dst)

    # Verify the checksum of the copied file
    dst_checksum = get_file_checksum(dst)

    if src_checksum == dst_checksum:
        # If checksums match, delete the original file
        os.remove(src)
        return True
    else:
        # If checksums don't match, delete the copy and report an error
        os.remove(dst)
        print(f"Error: File integrity check failed for {src}")
        return False

def organize_files(folder_path, duplicate_groups, hash_dict):
    non_duplicate_folder = os.path.join(folder_path, "NonDuplicateImages")
    duplicate_sets_folder = os.path.join(folder_path, "DuplicateImageSets")
    
    # Create master folders if they don't exist
    os.makedirs(non_duplicate_folder, exist_ok=True)
    os.makedirs(duplicate_sets_folder, exist_ok=True)
    
    # Count total files to process
    total_files = sum(len(file_list) for file_list in hash_dict.values())
    processed_files = 0
    start_time = time.time()

    print(f"\nOrganizing {total_files} files...")

    # Move non-duplicate images
    for hash_value, file_list in hash_dict.items():
        if len(file_list) == 1:
            file_path = file_list[0]
            file_name = os.path.basename(file_path)
            base_name, extension = os.path.splitext(file_name)
            
            # Check if a file with the same name already exists
            counter = 1
            new_file_name = file_name
            while os.path.exists(os.path.join(non_duplicate_folder, new_file_name)):
                new_file_name = f"{base_name}_{counter}{extension}"
                counter += 1
            
            if safe_move(file_path, os.path.join(non_duplicate_folder, new_file_name)):
                processed_files += 1
            else:
                print(f"Failed to move file: {file_path}")

            # Update progress
            if processed_files % 10 == 0:
                update_progress(processed_files, total_files, start_time)
    
    # Move duplicate images
    for hash_value, file_list in duplicate_groups.items():
        for file_path in file_list:
            file_name, file_ext = os.path.splitext(os.path.basename(file_path))
            
            # Check if a file with the same name already exists
            counter = 1
            new_file_name = f"{file_name}{file_ext}"
            while os.path.exists(os.path.join(duplicate_sets_folder, new_file_name)):
                new_file_name = f"{file_name}_{counter}{file_ext}"
                counter += 1
            
            if safe_move(file_path, os.path.join(duplicate_sets_folder, new_file_name)):
                processed_files += 1
            else:
                print(f"Failed to move file: {file_path}")

            # Update progress
            if processed_files % 10 == 0:
                update_progress(processed_files, total_files, start_time)

    # Final progress update
    update_progress(processed_files, total_files, start_time)
    print("\nFile organization completed.")

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

def remove_empty_folders(path):
    """
    Remove empty folders recursively
    """
    for root, dirs, files in os.walk(path, topdown=False):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if not os.listdir(dir_path):  # Check if the directory is empty
                try:
                    os.rmdir(dir_path)
                    print(f"Removed empty folder: {dir_path}")
                except OSError as e:
                    print(f"Error removing empty folder {dir_path}: {e}")                

def compare_duplicates_gui(duplicate_groups):
    shown_images = set()  # Set to store filenames of shown images

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
                
                display_images(pair[0], pair[1])
                
                # Add the filenames to the shown_images set
                shown_images.add(os.path.basename(pair[0]))
                shown_images.add(os.path.basename(pair[1]))
                
                current_pair_index += 1
                return
            except Exception as e:
                print(f"Error displaying pair {current_pair_index}: {str(e)}")
                current_pair_index += 1
        print("No more image pairs to compare.")
        root.quit()

    def get_file_size(file_path):
        size_bytes = os.path.getsize(file_path)
        size_mb = round(size_bytes / (1024 * 1024), 2)
        return f"{size_mb} MB"

    def display_images(img1_path, img2_path):
        def process_file(file_path, img_label, name_label, delete_button):
            file_name = os.path.basename(file_path)
            file_size = get_file_size(file_path)
            name_label.config(text=f"{file_name}\nSize: {file_size}")
            delete_button.config(text=f"Delete file: {file_name}")

            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                # Handle image files
                img = Image.open(file_path)
                img.thumbnail((400, 400))
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
                    img.thumbnail((400, 400))
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

        for file_path, img_label, name_label, delete_button in [
            (img1_path, img1_label, img1_name_label, delete1_button),
            (img2_path, img2_label, img2_name_label, delete2_button)
        ]:
            process_file(file_path, img_label, name_label, delete_button)

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

    # Load first pair
    load_next_pair()

    # Set up the closing protocol
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Start GUI event loop
    root.mainloop()



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

def run_gui_in_thread(duplicate_groups):
    gui_thread = threading.Thread(target=compare_duplicates_gui, args=(duplicate_groups,))
    gui_thread.start()
    return gui_thread

timeout_thread = threading.Thread(target=timeout_function)
timeout_thread.start()

try:
    start_time = time.time()
    duplicate_groups, hash_dict = find_duplicates(folder_path)
    
    if duplicate_groups is not None and hash_dict is not None:
        total_files = sum([len(files) for r, d, files in os.walk(folder_path)])
        total_duplicates = sum(len(file_list) for file_list in duplicate_groups.values()) - len(duplicate_groups)
        duplicate_percentage = (total_duplicates / total_files) * 100

        print(f"\nSummary:")
        print(f"Total files analyzed: {total_files}")
        print(f"Total duplicate copies found: {total_duplicates}")
        print(f"Percentage of files that are duplicates: {duplicate_percentage:.2f}%\n")

        print("Organizing files...")
        organize_files(folder_path, duplicate_groups, hash_dict)
        print("File organization completed.")
        
        print("\nRemoving empty folders...")
        remove_empty_folders(folder_path)
        print("Empty folder removal completed.")
        
        print(f"Duplicate groups variable looks like: {duplicate_groups}")
        

        end_time = time.time()
        print(f"Script completed in {end_time - start_time:.2f} seconds")

        print("Updating duplicate file paths...")
        duplicate_groups = update_duplicate_paths(duplicate_groups, folder_path)
        print("File paths updated.")

        # Prompt user to launch GUI
        launch_gui = input("Do you want to launch the duplicate comparison GUI? (y/n): ").lower().strip()
        if launch_gui == 'y':
            gui_thread = run_gui_in_thread(duplicate_groups)
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
    running = False
    timeout_thread.join()

print("\nIMPORTANT: Please verify that all files have been correctly organized before deleting any original files.")
print("It's recommended to keep a backup of the original folder until you've confirmed the results.")
