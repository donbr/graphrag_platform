# graphrag_platform/ingestion/dataset_manager.py
from typing import Dict, List, Optional
from datasets import Dataset, load_dataset
import logging
from .video_processor import VideoMetadata, TranscriptSegment

logger = logging.getLogger(__name__)

class DatasetManager:
    """Manages HuggingFace dataset operations"""
    
    def __init__(self, dataset_name: str):
        self.dataset_name = dataset_name
        self.dataset = None
    
    async def initialize(self):
        """Initialize or load dataset"""
        try:
            self.dataset = load_dataset(self.dataset_name)
            logger.info(f"Loaded existing dataset: {self.dataset_name}")
        except Exception as e:
            logger.info(f"Creating new dataset: {self.dataset_name}")
            self.dataset = Dataset.from_dict({
                'video_id': [],
                'title': [],
                'description': [],
                'transcript_segments': [],
                'metadata': [],
                'version': []
            })
    
    async def add_video(self,
                       metadata: VideoMetadata,
                       segments: List[TranscriptSegment],
                       version: str = "1.0.0"):
        """Add video data to dataset"""
        
        # Convert segments to dict format
        segment_dicts = []
        for seg in segments:
            segment_dict = {
                'start_time': seg.start_time,
                'end_time': seg.end_time,
                'text': seg.text,
                'speaker': seg.speaker,
                'code_blocks': seg.code_blocks,
                'technical_terms': seg.technical_terms
            }
            if seg.embedding:
                segment_dict['embedding'] = seg.embedding
            segment_dicts.append(segment_dict)
        
        # Create new row
        new_row = {
            'video_id': metadata.video_id,
            'title': metadata.title,
            'description': metadata.description,
            'transcript_segments': segment_dicts,
            'metadata': {
                'upload_date': metadata.upload_date,
                'duration': metadata.duration,
                'tags': metadata.tags,
                'speakers': metadata.speakers,
                'code_repos': metadata.code_repos,
                'chapters': metadata.chapters
            },
            'version': version
        }
        
        # Add to dataset
        self.dataset = self.dataset.add_item(new_row)
        
        # Push to hub
        await self.dataset.push_to_hub(self.dataset_name)
        logger.info(f"Added video {metadata.video_id} to dataset")
    
    async def get_video(self, video_id: str) -> Optional[Dict]:
        """Retrieve video data from dataset"""
        if not self.dataset:
            await self.initialize()
            
        matches = self.dataset.filter(lambda x: x['video_id'] == video_id)
        if not matches:
            return None
            
        return matches[0]
    
    async def list_videos(self) -> List[Dict]:
        """List all videos in dataset"""
        if not self.dataset:
            await self.initialize()
            
        return [{
            'video_id': item['video_id'],
            'title': item['title'],
            'upload_date': item['metadata']['upload_date']
        } for item in self.dataset]
