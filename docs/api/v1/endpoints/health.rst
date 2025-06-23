Health Endpoint
===============

.. automodule:: src.app.api.v1.endpoints.health
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The health endpoint provides a simple way to check if the Nexora AI service is running and operational. This endpoint is commonly used by load balancers, monitoring systems, and Laravel applications to verify service availability.

Endpoint Details
----------------

**GET** ``/api/v1/health``

Health check endpoint for monitoring service status.

Features:
* No authentication required
* Returns service health status
* Used for monitoring and load balancing
* Provides service name and version information

Request Format
--------------

.. code-block:: text

   GET /api/v1/health

No authentication or request body required.

Response Format
---------------

.. code-block:: http

   HTTP/1.1 200 OK
   Content-Type: application/json

   {
     "status": "healthy",
     "service": "Nexora AI",
     "version": "1.0.0"
   }

Response Schema
~~~~~~~~~~~~~~~

The response returns a ``HealthResponse`` object with:

* ``status`` (string): Service health status (always "healthy" if responding)
* ``service`` (string): Name of the service
* ``version`` (string): Version of the service

Use Cases
---------

* **Load Balancer Health Checks**: Determine if the service should receive traffic
* **Monitoring Systems**: Alert when the service becomes unavailable
* **Laravel Integration**: Verify the AI service is available before making requests
* **CI/CD Pipelines**: Ensure deployment was successful
* **Debugging**: Quick check if the service is responding

Examples
--------

Basic Health Check
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   curl -X GET "https://your-domain.com/api/v1/health"

Response:

.. code-block:: json

   {
     "status": "healthy",
     "service": "Nexora AI",
     "version": "1.0.0"
   }

Using with Monitoring
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Check if service is healthy and exit with appropriate code
   if curl -f -s "https://your-domain.com/api/v1/health" > /dev/null; then
     echo "Service is healthy"
     exit 0
   else
     echo "Service is down"
     exit 1
   fi

Integration with Load Balancers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For NGINX:

.. code-block:: nginx

   upstream nexora_backend {
       server nexora1:8000;
       server nexora2:8000;
   }

   location /health {
       proxy_pass http://nexora_backend/api/v1/health;
       proxy_set_header Host $host;
   }

For HAProxy:

.. code-block:: text

   backend nexora_servers
       option httpchk GET /api/v1/health
       server nexora1 nexora1:8000 check
       server nexora2 nexora2:8000 check

Error Scenarios
---------------

If the service is completely down, you'll receive a connection error rather than an HTTP response. If the service is partially functional but experiencing issues, it may return a 500 error instead of the expected 200 OK.

The health endpoint itself is designed to be lightweight and should respond quickly (typically under 100ms) when the service is healthy. 