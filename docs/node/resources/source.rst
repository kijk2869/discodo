AudioData
=========

AudioData Object
----------------

AudioData Structure
~~~~~~~~~~~~~~~~~~~

================ ===================== ==================================
 Field            Type                  Description
---------------- --------------------- ----------------------------------
 _type            string                fixed value ``AudioData``
---------------- --------------------- ----------------------------------
 tag              string                object tag (uuid)
---------------- --------------------- ----------------------------------
 id               string                source id
---------------- --------------------- ----------------------------------
 title            ?string               source title
---------------- --------------------- ----------------------------------
 webpage_url      ?string               source webpage url
---------------- --------------------- ----------------------------------
 thumbnail        ?string               source thumbnail
---------------- --------------------- ----------------------------------
 url              ?string               source stream url
---------------- --------------------- ----------------------------------
 duration         ?integer              source duration
---------------- --------------------- ----------------------------------
 is_live          boolean               source live state
---------------- --------------------- ----------------------------------
 uploader         ?string               source uploader
---------------- --------------------- ----------------------------------
 description      ?string               source description
---------------- --------------------- ----------------------------------
 subtitles        json                  source subtitles (Mostly SRV1)
---------------- --------------------- ----------------------------------
 chapters         json                  source chapters (Only in youtube)
---------------- --------------------- ----------------------------------
 related          boolean               related playing state
---------------- --------------------- ----------------------------------
 context          json                  object context
---------------- --------------------- ----------------------------------
 start_position   float                 source start position
================ ===================== ==================================

AudioSource Object
------------------

AudioSource Structure
~~~~~~~~~~~~~~~~~~~~~

================ ===================== ==================================
 Field            Type                  Description
---------------- --------------------- ----------------------------------
 _type            string                fixed value ``AudioSource``
---------------- --------------------- ----------------------------------
 tag              string                object tag (uuid)
---------------- --------------------- ----------------------------------
 id               string                source id
---------------- --------------------- ----------------------------------
 title            ?string               source title
---------------- --------------------- ----------------------------------
 webpage_url      ?string               source webpage url
---------------- --------------------- ----------------------------------
 thumbnail        ?string               source thumbnail
---------------- --------------------- ----------------------------------
 url              ?string               source stream url
---------------- --------------------- ----------------------------------
 duration         integer              source duration
---------------- --------------------- ----------------------------------
 is_live          boolean               source live state
---------------- --------------------- ----------------------------------
 uploader         ?string               source uploader
---------------- --------------------- ----------------------------------
 description      ?string               source description
---------------- --------------------- ----------------------------------
 subtitles        json                  source subtitles (Mostly SRV1)
---------------- --------------------- ----------------------------------
 chapters         json                  source chapters (Only in youtube)
---------------- --------------------- ----------------------------------
 related          boolean               related playing state
---------------- --------------------- ----------------------------------
 context          json                  object context
---------------- --------------------- ----------------------------------
 start_position   float                 start position
---------------- --------------------- ----------------------------------
 seekable         boolean               seekable state
---------------- --------------------- ----------------------------------
 position         ?float                source current position
================ ===================== ==================================

Get Current
-----------

.. http:get:: /current

    The source object that is currently playing

    **Example response**:

    .. code-block:: json5

        {
            // source object
        }

    :reqheader Authorization: Password for discodo server

    :reqheader User-ID: the bot user id
    :reqheader ?Shard-ID: the bot shard id
    :reqheader Guild-ID: the guild id of queue
    :reqheader VoiceClient-ID: the voiceclient id

    :statuscode 200: no error
    :statuscode 403: authorization failed or VoiceClient-ID mismatched
    :statuscode 404: ClientManager or VoiceClient not found

Get From The Queue
------------------

.. http:get:: /queue/{tag_or_index}

    The source object in queue

    **Example response**:

    .. code-block:: json5

        {
            // source object
        }

    :param tag_or_index: the tag or index of source object
    :type tag_or_index: int or str

    :reqheader Authorization: Password for discodo server

    :reqheader User-ID: the bot user id
    :reqheader ?Shard-ID: the bot shard id
    :reqheader Guild-ID: the guild id of queue
    :reqheader VoiceClient-ID: the voiceclient id

    :statuscode 200: no error
    :statuscode 403: authorization failed or VoiceClient-ID mismatched
    :statuscode 404: ClientManager or VoiceClient not found

Edit Current
------------

.. http:post:: /current

    Edit the source object that is currently playing

    **Example response**:

    .. code-block:: json5

        {
            // source object
        }

    :reqheader Authorization: Password for discodo server

    :reqheader User-ID: the bot user id
    :reqheader ?Shard-ID: the bot shard id
    :reqheader Guild-ID: the guild id of queue
    :reqheader VoiceClient-ID: the voiceclient id

    :jsonparam json ?context: context to save on the object

    :statuscode 200: no error
    :statuscode 403: authorization failed or VoiceClient-ID mismatched
    :statuscode 404: ClientManager or VoiceClient not found

Edit From The Queue
-------------------

.. http:post:: /queue/{tag_or_index}

    Edit the source object in queue

    **Example response**:

    .. code-block:: json5

        {
            // edited source object
        }

    :param tag_or_index: the tag or index of source object
    :type tag_or_index: int or str

    :reqheader Authorization: Password for discodo server

    :reqheader User-ID: the bot user id
    :reqheader ?Shard-ID: the bot shard id
    :reqheader Guild-ID: the guild id of queue
    :reqheader VoiceClient-ID: the voiceclient id

    :jsonparam integer ?index: index to move the source in queue
    :jsonparam json ?context: context to save on the object
    :jsonparam float ?start_position: position to start on (only in AudioData)

    :statuscode 200: no error
    :statuscode 403: authorization failed or VoiceClient-ID mismatched
    :statuscode 404: ClientManager or VoiceClient not found

Remove From The Queue
---------------------

.. http:delete:: /queue/{tag_or_index}

    Remove the source object in queue

    **Example response**:

    .. code-block:: json5

        {
            "removed": {
                // removed source object
            },
            "entries": [
                // list of source in queue
            ]
        }

    :param tag_or_index: the tag or index of source object
    :type tag_or_index: int or str

    :reqheader Authorization: Password for discodo server

    :reqheader User-ID: the bot user id
    :reqheader ?Shard-ID: the bot shard id
    :reqheader Guild-ID: the guild id of queue
    :reqheader VoiceClient-ID: the voiceclient id

    :statuscode 200: no error
    :statuscode 403: authorization failed or VoiceClient-ID mismatched
    :statuscode 404: ClientManager or VoiceClient not found
