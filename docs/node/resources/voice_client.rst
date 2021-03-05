Voice Client
============

Get State
---------

> Example getState
^^^^^^^^^^^^^^^^^^

.. code-block:: json

    {
        "op": "getState",
        "d": {
            "guild_id": "guild_id"
        }
    }


< Example getState response
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: json

    {
        "op": "getState",
        "d": {
            "id": "VoiceClient ID",
            "guild_id": "Guild ID",
            "channel_id": "Voice Channel ID",
            "state": "Current Player State",
            "current": "Current AudioSource Object",
            "duration": "Current source duration",
            "position": "Current source position",
            "remain": "Current source remain",
            "remainQueue": "Queue length",
            "options": {
                "autoplay": "autoplay boolean",
                "volume": "volume float",
                "crossfade": "crossfade float",
                "filter": {}
            }
        }
    }

Get Context
-----------

.. http:get:: /context

    Get context of the voice client

    **Example response**:

    .. code-block:: json5

        {
            // context
        }

    :reqheader Authorization: Password for discodo server

    :reqheader User-ID: the bot user id
    :reqheader ?Shard-ID: the bot shard id
    :reqheader Guild-ID: the guild id of queue
    :reqheader VoiceClient-ID: the voiceclient id

    :statuscode 200: no error
    :statuscode 403: authorization failed or VoiceClient-ID mismatched
    :statuscode 404: ClientManager or VoiceClient not found

Set Context
-----------

.. http:post:: /context

    Set context of the voice client

    **Example response**:

    .. code-block:: json5

        {
            // context
        }

    :reqheader Authorization: Password for discodo server

    :reqheader User-ID: the bot user id
    :reqheader ?Shard-ID: the bot shard id
    :reqheader Guild-ID: the guild id of queue
    :reqheader VoiceClient-ID: the voiceclient id

    :jsonparam json context: context to set

    :statuscode 200: no error
    :statuscode 403: authorization failed or VoiceClient-ID mismatched
    :statuscode 404: ClientManager or VoiceClient not found

Put Source
----------

.. http:post:: /putSource

    Put the source object on Queue

    **Example response**:

    .. code-block:: json5

        {
            "source": {
                // source object
            }
        }

    :reqheader Authorization: Password for discodo server

    :reqheader User-ID: the bot user id
    :reqheader ?Shard-ID: the bot shard id
    :reqheader Guild-ID: the guild id of queue
    :reqheader VoiceClient-ID: the voiceclient id

    :jsonparam json source: the source object to put

    :statuscode 200: no error
    :statuscode 403: authorization failed or VoiceClient-ID mismatched
    :statuscode 404: ClientManager or VoiceClient not found

Load Source
-----------

.. http:post:: /loadSource

    Search query and put it on Queue

    **Example response**:

    .. code-block:: json5

        {
            "source": {
                // source object
            }
        }

    :reqheader Authorization: Password for discodo server

    :reqheader User-ID: the bot user id
    :reqheader ?Shard-ID: the bot shard id
    :reqheader Guild-ID: the guild id of queue
    :reqheader VoiceClient-ID: the voiceclient id

    :jsonparam string query: query to search

    :statuscode 200: no error
    :statuscode 403: authorization failed or VoiceClient-ID mismatched
    :statuscode 404: ClientManager or VoiceClient not found

Get Options
-----------

.. http:get:: /options

    Get options of the voice_client

    **Example response**:

    .. code-block:: json

        {
            "autoplay": True,
            "volume": 1.0,
            "crossfade": 10.0,
            "filter": {}
        }

    :reqheader Authorization: Password for discodo server

    :reqheader User-ID: the bot user id
    :reqheader ?Shard-ID: the bot shard id
    :reqheader Guild-ID: the guild id of queue
    :reqheader VoiceClient-ID: the voiceclient id

    :statuscode 200: no error
    :statuscode 403: authorization failed or VoiceClient-ID mismatched
    :statuscode 404: ClientManager or VoiceClient not found

Set Options
-----------

