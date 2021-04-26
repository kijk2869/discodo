Websocket Connection
====================

Discodo using websocket to send and receive events.

Payloads
--------

Payload Structure
~~~~~~~~~~~~~~~~~

======= ===================== =================================
 Field        Type                   Description
------- --------------------- ---------------------------------
 op            string          operation name for the payload
------- --------------------- ---------------------------------
 d       ?mixed (Mostly JSON)            event data
======= ===================== =================================

Connecting to Discodo
---------------------

Connecting
~~~~~~~~~~

Websocket Headers
^^^^^^^^^^^^^^^^^

============== ===================== =================================
 Field            Type                   Description
-------------- --------------------- ---------------------------------
 Authorization            string          Password for discodo server
============== ===================== =================================

Once connected, the client should immediately receive ``HELLO`` with the connection's heartbeat interval unless you missed headers or mismatched, otherwise receive ``FORBIDDEN``.

> Example HELLO
^^^^^^^^^^^^^^^

.. code-block:: json

    {
        "op": "HELLO",
        "d": {
            "heartbeat_interval": 15.0
        }
    }

> Example FORBIDDEN
^^^^^^^^^^^^^^^^^^^

.. code-block:: json

    {
        "op": "FORBIDDEN",
        "d": "why the connection forbidden"
    }

Heartbeating
~~~~~~~~~~~~

Recieveing ``HELLO`` payload, the client should begin sending ``HEARTBEAT`` every ``heartbeat_interval`` seconds, until the connection closed.

< Example HEARTBEAT
^^^^^^^^^^^^^^^^^^^

.. code-block:: json5

    {
        "op": "HEARTBEAT",
        "d": 0 // timestamp
    }

Event Data (``d``) can be ``None``, the server will echo them.

> Example HEARTBEAT_ACK
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: json5

    {
        "op": "HEARTBEAT_ACK",
        "d": 0 // timestamp
    }

Identifying
~~~~~~~~~~~

The client must send ``IDENTIFY`` to configure the audio manager before using.

< Example IDENTIFY
^^^^^^^^^^^^^^^^^^

.. code-block:: json5

    {
        "op": "IDENTIFY",
        "d": {
            "user_id": "my bot id"
            "shard_id": null // shard id
        }
    }

Resumed
~~~~~~~

If the same ``user_id`` with the same ``shard_id`` is connected before ``VC_TIMEOUT``, it will be resumed.

> Example Resumed
^^^^^^^^^^^^^^^^^

.. code-block:: json5

    {
        "op": "RESUMED",
        "d": {
            "voice_clients": [
                [0, 0] // guild_id, voice_channel_id(can be null)
            ]
        }
    }

When the client recieve ``RESUMED``, must reconnect to each voice channel.

Disconnecting
~~~~~~~~~~~~~

If the connection is closed, the server will clean up manager and sources after ``VC_TIMEOUT``
