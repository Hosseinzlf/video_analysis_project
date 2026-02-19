import base64
from typing import List
import google.generativeai as genai
from pathlib import Path

from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger("llm_service")


class LLMService:
    """
    Service for analyzing video frames using Google Gemini Vision.
    
    Takes a list of frame image paths and returns a detailed
    description of what's happening in the video.
    """

    def __init__(self):
        """Initialize Gemini with API key from settings"""
        
        if not settings.google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY not set in .env file. "
                "Get your key from https://aistudio.google.com/app/apikey"
            )
        
        # Configure Gemini
        genai.configure(api_key=settings.google_api_key)
        
        # Use Gemini 2.5 Flash - best for vision + free tier
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        logger.info("Initialized Google Gemini (gemini-2.5-flash)")

    # ──────────────────────────────────────────────────────────────
    # Main Analysis Method
    # ──────────────────────────────────────────────────────────────
    def analyze_frames(self, frame_paths: List[str]) -> str:
        """
        Send frames to Gemini and get a video description.
        
        Args:
            frame_paths: List of paths to jpg frame files
            
        Returns:
            String description of what's happening in the video
        """
        try:
            logger.info(f"Analyzing {len(frame_paths)} frames with Gemini")

            # ── Build the prompt ──────────────────────────────────
            prompt = self._build_prompt(len(frame_paths))

            # ── Load frame images ─────────────────────────────────
            images = []
            for frame_path in frame_paths:
                try:
                    with open(frame_path, 'rb') as f:
                        image_data = f.read()
                        images.append({
                            'mime_type': 'image/jpeg',
                            'data': image_data
                        })
                except Exception as e:
                    logger.warning(f"Could not load frame {frame_path}: {e}")

            if not images:
                raise Exception("No frames could be loaded")

            logger.info(f"Loaded {len(images)} frame images")

            # ── Send to Gemini ────────────────────────────────────
            content_parts = [prompt] + images
            
            response = self.model.generate_content(
                content_parts,
                generation_config={
                    'temperature': 0.7,
                    'max_output_tokens': 1500,
                }
            )

            description = response.text
            
            logger.info("Gemini analysis completed successfully")
            logger.info(f"Response length: {len(description)} characters")
            
            return description

        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            raise Exception(f"AI analysis failed: {str(e)}")

    # ──────────────────────────────────────────────────────────────
    # Helper: Build Prompt
    # ──────────────────────────────────────────────────────────────
    def _build_prompt(self, num_frames: int) -> str:
        """
        Create the instruction prompt for Gemini.
        """
        prompt = f"""Analyze these {num_frames} sequential frames from a video and provide a detailed description of what's happening.

Please include:

1. **Main Content**: What is the primary subject or activity in the video?

2. **Setting & Environment**: Where does this take place? What's the setting like?

3. **Key Elements**: 
   - People (if any): who they are, what they're doing
   - Objects: important items or elements visible
   - Actions: what's happening, any movement or changes

4. **Progression**: How does the scene develop across the frames? Any changes or progression?

5. **Overall Context**: What is the purpose or context of this video? (e.g., tutorial, vlog, presentation, advertisement, etc.)

Provide a clear, coherent narrative in 2-3 paragraphs. Be specific and descriptive, but concise."""

        return prompt