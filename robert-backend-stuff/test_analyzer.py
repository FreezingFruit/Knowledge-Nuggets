import cv2
import numpy as np
from transformers import pipeline
import torch
from moviepy import VideoFileClip
import os
import yt_dlp
from PIL import Image
from vosk import Model, KaldiRecognizer
import wave
import json
from youtube_transcript_api import YouTubeTranscriptApi
import re
import pydub
import glob
from torch.utils.data import Dataset, DataLoader
from typing import List, Dict

def collate_frames(batch):
    """Custom collate function for PIL images"""
    return batch

class FrameDataset(Dataset):
    """Dataset for batch processing video frames"""
    def __init__(self, frames: List[np.ndarray]):
        self.frames = frames
        
    def __len__(self):
        return len(self.frames)
    
    def __getitem__(self, idx):
        frame = self.frames[idx]
        # Convert frame to RGB for the model
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Convert to PIL Image
        pil_image = Image.fromarray(frame_rgb)
        return pil_image

class VideoAnalysisBot:
    def __init__(self):
        # Check for GPU availability
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Using device: {self.device}")

        # Initialize models and pipelines with GPU support
        self.scene_detector = cv2.createBackgroundSubtractorMOG2()
        try:
            # Initialize image analyzer with GPU support
            self.image_analyzer = pipeline(
                "image-classification",
                model="microsoft/resnet-50",
                device=0 if torch.cuda.is_available() else -1  # Use GPU if available
            )
        except OSError:
            # Fallback to smaller model with GPU support
            self.image_analyzer = pipeline(
                "image-classification",
                model="google/vit-base-patch16-224",
                device=0 if torch.cuda.is_available() else -1
            )
        
        # Initialize CUDA-based video processing if available
        if torch.cuda.is_available():
            torch.backends.cudnn.benchmark = True  # Enable CUDNN benchmarking for faster processing
        
        # Initialize Vosk model with absolute path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, "models", "vosk-model-en-us-0.22")
        
        print(f"Loading Vosk model from: {model_path}")
        print(f"Model directory contents: {os.listdir(model_path)}")
        
        try:
            self.vosk_model = Model(model_path)
            print("Successfully loaded Vosk model!")
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            raise

        # Initialize video analysis attributes
        self.scenes = []
        self.frames = []
        self.transcription = ""
        self.youtube_captions = ""

    def preprocess_audio(self, audio_path):
        """Preprocess audio for better transcription"""
        processed_path = None
        try:
            # Generate unique filename using timestamp and process ID
            import time
            timestamp = int(time.time())
            processed_path = f"temp_processed_audio_{os.getpid()}_{timestamp}.wav"
            
            # Load audio
            audio = pydub.AudioSegment.from_wav(audio_path)
            
            # Convert to mono if stereo
            if audio.channels > 1:
                audio = audio.set_channels(1)
            
            # Normalize volume
            audio = pydub.effects.normalize(audio)
            
            # Set optimal sample rate for model
            audio = audio.set_frame_rate(16000)
            
            # Export processed audio
            audio.export(processed_path, format="wav", 
                        parameters=["-ac", "1", "-ar", "16000"])
            return processed_path
                
        except Exception as e:
            print(f"Error preprocessing audio: {str(e)}")
            if processed_path and os.path.exists(processed_path):
                try:
                    os.remove(processed_path)
                except:
                    pass
            return audio_path
                        
    def get_youtube_captions(self, url):
        """Get captions from YouTube video"""
        try:
            # Extract video ID from URL
            video_id = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
            if not video_id:
                return "[Could not extract video ID]"
            video_id = video_id.group(1)

            # Get transcript
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                transcript = transcript_list.find_transcript(['en'])
                captions = transcript.fetch()
                return ' '.join([entry['text'] for entry in captions])
            except:
                try:
                    # Try auto-generated captions
                    transcript = transcript_list.find_generated_transcript(['en'])
                    captions = transcript.fetch()
                    return ' '.join([entry['text'] for entry in captions])
                except Exception as e:
                    print(f"Error getting captions: {str(e)}")
                    return "[No captions available]"
        except Exception as e:
            print(f"Error getting YouTube captions: {str(e)}")
            return "[Error retrieving captions]"

    def download_video(self, url):
        """Download video from YouTube"""
        try:
            ydl_opts = {
                'format': 'best[ext=mp4]',
                'outtmpl': 'temp_youtube_video.%(ext)s',
                'quiet': False,
                'no_warnings': False
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            print("Video download completed successfully!")
            return "temp_youtube_video.mp4"
        except Exception as e:
            print(f"Error downloading video: {str(e)}")
            raise

    def frame_generator(self, video_path, chunk_size=32):
        """Generate frames in chunks to reduce memory usage"""
        video = cv2.VideoCapture(video_path)
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        current_chunk = []
        frame_count = 0
        
        try:
            while True:
                ret, frame = video.read()
                if not ret:
                    if current_chunk:  # Yield remaining frames
                        yield current_chunk, frame_count - len(current_chunk), frame_count
                    break
                    
                current_chunk.append(frame)
                frame_count += 1
                
                if frame_count % 100 == 0:
                    print(f"Reading frame {frame_count}/{total_frames}")
                
                if len(current_chunk) >= chunk_size:
                    yield current_chunk, frame_count - chunk_size, frame_count
                    current_chunk = []
        finally:
            video.release()

    def process_video(self, video_path, is_youtube_url=False):
            """Process video with memory-efficient streaming"""
            video_clip = None
            temp_audio_path = None
            chunk_size = 32  # Process 32 frames at a time
            
            try:
                import time
                
                if is_youtube_url:
                    print(f"Processing YouTube video: {video_path}")
                    self.youtube_captions = self.get_youtube_captions(video_path)
                    video_path = self.download_video(video_path)
                else:
                    print(f"Processing local video: {video_path}")
                    if not os.path.exists(video_path):
                        raise FileNotFoundError(f"Video file not found: {video_path}")
                    self.youtube_captions = ""
                
                print("Initializing video processing...")
                self.scenes = [0]  # Start with first frame
                self.frames = []  # Initialize frames list
                prev_scene = None
                total_frames = 0
                
                # Process frames in chunks
                print("Processing frames in chunks...")
                for frames_chunk, start_idx, end_idx in self.frame_generator(video_path, chunk_size):
                    # Create dataset and dataloader for current chunk
                    dataset = FrameDataset(frames_chunk)
                    dataloader = DataLoader(
                        dataset,
                        batch_size=len(frames_chunk),
                        num_workers=0,
                        pin_memory=True if hasattr(self, 'gpu_available') and self.gpu_available else False,
                        collate_fn=collate_frames
                    )
                    
                    # Process chunk
                    for batch in dataloader:
                        # Process the frames in the batch with the scene detector
                        for i, frame_pil in enumerate(batch):
                            # Convert PIL Image back to numpy array for scene detection
                            frame_np = np.array(frame_pil)
                            frame_np = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)
                            
                            # Store frame for later analysis
                            self.frames.append(frame_np)
                            
                            # Apply scene detection
                            fgmask = self.scene_detector.apply(frame_np)
                            scene_score = np.mean(fgmask)
                            
                            # Scene detection logic
                            if prev_scene is None or (abs(scene_score - prev_scene) > 50 and 
                                (len(self.scenes) == 1 or (start_idx + i) - self.scenes[-1] > 30)):
                                self.scenes.append(start_idx + i)
                            
                            prev_scene = scene_score
                    
                    total_frames = end_idx
                    
                    # Free up memory for the chunk
                    del frames_chunk
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                
                # Make sure we include the last frame
                if self.scenes[-1] != total_frames - 1:
                    self.scenes.append(total_frames - 1)
                    
                print(f"Detected {len(self.scenes)} scenes")
                print(f"Stored {len(self.frames)} frames for analysis")
                
                # Extract and transcribe audio
                print("Extracting audio...")
                try:
                    timestamp = int(time.time())
                    temp_audio_path = f"temp_audio_{os.getpid()}_{timestamp}.wav"
                    
                    video_clip = VideoFileClip(video_path)
                    if video_clip.audio is not None:
                        video_clip.audio.write_audiofile(temp_audio_path)
                        video_clip.close()
                        video_clip = None
                        
                        print("Transcribing audio...")
                        self.transcription = self.transcribe_audio(temp_audio_path)
                        print("Transcription completed!")
                    else:
                        print("No audio stream found in video")
                        self.transcription = "[No audio found]"
                except Exception as e:
                    print(f"Error processing audio: {str(e)}")
                    self.transcription = "[Audio processing error]"
                    
            except Exception as e:
                print(f"Error processing video: {str(e)}")
                raise
                
            finally:
                # Cleanup
                if video_clip is not None:
                    video_clip.close()
                
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                # Clean up temporary files
                time.sleep(0.1)
                
                if temp_audio_path and os.path.exists(temp_audio_path):
                    try:
                        os.remove(temp_audio_path)
                    except Exception as e:
                        print(f"Warning: Could not remove temporary audio file: {str(e)}")
                        with open("cleanup_files.txt", "a") as f:
                            f.write(f"{temp_audio_path}\n")
                
                if is_youtube_url and os.path.exists(video_path):
                    try:
                        os.remove(video_path)
                    except Exception as e:
                        print(f"Warning: Could not remove temporary video file: {str(e)}")
                        with open("cleanup_files.txt", "a") as f:
                            f.write(f"{video_path}\n")

    def transcribe_audio(self, audio_path):
        """Transcribe audio using Vosk"""
        processed_path = None
        wf = None
        try:
            # Preprocess audio
            processed_path = self.preprocess_audio(audio_path)
            
            # Open processed audio
            wf = wave.open(processed_path, "rb")
            
            # Create recognizer
            rec = KaldiRecognizer(self.vosk_model, wf.getframerate())
            rec.SetWords(True)
            rec.SetPartialWords(True)
            
            # Process in chunks
            chunk_size = 16000  # 1 second of audio at 16kHz
            transcription = []
            
            while True:
                data = wf.readframes(chunk_size)
                if len(data) == 0:
                    break
                    
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    if 'text' in result and result['text'].strip():
                        transcription.append(result['text'])
            
            # Get final result
            final = json.loads(rec.FinalResult())
            if 'text' in final and final['text'].strip():
                transcription.append(final['text'])
                
            # Join all transcribed pieces with proper spacing
            return ' '.join(text for text in transcription if text.strip())
            
        except Exception as e:
            print(f"Error in transcription: {str(e)}")
            return "[Transcription error]"
            
        finally:
            # Clean up resources in reverse order of creation
            if wf:
                wf.close()
            import time
            # Add a small delay before file removal
            time.sleep(0.1)
            
            # Remove processed file if it exists and is different from input
            if processed_path and processed_path != audio_path and os.path.exists(processed_path):
                try:
                    os.remove(processed_path)
                except Exception as e:
                    print(f"Warning: Could not remove temporary file {processed_path}: {str(e)}")
                    # If we can't remove it now, mark it for later cleanup
                    with open("cleanup_files.txt", "a") as f:
                        f.write(f"{processed_path}\n")
    
    def analyze_scenes(self):
        """Analyze scenes with batched processing for GPU efficiency"""
        print("Analyzing scenes with improved detection...")
        scene_analyses = []
        
        if len(self.scenes) < 2:
            print("Not enough scenes detected for analysis")
            return []
        
        try:
            print(f"Processing {len(self.scenes)-1} scenes...")
            
            # Analyze middle frame of each scene
            for i in range(len(self.scenes)-1):
                try:
                    start_idx = self.scenes[i]
                    end_idx = self.scenes[i+1]
                    
                    # Safety check for index bounds
                    if start_idx >= len(self.frames) or end_idx >= len(self.frames):
                        continue
                        
                    # Get middle frame of scene
                    mid_idx = start_idx + (end_idx - start_idx) // 2
                    frame = self.frames[mid_idx]
                    
                    # Convert frame to RGB for the model
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Convert to PIL Image
                    pil_image = Image.fromarray(frame_rgb)
                    
                    # Get visual analysis
                    visual_analysis = self.image_analyzer(pil_image)
                    if visual_analysis and len(visual_analysis) > 0:
                        analysis = visual_analysis[0]
                        
                        scene_analyses.append({
                            'start_frame': start_idx,
                            'end_frame': end_idx,
                            'visual_content': analysis['label'],
                            'confidence': analysis['score']
                        })
                        
                        print(f"Scene {i+1}/{len(self.scenes)-1} analyzed: {analysis['label']} ({analysis['score']:.2f})")
                    
                except Exception as e:
                    print(f"Error analyzing scene {i}: {str(e)}")
                    continue
                    
            print(f"Successfully analyzed {len(scene_analyses)} scenes")
            return scene_analyses
                
        except Exception as e:
            print(f"Error in scene analysis: {str(e)}")
            return []

    def generate_summary(self):
        """Generate a complete summary of the video"""
        print("\nGenerating video summary...")
        scene_analyses = self.analyze_scenes()
        
        if not scene_analyses:
            print("Warning: No scene analyses available")
            scene_analyses = []
        
        # Count scene frequencies
        scene_counts = {}
        for scene in scene_analyses:
            content = scene['visual_content']
            if content in scene_counts:
                scene_counts[content] += 1
            else:
                scene_counts[content] = 1
        
        # Sort scenes by frequency
        sorted_scenes = sorted(scene_counts.items(), key=lambda x: x[1], reverse=True)
        
        summary = {
            'scene_analyses': scene_analyses,
            'scene_frequency': dict(sorted_scenes),
            'transcription': self.transcription if hasattr(self, 'transcription') else "",
            'youtube_captions': self.youtube_captions if hasattr(self, 'youtube_captions') else ""
        }
        
        # Print complete report
        print("\n" + "="*50)
        print("COMPLETE VIDEO ANALYSIS REPORT")
        print("="*50)
        
        # Print YouTube captions first (if available)
        if summary['youtube_captions'] and summary['youtube_captions'] not in ["[No captions available]", "[Error retrieving captions]"]:
            print("\nYOUTUBE CAPTIONS")
            print("-"*30)
            print(summary['youtube_captions'])
            
        # Print transcription
        if summary['transcription'] and summary['transcription'] not in ["[No audio found]", "[Audio processing error]", "[Transcription error]"]:
            print("\nAUDIO TRANSCRIPTION")
            print("-"*30)
            print(summary['transcription'])
        
        # Print visual analysis statistics
        print("\nVISUAL CONTENT ANALYSIS")
        print("-"*30)
        if sorted_scenes:
            print("\nTop detected elements:")
            for content, count in list(summary['scene_frequency'].items())[:10]:  # Top 10 items
                print(f"• {content}: {count} occurrences")
        else:
            print("No visual elements detected")
                
        # Print scene timeline
        print("\nSCENE TIMELINE")
        print("-"*30)
        if scene_analyses:
            for scene in scene_analyses:
                start_time = scene['start_frame'] / 30  # Assuming 30 fps
                end_time = scene['end_frame'] / 30
                time_range = f"{start_time:.1f}s - {end_time:.1f}s"
                print(f"[{time_range}] {scene['visual_content']} (Confidence: {scene['confidence']:.2f})")
        else:
            print("No scene timeline available")
        
        return summary

    def cleanup_temp_files(self):
        """Clean up any temporary files"""
        # Clean up current temp files
        temp_patterns = [
            "temp_audio_*.wav",
            "temp_processed_audio_*.wav",
            "temp_youtube_video.mp4"
        ]
        
        for pattern in temp_patterns:
            for file in glob.glob(pattern):
                try:
                    if os.path.exists(file):
                        os.remove(file)
                except Exception as e:
                    print(f"Warning: Could not remove temporary file {file}: {str(e)}")
        
        # Clean up any files marked for cleanup
        if os.path.exists("cleanup_files.txt"):
            try:
                with open("cleanup_files.txt", "r") as f:
                    files_to_clean = f.readlines()
                
                for file in files_to_clean:
                    file = file.strip()
                    if os.path.exists(file):
                        try:
                            os.remove(file)
                        except Exception as e:
                            print(f"Warning: Could not remove marked file {file}: {str(e)}")
                
                os.remove("cleanup_files.txt")
            except Exception as e:
                print(f"Warning: Error during cleanup: {str(e)}")

