# whisper_youtube_extractor.py
"""
YouTube Transcript Extractor using OpenAI Whisper with Dual Personality Support
Downloads audio, transcribes using Whisper, and handles NetworkChuck and Bloomy content 
with proper metadata distinction and organized file structure
"""

import os
import re
import json
import time
import logging
import whisper
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import yt_dlp

class WhisperYouTubeExtractor:
    """
    Enhanced YouTube video processor with Whisper transcription and dual personality support
    """
    
    def __init__(self, model_size: str = "base"):
        """
        Initialize the extractor
        
        Args:
            model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
        """
        self.model_size = model_size
        self.model = None  # Lazy load the model
        
        # Create directory structure
        self.setup_directories()
        
        # Setup logging
        self.setup_logging()
        
        # Personality mappings
        self.personality_mappings = {
            'networkchuck': {
                'channel_indicators': ['networkchuck', 'chuck'],
                'domain': 'technology_networking',
                'expertise': ['networking', 'cybersecurity', 'linux', 'cloud', 'vpn', 'docker', 'kubernetes']
            },
            'bloomy': {
                'channel_indicators': ['explain how to simply', 'bloomy'],
                'domain': 'finance_excel',
                'expertise': ['bloomberg', 'excel', 'finance', 'data analysis', 'trading', 'financial modeling']
            }
        }
        
        print(f"🎤 WhisperYouTubeExtractor initialized with model: {model_size}")
    
    def setup_directories(self):
        """Create necessary directory structure"""
        self.base_dir = Path("data")
        
        # Main directories
        self.transcript_cache_dir = self.base_dir / "transcript_cache"
        self.transcript_csv_dir = self.base_dir / "transcript_csv"
        self.audio_cache_dir = self.base_dir / "audio_cache"
        self.logs_dir = self.base_dir / "logs"
        
        # Personality-specific directories
        self.nc_json_dir = self.transcript_cache_dir / "networkchuck"
        self.nc_csv_dir = self.transcript_csv_dir / "networkchuck"
        self.bloomy_json_dir = self.transcript_cache_dir / "bloomy"
        self.bloomy_csv_dir = self.transcript_csv_dir / "bloomy"
        
        # Create all directories
        for directory in [
            self.transcript_cache_dir, self.transcript_csv_dir, 
            self.audio_cache_dir, self.logs_dir,
            self.nc_json_dir, self.nc_csv_dir,
            self.bloomy_json_dir, self.bloomy_csv_dir
        ]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_file = self.logs_dir / f"extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_whisper_model(self):
        """Lazy load Whisper model"""
        if self.model is None:
            self.logger.info(f"🔄 Loading Whisper model: {self.model_size}")
            self.model = whisper.load_model(self.model_size)
            self.logger.info("✅ Whisper model loaded successfully")
        return self.model
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from YouTube URL
        
        Args:
            url: YouTube video URL
            
        Returns:
            Video ID string or None if not found
        """
        patterns = [
            r'(?:watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
            r'youtube\.com/v/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        self.logger.error(f"Could not extract video ID from URL: {url}")
        return None
    
    def clean_video_url(self, url: str) -> str:
        """
        Clean video URL by removing playlist parameters
        
        Args:
            url: Original video URL
            
        Returns:
            Clean video URL with just video ID
        """
        video_id = self.extract_video_id(url)
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"
        return url
    
    def detect_personality(self, video_info: Dict, video_url: str) -> str:
        """
        Detect personality based on video info and URL
        
        Args:
            video_info: Video metadata from yt-dlp
            video_url: Original video URL
            
        Returns:
            Personality string ('networkchuck' or 'bloomy')
        """
        # Check uploader/channel name
        uploader = video_info.get('uploader', '').lower()
        title = video_info.get('title', '').lower()
        channel = video_info.get('channel', '').lower()
        
        # NetworkChuck detection
        nc_indicators = self.personality_mappings['networkchuck']['channel_indicators']
        if any(indicator in uploader for indicator in nc_indicators) or \
           any(indicator in channel for indicator in nc_indicators):
            return 'networkchuck'
        
        # Bloomy detection  
        bloomy_indicators = self.personality_mappings['bloomy']['channel_indicators']
        if any(indicator in uploader for indicator in bloomy_indicators) or \
           any(indicator in channel for indicator in bloomy_indicators):
            return 'bloomy'
        
        # Fallback: detect by common terms in title
        if any(term in title for term in ['bloomberg', 'excel', 'finance', 'trading']):
            return 'bloomy'
        elif any(term in title for term in ['network', 'linux', 'vpn', 'cyber', 'docker', 'kubernetes']):
            return 'networkchuck'
        
        # Default fallback based on content
        self.logger.warning(f"Could not detect personality for: {uploader} - {title}")
        return 'unknown'
    
    def get_video_info(self, url: str) -> Dict:
        """
        Get video metadata using yt-dlp
        
        Args:
            url: YouTube video URL
            
        Returns:
            Video metadata dictionary
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    'title': info.get('title', 'Unknown'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'channel': info.get('channel', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'upload_date': info.get('upload_date', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'description': info.get('description', ''),
                    'tags': info.get('tags', [])
                }
        except Exception as e:
            self.logger.error(f"Error getting video info: {e}")
            return {
                'title': 'Unknown',
                'uploader': 'Unknown',
                'channel': 'Unknown',
                'duration': 0,
                'upload_date': 'Unknown',
                'view_count': 0,
                'description': '',
                'tags': []
            }
    
    def download_audio(self, url: str, video_id: str) -> Optional[Path]:
        """
        Download audio from YouTube video
        
        Args:
            url: YouTube video URL
            video_id: Video ID
            
        Returns:
            Path to downloaded audio file or None if failed
        """
        audio_file = self.audio_cache_dir / f"{video_id}.wav"
        
        # Check if already downloaded
        if audio_file.exists():
            self.logger.info(f"Audio already cached: {video_id}")
            return audio_file
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(self.audio_cache_dir / f"{video_id}.%(ext)s"),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            if audio_file.exists():
                self.logger.info(f"✅ Audio downloaded: {video_id}")
                return audio_file
            else:
                self.logger.error(f"Audio file not found after download: {video_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error downloading audio for {video_id}: {e}")
            return None
    
    def transcribe_audio(self, audio_path: Path, video_id: str) -> Optional[Dict]:
        """
        Transcribe audio using Whisper
        
        Args:
            audio_path: Path to audio file
            video_id: Video ID for caching
            
        Returns:
            Whisper transcription result or None if failed
        """
        try:
            model = self.load_whisper_model()
            
            self.logger.info(f"🎤 Transcribing audio: {video_id}")
            result = model.transcribe(str(audio_path))
            
            self.logger.info(f"✅ Transcription complete: {video_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error transcribing audio for {video_id}: {e}")
            return None
    
    def create_comprehensive_transcript_data(self, video_id: str, video_url: str, 
                                           video_info: Dict, whisper_result: Dict) -> Dict:
        """
        Create comprehensive transcript data structure
        
        Args:
            video_id: YouTube video ID
            video_url: Clean video URL
            video_info: Video metadata
            whisper_result: Whisper transcription result
            
        Returns:
            Comprehensive transcript data dictionary
        """
        # Detect personality
        personality = self.detect_personality(video_info, video_url)
        personality_meta = self.personality_mappings.get(personality, {})
        
        transcript_data = {
            'video_id': video_id,
            'video_url': video_url,
            'video_info': video_info,
            'personality': personality,
            'domain': personality_meta.get('domain', 'unknown'),
            'expertise_areas': personality_meta.get('expertise', []),
            'language': whisper_result.get('language', 'unknown'),
            'text': whisper_result.get('text', ''),
            'segments': whisper_result.get('segments', []),
            'processing_metadata': {
                'processed_at': datetime.now().isoformat(),
                'whisper_model': self.model_size,
                'personality_detected': personality,
                'domain_focus': personality_meta.get('domain', 'unknown')
            }
        }
        
        return transcript_data
    
    def save_transcript_json(self, transcript_data: Dict, video_id: str, personality: str):
        """Save transcript data as JSON file"""
        if personality == 'networkchuck':
            json_file = self.nc_json_dir / f"{video_id}.json"
        elif personality == 'bloomy':
            json_file = self.bloomy_json_dir / f"{video_id}.json"
        else:
            json_file = self.transcript_cache_dir / f"{video_id}.json"
        
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"💾 JSON saved: {json_file}")
        except Exception as e:
            self.logger.error(f"Error saving JSON for {video_id}: {e}")
    
    def create_csv_data(self, transcript_data: Dict) -> List[Dict]:
        """
        Create CSV data from transcript
        
        Args:
            transcript_data: Transcript data dictionary
            
        Returns:
            List of segment dictionaries for CSV
        """
        video_id = transcript_data['video_id']
        personality = transcript_data.get('personality', 'unknown')
        domain = transcript_data.get('domain', 'unknown')
        segments = transcript_data.get('segments', [])
        
        csv_data = []
        for i, segment in enumerate(segments):
            segment_data = {
                'segment_id': i,
                'start_time': segment.get('start', 0),
                'end_time': segment.get('end', 0),
                'duration': segment.get('end', 0) - segment.get('start', 0),
                'text': segment.get('text', '').strip(),
                'video_id': video_id,
                'video_title': transcript_data['video_info']['title'],
                'video_url': transcript_data['video_url'],
                'personality': personality,
                'domain': domain,
                'uploader': transcript_data['video_info']['uploader'],
                'upload_date': transcript_data['video_info']['upload_date'],
                'language': transcript_data.get('language', 'unknown'),
                'video_duration': transcript_data['video_info'].get('duration', 0),
                'expertise_areas': ','.join(transcript_data.get('expertise_areas', []))
            }
            csv_data.append(segment_data)
        
        return csv_data
    
    def save_individual_csv(self, transcript_data: Dict, video_id: str, personality: str):
        """Save individual CSV file for a video"""
        csv_data = self.create_csv_data(transcript_data)
        
        if not csv_data:
            return
        
        # Determine output directory based on personality
        if personality == 'networkchuck':
            csv_file = self.nc_csv_dir / f"transcript_{video_id}.csv"
        elif personality == 'bloomy':
            csv_file = self.bloomy_csv_dir / f"transcript_{video_id}.csv"
        else:
            csv_file = self.transcript_csv_dir / f"transcript_{video_id}.csv"
        
        try:
            df = pd.DataFrame(csv_data)
            df.to_csv(csv_file, index=False, encoding='utf-8')
            self.logger.info(f"📊 CSV saved: {csv_file}")
        except Exception as e:
            self.logger.error(f"Error saving CSV for {video_id}: {e}")
    
    def process_single_video(self, video_data: Dict) -> Optional[Dict]:
        """
        Process a single video completely
        
        Args:
            video_data: Dictionary containing 'url' and optional metadata
            
        Returns:
            Processed transcript data or None if failed
        """
        url = video_data.get('url', '')
        clean_url = self.clean_video_url(url)
        video_id = self.extract_video_id(clean_url)
        
        if not video_id:
            self.logger.error(f"Could not extract video ID from: {url}")
            return None
        
        try:
            self.logger.info(f"🎬 Processing video: {video_id}")
            start_time = time.time()
            
            # Get video info
            video_info = self.get_video_info(clean_url)
            
            # Download audio
            audio_path = self.download_audio(clean_url, video_id)
            if not audio_path:
                raise Exception("Failed to download audio")
            
            # Transcribe audio
            whisper_result = self.transcribe_audio(audio_path, video_id)
            if not whisper_result:
                raise Exception("Failed to transcribe audio")
            
            # Create comprehensive transcript data
            transcript_data = self.create_comprehensive_transcript_data(
                video_id, clean_url, video_info, whisper_result
            )
            
            # Add original metadata from video_data
            transcript_data['source_metadata'] = video_data
            
            # Detect personality for file organization
            personality = transcript_data['personality']
            
            # Save JSON file
            self.save_transcript_json(transcript_data, video_id, personality)
            
            # Save individual CSV
            self.save_individual_csv(transcript_data, video_id, personality)
            
            # Clean up audio file to save space (optional)
            # audio_path.unlink()
            
            processing_time = time.time() - start_time
            self.logger.info(f"✅ Completed {video_id} ({personality}) in {processing_time:.1f}s")
            
            return transcript_data
            
        except Exception as e:
            self.logger.error(f"❌ Failed to process {video_id}: {e}")
            return None
    
    def create_combined_csv(self, personality: str):
        """Create combined CSV for a specific personality"""
        if personality == 'networkchuck':
            json_dir = self.nc_json_dir
            csv_file = self.nc_csv_dir / "all_networkchuck_transcripts.csv"
        elif personality == 'bloomy':
            json_dir = self.bloomy_json_dir
            csv_file = self.bloomy_csv_dir / "all_bloomy_transcripts.csv"
        else:
            return
        
        try:
            all_segments = []
            
            # Process all JSON files for this personality
            for json_file in json_dir.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        transcript_data = json.load(f)
                    
                    csv_data = self.create_csv_data(transcript_data)
                    all_segments.extend(csv_data)
                    
                except Exception as e:
                    self.logger.error(f"Error processing {json_file}: {e}")
            
            if all_segments:
                df = pd.DataFrame(all_segments)
                df.to_csv(csv_file, index=False, encoding='utf-8')
                self.logger.info(f"✅ Combined {personality} CSV created: {csv_file}")
                self.logger.info(f"📊 Total {personality} segments: {len(all_segments)}")
            else:
                self.logger.warning(f"No segments found for {personality}")
                
        except Exception as e:
            self.logger.error(f"Failed to create combined {personality} CSV: {e}")
    
    def process_video_list(self, video_list: List[Dict]) -> Dict:
        """
        Process a list of videos
        
        Args:
            video_list: List of video dictionaries with 'url' key
            
        Returns:
            Processing summary
        """
        self.logger.info(f"🚀 Starting processing of {len(video_list)} videos")
        
        results = {'networkchuck': [], 'bloomy': [], 'unknown': []}
        successful = 0
        failed = 0
        
        for i, video_data in enumerate(video_list):
            try:
                self.logger.info(f"📹 Processing video {i+1}/{len(video_list)}")
                
                result = self.process_single_video(video_data)
                
                if result:
                    personality = result.get('personality', 'unknown')
                    results[personality].append(result)
                    successful += 1
                else:
                    failed += 1
                
                # Small delay to avoid overwhelming the system
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Unexpected error processing video {i+1}: {e}")
                failed += 1
        
        # Create combined CSVs for each personality
        for personality in ['networkchuck', 'bloomy']:
            if results[personality]:
                self.create_combined_csv(personality)
        
        summary = {
            'total_processed': successful,
            'total_failed': failed,
            'networkchuck_videos': len(results['networkchuck']),
            'bloomy_videos': len(results['bloomy']),
            'unknown_videos': len(results['unknown']),
            'processing_time': time.time()
        }
        
        self.logger.info(f"🎉 Processing complete!")
        self.logger.info(f"✅ Successful: {successful}")
        self.logger.info(f"❌ Failed: {failed}")
        self.logger.info(f"🎬 NetworkChuck: {len(results['networkchuck'])}")
        self.logger.info(f"📊 Bloomy: {len(results['bloomy'])}")
        
        return summary

def process_from_json(json_file: str, model_size: str = "base") -> Dict:
    """
    Convenience function to process videos from JSON file
    
    Args:
        json_file: Path to JSON file containing video URLs
        model_size: Whisper model size
        
    Returns:
        Processing summary
    """
    extractor = WhisperYouTubeExtractor(model_size=model_size)
    
    # Load video data
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Combine all videos
    all_videos = []
    all_videos.extend(data.get('networkchuck_videos', []))
    all_videos.extend(data.get('bloomy_videos', []))
    
    return extractor.process_video_list(all_videos)

if __name__ == "__main__":
    print("🎤 WhisperYouTubeExtractor - Dual Personality Edition")
    print("=" * 60)
    
    # Process videos from the enhanced dataset
    result = process_from_json("enhanced_video_dataset.json", model_size="base")
    print(f"\n🎉 Final result: {result}")