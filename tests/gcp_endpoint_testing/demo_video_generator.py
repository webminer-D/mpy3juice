#!/usr/bin/env python3
"""
Demonstration script for the VideoFileGenerator utility.
Shows how to create various types of test video files.
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Add the parent directory to the path to import the video generator
sys.path.append(str(Path(__file__).parent.parent))
from utils.video_generator import VideoFileGenerator


def main():
    """Demonstrate VideoFileGenerator capabilities."""
    print("VideoFileGenerator Demonstration")
    print("=" * 40)
    
    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    generator = VideoFileGenerator(temp_dir)
    
    try:
        print(f"Working in temporary directory: {temp_dir}")
        print()
        
        # 1. Generate valid video files in all formats
        print("1. Generating valid video files in all supported formats:")
        for format in VideoFileGenerator.SUPPORTED_FORMATS:
            # Video with audio
            video_data = generator.generate_video_with_audio(format=format, duration=2)
            file_path = generator.save_video_file(video_data, f"demo_with_audio.{format}")
            validation = generator.validate_generated_file(file_path, format)
            
            print(f"   {format.upper()} (with audio): {validation['size_mb']:.2f} MB - "
                  f"{'✓' if validation['is_valid'] else '✗'} "
                  f"({validation['format_detected']}) "
                  f"Audio: {'✓' if validation['has_audio_track'] else '✗'}")
            
            # Video without audio
            video_no_audio = generator.generate_video_without_audio(format=format, duration=2)
            file_path_no_audio = generator.save_video_file(video_no_audio, f"demo_no_audio.{format}")
            validation_no_audio = generator.validate_generated_file(file_path_no_audio, format)
            
            print(f"   {format.upper()} (no audio): {validation_no_audio['size_mb']:.2f} MB - "
                  f"{'✓' if validation_no_audio['is_valid'] else '✗'} "
                  f"({validation_no_audio['format_detected']}) "
                  f"Audio: {'✓' if validation_no_audio['has_audio_track'] else '✗'}")
        
        print()
        
        # 2. Generate videos with custom properties
        print("2. Generating videos with custom properties:")
        
        # High resolution video
        hd_video = generator.generate_valid_video(
            format='mp4', 
            duration=3, 
            width=1920, 
            height=1080,
            fps=30,
            has_audio=True
        )
        hd_path = generator.save_video_file(hd_video, "demo_hd.mp4")
        hd_validation = generator.validate_generated_file(hd_path, 'mp4')
        print(f"   HD Video (1920x1080): {hd_validation['size_mb']:.2f} MB - "
              f"{'✓' if hd_validation['is_valid'] else '✗'}")
        
        # High FPS video
        high_fps_video = generator.generate_valid_video(
            format='mp4',
            duration=2,
            fps=60,
            has_audio=True
        )
        high_fps_path = generator.save_video_file(high_fps_video, "demo_high_fps.mp4")
        high_fps_validation = generator.validate_generated_file(high_fps_path, 'mp4')
        print(f"   High FPS (60fps): {high_fps_validation['size_mb']:.2f} MB - "
              f"{'✓' if high_fps_validation['is_valid'] else '✗'}")
        
        # Small resolution video
        small_video = generator.generate_valid_video(
            format='mp4',
            duration=3,
            width=320,
            height=240,
            has_audio=False
        )
        small_path = generator.save_video_file(small_video, "demo_small.mp4")
        small_validation = generator.validate_generated_file(small_path, 'mp4')
        print(f"   Small Video (320x240): {small_validation['size_mb']:.2f} MB - "
              f"{'✓' if small_validation['is_valid'] else '✗'}")
        
        print()
        
        # 3. Generate edge case videos
        print("3. Generating edge case video files:")
        edge_cases = generator.generate_edge_case_videos()
        for case_name, case_data in edge_cases:
            case_path = generator.save_video_file(case_data, f"demo_{case_name}.mp4")
            case_validation = generator.validate_generated_file(case_path)
            print(f"   {case_name}: {case_validation['size_mb']:.3f} MB - "
                  f"{'✓' if case_validation['is_valid'] else '✗'} "
                  f"Audio: {'✓' if case_validation['has_audio_track'] else '✗' if case_validation['has_audio_track'] is not None else 'N/A'}")
        
        print()
        
        # 4. Generate invalid and corrupted files
        print("4. Generating invalid and corrupted files:")
        
        # Invalid file
        invalid_data = generator.generate_invalid_video()
        invalid_path = generator.save_video_file(invalid_data, "demo_invalid.bin")
        invalid_validation = generator.validate_generated_file(invalid_path)
        print(f"   Invalid file: {invalid_validation['size_mb']:.3f} MB - "
              f"{'✓' if invalid_validation['is_valid'] else '✗'} "
              f"({invalid_validation['format_detected']})")
        
        # Empty file
        empty_data = generator.generate_empty_video()
        empty_path = generator.save_video_file(empty_data, "demo_empty.mp4")
        empty_validation = generator.validate_generated_file(empty_path)
        print(f"   Empty file: {empty_validation['size_mb']:.3f} MB - "
              f"{'✓' if empty_validation['is_valid'] else '✗'}")
        
        # Corrupted files
        for format in ['mp4', 'avi', 'mkv']:
            corrupted_data = generator.generate_corrupted_video(format=format)
            corrupted_path = generator.save_video_file(corrupted_data, f"demo_corrupted.{format}")
            corrupted_validation = generator.validate_generated_file(corrupted_path, format)
            print(f"   Corrupted {format.upper()}: {corrupted_validation['size_mb']:.3f} MB - "
                  f"{'✓' if corrupted_validation['is_valid'] else '✗'}")
        
        print()
        
        # 5. Create comprehensive test set
        print("5. Creating comprehensive test video set:")
        test_files = generator.create_test_video_set()
        print(f"   Created {len(test_files)} test files:")
        
        # Group by category
        categories = {}
        for file_type, file_path in test_files.items():
            category = file_type.split('_')[0]
            if category not in categories:
                categories[category] = []
            categories[category].append((file_type, file_path))
        
        for category, files in categories.items():
            print(f"     {category.capitalize()}: {len(files)} files")
        
        print()
        
        # 6. Show total files created
        all_files = list(Path(temp_dir).glob("*"))
        total_size = sum(f.stat().st_size for f in all_files if f.is_file())
        print(f"Total files created: {len(all_files)}")
        print(f"Total size: {total_size / (1024 * 1024):.2f} MB")
        
        print()
        print("Demo completed successfully!")
        print(f"Files are available in: {temp_dir}")
        print("Note: Files will be cleaned up when the script exits.")
        
    except Exception as e:
        print(f"Error during demo: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up
        print("\nCleaning up temporary files...")
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("Cleanup completed.")


if __name__ == "__main__":
    main()