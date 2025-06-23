Voice Endpoints
===============

.. automodule:: src.app.api.v1.endpoints.voice
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The voice endpoints provide speech-to-text and text-to-speech capabilities, enabling voice interaction with the Nexora Campus Copilot. These endpoints support various audio formats and provide high-quality voice synthesis.

Endpoints
---------

Speech to Text (Transcription)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**POST** ``/api/v1/voice/transcribe``

Converts audio input to text using advanced speech recognition.

Request Format:

.. code-block:: text

   POST /api/v1/voice/transcribe
   Content-Type: multipart/form-data
   Authorization: Bearer YOUR_API_KEY

   audio: [audio file]
   language: en (optional)

Supported audio formats:
* WAV
* MP3
* M4A
* FLAC
* OGG

Response Format:

.. code-block:: json

   {
     "text": "What events are happening on campus today?",
     "language": "en",
     "confidence": 0.95,
     "duration": 3.2
   }

Text to Speech (Synthesis)
~~~~~~~~~~~~~~~~~~~~~~~~~~

**POST** ``/api/v1/voice/synthesize``

Converts text to natural-sounding speech audio.

Request Format:

.. code-block:: text

   POST /api/v1/voice/synthesize
   Content-Type: application/json
   Authorization: Bearer YOUR_API_KEY

   {
     "text": "Here are the events happening on campus today...",
     "voice": "female",
     "speed": 1.0,
     "format": "mp3"
   }

Response Format:

The response is the audio file in the requested format with appropriate headers:

.. code-block:: http

   HTTP/1.1 200 OK
   Content-Type: audio/mpeg
   Content-Disposition: attachment; filename="speech.mp3"
   Content-Length: [file size]

   [binary audio data]

Request Parameters
------------------

Transcription Parameters
~~~~~~~~~~~~~~~~~~~~~~~~

* ``audio`` (file, required): Audio file to transcribe
* ``language`` (string, optional): Language code (default: "en")
* ``model`` (string, optional): Transcription model to use

Synthesis Parameters
~~~~~~~~~~~~~~~~~~~~

* ``text`` (string, required): Text to convert to speech
* ``voice`` (string, optional): Voice type ("male", "female", "neutral")
* ``speed`` (float, optional): Speech speed (0.5 - 2.0, default: 1.0)
* ``format`` (string, optional): Output format ("mp3", "wav", "ogg")

Response Models
---------------

Transcription Response
~~~~~~~~~~~~~~~~~~~~~~

* ``text`` (string): Transcribed text
* ``language`` (string): Detected or specified language
* ``confidence`` (float): Confidence score (0.0 - 1.0)
* ``duration`` (float): Audio duration in seconds

Synthesis Response
~~~~~~~~~~~~~~~~~~

Binary audio data with appropriate MIME type headers.

Error Responses
---------------

**400 Bad Request**

Invalid audio format or parameters:

.. code-block:: json

   {
     "detail": "Unsupported audio format. Please use WAV, MP3, M4A, FLAC, or OGG."
   }

**413 Payload Too Large**

Audio file too large:

.. code-block:: json

   {
     "detail": "Audio file too large. Maximum size is 25MB."
   }

**422 Unprocessable Entity**

Invalid request parameters:

.. code-block:: json

   {
     "detail": "Text is required for speech synthesis"
   }

Examples
--------

Transcribe Audio File
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   curl -X POST "https://your-domain.com/api/v1/voice/transcribe" \
        -H "Authorization: Bearer YOUR_API_KEY" \
        -F "audio=@recording.wav" \
        -F "language=en"

Synthesize Speech
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   curl -X POST "https://your-domain.com/api/v1/voice/synthesize" \
        -H "Authorization: Bearer YOUR_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{
          "text": "Welcome to campus! How can I help you today?",
          "voice": "female",
          "speed": 1.0,
          "format": "mp3"
        }' \
        --output response.mp3

Python Example
~~~~~~~~~~~~~~

.. code-block:: python

   import requests

   # Transcribe audio
   with open('audio.wav', 'rb') as audio_file:
       response = requests.post(
           'https://your-domain.com/api/v1/voice/transcribe',
           headers={'Authorization': 'Bearer YOUR_API_KEY'},
           files={'audio': audio_file}
       )
       transcription = response.json()
       print(f"Transcribed text: {transcription['text']}")

   # Synthesize speech
   response = requests.post(
       'https://your-domain.com/api/v1/voice/synthesize',
       headers={'Authorization': 'Bearer YOUR_API_KEY'},
       json={
           'text': 'Hello, this is Nexora Campus Copilot',
           'voice': 'female',
           'format': 'mp3'
       }
   )
   
   with open('output.mp3', 'wb') as f:
       f.write(response.content)

Use Cases
---------

* **Voice Chat Interface**: Enable voice conversations with the campus copilot
* **Accessibility**: Provide audio output for visually impaired users
* **Mobile Apps**: Voice interaction on mobile devices
* **Kiosks**: Voice-enabled campus information kiosks
* **Language Learning**: Pronunciation examples and practice

Technical Details
-----------------

* **Maximum audio file size**: 25MB
* **Supported sample rates**: 8kHz - 48kHz
* **Supported channels**: Mono and stereo
* **Transcription accuracy**: >95% for clear English speech
* **Synthesis quality**: High-quality neural voices
* **Response time**: Typically under 5 seconds for files under 1 minute 