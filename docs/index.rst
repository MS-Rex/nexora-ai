Nexora AI Documentation
========================

Welcome to Nexora AI's documentation. This is a comprehensive guide for the Nexora Campus Copilot API.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api/index
   modules

Overview
--------

Nexora AI is a campus-focused AI assistant that provides intelligent responses to university-related queries. The system includes:

* **Chat API**: Enhanced chat functionality with content moderation
* **Conversation Management**: Track and manage conversation history
* **Health Monitoring**: Service health and status endpoints
* **Voice Integration**: Voice-to-text and text-to-voice capabilities
* **Content Moderation**: Automatic filtering of inappropriate content

Features
--------

* 🤖 **AI-Powered Chat**: University-focused conversational AI
* 🛡️ **Content Moderation**: Automatic filtering of inappropriate content
* 📝 **Conversation History**: Track and retrieve conversation history
* 🎤 **Voice Support**: Voice input and output capabilities
* 🔐 **API Authentication**: Secure API key-based authentication
* 📊 **Health Monitoring**: Service status and monitoring endpoints

Quick Start
-----------

1. Install dependencies::

    uv sync

2. Set up environment variables::

    cp .env.example .env
    # Edit .env with your configuration

3. Run the development server::

    uvicorn src.app.main:app --reload

4. Access the API documentation at ``http://localhost:8000/docs``

API Reference
-------------

The API is organized into the following main sections:

* :doc:`api/v1/endpoints/chat` - Chat functionality
* :doc:`api/v1/endpoints/conversations` - Conversation management
* :doc:`api/v1/endpoints/health` - Health monitoring
* :doc:`api/v1/endpoints/voice` - Voice capabilities
* :doc:`api/v1/endpoints/moderation` - Content moderation

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search` 