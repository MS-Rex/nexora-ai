Chat Endpoint
=============

.. automodule:: src.app.api.v1.endpoints.chat
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The chat endpoint provides enhanced conversational AI capabilities specifically designed for university and campus-related queries. It includes automatic content moderation and intelligent tool selection.

Endpoint Details
----------------

**POST** ``/api/v1/chat``

Enhanced chat endpoint with Nexora Campus Copilot.

Features:
* Authenticates requests using API key
* Performs content moderation to filter inappropriate messages
* Uses Nexora Campus Copilot to handle university and campus-related queries
* Automatically selects appropriate tools (events, departments, both, or none)
* Politely redirects non-university questions to campus topics
* Returns comprehensive response for campus-related queries

Request Format
--------------

.. code-block:: text

   POST /api/v1/chat
   Content-Type: application/json
   Authorization: Bearer YOUR_API_KEY

   {
     "message": "What events are happening on campus today?",
     "user_id": "user123",
     "session_id": "session456"
   }

Request Schema
~~~~~~~~~~~~~~

The request must include a ``ChatRequest`` object with the following fields:

* ``message`` (string, required): The user's message/question
* ``user_id`` (string, optional): Unique identifier for the user
* ``session_id`` (string, required): Session identifier for conversation tracking

Response Format
---------------

.. code-block:: http

   HTTP/1.1 200 OK
   Content-Type: application/json

   {
     "response": "Here are the events happening on campus today...",
     "agent_name": "Nexora Campus Copilot",
     "intent": "campus",
     "agent_used": "EventsAgent",
     "success": true,
     "error": null,
     "session_id": "session456",
     "moderated": true,
     "content_flagged": false,
     "moderation_reason": null
   }

Response Schema
~~~~~~~~~~~~~~~

The response returns an ``EnhancedChatResponse`` object with:

* ``response`` (string): The AI assistant's response
* ``agent_name`` (string): Name of the AI agent (always "Nexora Campus Copilot")
* ``intent`` (string): Detected intent ("campus" or "moderation")
* ``agent_used`` (string): Which specific agent handled the request
* ``success`` (boolean): Whether the request was processed successfully
* ``error`` (string, nullable): Error message if any
* ``session_id`` (string): Echo of the request session ID
* ``moderated`` (boolean): Whether content moderation was applied
* ``content_flagged`` (boolean): Whether the content was flagged by moderation
* ``moderation_reason`` (string, nullable): Reason for moderation if flagged

Content Moderation
------------------

All chat messages are automatically checked for inappropriate content before processing. If content is flagged:

* The message is not processed by the AI
* A moderation response is returned immediately
* ``content_flagged`` is set to ``true``
* ``moderation_reason`` explains why it was flagged

Example moderated response:

.. code-block:: json

   {
     "response": "I'm sorry, but I can't assist with that type of content. Let's focus on campus-related topics instead.",
     "agent_name": "Nexora Campus Copilot",
     "intent": "moderation",
     "agent_used": "Content Moderation",
     "success": true,
     "error": null,
     "session_id": "session456",
     "moderated": true,
     "content_flagged": true,
     "moderation_reason": "Inappropriate content detected"
   }

Error Responses
---------------

If an error occurs, the endpoint returns an HTTP error status with details:

.. code-block:: http

   HTTP/1.1 500 Internal Server Error
   Content-Type: application/json

   {
     "detail": "Error processing enhanced chat request: [specific error message]"
   }

Common error scenarios:

* **401 Unauthorized**: Invalid or missing API key
* **422 Unprocessable Entity**: Invalid request format
* **500 Internal Server Error**: Server processing error

Examples
--------

Campus Events Query
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   curl -X POST "https://your-domain.com/api/v1/chat" \
        -H "Authorization: Bearer YOUR_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{
          "message": "What events are happening this week?",
          "user_id": "student123",
          "session_id": "conv456"
        }'

Department Information Query
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   curl -X POST "https://your-domain.com/api/v1/chat" \
        -H "Authorization: Bearer YOUR_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{
          "message": "Tell me about the Computer Science department",
          "user_id": "visitor789",
          "session_id": "conv123"
        }'

General Campus Query
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   curl -X POST "https://your-domain.com/api/v1/chat" \
        -H "Authorization: Bearer YOUR_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{
          "message": "Where is the library located?",
          "user_id": "student456",
          "session_id": "conv789"
        }' 