API Reference
=============

This section contains the complete API reference for Nexora AI.

.. toctree::
   :maxdepth: 3
   :caption: API Versions:

   v1/index

Overview
--------

The Nexora AI API provides a RESTful interface for interacting with the campus copilot system. All endpoints require authentication via API key unless otherwise specified.

Base URL: ``https://your-domain.com/api``

Authentication
--------------

All API endpoints (except health check) require authentication using an API key. Include the API key in the request headers:

.. code-block:: text

   Authorization: Bearer YOUR_API_KEY

Or as a query parameter:

.. code-block:: text

   GET /api/v1/endpoint?api_key=YOUR_API_KEY

Response Format
---------------

All API responses follow a consistent JSON format:

.. code-block:: json

   {
     "response": "The actual response content",
     "agent_name": "Nexora Campus Copilot",
     "intent": "campus",
     "agent_used": "OrchestratorAgent",
     "success": true,
     "error": null,
     "session_id": "unique-session-identifier"
   }

Error Handling
--------------

The API uses standard HTTP status codes to indicate the success or failure of requests:

* ``200 OK`` - Request was successful
* ``400 Bad Request`` - Invalid request parameters
* ``401 Unauthorized`` - Authentication required or invalid API key
* ``404 Not Found`` - Resource not found
* ``422 Unprocessable Entity`` - Validation error
* ``500 Internal Server Error`` - Server error

Error responses include additional details:

.. code-block:: json

   {
     "detail": "Error description",
     "type": "error_type"
   }

Rate Limiting
-------------

API requests are rate-limited to ensure fair usage. Current limits:

* 100 requests per minute per API key
* 1000 requests per hour per API key

Rate limit headers are included in all responses:

.. code-block:: text

   X-RateLimit-Limit: 100
   X-RateLimit-Remaining: 95
   X-RateLimit-Reset: 1640995200 