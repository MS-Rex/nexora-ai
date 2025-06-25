import json
import logging
import base64
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from src.app.services.voice_service import voice_service

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"🔗 Client {client_id} connected")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"❌ Client {client_id} disconnected")

    async def send_message(self, client_id: str, message: Dict[str, Any]):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"❌ Error sending message to {client_id}: {e}")
                self.disconnect(client_id)


manager = ConnectionManager()


@router.websocket("/voice-chat/{client_id}")
async def voice_chat_websocket(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time voice-to-voice communication

    Message format:
    {
        "type": "audio_chunk",
        "data": "<base64_encoded_audio>",
        "format": "webm" | "wav" | "mp3",
        "sample_rate": 44100,
        "channels": 1
    }

    Response format:
    {
        "type": "transcription" | "response_audio" | "error",
        "data": "<base64_encoded_response_audio>",
        "text": "<transcribed_or_response_text>",
        "message": "<error_message>"
    }
    """
    await manager.connect(websocket, client_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                await process_voice_message(websocket, client_id, message)

            except json.JSONDecodeError:
                await manager.send_message(
                    client_id, {"type": "error", "message": "Invalid JSON format"}
                )
            except Exception as e:
                logger.error(f"❌ Error processing message from {client_id}: {e}")
                await manager.send_message(
                    client_id,
                    {"type": "error", "message": f"Error processing message: {str(e)}"},
                )

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"❌ WebSocket error for {client_id}: {e}")
        manager.disconnect(client_id)


async def process_voice_message(
    websocket: WebSocket, client_id: str, message: Dict[str, Any]
):
    """Process incoming voice message"""
    message_type = message.get("type")

    if message_type == "audio_chunk":
        await handle_audio_chunk(websocket, client_id, message)
    elif message_type == "ping":
        await manager.send_message(client_id, {"type": "pong"})
    else:
        await manager.send_message(
            client_id,
            {"type": "error", "message": f"Unknown message type: {message_type}"},
        )


async def handle_audio_chunk(
    websocket: WebSocket, client_id: str, message: Dict[str, Any]
):
    """Handle audio chunk processing"""
    try:
        # Extract audio data
        audio_data_b64 = message.get("data")
        if not audio_data_b64:
            await manager.send_message(
                client_id, {"type": "error", "message": "No audio data provided"}
            )
            return

        # Decode base64 audio data
        try:
            audio_bytes = base64.b64decode(audio_data_b64)
        except Exception as e:
            await manager.send_message(
                client_id,
                {"type": "error", "message": f"Invalid base64 audio data: {str(e)}"},
            )
            return

        logger.info(
            f"🎤 Processing audio chunk from {client_id} ({len(audio_bytes)} bytes)"
        )

        # Send acknowledgment
        await manager.send_message(
            client_id,
            {"type": "processing", "message": "Processing your voice message..."},
        )

        # Process voice message through the pipeline with client_id as user_id
        transcribed_text, response_audio = await voice_service.process_voice_message(
            audio_bytes, user_id=client_id
        )

        # Send transcription result
        if transcribed_text:
            await manager.send_message(
                client_id, {"type": "transcription", "text": transcribed_text}
            )

        # Send response audio
        if response_audio:
            response_audio_b64 = base64.b64encode(response_audio).decode("utf-8")
            await manager.send_message(
                client_id,
                {"type": "response_audio", "data": response_audio_b64, "format": "wav"},
            )

        logger.info(f"✅ Voice processing completed for {client_id}")

    except Exception as e:
        logger.error(f"❌ Error handling audio chunk for {client_id}: {e}")
        await manager.send_message(
            client_id, {"type": "error", "message": f"Error processing audio: {str(e)}"}
        )


@router.get("/voice-status")
async def voice_status():
    """Get voice service status"""
    try:
        return {
            "status": "active",
            "groq_client_initialized": voice_service.groq_client is not None,
            "groq_api_key_configured": voice_service.settings.GROQ_API_KEY is not None,
            "orchestrator_agent_configured": voice_service.orchestrator_agent is not None,
            "active_connections": len(manager.active_connections),
            "message": "Voice-to-voice service is running with Groq STT/TTS and OrchestratorAgent",
        }
    except Exception as e:
        logger.error(f"❌ Error getting voice status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
