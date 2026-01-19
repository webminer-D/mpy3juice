#!/usr/bin/env python3
"""
Demonstration script for the AudioFileGenerator utility.
Shows how to create various types of test audio files.
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Add the parent directory to the path to import the audio generator
sys.path.append(str(Path(__file__).parent.parent))
from utils.audio_generator import AudioFileGenerator


def main():
    """Demonstrate AudioFileGenerator capabilities."""
    print("AudioFileGenerator Demonstration")
    print("=" * 40)
    
    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    generator = AudioFileGenerator(temp_dir)
    
    try:
        print(f"Working in temporary directory: {temp_dir}")
        print()
        
        # 1. Generate valid audio files in all formats
        print("1. Generating valid audio files in all supported formats:")
        for format in AudioFileGenerator.SUPPORTED_FORMATS:
            audio_data = generator.generate_valid_audio(format=format, duration=2)
            file_path = generator.save_audio_file(audio_data, f"demo_valid.{format}")
            validation = generator.validate_generated_file(file_path, format)
            
            print(f"   {format.upper()}: {validation['size_mb']:.2f} MB - "
                  f"{'✓' if validation['is_valid'] else '✗'} "
                  f"({validation['format_detected']})")
        
        print()
        
        # 2. Generate files with custom metadata
        print("2. Generating audio with custom metadata:")
        custom_metadata = {
            'title': 'Demo Song',
            'artist': 'AudioFileGenerator',
            'album': 'Test Suite Demo',
            'year': '2024',
            'genre': 'Electronic Test'
        }
        
        metadata_audio = generator.generate_valid_audio(
            format='wav', 
            duration=3, 
            metadata=custom_metadata
        )
        metadata_path = generator.save_audio_file(metadata_audio, "demo_with_metadata.wav")
        metadata_validation = generator.validate_generated_file(metadata_path, 'wav')
        print(f"   WAV with metadata: {metadata_validation['size_mb']:.2f} MB - "
              f"{'✓' if metadata_validation['is_valid'] else '✗'}")
        
        print()
        
        # 3. Generate edge case files
        print("3. Generating edge case audio files:")
        edge_cases = generator.generate_edge_case_audio()
        for case_name, case_data in edge_cases:
            case_path = generator.save_audio_file(case_data, f"demo_{case_name}.wav")
            case_validation = generator.validate_generated_file(case_path)
            print(f"   {case_name}: {case_validation['size_mb']:.3f} MB - "
                  f"{'✓' if case_validation['is_valid'] else '✗'}")
        
        print()
        
        # 4. Generate invalid/corrupted files
        print("4. Generating invalid and corrupted files:")
        
        # Invalid file
        invalid_data = generator.generate_invalid_audio()
        invalid_path = generator.save_audio_file(invalid_data, "demo_invalid.bin")
        invalid_validation = generator.validate_generated_file(invalid_path)
        print(f"   Invalid file: {invalid_validation['size_mb']:.3f} MB - "
              f"{'✓' if invalid_validation['is_valid'] else '✗'} "
              f"({invalid_validation['format_detected']})")
        
        # Empty file
        empty_data = generator.generate_empty_audio()
        empty_path = generator.save_audio_file(empty_data, "demo_empty.wav")
        empty_validation = generator.validate_generated_file(empty_path)
        print(f"   Empty file: {empty_validation['size_mb']:.3f} MB - "
              f"{'✓' if empty_validation['is_valid'] else '✗'}")
        
        # Corrupted files
        for format in ['wav', 'mp3']:
            corrupted_data = generator.generate_corrupted_audio(format=format)
            corrupted_path = generator.save_audio_file(corrupted_data, f"demo_corrupted.{format}")
            corrupted_validation = generator.validate_generated_file(corrupted_path, format)
            print(f"   Corrupted {format.upper()}: {corrupted_validation['size_mb']:.3f} MB - "
                  f"{'✓' if corrupted_validation['is_valid'] else '✗'}")
        
        print()
        
        # 5. Generate malformed header files
        print("5. Generating files with malformed headers:")
        malformed_cases = generator.generate_malformed_headers('wav')
        for malformed_name, malformed_data in malformed_cases:
            malformed_path = generator.save_audio_file(malformed_data, f"demo_{malformed_name}.wav")
            malformed_validation = generator.validate_generated_file(malformed_path)
            print(f"   {malformed_name}: {malformed_validation['size_mb']:.3f} MB - "
                  f"{'✓' if malformed_validation['is_valid'] else '✗'}")
        
        print()
        
        # 6. Create comprehensive test set
        print("6. Creating comprehensive test audio set:")
        test_files = generator.create_test_audio_set()
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
        
        # 7. Show total files created
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
        
    finally:
        # Clean up
        print("\nCleaning up temporary files...")
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("Cleanup completed.")


if __name__ == "__main__":
    main()