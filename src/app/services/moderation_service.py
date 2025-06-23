"""
Content moderation service using OpenAI's moderation API with keyword fallback.

This module provides functionality to check user-generated content for policy violations
including hate speech, harassment, violence, sexual content, and self-harm.
"""

import logging
from typing import Optional

import httpx
from pydantic import BaseModel, Field

from src.app.core.config.settings import settings

logger = logging.getLogger(__name__)


class ModerationCategory(BaseModel):
    """Moderation category result."""

    hate: bool = False
    hate_threatening: bool = False
    harassment: bool = False
    harassment_threatening: bool = False
    self_harm: bool = False
    self_harm_intent: bool = False
    self_harm_instructions: bool = False
    sexual: bool = False
    sexual_minors: bool = False
    violence: bool = False
    violence_graphic: bool = False


class ModerationResult(BaseModel):
    """Moderation check result."""

    flagged: bool = Field(..., description="Whether content was flagged")
    categories: ModerationCategory = Field(
        ..., description="Detailed category breakdown"
    )
    reason: Optional[str] = Field(
        None, description="Human-readable reason for flagging"
    )
    confidence: Optional[float] = Field(
        None, description="Confidence score if available"
    )


class ModerationService:
    """Service for content moderation using OpenAI's moderation API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, "OPENAI_API_KEY", None)
        self.base_url = "https://api.openai.com/v1/moderations"

        # Fallback keywords for basic filtering if OpenAI API is unavailable
        self.flagged_keywords = {
            "hate": ["hate", "racist", "nazi", "white supremacy"],
            "violence": ["kill", "murder", "bomb", "terrorist"],
            "sexual": ["Fuck", "Tits", "Porn", "Nude"],
            "harassment": ["harass", "bully", "threaten"],
            "self_harm": ["suicide", "self harm", "cut myself"],
        }

    async def moderate_content(self, content: str) -> ModerationResult:
        """
        Check content for policy violations.

        Args:
            content: Text content to moderate

        Returns:
            ModerationResult with flagging status and details
        """
        try:
            # Try OpenAI moderation API first (most robust)
            if self.api_key:
                return await self._openai_moderation(content)

            logger.warning(
                "OpenAI API key not configured, falling back to keyword filtering"
            )
            return await self._keyword_moderation(content)

        except Exception as e:
            logger.error("Moderation service error: %s", e)
            logger.warning(
                "Moderation failed for content (allowing): %s...", content[:100]
            )
            return ModerationResult(
                flagged=False,
                categories=ModerationCategory(),
                reason="Moderation service unavailable",
            )

    async def _openai_moderation(self, content: str) -> ModerationResult:
        """Use OpenAI's moderation API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {"input": content}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url, headers=headers, json=payload, timeout=10.0
            )

            if response.status_code != 200:
                logger.error("OpenAI moderation API error: %s", response.status_code)
                return await self._keyword_moderation(content)

            data = response.json()
            result = data["results"][0]

            # Convert OpenAI categories to our format
            categories = ModerationCategory(
                hate=result["categories"].get("hate", False),
                hate_threatening=result["categories"].get("hate/threatening", False),
                harassment=result["categories"].get("harassment", False),
                harassment_threatening=result["categories"].get(
                    "harassment/threatening", False
                ),
                self_harm=result["categories"].get("self-harm", False),
                self_harm_intent=result["categories"].get("self-harm/intent", False),
                self_harm_instructions=result["categories"].get(
                    "self-harm/instructions", False
                ),
                sexual=result["categories"].get("sexual", False),
                sexual_minors=result["categories"].get("sexual/minors", False),
                violence=result["categories"].get("violence", False),
                violence_graphic=result["categories"].get("violence/graphic", False),
            )

            # Generate human-readable reason
            reason = None
            if result["flagged"]:
                flagged_cats = [
                    cat for cat, flagged in result["categories"].items() if flagged
                ]
                reason = f"Content flagged for: {', '.join(flagged_cats)}"

            return ModerationResult(
                flagged=result["flagged"], categories=categories, reason=reason
            )

    async def _keyword_moderation(self, content: str) -> ModerationResult:
        """Fallback keyword-based moderation."""
        content_lower = content.lower()
        flagged_categories = []

        for category, keywords in self.flagged_keywords.items():
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    flagged_categories.append(category)
                    break

        flagged = len(flagged_categories) > 0
        reason = (
            f"Content flagged for: {', '.join(flagged_categories)}" if flagged else None
        )

        # Create categories object
        categories = ModerationCategory(
            hate="hate" in flagged_categories,
            violence="violence" in flagged_categories,
            sexual="sexual" in flagged_categories,
            harassment="harassment" in flagged_categories,
            self_harm="self_harm" in flagged_categories,
        )

        return ModerationResult(
            flagged=flagged,
            categories=categories,
            reason=reason,
            confidence=0.5 if flagged else 0.0,  # Low confidence for keyword matching
        )

    def get_moderation_response_message(self, result: ModerationResult) -> str:
        """
        Generate appropriate response message for flagged content.

        Args:
            result: Moderation result

        Returns:
            Human-friendly response message
        """
        if not result.flagged:
            return ""

        # Campus-appropriate response for Nexora
        return (
            "I'm sorry, but I cannot process messages that may contain inappropriate content. "
            "As Nexora Campus Copilot, I'm designed to help with university-related questions "
            "and maintain a respectful academic environment. Please rephrase your question "
            "in a way that focuses on campus resources, events, departments, or academic support."
        )


# Global moderation service instance
moderation_service = ModerationService()
