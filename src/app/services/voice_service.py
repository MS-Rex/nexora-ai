"""
Voice service for handling speech-to-text, AI response generation, and text-to-speech.

This module provides comprehensive voice interaction functionality using Groq API 
for both speech recognition (Whisper-large-v3-turbo) and text-to-speech (PlayAI Dialog),
along with orchestrator agent for response generation.
"""

import asyncio
import io
import logging
import os
import re
import tempfile
import traceback
from typing import Optional, Tuple, List, Dict

from groq import Groq
from pydub import AudioSegment

from src.app.agents.orchestrator_agent import orchestrator_agent
from src.app.core.config.settings import get_settings

logger = logging.getLogger(__name__)


class VoiceService:
    """
    Voice service for handling speech-to-text, AI response generation, and text-to-speech
    """

    def __init__(self):
        self.groq_client = None
        self.orchestrator_agent = orchestrator_agent
        self.settings = get_settings()
        self._load_models()

    def _load_models(self):
        """Initialize Groq client for both STT and TTS, and orchestrator agent"""
        try:
            # Initialize Groq client for speech-to-text and text-to-speech
            if self.settings.GROQ_API_KEY:
                logger.info("Initializing Groq client...")
                self.groq_client = Groq(api_key=self.settings.GROQ_API_KEY)
                logger.info("✅ Groq client initialized successfully for STT and TTS")
            else:
                logger.warning(
                    "❌ GROQ_API_KEY not found in environment variables"
                )

            # Check if orchestrator agent is available
            if self.orchestrator_agent:
                logger.info("✅ Orchestrator agent initialized successfully")
            else:
                logger.warning("❌ Orchestrator agent not available")

        except Exception as e:
            logger.error("❌ Error loading models: %s", e)

    async def get_available_voices(self) -> List[Dict[str, str]]:
        """
        Get available voices for Groq PlayAI TTS

        Returns:
            List of available voices with their details
        """
        try:
            # Groq PlayAI TTS supported voices
            # English voices for playai-tts model
            english_voices = [
                {"voice_id": "Arista-PlayAI", "name": "Arista", "description": "Conversational and warm", "language": "English"},
                {"voice_id": "Atlas-PlayAI", "name": "Atlas", "description": "Strong and confident", "language": "English"},
                {"voice_id": "Basil-PlayAI", "name": "Basil", "description": "Gentle and soothing", "language": "English"},
                {"voice_id": "Briggs-PlayAI", "name": "Briggs", "description": "Professional and clear", "language": "English"},
                {"voice_id": "Calum-PlayAI", "name": "Calum", "description": "Friendly and approachable", "language": "English"},
                {"voice_id": "Celeste-PlayAI", "name": "Celeste", "description": "Elegant and sophisticated", "language": "English"},
                {"voice_id": "Cheyenne-PlayAI", "name": "Cheyenne", "description": "Energetic and vibrant", "language": "English"},
                {"voice_id": "Chip-PlayAI", "name": "Chip", "description": "Cheerful and upbeat", "language": "English"},
                {"voice_id": "Cillian-PlayAI", "name": "Cillian", "description": "Smooth and articulate", "language": "English"},
                {"voice_id": "Deedee-PlayAI", "name": "Deedee", "description": "Animated and expressive", "language": "English"},
                {"voice_id": "Fritz-PlayAI", "name": "Fritz", "description": "Reliable and steady", "language": "English"},
                {"voice_id": "Gail-PlayAI", "name": "Gail", "description": "Warm and caring", "language": "English"},
                {"voice_id": "Indigo-PlayAI", "name": "Indigo", "description": "Creative and unique", "language": "English"},
                {"voice_id": "Mamaw-PlayAI", "name": "Mamaw", "description": "Wise and nurturing", "language": "English"},
                {"voice_id": "Mason-PlayAI", "name": "Mason", "description": "Strong and dependable", "language": "English"},
                {"voice_id": "Mikail-PlayAI", "name": "Mikail", "description": "Intelligent and thoughtful", "language": "English"},
                {"voice_id": "Mitch-PlayAI", "name": "Mitch", "description": "Casual and relaxed", "language": "English"},
                {"voice_id": "Quinn-PlayAI", "name": "Quinn", "description": "Modern and crisp", "language": "English"},
                {"voice_id": "Thunder-PlayAI", "name": "Thunder", "description": "Powerful and commanding", "language": "English"},
            ]

            # Arabic voices for playai-tts-arabic model
            arabic_voices = [
                {"voice_id": "Ahmad-PlayAI", "name": "Ahmad", "description": "Professional Arabic male voice", "language": "Arabic"},
                {"voice_id": "Amira-PlayAI", "name": "Amira", "description": "Elegant Arabic female voice", "language": "Arabic"},
                {"voice_id": "Khalid-PlayAI", "name": "Khalid", "description": "Confident Arabic male voice", "language": "Arabic"},
                {"voice_id": "Nasser-PlayAI", "name": "Nasser", "description": "Authoritative Arabic male voice", "language": "Arabic"},
            ]

            all_voices = english_voices + arabic_voices

            logger.info("✅ Found %d available voices (%d English, %d Arabic)", 
                       len(all_voices), len(english_voices), len(arabic_voices))
            return all_voices

        except Exception as e:
            logger.error("❌ Error fetching voices: %s", e)
            return []

    async def transcribe_audio(self, audio_data: bytes) -> str:
        """
        Transcribe audio bytes to text using Groq API (Whisper-large-v3-turbo)

        Args:
            audio_data: Raw audio bytes

        Returns:
            Transcribed text
        """
        try:
            if not self.groq_client:
                logger.error("❌ Groq client not initialized")
                return ""

            logger.info("📥 Received audio data: %d bytes", len(audio_data))

            # Create temporary file for audio processing
            with tempfile.NamedTemporaryFile(
                suffix=".webm", delete=False
            ) as temp_file:
                temp_file.write(audio_data)
                temp_filename = temp_file.name

            logger.info("💾 Saved audio to temp file: %s", temp_filename)

            try:
                # Try to load the audio file with pydub
                try:
                    audio_segment = AudioSegment.from_file(temp_filename)
                    logger.info(
                        "🎵 Audio loaded: %dms, %d channels, %dHz",
                        len(audio_segment),
                        audio_segment.channels,
                        audio_segment.frame_rate,
                    )
                except Exception as e:
                    logger.error("❌ Error loading audio with pydub: %s", e)
                    # Try loading as WebM specifically
                    audio_segment = AudioSegment.from_file(temp_filename, format="webm")
                    logger.info("🎵 Audio loaded as WebM: %dms", len(audio_segment))

                # Ensure audio is at least 1 second long
                if len(audio_segment) < 1000:  # Less than 1 second
                    logger.warning("⚠️  Audio too short: %dms", len(audio_segment))
                    return ""

                # Process audio for optimal transcription
                processed_filename = self._process_audio_segment(
                    audio_segment, temp_filename
                )
                
                # Transcribe using Groq API
                transcribed_text = await self._transcribe_with_groq(processed_filename)

                return transcribed_text

            finally:
                # Clean up temporary files
                self._cleanup_temp_files(temp_filename, locals())

        except Exception as e:
            logger.error("❌ Error transcribing audio: %s", e)
            logger.error("Full traceback: %s", traceback.format_exc())
            return ""

    def _process_audio_segment(
        self, audio_segment: AudioSegment, temp_filename: str
    ) -> str:
        """Process audio segment for optimal transcription."""
        # Convert to mono and set appropriate sample rate
        audio_segment = audio_segment.set_channels(1)
        audio_segment = audio_segment.set_frame_rate(16000)

        # Remove silence and normalize
        audio_segment = audio_segment.strip_silence(silence_thresh=-40)
        audio_segment = audio_segment.normalize()

        # Export to WAV file for Whisper (Whisper works best with WAV)
        processed_filename = temp_filename.replace(".webm", "_processed.wav")
        audio_segment.export(
            processed_filename,
            format="wav",
            parameters=["-ar", "16000", "-ac", "1"],
        )

        logger.info("🔄 Processed audio saved to: %s", processed_filename)
        return processed_filename

    async def _transcribe_with_groq(self, audio_file_path: str) -> str:
        """Transcribe audio file using Groq API."""
        try:
            logger.info("🎯 Starting Groq transcription...")
            
            # Read the audio file
            with open(audio_file_path, "rb") as audio_file:
                # Create transcription using Groq's Whisper-large-v3-turbo
                loop = asyncio.get_event_loop()
                transcription = await loop.run_in_executor(
                    None,
                    lambda: self.groq_client.audio.transcriptions.create(
                        file=("audio.wav", audio_file.read(), "audio/wav"),
                        model="whisper-large-v3-turbo",
                        language="en",  # Force English for better accuracy
                        response_format="text"
                    )
                )
                
                transcribed_text = transcription.strip()
                logger.info("🎙️ Transcribed: '%s'", transcribed_text)

                # Check if transcription is meaningful
                if len(transcribed_text) < 2:
                    logger.warning("⚠️  Transcription too short, likely silence or noise")
                    return ""

                return transcribed_text

        except Exception as e:
            logger.error("❌ Groq transcription failed: %s", e)
            return ""

    def _cleanup_temp_files(self, temp_filename: str, local_vars: dict):
        """Clean up temporary files."""
        try:
            os.unlink(temp_filename)
            if "processed_filename" in local_vars:
                os.unlink(local_vars["processed_filename"])
        except Exception as cleanup_error:
            logger.warning("⚠️  Error cleaning up temp files: %s", cleanup_error)

    async def generate_response(self, text: str, user_id: Optional[str] = None) -> str:
        """
        Generate AI response using OrchestratorAgent

        Args:
            text: Input text from user
            user_id: Optional user ID for context

        Returns:
            AI generated response
        """
        try:
            if not self.orchestrator_agent:
                return "Sorry, I'm not properly configured to generate responses."

            logger.info("🤖 Sending to OrchestratorAgent: '%s'", text)

            # Use the orchestrator agent to handle the query
            response = await self.orchestrator_agent.handle_query(
                message=text, user_id=user_id
            )

            logger.info("🤖 OrchestratorAgent Response: %s", response)

            return response

        except Exception as e:
            logger.error("❌ Error generating response with OrchestratorAgent: %s", e)
            logger.error("Full traceback: %s", traceback.format_exc())
            return "Sorry, I encountered an error while generating a response."

    async def text_to_speech(
        self, text: str, voice_id: str = "Fritz-PlayAI"
    ) -> bytes:
        """
        Convert text to speech using Groq PlayAI TTS

        Args:
            text: Text to convert to speech
            voice_id: PlayAI voice ID (default: Fritz-PlayAI - a reliable and steady voice)

        Returns:
            Audio bytes in WAV format
        """
        try:
            if not self.groq_client:
                logger.error("❌ Groq client not initialized")
                return b""

            # Clean the text for better speech synthesis
            cleaned_text = self._clean_markdown_for_speech(text)

            logger.info("🔊 Converting text to speech: '%s' with voice '%s'", 
                       cleaned_text[:100], voice_id)

            # Determine model based on voice
            model = "playai-tts-arabic" if voice_id.endswith("-PlayAI") and voice_id.startswith(("Ahmad", "Amira", "Khalid", "Nasser")) else "playai-tts"

            # Generate audio using Groq PlayAI TTS
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.groq_client.audio.speech.create(
                    model=model,
                    input=cleaned_text,
                    voice=voice_id,
                    response_format="wav"
                ),
            )

            # Get audio bytes from response
            audio_bytes = b""
            if hasattr(response, 'content'):
                audio_bytes = response.content
            elif hasattr(response, 'read'):
                audio_bytes = response.read()
            else:
                # If response is iterable (streaming), collect all chunks
                for chunk in response:
                    audio_bytes += chunk

            logger.info("✅ Successfully generated %d bytes of audio using Groq TTS", len(audio_bytes))
            return audio_bytes

        except Exception as e:
            logger.error("❌ Error converting text to speech with Groq: %s", e)
            logger.error("Full traceback: %s", traceback.format_exc())
            return b""

    def preprocess_audio_chunk(self, audio_chunk: bytes) -> bytes:
        """
        Preprocess audio chunk for better transcription accuracy

        Args:
            audio_chunk: Raw audio chunk bytes

        Returns:
            Processed audio bytes
        """
        try:
            # Load audio from bytes
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_chunk))

            # Apply preprocessing
            # 1. Convert to mono
            audio_segment = audio_segment.set_channels(1)

            # 2. Normalize sample rate to 16kHz (optimal for Whisper)
            audio_segment = audio_segment.set_frame_rate(16000)

            # 3. Normalize volume
            audio_segment = audio_segment.normalize()

            # 4. Remove silence from beginning and end
            audio_segment = audio_segment.strip_silence(silence_thresh=-40)

            # Convert back to bytes
            buffer = io.BytesIO()
            audio_segment.export(buffer, format="wav")
            return buffer.getvalue()

        except Exception as e:
            logger.error("❌ Error preprocessing audio chunk: %s", e)
            return audio_chunk  # Return original if preprocessing fails

    def _clean_markdown_for_speech(self, text: str) -> str:
        """
        Clean markdown formatting and other text artifacts for better speech synthesis

        Args:
            text: Raw text that may contain markdown

        Returns:
            Cleaned text suitable for speech synthesis
        """
        # Remove markdown headers
        text = re.sub(r"#{1,6}\s+", "", text)

        # Remove markdown links - keep just the text
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)

        # Remove markdown emphasis (bold, italic)
        text = re.sub(r"\*\*([^\*]+)\*\*", r"\1", text)
        text = re.sub(r"\*([^\*]+)\*", r"\1", text)
        text = re.sub(r"__([^_]+)__", r"\1", text)
        text = re.sub(r"_([^_]+)_", r"\1", text)

        # Remove markdown code blocks
        text = re.sub(r"```[^`]*```", "code block", text)
        text = re.sub(r"`([^`]+)`", r"\1", text)

        # Remove markdown lists
        text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)

        # Remove excessive whitespace
        text = re.sub(r"\n\s*\n", ". ", text)
        text = re.sub(r"\s+", " ", text)

        # Remove special characters that might cause issues
        text = re.sub(r"[^\w\s.,!?;:()\-']", "", text)

        # Ensure proper sentence endings
        text = re.sub(r"([.!?])\s*([A-Z])", r"\1 \2", text)

        # Limit text length for TTS (Groq has 10K character limit)
        if len(text) > 10000:
            text = text[:9997] + "..."

        return text.strip()

    async def process_voice_message(
        self, audio_data: bytes, user_id: Optional[str] = None, voice_id: str = "Fritz-PlayAI"
    ) -> Tuple[str, bytes]:
        """
        Process a complete voice message: transcribe -> generate response -> synthesize

        Args:
            audio_data: Raw audio bytes from user
            user_id: Optional user ID for context
            voice_id: Voice to use for response synthesis

        Returns:
            Tuple of (transcribed_text, response_audio_bytes)
        """
        try:
            logger.info("🎤 Starting voice message processing...")

            # Step 1: Transcribe audio to text
            transcribed_text = await self.transcribe_audio(audio_data)

            if not transcribed_text:
                logger.warning("⚠️  No transcription available")
                return "", b""

            logger.info("📝 Transcribed: %s", transcribed_text)

            # Step 2: Generate AI response
            response_text = await self.generate_response(transcribed_text, user_id)

            if not response_text:
                logger.warning("⚠️  No response generated")
                return transcribed_text, b""

            logger.info("🤖 Generated response: %s", response_text[:100])

            # Step 3: Convert response to speech using Groq TTS
            response_audio = await self.text_to_speech(response_text, voice_id)

            if not response_audio:
                logger.warning("⚠️  No audio generated")
                return transcribed_text, b""

            logger.info(
                "✅ Voice message processing complete - %d audio bytes generated",
                len(response_audio),
            )

            return transcribed_text, response_audio

        except Exception as e:
            logger.error("❌ Error processing voice message: %s", e)
            logger.error("Full traceback: %s", traceback.format_exc())
            return "", b""

    def _get_fallback_response_audio(self) -> bytes:
        """Generate fallback audio response for errors."""
        try:
            fallback_text = (
                "I'm sorry, I couldn't process your request properly. "
                "Please try again or type your question instead."
            )
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.text_to_speech(fallback_text))
        except Exception as e:
            logger.error("❌ Error generating fallback response: %s", e)
            return b""


# Global voice service instance
voice_service = VoiceService()
