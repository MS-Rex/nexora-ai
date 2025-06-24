"""
Voice service for handling speech-to-text, AI response generation, and text-to-speech.

This module provides comprehensive voice interaction functionality using Groq API 
(Whisper-large-v3-turbo) for speech recognition, orchestrator agent for response 
generation, and ElevenLabs for text-to-speech synthesis.
"""

import asyncio
import io
import logging
import os
import re
import tempfile
import traceback
from typing import Optional, Tuple

from groq import Groq
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
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
        self.elevenlabs_client = None
        self._load_models()

    def _load_models(self):
        """Initialize Groq client, orchestrator agent, and setup ElevenLabs client"""
        try:
            # Initialize Groq client for speech-to-text
            if self.settings.GROQ_API_KEY:
                logger.info("Initializing Groq client...")
                self.groq_client = Groq(api_key=self.settings.GROQ_API_KEY)
                logger.info("✅ Groq client initialized successfully")
            else:
                logger.warning(
                    "❌ GROQ_API_KEY not found in environment variables"
                )

            # Initialize ElevenLabs client
            if self.settings.ELEVEN_LABS_API_KEY:
                logger.info("Initializing ElevenLabs client...")
                self.elevenlabs_client = ElevenLabs(
                    api_key=self.settings.ELEVEN_LABS_API_KEY
                )
                logger.info("✅ ElevenLabs client initialized successfully")
            else:
                logger.warning(
                    "❌ ELEVEN_LABS_API_KEY not found in environment variables"
                )

            # Check if orchestrator agent is available
            if self.orchestrator_agent:
                logger.info("✅ Orchestrator agent initialized successfully")
            else:
                logger.warning("❌ Orchestrator agent not available")

        except Exception as e:
            logger.error("❌ Error loading models: %s", e)

    async def get_available_voices(self) -> list:
        """
        Get available voices from ElevenLabs

        Returns:
            List of available voices
        """
        try:
            if not self.elevenlabs_client:
                logger.error("❌ ElevenLabs client not initialized")
                return []

            loop = asyncio.get_event_loop()
            voices = await loop.run_in_executor(
                None, self.elevenlabs_client.voices.search
            )

            voice_list = []
            for voice in voices.voices:
                voice_list.append(
                    {
                        "voice_id": voice.voice_id,
                        "name": voice.name,
                        "description": getattr(voice, "description", "No description"),
                        "category": getattr(voice, "category", "Unknown"),
                    }
                )

            logger.info("✅ Found %d available voices", len(voice_list))
            return voice_list

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
        self, text: str, voice_id: str = "EXAVITQu4vr4xnSDxMaL"
    ) -> bytes:
        """
        Convert text to speech using ElevenLabs

        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID (default: Bella - a pleasant female voice)

        Returns:
            Audio bytes in MP3 format
        """
        try:
            if not self.elevenlabs_client:
                logger.error("❌ ElevenLabs client not initialized")
                return b""

            # Clean the text for better speech synthesis
            cleaned_text = self._clean_markdown_for_speech(text)

            logger.info("🔊 Converting text to speech: '%s'", cleaned_text[:100])

            # Configure voice settings for natural speech
            voice_settings = VoiceSettings(
                stability=0.71, similarity_boost=0.75, style=0.0, use_speaker_boost=True
            )

            # Generate audio
            loop = asyncio.get_event_loop()
            audio_generator = await loop.run_in_executor(
                None,
                lambda: self.elevenlabs_client.text_to_speech.convert(
                    text=cleaned_text,
                    voice_id=voice_id,
                    voice_settings=voice_settings,
                    model_id="eleven_multilingual_v2",
                ),
            )

            # Convert generator to bytes
            audio_bytes = b""
            for chunk in audio_generator:
                audio_bytes += chunk

            logger.info("✅ Successfully generated %d bytes of audio", len(audio_bytes))
            return audio_bytes

        except Exception as e:
            logger.error("❌ Error converting text to speech: %s", e)
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

        return text.strip()

    async def process_voice_message(
        self, audio_data: bytes, user_id: Optional[str] = None
    ) -> Tuple[str, bytes]:
        """
        Process a complete voice message: transcribe -> generate response -> synthesize

        Args:
            audio_data: Raw audio bytes from user
            user_id: Optional user ID for context

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

            # Step 3: Convert response to speech
            response_audio = await self.text_to_speech(response_text)

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