# Example usage
if __name__ == "__main__":
    try:
        bot = VideoAnalysisBot()
        video_url = "https://www.youtube.com/watch?v=-moW9jvvMr4"
        
        print("Starting video analysis...")
        bot.process_video(video_url, is_youtube_url=True)
        result = bot.generate_summary()
        
        # Print complete report
        print("\n" + "="*50)
        print("COMPLETE VIDEO ANALYSIS REPORT")
        print("="*50)
        
        # Print YouTube captions first (if available)
        if result['youtube_captions'] and result['youtube_captions'] not in ["[No captions available]", "[Error retrieving captions]"]:
            print("\nYOUTUBE CAPTIONS")
            print("-"*30)
            print(result['youtube_captions'])
            
        # Print Vosk transcription
        if result['transcription'] and result['transcription'] not in ["[No audio found]", "[Audio processing error]", "[Transcription error]"]:
            print("\nVOSK AUDIO TRANSCRIPTION")
            print("-"*30)
            print(result['transcription'])
        
        # Print visual analysis statistics
        print("\nVISUAL CONTENT ANALYSIS")
        print("-"*30)
        print("\nTop detected elements:")
        for content, count in list(result['scene_frequency'].items())[:10]:  # Top 10 items
            print(f"• {content}: {count} occurrences")
            
        # Print scene timeline
        print("\nSCENE TIMELINE")
        print("-"*30)
        for scene in result['scene_analyses']:
            start_time = scene['start_frame'] / 30  # Assuming 30 fps
            end_time = scene['end_frame'] / 30
            time_range = f"{start_time:.1f}s - {end_time:.1f}s"
            print(f"[{time_range}] {scene['visual_content']} (Confidence: {scene['confidence']:.2f})")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Clean up any remaining temporary files
        bot.cleanup_temp_files()