import os
import io
import tempfile
import asyncio
import logging
import re
from typing import Optional, Tuple
import numpy as np
import whisper
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from pydub import AudioSegment
from pydub.silence import split_on_silence
import soundfile as sf
import librosa
from src.app.agents.orchestrator_agent import orchestrator_agent
from src.app.core.config.settings import get_settings

logger = logging.getLogger(__name__)


class VoiceService:
    """
    Voice service for handling speech-to-text, AI response generation, and text-to-speech
    """

    def __init__(self):
        self.whisper_model = None
        self.orchestrator_agent = orchestrator_agent
        self.settings = get_settings()
        self.elevenlabs_client = None
        self._load_models()

    def _load_models(self):
        """Load Whisper model, initialize orchestrator agent, and setup ElevenLabs client"""
        try:
            # Load Whisper model (using base model for balance of speed/accuracy)
            logger.info("Loading Whisper model...")
            self.whisper_model = whisper.load_model("small")
            logger.info("✅ Whisper model loaded successfully")

            # Initialize ElevenLabs client
            if self.settings.ELEVEN_LABS_API_KEY:
                logger.info("Initializing ElevenLabs client...")
                self.elevenlabs_client = ElevenLabs(
                    api_key=self.settings.ELEVEN_LABS_API_KEY
                )
                logger.info("✅ ElevenLabs client initialized successfully")
            else:
                logger.warning("❌ ELEVEN_LABS_API_KEY not found in environment variables")

            # Check if orchestrator agent is available
            if self.orchestrator_agent:
                logger.info("✅ Orchestrator agent initialized successfully")
            else:
                logger.warning("❌ Orchestrator agent not available")

        except Exception as e:
            logger.error(f"❌ Error loading models: {e}")

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
                None, lambda: self.elevenlabs_client.voices.search()
            )
            
            voice_list = []
            for voice in voices.voices:
                voice_list.append({
                    "voice_id": voice.voice_id,
                    "name": voice.name,
                    "description": getattr(voice, 'description', 'No description'),
                    "category": getattr(voice, 'category', 'Unknown')
                })
            
            logger.info(f"✅ Found {len(voice_list)} available voices")
            return voice_list

        except Exception as e:
            logger.error(f"❌ Error fetching voices: {e}")
            return []

    async def transcribe_audio(self, audio_data: bytes) -> str:
        """
        Transcribe audio bytes to text using Whisper

        Args:
            audio_data: Raw audio bytes

        Returns:
            Transcribed text
        """
        try:
            logger.info(f"📥 Received audio data: {len(audio_data)} bytes")

            # Create temporary file for audio processing - use generic extension first
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_filename = temp_file.name

            logger.info(f"💾 Saved audio to temp file: {temp_filename}")

            try:
                # Try to load the audio file with pydub
                try:
                    audio_segment = AudioSegment.from_file(temp_filename)
                    logger.info(
                        f"🎵 Audio loaded: {len(audio_segment)}ms, {audio_segment.channels} channels, {audio_segment.frame_rate}Hz"
                    )
                except Exception as e:
                    logger.error(f"❌ Error loading audio with pydub: {e}")
                    # Try loading as WebM specifically
                    audio_segment = AudioSegment.from_file(temp_filename, format="webm")
                    logger.info(f"🎵 Audio loaded as WebM: {len(audio_segment)}ms")

                # Ensure audio is at least 1 second long
                if len(audio_segment) < 1000:  # Less than 1 second
                    logger.warning(f"⚠️  Audio too short: {len(audio_segment)}ms")
                    return ""

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

                logger.info(f"🔄 Processed audio saved to: {processed_filename}")

                # Transcribe using Whisper
                logger.info("🎯 Starting Whisper transcription...")
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, self._transcribe_with_whisper, processed_filename
                )

                transcribed_text = result["text"].strip()
                logger.info(f"🎙️ Transcribed: '{transcribed_text}'")

                # Check if transcription is meaningful
                if len(transcribed_text) < 2:
                    logger.warning(
                        "⚠️  Transcription too short, likely silence or noise"
                    )
                    return ""

                return transcribed_text

            finally:
                # Clean up temporary files
                try:
                    os.unlink(temp_filename)
                    if "processed_filename" in locals():
                        os.unlink(processed_filename)
                except Exception as cleanup_error:
                    logger.warning(f"⚠️  Error cleaning up temp files: {cleanup_error}")

        except Exception as e:
            logger.error(f"❌ Error transcribing audio: {e}")
            import traceback

            logger.error(f"Full traceback: {traceback.format_exc()}")
            return ""

    def _transcribe_with_whisper(self, audio_file_path: str) -> dict:
        """Helper method to run Whisper transcription synchronously"""
        try:
            result = self.whisper_model.transcribe(
                audio_file_path,
                language="en",  # Force English for better accuracy
                task="transcribe",
                verbose=False,
            )
            return result
        except Exception as e:
            logger.error(f"❌ Whisper transcription failed: {e}")
            return {"text": ""}

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

            logger.info(f"🤖 Sending to OrchestratorAgent: '{text}'")

            # Use the orchestrator agent to handle the query
            response = await self.orchestrator_agent.handle_query(
                message=text, user_id=user_id
            )

            logger.info(f"🤖 OrchestratorAgent Response: {response}")

            return response

        except Exception as e:
            logger.error(f"❌ Error generating response with OrchestratorAgent: {e}")
            import traceback

            logger.error(f"Full traceback: {traceback.format_exc()}")
            return "Sorry, I encountered an error while generating a response."

    async def text_to_speech(self, text: str, voice_id: str = "EXAVITQu4vr4xnSDxMaL") -> bytes:
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

            # Detect if text likely contains markdown and clean it if needed
            if any(
                marker in text for marker in ["#", "```", "`", "*", "_", "[", "]", "->"]
            ):
                logger.info("📝 Detected markdown in text for speech, cleaning...")
                text = self._clean_markdown_for_speech(text)

            logger.info(f"🔊 Generating speech with ElevenLabs for: {text[:50]}...")

            # Generate speech using ElevenLabs
            loop = asyncio.get_event_loop()
            audio_generator = await loop.run_in_executor(
                None, 
                lambda: self.elevenlabs_client.text_to_speech.convert(
                    text=text,
                    voice_id=voice_id,
                    model_id="eleven_multilingual_v2",
                    voice_settings=VoiceSettings(
                        stability=0.71,
                        similarity_boost=0.5,
                        style=0.0,
                        use_speaker_boost=True,
                    ),
                    output_format="mp3_44100_128",
                )
            )

            # Convert generator to bytes
            audio_bytes = b"".join(audio_generator)
            logger.info(f"✅ Generated {len(audio_bytes)} bytes of audio with ElevenLabs")

            return audio_bytes

        except Exception as e:
            logger.error(f"❌ Error generating speech with ElevenLabs: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # Fallback to a simple error message
            logger.info("🔄 Attempting to generate simple fallback audio...")
            try:
                # Create a simple fallback message
                fallback_text = "Sorry, there was an issue generating speech."
                # For now, return empty bytes - you could implement a basic TTS fallback here if needed
                return b""
            except Exception as fallback_error:
                logger.error(f"❌ Fallback audio generation also failed: {fallback_error}")
                return b""

    def preprocess_audio_chunk(self, audio_chunk: bytes) -> bytes:
        """
        Preprocess audio chunk for better transcription

        Args:
            audio_chunk: Raw audio bytes

        Returns:
            Processed audio bytes
        """
        try:
            logger.info(f"🔄 Preprocessing audio chunk: {len(audio_chunk)} bytes")

            # Try to load audio with different formats
            audio_segment = None
            for fmt in ["webm", "wav", "mp3", "m4a"]:
                try:
                    audio_segment = AudioSegment.from_file(
                        io.BytesIO(audio_chunk), format=fmt
                    )
                    logger.info(f"✅ Successfully loaded audio as {fmt}")
                    break
                except Exception as e:
                    logger.debug(f"Failed to load as {fmt}: {e}")
                    continue

            if audio_segment is None:
                logger.error("❌ Could not load audio in any supported format")
                return audio_chunk

            # Basic audio validation
            if len(audio_segment) < 500:  # Less than 0.5 seconds
                logger.warning(
                    f"⚠️  Audio too short for preprocessing: {len(audio_segment)}ms"
                )
                return audio_chunk

            # Remove silence at the beginning and end (more aggressive)
            audio_segment = audio_segment.strip_silence(
                silence_thresh=-35, silence_chunk_len=300
            )

            # Normalize audio levels
            audio_segment = audio_segment.normalize()

            # Apply some basic noise reduction by removing very quiet parts
            # This helps with browser audio capture issues
            if audio_segment.max_dBFS < -30:  # Very quiet audio
                logger.warning("⚠️  Audio appears very quiet, boosting volume")
                audio_segment = audio_segment + (20 - audio_segment.max_dBFS)

            # Convert back to bytes in WAV format for better compatibility
            output_buffer = io.BytesIO()
            audio_segment.export(
                output_buffer, format="wav", parameters=["-ar", "16000", "-ac", "1"]
            )
            output_buffer.seek(0)

            processed_bytes = output_buffer.getvalue()
            logger.info(f"✅ Audio preprocessed: {len(processed_bytes)} bytes")

            return processed_bytes

        except Exception as e:
            logger.error(f"❌ Error preprocessing audio: {e}")
            import traceback

            logger.error(f"Full traceback: {traceback.format_exc()}")
            return audio_chunk

    def _clean_markdown_for_speech(self, text: str) -> str:
        """
        Clean markdown formatting for better speech synthesis

        Args:
            text: Text that may contain markdown formatting

        Returns:
            Cleaned text suitable for speech synthesis
        """
        # Remove code blocks (```...```)
        text = re.sub(r"```[\s\S]*?```", "", text)

        # Remove inline code blocks (`...`)
        text = re.sub(r"`([^`]*)`", r"\1", text)

        # Remove headers (# Header)
        text = re.sub(r"^\s*#{1,6}\s+(.*?)$", r"\1", text, flags=re.MULTILINE)

        # Convert links [text](url) to just text
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

        # Remove bold and italic markers
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
        text = re.sub(r"__(.*?)__", r"\1", text)
        text = re.sub(r"\*(.*?)\*", r"\1", text)
        text = re.sub(r"_(.*?)_", r"\1", text)

        # Remove bullet points and numbered lists
        text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)

        # Remove horizontal rules
        text = re.sub(r"^\s*[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)

        # Remove HTML tags
        text = re.sub(r"<[^>]*>", "", text)

        # Remove blockquote markers
        text = re.sub(r"^\s*>\s+", "", text, flags=re.MULTILINE)

        # Collapse multiple blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    async def process_voice_message(
        self, audio_data: bytes, user_id: Optional[str] = None
    ) -> Tuple[str, bytes]:
        """
        Complete voice-to-voice processing pipeline

        Args:
            audio_data: Raw audio bytes from user
            user_id: Optional user ID for context

        Returns:
            Tuple of (transcribed_text, response_audio_bytes)
        """
        try:
            logger.info(
                f"🚀 Starting voice processing pipeline with {len(audio_data)} bytes for user: {user_id}"
            )

            # Step 1: Preprocess audio
            logger.info("📝 Step 1: Preprocessing audio...")
            processed_audio = self.preprocess_audio_chunk(audio_data)

            # Step 2: Transcribe speech to text
            logger.info("📝 Step 2: Transcribing audio to text...")
            transcribed_text = await self.transcribe_audio(processed_audio)

            if not transcribed_text:
                logger.warning("⚠️  No text transcribed from audio")
                error_msg = "Sorry, I couldn't understand your message. Please try speaking more clearly and try again."
                error_audio = await self.text_to_speech(error_msg)
                return "", error_audio

            logger.info(f"✅ Successfully transcribed: '{transcribed_text}'")

            # Step 3: Generate AI response using OrchestratorAgent
            logger.info("📝 Step 3: Generating AI response via OrchestratorAgent...")
            response_text = await self.generate_response(transcribed_text, user_id)

            # Clean markdown from response text for voice output only
            cleaned_response_text = self._clean_markdown_for_speech(response_text)
            logger.info(
                f"✅ Cleaned markdown for speech: original length {len(response_text)}, cleaned length {len(cleaned_response_text)}"
            )

            # Step 4: Convert response to speech
            logger.info("📝 Step 4: Converting response to speech...")
            response_audio = await self.text_to_speech(cleaned_response_text)

            logger.info("🎉 Voice processing pipeline completed successfully!")
            return transcribed_text, response_audio

        except Exception as e:
            logger.error(f"❌ Error in voice processing pipeline: {e}")
            import traceback

            logger.error(f"Full traceback: {traceback.format_exc()}")
            error_msg = "Sorry, I encountered an error processing your message."
            error_audio = await self.text_to_speech(error_msg)
            return "", error_audio


# Global voice service instance
voice_service = VoiceService()
