"""
Video Splitter - Split long videos into 60-second clips

This script provides two implementations:
1. MoviePy-based (Pythonic, easy to use)
2. FFmpeg-based (faster, more efficient for large videos)

Requirements:
- moviepy (for MoviePy implementation)
- ffmpeg (for FFmpeg implementation - binary should be in PATH or in ffmpeg/ folder)

Usage:
    python app.py <input_video> [--method moviepy|ffmpeg] [--output-dir <dir>] [--duration <seconds>]
"""

import os
import sys
import argparse
import subprocess
import math
from pathlib import Path

def get_video_duration_ffmpeg(video_path):
    """Get video duration using FFmpeg."""
    try:
        # Use system FFmpeg installation
        ffmpeg_path = "C:\\ffmpeg\\ffprobe.exe" if os.path.exists("C:\\ffmpeg\\ffprobe.exe") else "ffprobe"
        
        cmd = [
            ffmpeg_path,
            "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return float(result.stdout.strip())
        else:
            raise Exception(f"FFprobe error: {result.stderr}")
    except Exception as e:
        print(f"Error getting video duration with FFmpeg: {e}")
        return None

def split_video_ffmpeg(input_path, output_dir, chunk_duration=60):
    """Split video using FFmpeg (faster method)."""
    print("Using FFmpeg method...")
    
    # Get video duration
    duration = get_video_duration_ffmpeg(input_path)
    if duration is None:
        print("Failed to get video duration. Please check if FFmpeg is installed.")
        return False
    
    print(f"Video duration: {duration:.2f} seconds")
    
    # Calculate number of chunks
    num_chunks = math.ceil(duration / chunk_duration)
    print(f"Will create {num_chunks} chunks of {chunk_duration} seconds each")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Get input file extension
    input_path_obj = Path(input_path)
    extension = input_path_obj.suffix
    
    # Try to use system FFmpeg installation
    ffmpeg_path = "C:\\ffmpeg\\ffmpeg.exe" if os.path.exists("C:\\ffmpeg\\ffmpeg.exe") else "ffmpeg"
    
    # Split the video
    success_count = 0
    for i in range(num_chunks):
        start_time = i * chunk_duration
        output_file = os.path.join(output_dir, f"chunk_{i+1}{extension}")
        
        cmd = [
            ffmpeg_path,
            "-i", input_path,
            "-ss", str(start_time),
            "-t", str(chunk_duration),
            "-c", "copy",  # Copy streams without re-encoding (faster)
            "-avoid_negative_ts", "make_zero",
            output_file,
            "-y"  # Overwrite output files
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                success_count += 1
                print(f"Created chunk {i+1}/{num_chunks}: {output_file}")
            else:
                print(f"Error creating chunk {i+1}: {result.stderr}")
        except Exception as e:
            print(f"Error creating chunk {i+1}: {e}")
    
    print(f"\nCompleted! Created {success_count}/{num_chunks} chunks in '{output_dir}'")
    return success_count == num_chunks

def split_video_moviepy(input_path, output_dir, chunk_duration=60):
    """Split video using MoviePy (Python-based method)."""
    try:
        # moviepy's VideoFileClip is provided from moviepy.editor
        from moviepy.editor import VideoFileClip
    except ImportError:
        print("MoviePy not installed. Install it with: pip install moviepy")
        return False
    
    print("Using MoviePy method...")
    
    # Load the video
    try:
        video = VideoFileClip(input_path)
    except Exception as e:
        print(f"Error loading video: {e}")
        print("This might be due to:")
        print("  - Corrupted video file")
        print("  - Unsupported video format")
        print("  - Missing video metadata")
        print("  - File is not a valid video")
        return False
    
    duration = video.duration
    print(f"Video duration: {duration:.2f} seconds")
    
    # Calculate number of chunks
    num_chunks = math.ceil(duration / chunk_duration)
    print(f"Will create {num_chunks} chunks of {chunk_duration} seconds each")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Get input file extension
    input_path_obj = Path(input_path)
    extension = input_path_obj.suffix
    
    # Split the video
    success_count = 0
    for i in range(num_chunks):
        start_time = i * chunk_duration
        end_time = min((i + 1) * chunk_duration, duration)
        
        output_file = os.path.join(output_dir, f"chunk_{i+1}{extension}")
        
        print(f"Processing chunk {i+1}: {start_time:.2f}s to {end_time:.2f}s")
        
        try:
            # Create subclip
            subclip = video.subclip(start_time, end_time)
            
            # Write the subclip
            subclip.write_videofile(
                output_file,
                codec='libx264',
                audio_codec='aac',
                logger=None
            )
            
            # Close the subclip to free memory
            subclip.close()
            
            success_count += 1
            print(f"Created chunk {i+1}/{num_chunks}: {output_file}")
            
        except Exception as e:
            print(f"Error creating chunk {i+1}: {e}")
            # Try without audio codec for problematic files
            try:
                print(f"Retrying chunk {i+1} without audio codec...")
                subclip = video.subclip(start_time, end_time)
                subclip.write_videofile(
                    output_file,
                    codec='libx264',
                    logger=None
                )
                subclip.close()
                success_count += 1
                print(f"Created chunk {i+1}/{num_chunks}: {output_file} (retry successful)")
            except Exception as e2:
                print(f"Retry also failed for chunk {i+1}: {e2}")
                # Try one more time with minimal settings
                try:
                    print(f"Final retry for chunk {i+1} with basic settings...")
                    subclip = video.subclip(start_time, end_time)
                    subclip.write_videofile(output_file, logger=None)
                    subclip.close()
                    success_count += 1
                    print(f"Created chunk {i+1}/{num_chunks}: {output_file} (final retry successful)")
                except Exception as e3:
                    print(f"All retries failed for chunk {i+1}: {e3}")
    
    # Close the original video
    video.close()
    
    print(f"\nCompleted! Created {success_count}/{num_chunks} chunks in '{output_dir}'")
    return success_count == num_chunks

def check_ffmpeg_availability():
    """Check if FFmpeg is available."""
    try:
        # Check system FFmpeg installation first
        if os.path.exists("C:\\ffmpeg\\ffmpeg.exe"):
            return True
        
        # Check system PATH
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_moviepy_availability():
    """Check if MoviePy is available."""
    try:
        from moviepy import VideoFileClip
        return True
    except ImportError:
        return False

def main():
    parser = argparse.ArgumentParser(description="Split videos into chunks")
    # Remove this line: parser.add_argument("input_video", help="Path to input video file")
    parser.add_argument("--method", choices=["moviepy", "ffmpeg", "auto"], 
                       default="auto", help="Method to use for splitting")
    parser.add_argument("--output-dir", default="output_chunks", 
                       help="Output directory for chunks")
    parser.add_argument("--duration", type=int, default=60, 
                       help="Duration of each chunk in seconds")
    
    args = parser.parse_args()
    
    # Add interactive input for video path
    input_video = input("Enter the path to the video file: ").strip()
    
    # Then use input_video instead of args.input_video throughout the rest of the function
    # For example, change: if not os.path.exists(args.input_video):
    # To: if not os.path.exists(input_video):
    
    # And update all other references from args.input_video to input_video
    
    # Check if input file exists
    if not os.path.exists(input_video):
        print(f"Error: Input file '{input_video}' not found.")
        return 1
    
    # Handle video shorter than chunk duration
    if args.method == "ffmpeg" or args.method == "auto":
        duration = get_video_duration_ffmpeg(input_video)
        if duration and duration <= args.duration:
            print(f"Video duration ({duration:.2f}s) is shorter than or equal to chunk duration ({args.duration}s).")
            print("Copying original file to output directory...")
            
            os.makedirs(args.output_dir, exist_ok=True)
            input_path_obj = Path(input_video)
            output_file = os.path.join(args.output_dir, f"chunk_1{input_path_obj.suffix}")
            
            import shutil
            shutil.copy2(input_video, output_file)
            print(f"Created: {output_file}")
            return 0
    
    # Determine method
    method = args.method
    if method == "auto":
        ffmpeg_available = check_ffmpeg_availability()
        moviepy_available = check_moviepy_availability()
        
        if ffmpeg_available:
            method = "ffmpeg"
            print("Auto-selected FFmpeg method (faster)")
        elif moviepy_available:
            method = "moviepy"
            print("Auto-selected MoviePy method")
        else:
            print("Error: Neither FFmpeg nor MoviePy is available.")
            print("Please install MoviePy with: pip install moviepy")
            print("Or download FFmpeg and place it in the ffmpeg/ folder")
            return 1
    
    # Split the video
    success = False
    if method == "ffmpeg":
        if not check_ffmpeg_availability():
            print("Error: FFmpeg not found. Please install FFmpeg or use --method moviepy")
            return 1
        success = split_video_ffmpeg(input_video, args.output_dir, args.duration)
    elif method == "moviepy":
        if not check_moviepy_availability():
            print("Error: MoviePy not found. Please install with: pip install moviepy")
            return 1
        success = split_video_moviepy(input_video, args.output_dir, args.duration)
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
