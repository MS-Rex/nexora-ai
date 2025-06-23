Moderation Endpoint
===================

.. automodule:: src.app.api.v1.endpoints.moderation
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The moderation endpoint provides content filtering capabilities to detect and handle inappropriate content before it reaches the AI system. This ensures a safe and appropriate user experience.

Endpoint Details
----------------

**POST** ``/api/v1/moderation/check``

Analyzes content for potential policy violations.

Features:
* Detects inappropriate language, harassment, and harmful content
* Returns detailed moderation results with confidence scores
* Categorizes different types of violations
* Provides suggestions for content improvement

Request Format
--------------

.. code-block:: text

   POST /api/v1/moderation/check
   Content-Type: application/json
   Authorization: Bearer YOUR_API_KEY

   {
     "content": "Text content to moderate",
     "context": "chat",
     "user_id": "user123"
   }

Request Schema
~~~~~~~~~~~~~~

* ``content`` (string, required): The text content to moderate
* ``context`` (string, optional): Context where content will be used ("chat", "comment", "post")
* ``user_id`` (string, optional): User identifier for tracking and personalization

Response Format
---------------

.. code-block:: http

   HTTP/1.1 200 OK
   Content-Type: application/json

   {
     "flagged": false,
     "confidence": 0.95,
     "categories": {
       "harassment": false,
       "hate_speech": false,
       "inappropriate_language": false,
       "spam": false,
       "violence": false,
       "sexual_content": false
     },
     "category_scores": {
       "harassment": 0.001,
       "hate_speech": 0.002,
       "inappropriate_language": 0.005,
       "spam": 0.001,
       "violence": 0.000,
       "sexual_content": 0.001
     },
     "reason": null,
     "suggestion": null
   }

Response Schema
~~~~~~~~~~~~~~~

* ``flagged`` (boolean): Whether content violates policies
* ``confidence`` (float): Overall confidence score (0.0 - 1.0)
* ``categories`` (object): Boolean flags for each category
* ``category_scores`` (object): Numerical scores for each category (0.0 - 1.0)
* ``reason`` (string, nullable): Explanation if content is flagged
* ``suggestion`` (string, nullable): Suggestion for improvement

Examples
--------

Check Safe Content
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   curl -X POST "https://your-domain.com/api/v1/moderation/check" \
        -H "Authorization: Bearer YOUR_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{
          "content": "What events are happening on campus today?",
          "context": "chat",
          "user_id": "student123"
        }' 