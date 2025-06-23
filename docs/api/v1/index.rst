API Version 1
=============

The v1 API provides the core functionality for the Nexora Campus Copilot system.

.. toctree::
   :maxdepth: 2
   :caption: Endpoints:

   endpoints/chat
   endpoints/conversations
   endpoints/health
   endpoints/voice
   endpoints/moderation

Base URL
--------

All v1 API endpoints are prefixed with: ``/api/v1/``

Endpoints Overview
------------------

Chat Endpoints
~~~~~~~~~~~~~~

* ``POST /chat`` - Enhanced chat with the campus copilot

Conversation Endpoints
~~~~~~~~~~~~~~~~~~~~~~

* ``GET /conversations/{session_id}/summary`` - Get conversation summary
* ``GET /conversations/{session_id}/history`` - Get conversation message history
* ``DELETE /conversations/{session_id}`` - Deactivate a conversation

Health Endpoints
~~~~~~~~~~~~~~~~

* ``GET /health`` - Service health check

Voice Endpoints
~~~~~~~~~~~~~~~

* ``POST /voice/transcribe`` - Convert speech to text
* ``POST /voice/synthesize`` - Convert text to speech

Moderation Endpoints
~~~~~~~~~~~~~~~~~~~~

* ``POST /moderation/check`` - Check content for moderation

Request/Response Models
-----------------------

All endpoints use Pydantic models for request and response validation. See the individual endpoint documentation for detailed schemas.

Common Headers
--------------

All requests should include:

.. code-block:: text

   Content-Type: application/json
   Authorization: Bearer YOUR_API_KEY

WebSocket Support
-----------------

Some endpoints support WebSocket connections for real-time communication:

* ``/ws/chat`` - Real-time chat interface 