# whisper_youtube_extractor_v2.py
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
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import yt_dlp

class ProcessingMode(Enum):
    """Processing mode options"""
    INCREMENTAL = "incremental"    # Skip existing, add new
    FORCE_ALL = "force_all"        # Reprocess everything  
    VALIDATE_ONLY = "validate"     # Check integrity, fix issues
    CLEANUP_ONLY = "cleanup"       # Remove orphans, deduplicate

class CacheConfig:
    """Cache management configuration"""
    KEEP_AUDIO = False  # Delete after transcription
    MAX_AUDIO_AGE_DAYS = 7  # Auto-cleanup old audio
    VALIDATE_EXISTING = True  # Check JSON integrity
    CREATE_INDIVIDUAL_CSVS = False  # Only create combined CSVs
    ENABLE_DEDUPLICATION = True  # Remove duplicates

class WhisperYouTubeExtractor:
    """
    Enhanced YouTube video processor with Whisper transcription and dual personality support
    Features: Smart caching, deduplication, cleanup, and validation
    """
    
    def __init__(self, model_size: str = "base", cache_config: CacheConfig = None):
        """
        Initialize the extractor
        
        Args:
            model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
            cache_config: Cache configuration object
        """
        self.model_size = model_size
        self.model = None  # Lazy load the model
        self.cache_config = cache_config or CacheConfig()
        
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
        
        print(f"🎤 Enhanced WhisperYouTubeExtractor initialized with model: {model_size}")
        print(f"📁 Cache config: Audio={self.cache_config.KEEP_AUDIO}, Individual CSVs={self.cache_config.CREATE_INDIVIDUAL_CSVS}")
    
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
        """Extract video ID from YouTube URL"""
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
        """Clean video URL by removing playlist parameters"""
        video_id = self.extract_video_id(url)
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"
        return url
    
    def get_json_paths(self, video_id: str) -> List[Path]:
        """Get all possible JSON file paths for a video ID"""
        return [
            self.nc_json_dir / f"{video_id}.json",
            self.bloomy_json_dir / f"{video_id}.json",
            self.transcript_cache_dir / f"{video_id}.json"
        ]
    
    def get_json_dir(self, personality: str) -> Path:
        """Get JSON directory for personality"""
        if personality == 'networkchuck':
            return self.nc_json_dir
        elif personality == 'bloomy':
            return self.bloomy_json_dir
        else:
            return self.transcript_cache_dir
    
    def get_csv_dir(self, personality: str) -> Path:
        """Get CSV directory for personality"""
        if personality == 'networkchuck':
            return self.nc_csv_dir
        elif personality == 'bloomy':
            return self.bloomy_csv_dir
        else:
            return self.transcript_csv_dir
    
    def check_existing_transcript(self, video_id: str) -> Optional[Dict]:
        """
        Check if transcript already exists and return it
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Existing transcript data or None if not found
        """
        possible_paths = self.get_json_paths(video_id)
        
        for path in possible_paths:
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Validate JSON structure if enabled
                    if self.cache_config.VALIDATE_EXISTING:
                        if self.validate_transcript_json(data):
                            self.logger.info(f"📋 Using cached transcript: {video_id}")
                            return data
                        else:
                            self.logger.warning(f"⚠️ Invalid cached transcript, will reprocess: {video_id}")
                            path.unlink()  # Delete invalid file
                    else:
                        self.logger.info(f"📋 Using cached transcript: {video_id}")
                        return data
                        
                except Exception as e:
                    self.logger.warning(f"Error reading cached transcript {path}: {e}")
                    continue
        
        return None
    
    def validate_transcript_json(self, data: Dict) -> bool:
        """
        Validate transcript JSON structure
        
        Args:
            data: Transcript data dictionary
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['video_id', 'video_url', 'personality', 'text', 'segments']
        
        try:
            # Check required fields
            for field in required_fields:
                if field not in data:
                    return False
            
            # Check segments structure
            segments = data.get('segments', [])
            if not isinstance(segments, list):
                return False
            
            # Validate a few segments
            for segment in segments[:3]:  # Check first 3 segments
                if not isinstance(segment, dict):
                    return False
                if 'start' not in segment or 'end' not in segment or 'text' not in segment:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def cleanup_old_audio(self):
        """Remove old audio files based on age"""
        if not self.cache_config.KEEP_AUDIO and self.cache_config.MAX_AUDIO_AGE_DAYS > 0:
            cutoff_date = datetime.now() - timedelta(days=self.cache_config.MAX_AUDIO_AGE_DAYS)
            
            removed_count = 0
            for audio_file in self.audio_cache_dir.glob("*.wav"):
                try:
                    file_time = datetime.fromtimestamp(audio_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        audio_file.unlink()
                        removed_count += 1
                except Exception as e:
                    self.logger.warning(f"Error removing old audio file {audio_file}: {e}")
            
            if removed_count > 0:
                self.logger.info(f"🧹 Cleaned up {removed_count} old audio files")
    
    def detect_personality(self, video_info: Dict, video_url: str) -> str:
        """Detect personality based on video info and URL"""
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
        """Get video metadata using yt-dlp"""
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
        """Download audio from YouTube video"""
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
        """Transcribe audio using Whisper"""
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
        """Create comprehensive transcript data structure"""
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
        json_dir = self.get_json_dir(personality)
        json_file = json_dir / f"{video_id}.json"
        
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"💾 JSON saved: {json_file}")
        except Exception as e:
            self.logger.error(f"Error saving JSON for {video_id}: {e}")
    
    def create_csv_data(self, transcript_data: Dict) -> List[Dict]:
        """Create CSV data from transcript"""
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
        """Save individual CSV file for a video (if enabled)"""
        if not self.cache_config.CREATE_INDIVIDUAL_CSVS:
            return
            
        csv_data = self.create_csv_data(transcript_data)
        
        if not csv_data:
            return
        
        csv_dir = self.get_csv_dir(personality)
        csv_file = csv_dir / f"transcript_{video_id}.csv"
        
        try:
            df = pd.DataFrame(csv_data)
            df.to_csv(csv_file, index=False, encoding='utf-8')
            self.logger.info(f"📊 Individual CSV saved: {csv_file}")
        except Exception as e:
            self.logger.error(f"Error saving individual CSV for {video_id}: {e}")
    
    def update_combined_csv_incrementally(self, transcript_data: Dict, personality: str):
        """
        Update combined CSV incrementally
        
        Args:
            transcript_data: New transcript data
            personality: Video personality
        """
        if personality not in ['networkchuck', 'bloomy']:
            return
        
        csv_dir = self.get_csv_dir(personality)
        combined_csv = csv_dir / f"all_{personality}_transcripts.csv"
        
        # Get new segments
        new_segments = self.create_csv_data(transcript_data)
        if not new_segments:
            return
        
        try:
            # Load existing CSV or create new DataFrame
            if combined_csv.exists():
                existing_df = pd.read_csv(combined_csv)
                
                # Remove old entries for this video_id if they exist
                video_id = transcript_data['video_id']
                existing_df = existing_df[existing_df['video_id'] != video_id]
                
                # Add new segments
                new_df = pd.DataFrame(new_segments)
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            else:
                # Create new CSV
                combined_df = pd.DataFrame(new_segments)
            
            # Save updated CSV
            combined_df.to_csv(combined_csv, index=False, encoding='utf-8')
            self.logger.info(f"📈 Updated combined CSV: {combined_csv}")
            
        except Exception as e:
            self.logger.error(f"Error updating combined CSV for {personality}: {e}")
    
    def deduplicate_csv(self, csv_file: Path):
        """
        Remove duplicate entries from CSV based on video_id + segment_id
        
        Args:
            csv_file: Path to CSV file
        """
        if not csv_file.exists():
            return
        
        try:
            df = pd.read_csv(csv_file)
            original_count = len(df)
            
            # Remove duplicates keeping the last occurrence
            df_clean = df.drop_duplicates(subset=['video_id', 'segment_id'], keep='last')
            
            duplicates_removed = original_count - len(df_clean)
            if duplicates_removed > 0:
                df_clean.to_csv(csv_file, index=False, encoding='utf-8')
                self.logger.info(f"🧹 Removed {duplicates_removed} duplicates from {csv_file}")
            
        except Exception as e:
            self.logger.error(f"Error deduplicating CSV {csv_file}: {e}")
    
    def cleanup_orphaned_files(self, personality: str):
        """
        Remove individual CSVs for videos no longer in JSON cache
        
        Args:
            personality: Video personality
        """
        if not self.cache_config.CREATE_INDIVIDUAL_CSVS:
            return
        
        json_dir = self.get_json_dir(personality)
        csv_dir = self.get_csv_dir(personality)
        
        # Get list of video IDs that have JSON files
        json_ids = {f.stem for f in json_dir.glob("*.json")}
        
        # Check individual CSV files
        csv_files = csv_dir.glob("transcript_*.csv")
        removed_count = 0
        
        for csv_file in csv_files:
            video_id = csv_file.stem.replace("transcript_", "")
            if video_id not in json_ids:
                try:
                    csv_file.unlink()
                    removed_count += 1
                except Exception as e:
                    self.logger.warning(f"Error removing orphaned CSV {csv_file}: {e}")
        
        if removed_count > 0:
            self.logger.info(f"🧹 Removed {removed_count} orphaned CSV files for {personality}")
    
    def create_combined_csv(self, personality: str):
        """Create combined CSV for a specific personality from all JSON files"""
        if personality not in ['networkchuck', 'bloomy']:
            return
        
        json_dir = self.get_json_dir(personality)
        csv_dir = self.get_csv_dir(personality)
        csv_file = csv_dir / f"all_{personality}_transcripts.csv"
        
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
                
                # Deduplicate if enabled
                if self.cache_config.ENABLE_DEDUPLICATION:
                    original_count = len(df)
                    df = df.drop_duplicates(subset=['video_id', 'segment_id'], keep='last')
                    duplicates_removed = original_count - len(df)
                    if duplicates_removed > 0:
                        self.logger.info(f"🧹 Removed {duplicates_removed} duplicates during CSV creation")
                
                df.to_csv(csv_file, index=False, encoding='utf-8')
                self.logger.info(f"✅ Combined {personality} CSV created: {csv_file}")
                self.logger.info(f"📊 Total {personality} segments: {len(df)}")
            else:
                self.logger.warning(f"No segments found for {personality}")
                
        except Exception as e:
            self.logger.error(f"Failed to create combined {personality} CSV: {e}")
    
    def validate_data_integrity(self):
        """Check JSON-CSV consistency and report issues"""
        self.logger.info("🔍 Validating data integrity...")
        
        issues = []
        
        for personality in ['networkchuck', 'bloomy']:
            json_dir = self.get_json_dir(personality)
            csv_dir = self.get_csv_dir(personality)
            combined_csv = csv_dir / f"all_{personality}_transcripts.csv"
            
            # Check if combined CSV exists
            if not combined_csv.exists():
                issues.append(f"Missing combined CSV for {personality}")
                continue
            
            # Check JSON files vs CSV entries
            json_ids = {f.stem for f in json_dir.glob("*.json")}
            
            try:
                df = pd.read_csv(combined_csv)
                csv_ids = set(df['video_id'].unique())
                
                # Find discrepancies
                missing_in_csv = json_ids - csv_ids
                extra_in_csv = csv_ids - json_ids
                
                if missing_in_csv:
                    issues.append(f"{personality}: {len(missing_in_csv)} JSON files missing from CSV")
                
                if extra_in_csv:
                    issues.append(f"{personality}: {len(extra_in_csv)} extra video IDs in CSV")
                
            except Exception as e:
                issues.append(f"Error reading {personality} CSV: {e}")
        
        if issues:
            self.logger.warning("⚠️ Data integrity issues found:")
            for issue in issues:
                self.logger.warning(f"  - {issue}")
        else:
            self.logger.info("✅ Data integrity check passed")
        
        return issues
    
    def process_single_video(self, video_data: Dict, mode: ProcessingMode = ProcessingMode.INCREMENTAL) -> Optional[Dict]:
        """
        Process a single video completely
        
        Args:
            video_data: Dictionary containing 'url' and optional metadata
            mode: Processing mode
            
        Returns:
            Processed transcript data or None if failed
        """
        url = video_data.get('url', '')
        clean_url = self.clean_video_url(url)
        video_id = self.extract_video_id(clean_url)
        
        if not video_id:
            self.logger.error(f"Could not extract video ID from: {url}")
            return None
        
        # Check for existing transcript (unless forcing reprocess)
        if mode == ProcessingMode.INCREMENTAL:
            existing_transcript = self.check_existing_transcript(video_id)
            if existing_transcript:
                return existing_transcript
        
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
            
            # Save individual CSV (if enabled)
            self.save_individual_csv(transcript_data, video_id, personality)
            
            # Update combined CSV incrementally
            self.update_combined_csv_incrementally(transcript_data, personality)
            
            # Clean up audio file if configured
            if not self.cache_config.KEEP_AUDIO:
                try:
                    audio_path.unlink()
                    self.logger.info(f"🧹 Removed audio file: {video_id}")
                except Exception as e:
                    self.logger.warning(f"Could not remove audio file: {e}")
            
            processing_time = time.time() - start_time
            self.logger.info(f"✅ Completed {video_id} ({personality}) in {processing_time:.1f}s")
            
            return transcript_data
            
        except Exception as e:
            self.logger.error(f"❌ Failed to process {video_id}: {e}")
            return None
    
    def process_video_list(self, video_list: List[Dict], mode: ProcessingMode = ProcessingMode.INCREMENTAL) -> Dict:
        """
        Process a list of videos with enhanced tracking and management
        
        Args:
            video_list: List of video dictionaries with 'url' key
            mode: Processing mode
            
        Returns:
            Processing summary with detailed tracking
        """
        self.logger.info(f"🚀 Starting processing of {len(video_list)} videos in {mode.value} mode")
        
        # Cleanup old audio files at start
        self.cleanup_old_audio()
        
        results = {'networkchuck': [], 'bloomy': [], 'unknown': []}
        successful = 0
        failed = 0
        skipped = 0
        
        # Track problematic URLs
        failed_urls = []
        unknown_urls = []
        
        for i, video_data in enumerate(video_list):
            try:
                self.logger.info(f"📹 Processing video {i+1}/{len(video_list)}")
                
                result = self.process_single_video(video_data, mode)
                
                if result:
                    personality = result.get('personality', 'unknown')
                    results[personality].append(result)
                    
                    # Track unknown personality videos
                    if personality == 'unknown':
                        url = video_data.get('url', '')
                        title = result.get('video_info', {}).get('title', 'N/A')
                        unknown_urls.append({'url': url, 'title': title})
                        print(f"❌ Unknown video: {url} - Title: {title}")
                    
                    successful += 1
                else:
                    url = video_data.get('url', '')
                    failed_urls.append({'url': url, 'error': 'Processing failed'})
                    print(f"🚫 Failed to process: {url}")
                    failed += 1
                
                # Small delay to avoid overwhelming the system
                time.sleep(1)
                
            except Exception as e:
                url = video_data.get('url', '')
                failed_urls.append({'url': url, 'error': str(e)})
                print(f"🚫 Failed to process: {url} - Error: {e}")
                self.logger.error(f"Unexpected error processing video {i+1}: {e}")
                failed += 1
        
        # Post-processing cleanup and validation
        if mode != ProcessingMode.VALIDATE_ONLY:
            # Create/update combined CSVs for each personality
            for personality in ['networkchuck', 'bloomy']:
                if results[personality] or mode == ProcessingMode.FORCE_ALL:
                    self.create_combined_csv(personality)
                    
                    # Deduplicate if enabled
                    if self.cache_config.ENABLE_DEDUPLICATION:
                        csv_dir = self.get_csv_dir(personality)
                        combined_csv = csv_dir / f"all_{personality}_transcripts.csv"
                        self.deduplicate_csv(combined_csv)
                    
                    # Cleanup orphaned files
                    self.cleanup_orphaned_files(personality)
        
        # Data integrity validation
        if mode in [ProcessingMode.VALIDATE_ONLY, ProcessingMode.FORCE_ALL]:
            integrity_issues = self.validate_data_integrity()
        else:
            integrity_issues = []
        
        # Print detailed summary
        print(f"\n📊 Processing Summary:")
        print(f"Mode: {mode.value}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Skipped: {skipped}")
        
        if failed_urls:
            print(f"\nFailed URLs ({len(failed_urls)}):")
            for item in failed_urls:
                print(f"  - {item['url']} | Error: {item['error']}")
        
        if unknown_urls:
            print(f"\nUnknown URLs ({len(unknown_urls)}):")
            for item in unknown_urls:
                print(f"  - {item['url']} | Title: {item['title']}")
        
        if integrity_issues:
            print(f"\nData Integrity Issues ({len(integrity_issues)}):")
            for issue in integrity_issues:
                print(f"  - {issue}")
        
        summary = {
            'total_processed': successful,
            'total_failed': failed,
            'total_skipped': skipped,
            'networkchuck_videos': len(results['networkchuck']),
            'bloomy_videos': len(results['bloomy']),
            'unknown_videos': len(results['unknown']),
            'failed_urls': failed_urls,
            'unknown_urls': unknown_urls,
            'integrity_issues': integrity_issues,
            'processing_mode': mode.value,
            'processing_time': time.time()
        }
        
        self.logger.info(f"🎉 Processing complete!")
        self.logger.info(f"✅ Successful: {successful}")
        self.logger.info(f"❌ Failed: {failed}")
        self.logger.info(f"⏭️ Skipped: {skipped}")
        self.logger.info(f"🎬 NetworkChuck: {len(results['networkchuck'])}")
        self.logger.info(f"📊 Bloomy: {len(results['bloomy'])}")
        self.logger.info(f"❓ Unknown: {len(results['unknown'])}")
        
        return summary
    
    def cleanup_all(self):
        """
        Perform comprehensive cleanup
        """
        self.logger.info("🧹 Starting comprehensive cleanup...")
        
        # Cleanup old audio files
        self.cleanup_old_audio()
        
        # Cleanup orphaned files for each personality
        for personality in ['networkchuck', 'bloomy']:
            self.cleanup_orphaned_files(personality)
        
        # Deduplicate all CSVs
        if self.cache_config.ENABLE_DEDUPLICATION:
            for personality in ['networkchuck', 'bloomy']:
                csv_dir = self.get_csv_dir(personality)
                combined_csv = csv_dir / f"all_{personality}_transcripts.csv"
                self.deduplicate_csv(combined_csv)
        
        # Validate data integrity
        self.validate_data_integrity()
        
        self.logger.info("✅ Cleanup complete!")
    
    def get_processing_stats(self) -> Dict:
        """
        Get comprehensive processing statistics
        
        Returns:
            Statistics dictionary
        """
        stats = {
            'personalities': {},
            'cache_info': {},
            'file_counts': {}
        }
        
        # Per-personality stats
        for personality in ['networkchuck', 'bloomy']:
            json_dir = self.get_json_dir(personality)
            csv_dir = self.get_csv_dir(personality)
            combined_csv = csv_dir / f"all_{personality}_transcripts.csv"
            
            json_count = len(list(json_dir.glob("*.json")))
            individual_csv_count = len(list(csv_dir.glob("transcript_*.csv")))
            
            personality_stats = {
                'json_files': json_count,
                'individual_csvs': individual_csv_count,
                'combined_csv_exists': combined_csv.exists()
            }
            
            # Get combined CSV stats
            if combined_csv.exists():
                try:
                    df = pd.read_csv(combined_csv)
                    personality_stats.update({
                        'total_segments': len(df),
                        'unique_videos': df['video_id'].nunique(),
                        'total_duration_hours': df['video_duration'].sum() / 3600
                    })
                except Exception as e:
                    personality_stats['csv_error'] = str(e)
            
            stats['personalities'][personality] = personality_stats
        
        # Cache info
        audio_files = list(self.audio_cache_dir.glob("*.wav"))
        stats['cache_info'] = {
            'audio_files_cached': len(audio_files),
            'audio_cache_size_mb': sum(f.stat().st_size for f in audio_files) / (1024 * 1024),
            'cache_config': {
                'keep_audio': self.cache_config.KEEP_AUDIO,
                'max_audio_age_days': self.cache_config.MAX_AUDIO_AGE_DAYS,
                'create_individual_csvs': self.cache_config.CREATE_INDIVIDUAL_CSVS,
                'enable_deduplication': self.cache_config.ENABLE_DEDUPLICATION
            }
        }
        
        return stats

def process_from_json(json_file: str, model_size: str = "base", 
                     mode: ProcessingMode = ProcessingMode.INCREMENTAL,
                     cache_config: CacheConfig = None) -> Dict:
    """
    Enhanced convenience function to process videos from JSON file
    
    Args:
        json_file: Path to JSON file containing video URLs
        model_size: Whisper model size
        mode: Processing mode
        cache_config: Cache configuration
        
    Returns:
        Processing summary with detailed tracking
    """
    extractor = WhisperYouTubeExtractor(model_size=model_size, cache_config=cache_config)
    
    # Load video data
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Combine all videos
    all_videos = []
    all_videos.extend(data.get('networkchuck_videos', []))
    all_videos.extend(data.get('bloomy_videos', []))
    
    return extractor.process_video_list(all_videos, mode)

def cleanup_data(cache_config: CacheConfig = None):
    """
    Standalone cleanup function
    
    Args:
        cache_config: Cache configuration
    """
    extractor = WhisperYouTubeExtractor(cache_config=cache_config)
    extractor.cleanup_all()

def validate_data(cache_config: CacheConfig = None) -> List[str]:
    """
    Standalone data validation function
    
    Args:
        cache_config: Cache configuration
        
    Returns:
        List of integrity issues
    """
    extractor = WhisperYouTubeExtractor(cache_config=cache_config)
    return extractor.validate_data_integrity()

def get_stats(cache_config: CacheConfig = None) -> Dict:
    """
    Get processing statistics
    
    Args:
        cache_config: Cache configuration
        
    Returns:
        Statistics dictionary
    """
    extractor = WhisperYouTubeExtractor(cache_config=cache_config)
    return extractor.get_processing_stats()

if __name__ == "__main__":
    print("🎤 Enhanced WhisperYouTubeExtractor - Smart Caching Edition")
    print("=" * 60)
    
    # Example usage with different modes
    
    # Configure cache settings
    cache_config = CacheConfig()
    cache_config.KEEP_AUDIO = False  # Delete audio after processing
    cache_config.CREATE_INDIVIDUAL_CSVS = False  # Only combined CSVs
    cache_config.ENABLE_DEDUPLICATION = True  # Remove duplicates
    cache_config.MAX_AUDIO_AGE_DAYS = 3  # Cleanup audio older than 3 days
    
    # Process videos in incremental mode (skip existing)
    print("🚀 Running incremental processing...")
    result = process_from_json("data/video_urls.json", 
                             model_size="small", 
                             mode=ProcessingMode.INCREMENTAL,
                             cache_config=cache_config)
    
    print(f"\n🎉 Final result: {result}")
    
    # Get comprehensive stats
    print("\n📊 Processing Statistics:")
    stats = get_stats(cache_config)
    for personality, data in stats['personalities'].items():
        print(f"{personality.title()}: {data['unique_videos']} videos, {data['total_segments']} segments")
    
    print(f"Cache: {stats['cache_info']['audio_files_cached']} audio files, "
          f"{stats['cache_info']['audio_cache_size_mb']:.1f} MB")