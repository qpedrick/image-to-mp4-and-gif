import os
import re
import shutil
from datetime import datetime
from typing import List, Optional

from PIL import Image
import imageio

# --- Configuration ---
IMAGE_FOLDER = 'images'
OUTPUT_BASE_DIR = 'output'
ARCHIVE_DIR = 'output_archive'

def process_images() -> Optional[List[Image.Image]]:
    """Loads, sorts, and resizes all images from the source folder."""
    try:
        files = [f for f in os.listdir(IMAGE_FOLDER) if f.endswith('.png')]
        if not files:
            print(f"Error: No PNG images found in the '{IMAGE_FOLDER}' directory.")
            print("Please add your numbered images (e.g., image-1.png) to that folder.")
            return None

        files.sort(key=lambda f: int(re.search(r'(\d+)', f).group()))
        
        images: List[Image.Image] = []
        target_size: Optional[tuple[int, int]] = None

        print(f"Found {len(files)} images to process.")
        for i, filename in enumerate(files):
            filepath = os.path.join(IMAGE_FOLDER, filename)
            img = Image.open(filepath).convert("RGBA")

            if i == 0:
                target_size = img.size
                print(f"All frames will be resized to {target_size[0]}x{target_size[1]} pixels.")

            if img.size != target_size:
                img = img.resize(target_size, Image.Resampling.LANCZOS)
            
            images.append(img)
        
        return images
    except FileNotFoundError:
        print(f"Error: The directory '{IMAGE_FOLDER}' was not found.")
        return None
    except Exception as e:
        print(f"An error occurred while processing images: {e}")
        return None

def handle_existing_output() -> bool:
    """Checks for existing output and asks the user how to proceed.

    Returns:
        bool: True if the process should continue, False otherwise.
    """
    if os.path.exists(OUTPUT_BASE_DIR) and os.listdir(OUTPUT_BASE_DIR):
        while True:
            choice = input(
                f"\nThe '{OUTPUT_BASE_DIR}' directory is not empty. "
                "Would you like to [A]rchive the old files or [D]elete them? (A/D): "
            ).lower()
            if choice in ['a', 'archive']:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                archive_path = os.path.join(ARCHIVE_DIR, f"output_{timestamp}")
                os.makedirs(ARCHIVE_DIR, exist_ok=True)
                shutil.move(OUTPUT_BASE_DIR, archive_path)
                print(f"Archived existing output to '{archive_path}'")
                return True
            elif choice in ['d', 'delete']:
                shutil.rmtree(OUTPUT_BASE_DIR)
                print(f"Deleted existing contents of '{OUTPUT_BASE_DIR}'")
                return True
            else:
                print("Invalid choice. Please enter 'A' to archive or 'D' to delete.")
    return True # No existing output, so we can proceed

def create_mp4(images: List[Image.Image], fps: int, output_path: str, target_duration: int) -> None:
    """Creates a fixed-duration MP4 video by looping the image sequence."""
    print(f"\n--- Creating MP4 at {fps} FPS ---")
    num_frames = len(images)
    sequence_duration = num_frames / fps
    num_loops = max(1, round(target_duration / sequence_duration))

    print(f"The {num_frames}-frame sequence will be looped {num_loops} times for a ~{target_duration}s video.")
    
    with imageio.get_writer(output_path, fps=fps, codec='libx264', quality=8) as writer:
        for _ in range(num_loops):
            for image in images:
                writer.append_data(imageio.core.asarray(image))
    print(f"Successfully created video: {output_path}")

def create_gif(images: List[Image.Image], fps: int, output_path: str) -> None:
    """Creates an infinitely looping GIF."""
    print(f"\n--- Creating GIF at {fps} FPS ---")
    frame_duration = 1 / fps
    imageio.mimsave(output_path, images, duration=frame_duration, loop=0)
    print(f"Successfully created GIF: {output_path}")


def main():
    """Main function to run the interactive CLI."""
    print("--- T-Rex Animation Generator ---")

    # 0. Handle existing output before asking for new parameters
    if not handle_existing_output():
        return # User chose not to proceed or an error occurred

    # 1. Get user input for video duration
    while True:
        try:
            duration_str = input("Enter the target video duration in seconds (e.g., 30): ")
            target_duration = int(duration_str)
            if target_duration > 0:
                break
            print("Please enter a positive number.")
        except ValueError:
            print("Invalid input. Please enter a whole number.")

    # 2. Get user input for FPS options
    while True:
        try:
            fps_str = input("Enter desired FPS options, separated by commas (e.g., 5,3,2): ")
            fps_options = [int(fps.strip()) for fps in fps_str.split(',')]
            if all(fps > 0 for fps in fps_options):
                break
            print("All FPS values must be positive numbers.")
        except (ValueError, IndexError):
            print("Invalid format. Please enter numbers separated by commas.")

    # 3. Process images
    processed_images = process_images()
    if not processed_images:
        print("\nExiting due to image processing errors.")
        return

    # 4. Create output directories
    mp4_dir = os.path.join(OUTPUT_BASE_DIR, 'mp4')
    gif_dir = os.path.join(OUTPUT_BASE_DIR, 'gif')
    os.makedirs(mp4_dir, exist_ok=True)
    os.makedirs(gif_dir, exist_ok=True)

    # 5. Generate all outputs
    for fps_option in fps_options:
        mp4_path = os.path.join(mp4_dir, f't-rex-attack-{fps_option}fps.mp4')
        gif_path = os.path.join(gif_dir, f't-rex-attack-{fps_option}fps.gif')
        
        create_mp4(processed_images, fps_option, mp4_path, target_duration)
        create_gif(processed_images, fps_option, gif_path)

    print("\nFinished generating all video and GIF options.")


if __name__ == '__main__':
    main()