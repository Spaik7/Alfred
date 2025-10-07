#!/usr/bin/env python3
"""
Mycroft Precise Audio Recording Tool
Records audio samples and organizes them for training
"""

import os
import wave
import argparse
import pyaudio
import numpy as np
from pathlib import Path
from datetime import datetime
import time
from scipy import signal


class AudioRecorder:
    def __init__(self, base_dir="data", sample_rate=16000, channels=1, recording_rate=48000):
        self.base_dir = Path(base_dir)
        self.target_sample_rate = sample_rate  # What we want (16kHz for Precise)
        self.recording_sample_rate = recording_rate  # What device uses (48kHz)
        self.channels = channels
        self.chunk_size = 2048
        self.format = pyaudio.paInt16
        
        # Directory mapping
        self.dirs = {
            'train_wake': self.base_dir / 'train' / 'wake-word',
            'train_not_wake': self.base_dir / 'train' / 'not-wake-word',
            'test_wake': self.base_dir / 'test' / 'wake-word',
            'test_not_wake': self.base_dir / 'test' / 'not-wake-word',
        }
        
        self.audio = pyaudio.PyAudio()
        
        if self.recording_sample_rate != self.target_sample_rate:
            print(f"ℹ️  Recording at {self.recording_sample_rate}Hz, will save as {self.target_sample_rate}Hz")
    
    def setup_directories(self):
        """Create directory structure if it doesn't exist"""
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def list_audio_devices(self):
        """List all available audio input devices"""
        print("\n" + "=" * 60)
        print("Available Audio Input Devices:")
        print("=" * 60)
        
        info = self.audio.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        
        for i in range(num_devices):
            device_info = self.audio.get_device_info_by_host_api_device_index(0, i)
            if device_info.get('maxInputChannels') > 0:
                print(f"[{i}] {device_info.get('name')}")
                print(f"    Sample Rate: {int(device_info.get('defaultSampleRate'))} Hz")
                print(f"    Input Channels: {device_info.get('maxInputChannels')}")
        print()
    
    def get_next_filename(self, directory):
        """Generate next available filename in directory"""
        existing_files = list(directory.glob('sample_*.wav'))
        if not existing_files:
            return directory / 'sample_0001.wav'
        
        numbers = []
        for f in existing_files:
            try:
                num = int(f.stem.split('_')[1])
                numbers.append(num)
            except (IndexError, ValueError):
                continue
        
        next_num = max(numbers) + 1 if numbers else 1
        return directory / f'sample_{next_num:04d}.wav'
    
    def _resample_audio(self, audio_data):
        """Resample audio from recording rate to target rate using proper decimation"""
        if self.recording_sample_rate == self.target_sample_rate:
            return audio_data
            
        # Convert bytes to numpy array
        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
        
        # Normalize to -1.0 to 1.0
        audio_np = audio_np / 32768.0
        
        # Use resample_poly for better quality (it uses polyphase filtering)
        # 48000 -> 16000 is a ratio of 3:1, so downsample by 3
        from scipy.signal import resample_poly
        
        # Calculate the resampling ratio
        gcd = np.gcd(self.recording_sample_rate, self.target_sample_rate)
        up = self.target_sample_rate // gcd
        down = self.recording_sample_rate // gcd
        
        resampled = resample_poly(audio_np, up, down)
        
        # Convert back to int16
        resampled = np.clip(resampled * 32768.0, -32768, 32767).astype(np.int16)
        
        return resampled.tobytes()
    
    def record_audio(self, duration=3, device_index=None):
        """Record audio for specified duration"""
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.recording_sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.chunk_size
        )
        
        print("🎤 Recording...", end='', flush=True)
        frames = []
        
        num_chunks = int(self.recording_sample_rate / self.chunk_size * duration)
        for i in range(num_chunks):
            try:
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                frames.append(data)
                
                # Progress indicator
                if i % 5 == 0:
                    print(".", end='', flush=True)
            except Exception as e:
                print(f"\n⚠ Warning: {e}")
                continue
        
        print(" Done! ✓")
        
        stream.stop_stream()
        stream.close()
        
        audio_data = b''.join(frames)
        
        # Resample if needed
        audio_data = self._resample_audio(audio_data)
        
        return audio_data
    
    def save_audio(self, audio_data, filepath):
        """Save recorded audio to WAV file"""
        with wave.open(str(filepath), 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.target_sample_rate)
            wf.writeframes(audio_data)
    
    def play_audio(self, filepath):
        """Play back recorded audio"""
        with wave.open(str(filepath), 'rb') as wf:
            stream = self.audio.open(
                format=self.audio.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )
            
            print("🔊 Playing back...", end='', flush=True)
            data = wf.readframes(self.chunk_size)
            
            while data:
                stream.write(data)
                data = wf.readframes(self.chunk_size)
            
            print(" Done! ✓")
            
            stream.stop_stream()
            stream.close()
    
    def record_session(self, sample_type, target_count=50, duration=3,
                      test_split=0.15, device_index=None, resume=False, auto_mode=False):
        """
        Interactive recording session

        Args:
            sample_type: 'wake' or 'not-wake'
            target_count: Number of samples to record
            duration: Duration of each recording in seconds
            test_split: Percentage of samples to put in test set
            device_index: Audio device index (None for default)
            resume: Continue from existing recordings
            auto_mode: Automatically record without waiting for Enter (useful for not-wake-word samples)
        """
        self.setup_directories()
        
        # Determine target directories
        if sample_type == 'wake':
            train_dir = self.dirs['train_wake']
            test_dir = self.dirs['test_wake']
            sample_name = "WAKE WORD"
        else:
            train_dir = self.dirs['train_not_wake']
            test_dir = self.dirs['test_not_wake']
            sample_name = "NOT-WAKE-WORD"
        
        # Count existing samples
        existing_train = len(list(train_dir.glob('sample_*.wav')))
        existing_test = len(list(test_dir.glob('sample_*.wav')))
        existing_total = existing_train + existing_test
        
        if existing_total > 0:
            print(f"\n📊 Found {existing_total} existing samples ({existing_train} train, {existing_test} test)")
            if resume:
                print(f"   Resuming from {existing_total} samples...")
                recorded_start = existing_total
            else:
                response = input("   Resume from existing? [Y/n]: ").strip().lower()
                if response == 'n':
                    recorded_start = 0
                    print("   Starting fresh (existing files will be kept but counting from 0)")
                else:
                    recorded_start = existing_total
                    print("   Resuming...")
        else:
            recorded_start = 0
        
        print("\n" + "=" * 60)
        print(f"Recording {sample_name} Samples")
        print("=" * 60)
        print(f"Target: {target_count} samples")
        print(f"Currently have: {existing_total} samples")
        print(f"Need to record: {max(0, target_count - existing_total)} more")
        print(f"Duration: {duration} seconds per sample")
        print(f"Test split: {int(test_split * 100)}%")
        print(f"Train dir: {train_dir}")
        print(f"Test dir: {test_dir}")
        print("\nControls:")
        if auto_mode:
            print("  AUTO MODE: Recording automatically with 3-second countdown")
            print("  Press Ctrl+C to pause/quit")
        else:
            print("  [Enter]  - Start recording")
            print("  's'      - Skip (don't save)")
            print("  'p'      - Play back last recording")
            print("  'q'      - Quit session")
        print("=" * 60)
        
        recorded = recorded_start
        test_samples = int(target_count * test_split)
        train_samples = target_count - test_samples
        
        last_filepath = None

        try:
            while recorded < target_count:
                # Determine if this should be train or test
                if recorded < train_samples:
                    target_dir = train_dir
                    split_type = "TRAIN"
                else:
                    target_dir = test_dir
                    split_type = "TEST"

                print(f"\n[{recorded + 1}/{target_count}] ({split_type}) ", end='')

                if sample_type == 'wake':
                    print("Say the wake word")
                else:
                    print("Say anything else or make noise")

                # Auto mode or interactive mode
                if auto_mode:
                    # Countdown
                    print("Recording in: ", end='', flush=True)
                    for i in range(3, 0, -1):
                        print(f"{i}...", end='', flush=True)
                        time.sleep(1)
                    print()
                else:
                    command = input("Ready? [Enter/s/p/q]: ").strip().lower()

                    if command == 'q':
                        print(f"\n✓ Session paused at {recorded}/{target_count} samples")
                        print(f"   Run with --resume to continue later")
                        break
                    elif command == 's':
                        print("⊘ Skipped")
                        continue
                    elif command == 'p':
                        if last_filepath and last_filepath.exists():
                            self.play_audio(last_filepath)
                        else:
                            print("⚠ No recording to play back")
                        continue

                    # Countdown
                    print("Recording in: ", end='', flush=True)
                    for i in range(3, 0, -1):
                        print(f"{i}...", end='', flush=True)
                        time.sleep(1)
                    print()

                # Record
                audio_data = self.record_audio(duration, device_index)

                # Save
                filepath = self.get_next_filename(target_dir)
                self.save_audio(audio_data, filepath)
                last_filepath = filepath

                print(f"💾 Saved: {filepath.name}")

                # Ask to replay (only in interactive mode)
                if not auto_mode:
                    replay = input("Play back? [y/N]: ").strip().lower()
                    if replay == 'y':
                        self.play_audio(filepath)
                        keep = input("Keep this recording? [Y/n]: ").strip().lower()
                        if keep == 'n':
                            filepath.unlink()
                            print("🗑️  Deleted")
                            continue

                recorded += 1

                # In auto mode, add a small delay between recordings
                if auto_mode and recorded < target_count:
                    time.sleep(0.5)

        except KeyboardInterrupt:
            print(f"\n\n⚠ Interrupted by user")
            print(f"✓ Session paused at {recorded}/{target_count} samples")
            print(f"   Run with --resume to continue later")
        
        print("\n" + "=" * 60)
        if recorded >= target_count:
            print(f"✓ Recording session completed!")
        else:
            print(f"✓ Session saved at {recorded}/{target_count}")
        print(f"Total recorded: {recorded} samples")
        print("=" * 60)
    
    def guided_recording(self, wake_word_phrase, wake_count=150, device_index=None, resume=False, auto_not_wake=False):
        """Guided recording session for complete dataset"""
        # Calculate not-wake count (2x wake count recommended)
        not_wake_count = int(wake_count * 2)

        self.setup_directories()

        print("\n" + "=" * 60)
        print("Mycroft Precise - Guided Recording Session")
        print("=" * 60)
        print(f"Wake Word: '{wake_word_phrase}'")
        print(f"\nTarget counts:")
        print(f"  1. Wake word samples: {wake_count}")
        print(f"  2. Not-wake-word samples: {not_wake_count} (2x wake count)")
        print("=" * 60)

        # Check existing wake word samples
        wake_train = len(list(self.dirs['train_wake'].glob('sample_*.wav')))
        wake_test = len(list(self.dirs['test_wake'].glob('sample_*.wav')))
        wake_total = wake_train + wake_test

        # Step 1: Wake word samples (skip if already complete)
        if wake_total >= wake_count:
            print(f"\n📍 STEP 1: Wake Word Samples - ✓ COMPLETE")
            print(f"   Found {wake_total} existing samples ({wake_train} train, {wake_test} test)")
            print(f"   Skipping wake word recording...")
        else:
            print(f"\n📍 STEP 1: Wake Word Samples")
            if wake_total > 0:
                print(f"   Found {wake_total} existing samples, need {wake_count - wake_total} more")
            print(f"Say '{wake_word_phrase}' clearly each time")
            input("Press Enter to start...")

            self.record_session(
                sample_type='wake',
                target_count=wake_count,
                duration=3,
                test_split=0.15,
                device_index=device_index,
                resume=resume,
                auto_mode=False  # Wake word always interactive
            )

        # Check existing not-wake-word samples
        not_wake_train = len(list(self.dirs['train_not_wake'].glob('sample_*.wav')))
        not_wake_test = len(list(self.dirs['test_not_wake'].glob('sample_*.wav')))
        not_wake_total = not_wake_train + not_wake_test

        # Step 2: Not-wake-word samples (skip if already complete)
        if not_wake_total >= not_wake_count:
            print(f"\n📍 STEP 2: Not-Wake-Word Samples - ✓ COMPLETE")
            print(f"   Found {not_wake_total} existing samples ({not_wake_train} train, {not_wake_test} test)")
            print(f"   Skipping not-wake-word recording...")
        else:
            print(f"\n📍 STEP 2: Not-Wake-Word Samples")
            if not_wake_total > 0:
                print(f"   Found {not_wake_total} existing samples, need {not_wake_count - not_wake_total} more")
            print("Say anything EXCEPT the wake word:")
            print("  - Random phrases")
            print("  - Similar sounding words")
            print("  - Background noise")
            print("  - Music, TV sounds, etc.")

            if auto_not_wake:
                print("\n🤖 AUTO MODE ENABLED: Recordings will start automatically")
                print("   Just talk, play music, or make noise continuously")
                print("   Press Ctrl+C to pause/stop")

            input("Press Enter to start...")

            self.record_session(
                sample_type='not-wake',
                target_count=not_wake_count,
                duration=3,
                test_split=0.15,
                device_index=device_index,
                resume=resume,
                auto_mode=auto_not_wake  # Use auto mode if enabled
            )
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print summary of recorded samples"""
        print("\n" + "=" * 60)
        print("Recording Summary")
        print("=" * 60)
        
        for name, path in self.dirs.items():
            count = len(list(path.glob('*.wav')))
            print(f"{name:20s}: {count:4d} samples")
        
        print("\n✓ Ready for training!")
        print(f"Run: python precise_trainer.py \"your wake word\"")
        print("=" * 60)
    
    def cleanup(self):
        """Cleanup audio resources"""
        self.audio.terminate()


def main():
    parser = argparse.ArgumentParser(
        description='Record audio samples for Mycroft Precise training'
    )
    parser.add_argument(
        '--wake-word',
        help='Wake word phrase (for guided mode)'
    )
    parser.add_argument(
        '--mode',
        choices=['wake', 'not-wake', 'guided'],
        default='guided',
        help='Recording mode (default: guided)'
    )
    parser.add_argument(
        '--count', '-c',
        type=int,
        default=150,
        help='Number of wake word samples to record (default: 150). In guided mode, not-wake samples will be 2x this.'
    )
    parser.add_argument(
        '--duration', '-d',
        type=int,
        default=3,
        help='Duration of each recording in seconds (default: 3)'
    )
    parser.add_argument(
        '--device', '-i',
        type=int,
        default=None,
        help='Audio input device index (use --list-devices to see options)'
    )
    parser.add_argument(
        '--list-devices',
        action='store_true',
        help='List available audio devices and exit'
    )
    parser.add_argument(
        '--data-dir',
        default='data',
        help='Base directory for data (default: data)'
    )
    parser.add_argument(
        '--resume', '-r',
        action='store_true',
        help='Resume from existing recordings'
    )
    parser.add_argument(
        '--auto',
        action='store_true',
        help='Auto-record mode for not-wake-word samples (no Enter key required)'
    )

    args = parser.parse_args()
    
    recorder = AudioRecorder(base_dir=args.data_dir, recording_rate=48000)
    
    try:
        if args.list_devices:
            recorder.list_audio_devices()
            return
        
        if args.mode == 'guided':
            if not args.wake_word:
                args.wake_word = input("Enter your wake word phrase: ").strip()
            recorder.guided_recording(
                args.wake_word,
                wake_count=args.count,
                device_index=args.device,
                resume=args.resume,
                auto_not_wake=args.auto
            )
        elif args.mode == 'wake':
            recorder.record_session(
                sample_type='wake',
                target_count=args.count,
                duration=args.duration,
                device_index=args.device,
                resume=args.resume,
                auto_mode=False  # Wake word never uses auto mode
            )
        elif args.mode == 'not-wake':
            recorder.record_session(
                sample_type='not-wake',
                target_count=args.count,
                duration=args.duration,
                device_index=args.device,
                resume=args.resume,
                auto_mode=args.auto  # Use auto mode if --auto flag is set
            )
    
    finally:
        recorder.cleanup()


if __name__ == '__main__':
    main()