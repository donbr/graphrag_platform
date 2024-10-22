# graphrag_platform/ingestion/video_processor.py
import asyncio
import yt_dlp
import whisper
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import logging
from transformers import pipeline
import torch
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class VideoMetadata:
    video_id: str
    title: str
    description: str
    upload_date: str
    duration: int
    tags: List[str]
    speakers: List[str]
    code_repos: List[str]
    chapters: List[Dict]

@dataclass
class TranscriptSegment:
    start_time: float
    end_time: float
    text: str
    speaker: Optional[str]
    code_blocks: List[str]
    technical_terms: List[str]
    embedding: Optional[List[float]] = None

class VideoProcessor:
    def __init__(self, 
                 output_dir: str = "data",
                 max_workers: int = 4,
                 gpu_device: int = 0):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.whisper_model = whisper.load_model("large-v3")
        self.diarization = pipeline(
            "automatic-speech-recognition",
            model="pyannote/speaker-diarization",
            device=f"cuda:{gpu_device}" if torch.cuda.is_available() else "cpu"
        )
        self.code_detector = pipeline(
            "text-classification",
            model="microsoft/codebert-base"
        )
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
    async def process_video(self, url: str) -> Tuple[VideoMetadata, List[TranscriptSegment]]:
        """Process video through complete pipeline"""
        # Download video
        video_path, metadata = await self._download_video(url)
        
        # Process in parallel
        tasks = [
            self._transcribe_audio(video_path),
            self._extract_speakers(video_path),
            self._detect_code_blocks(metadata.description)
        ]
        
        transcription, speakers, code_blocks = await asyncio.gather(*tasks)
        
        # Create segments
        segments = await self._create_segments(
            transcription,
            speakers,
            code_blocks
        )
        
        return metadata, segments
    
    async def _download_video(self, url: str) -> Tuple[Path, VideoMetadata]:
        """Download video and extract metadata"""
        ydl_opts = {
            'format': 'bestaudio/best',
            'paths': {'home': str(self.output_dir)},
            'extract_audio': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }]
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            metadata = VideoMetadata(
                video_id=info['id'],
                title=info['title'],
                description=info['description'],
                upload_date=info['upload_date'],
                duration=info['duration'],
                tags=info.get('tags', []),
                speakers=[],  # Will be filled later
                code_repos=self._extract_code_repos(info['description']),
                chapters=info.get('chapters', [])
            )
            
            video_path = self.output_dir / f"{info['id']}.wav"
            return video_path, metadata
    
    async def _transcribe_audio(self, audio_path: Path) -> Dict:
        """Transcribe audio using Whisper"""
        def _transcribe():
            return self.whisper_model.transcribe(
                str(audio_path),
                task="transcribe",
                language="en"
            )
        
        return await asyncio.get_event_loop().run_in_executor(
            self.executor,
            _transcribe
        )
    
    async def _extract_speakers(self, audio_path: Path) -> List[Dict]:
        """Extract speaker segments using diarization"""
        def _diarize():
            return self.diarization(str(audio_path))
        
        diarization = await asyncio.get_event_loop().run_in_executor(
            self.executor,
            _diarize
        )
        return diarization['chunks']
    
    async def _detect_code_blocks(self, text: str) -> List[str]:
        """Detect code blocks in text"""
        def _detect():
            # Split text into potential code blocks
            blocks = text.split("```")
            code_blocks = []
            
            for i, block in enumerate(blocks):
                if i % 2 == 1:  # Inside code block
                    code_blocks.append(block.strip())
                else:
                    # Check for indented code blocks
                    lines = block.split("\n")
                    current_block = []
                    for line in lines:
                        if line.startswith("    ") or line.startswith("\t"):
                            current_block.append(line.strip())
                        elif current_block:
                            code_blocks.append("\n".join(current_block))
                            current_block = []
            
            return code_blocks
        
        return await asyncio.get_event_loop().run_in_executor(
            self.executor,
            _detect
        )
    
    async def _create_segments(self,
                             transcription: Dict,
                             speakers: List[Dict],
                             code_blocks: List[str]) -> List[TranscriptSegment]:
        """Create transcript segments with metadata"""
        segments = []
        
        for segment in transcription['segments']:
            # Find speaker for this segment
            speaker = self._find_speaker(segment['start'], speakers)
            
            # Extract any code blocks in this segment
            segment_code_blocks = await self._detect_code_blocks(segment['text'])
            
            # Extract technical terms (placeholder for now)
            technical_terms = []
            
            segments.append(TranscriptSegment(
                start_time=segment['start'],
                end_time=segment['end'],
                text=segment['text'],
                speaker=speaker,
                code_blocks=segment_code_blocks,
                technical_terms=technical_terms
            ))
        
        return segments
    
    def _find_speaker(self, timestamp: float, speakers: List[Dict]) -> Optional[str]:
        """Find speaker at given timestamp"""
        for speaker in speakers:
            if speaker['start'] <= timestamp <= speaker['end']:
                return speaker['speaker']
        return None
    
    @staticmethod
    def _extract_code_repos(description: str) -> List[str]:
        """Extract code repository links from description"""
        import re
        
        # Common code repository patterns
        repo_patterns = [
            r'https?://github\.com/[\w-]+/[\w-]+',
            r'https?://gitlab\.com/[\w-]+/[\w-]+',
            r'https?://bitbucket\.org/[\w-]+/[\w-]+'
        ]
        
        repos = []
        for pattern in repo_patterns:
            repos.extend(re.findall(pattern, description))
            
        return repos