.. http:post:: /options

    Set options of the voice_client

    **Example response**:

    .. code-block:: json

        {
            "autoplay": True,
            "volume": 1.0,
            "crossfade": 10.0,
            "filter": {}
        }

    :reqheader Authorization: Password for discodo server

    :reqheader User-ID: the bot user id
    :reqheader ?Shard-ID: the bot shard id
    :reqheader Guild-ID: the guild id of queue
    :reqheader VoiceClient-ID: the voiceclient id

    :jsonparam float ?volume: volume value
    :jsonparam float ?crossafde: crossfade value
    :jsonparam boolean ?autoplay: autoplay value
    :jsonparam json ?filter: filter value

    :statuscode 200: no error
    :statuscode 403: authorization failed or VoiceClient-ID mismatched
    :statuscode 404: ClientManager or VoiceClient not found

Get Position
------------

.. http:get:: /seek

    Get position of the voice_client

    **Example response**:

    .. code-block:: json

        {
            "duration": 300.0,
            "position": 200.0,
            "remain": 100.0
        }

    :reqheader Authorization: Password for discodo server

    :reqheader User-ID: the bot user id
    :reqheader ?Shard-ID: the bot shard id
    :reqheader Guild-ID: the guild id of queue
    :reqheader VoiceClient-ID: the voiceclient id

    :statuscode 200: no error
    :statuscode 403: authorization failed or VoiceClient-ID mismatched
    :statuscode 404: ClientManager or VoiceClient not found

Set Position (Seek)
-------------------

.. http:post:: /seek

    Set position of the voice_client

    :reqheader Authorization: Password for discodo server

    :reqheader User-ID: the bot user id
    :reqheader ?Shard-ID: the bot shard id
    :reqheader Guild-ID: the guild id of queue
    :reqheader VoiceClient-ID: the voiceclient id

    :jsonparam float offset: position to seek

    :statuscode 200: no error
    :statuscode 403: authorization failed or VoiceClient-ID mismatched
    :statuscode 404: ClientManager or VoiceClient not found

Skip Current
------------

.. http:post:: /skip

    Skip current of the voice_client

    :reqheader Authorization: Password for discodo server

    :reqheader User-ID: the bot user id
    :reqheader ?Shard-ID: the bot shard id
    :reqheader Guild-ID: the guild id of queue
    :reqheader VoiceClient-ID: the voiceclient id

    :statuscode 200: no error
    :statuscode 403: authorization failed or VoiceClient-ID mismatched
    :statuscode 404: ClientManager or VoiceClient not found

Pause
-----

.. http:post:: /pause

    Pause current of the voice_client

    :reqheader Authorization: Password for discodo server

    :reqheader User-ID: the bot user id
    :reqheader ?Shard-ID: the bot shard id
    :reqheader Guild-ID: the guild id of queue
    :reqheader VoiceClient-ID: the voiceclient id

    :statuscode 200: no error
    :statuscode 403: authorization failed or VoiceClient-ID mismatched
    :statuscode 404: ClientManager or VoiceClient not found

Resume
------

.. http:post:: /resume

    Resume current of the voice_client

    :reqheader Authorization: Password for discodo server

    :reqheader User-ID: the bot user id
    :reqheader ?Shard-ID: the bot shard id
    :reqheader Guild-ID: the guild id of queue
    :reqheader VoiceClient-ID: the voiceclient id

    :statuscode 200: no error
    :statuscode 403: authorization failed or VoiceClient-ID mismatched
    :statuscode 404: ClientManager or VoiceClient not found

Shuffle Queue
-------------

.. http:post:: /shuffle

    Shuffle the queue of the voice_client

    **Example response**:

    .. code-block:: json5

        {
            "entries": [
                // source object
            ]
        }

    :reqheader Authorization: Password for discodo server

    :reqheader User-ID: the bot user id
    :reqheader ?Shard-ID: the bot shard id
    :reqheader Guild-ID: the guild id of queue
    :reqheader VoiceClient-ID: the voiceclient id

    :statuscode 200: no error
    :statuscode 403: authorization failed or VoiceClient-ID mismatched
    :statuscode 404: ClientManager or VoiceClient not found

Get Queue
---------

.. http:get:: /queue

    Get the queue of the voice_client

    **Example response**:

    .. code-block:: json5

        {
            "entries": [
                // source object
            ]
        }

    :reqheader Authorization: Password for discodo server

    :reqheader User-ID: the bot user id
    :reqheader ?Shard-ID: the bot shard id
    :reqheader Guild-ID: the guild id of queue
    :reqheader VoiceClient-ID: the voiceclient id

    :statuscode 200: no error
    :statuscode 403: authorization failed or VoiceClient-ID mismatched
    :statuscode 404: ClientManager or VoiceClient not found
