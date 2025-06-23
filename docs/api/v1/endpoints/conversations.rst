Conversations Endpoints
=======================

.. automodule:: src.app.api.v1.endpoints.conversations
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The conversations endpoints provide functionality to manage and retrieve conversation history, summaries, and metadata. These endpoints allow you to track user interactions over time.

Endpoints
---------

Get Conversation Summary
~~~~~~~~~~~~~~~~~~~~~~~~

**GET** ``/api/v1/conversations/{session_id}/summary``

Retrieves a summary of a conversation including metadata like total messages, creation time, and activity status.

Request Format:

.. code-block:: text

   GET /api/v1/conversations/session123/summary
   Authorization: Bearer YOUR_API_KEY

Response Format:

.. code-block:: json

   {
     "conversation_id": "conv_12345",
     "session_id": "session123",
     "user_id": "user456",
     "title": "Campus Events Discussion",
     "total_messages": 15,
     "created_at": "2025-01-08T10:30:00Z",
     "last_activity": "2025-01-08T11:45:00Z",
     "is_active": true
   }

Get Conversation History
~~~~~~~~~~~~~~~~~~~~~~~~

**GET** ``/api/v1/conversations/{session_id}/history``

Retrieves the complete message history for a conversation in chronological order.

Request Format:

.. code-block:: text

   GET /api/v1/conversations/session123/history?limit=50
   Authorization: Bearer YOUR_API_KEY

Query Parameters:

* ``limit`` (integer, optional): Maximum number of messages to retrieve (1-100, default: 50)

Response Format:

.. code-block:: json

   [
     {
       "id": "msg_001",
       "role": "user",
       "content": "What events are happening today?",
       "created_at": "2025-01-08T10:30:00Z",
       "agent_name": null,
       "agent_used": null,
       "intent": null,
       "success": null,
       "response_time_ms": null
     },
     {
       "id": "msg_002",
       "role": "assistant",
       "content": "Here are today's campus events...",
       "created_at": "2025-01-08T10:30:15Z",
       "agent_name": "Nexora Campus Copilot",
       "agent_used": "EventsAgent",
       "intent": "campus",
       "success": true,
       "response_time_ms": 1250
     }
   ]

Deactivate Conversation
~~~~~~~~~~~~~~~~~~~~~~~

**DELETE** ``/api/v1/conversations/{session_id}``

Deactivates a conversation (soft delete). The conversation and its messages remain in the database but are marked as inactive.

Request Format:

.. code-block:: text

   DELETE /api/v1/conversations/session123
   Authorization: Bearer YOUR_API_KEY

Response Format:

.. code-block:: json

   {
     "message": "Conversation session123 deactivated successfully"
   }

Data Models
-----------

ConversationSummaryResponse
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Response model for conversation summary:

* ``conversation_id`` (string): Unique conversation identifier
* ``session_id`` (string): Session identifier
* ``user_id`` (string, nullable): User identifier
* ``title`` (string, nullable): Auto-generated conversation title
* ``total_messages`` (integer): Total number of messages in conversation
* ``created_at`` (string): ISO timestamp of conversation creation
* ``last_activity`` (string): ISO timestamp of last activity
* ``is_active`` (boolean): Whether the conversation is active

MessageResponse
~~~~~~~~~~~~~~~

Response model for individual messages:

* ``id`` (string): Unique message identifier
* ``role`` (string): Message role ("user" or "assistant")
* ``content`` (string): Message content
* ``created_at`` (string): ISO timestamp of message creation
* ``agent_name`` (string, nullable): Name of the agent that generated the response
* ``agent_used`` (string, nullable): Specific agent/tool used
* ``intent`` (string, nullable): Detected intent
* ``success`` (boolean, nullable): Whether the response was successful
* ``response_time_ms`` (integer, nullable): Response time in milliseconds

Error Responses
---------------

**404 Not Found**

When a conversation doesn't exist:

.. code-block:: json

   {
     "detail": "Conversation not found"
   }

**422 Unprocessable Entity**

When query parameters are invalid:

.. code-block:: json

   {
     "detail": [
       {
         "loc": ["query", "limit"],
         "msg": "ensure this value is greater than or equal to 1",
         "type": "value_error.number.not_ge"
       }
     ]
   }

**500 Internal Server Error**

When a server error occurs:

.. code-block:: json

   {
     "detail": "Error retrieving conversation summary: [specific error]"
   }

Examples
--------

Get Conversation Summary
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   curl -X GET "https://your-domain.com/api/v1/conversations/session123/summary" \
        -H "Authorization: Bearer YOUR_API_KEY"

Get Recent Messages
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   curl -X GET "https://your-domain.com/api/v1/conversations/session123/history?limit=10" \
        -H "Authorization: Bearer YOUR_API_KEY"

Archive a Conversation
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   curl -X DELETE "https://your-domain.com/api/v1/conversations/session123" \
        -H "Authorization: Bearer YOUR_API_KEY"

Use Cases
---------

* **Chat History Display**: Show previous conversations to users
* **Analytics**: Track conversation patterns and user engagement
* **Cleanup**: Archive old or inactive conversations
* **Debugging**: Review conversation flow for troubleshooting
* **User Experience**: Resume conversations where users left off 