.. _client_events:

Event Reference
===============

This section outlines the different types of events dispatched by discodo client.

.. note::
    If you are using a standalone discodo node server while not using :py:class:`DPYClient`, the events that you get will have something different. See this :ref:`node_events`.

To listen an event, use :py:class:`EventDispatcher` of the :py:class:`DPYClient`

.. code-block:: python

    import discord
    import discodo

    bot = discord.Client()
    codo = discodo.DPYClient(bot)

    # Using DPYClient.event

    @codo.event("SOURCE_START")
    async def start_event(VC, source):
        print(f"{VC} is now playing {source}")

    # Using DPYClient.dispatcher.on

    async def stop_event(VC, source):
        print(f"{VC} is stopped {source}")

    codo.dispatcher.on("SOURCE_STOP", stop_event)

VC_CREATED(:py:class:`VoiceClient`, :py:class:`dict` data)
----------------------------------------------------------

Called when the new voice client has successfully created. This is not the same as the client being fully connected.

.. _VC_CREATED_DATA_STRUCTURE:

Data Structure
~~~~~~~~~~~~~~

================ ===================== ==================================
 Field            Type                  Description
---------------- --------------------- ----------------------------------
 guild_id         int                   The guild id of the voice client
---------------- --------------------- ----------------------------------
 id               str                   The id of the voice client
================ ===================== ==================================

QUEUE_EVENT(:py:class:`VoiceClient`, :py:class:`dict` data)
-----------------------------------------------------------

Called when there is something changed in the queue of the voice client. If you are using :py:class:`DPYClient`, Ignore this event.

.. _QUEUE_EVENT_DATA_STRUCTURE:

Data Structure
~~~~~~~~~~~~~~

================ ===================== ==================================
 Field            Type                  Description
---------------- --------------------- ----------------------------------
 guild_id         int                   The guild id of the voice client
---------------- --------------------- ----------------------------------
 name             str                   The name of the method
---------------- --------------------- ----------------------------------
 args             list                  The arguments of the method
================ ===================== ==================================

VC_CHANNEL_EDITED(:py:class:`VoiceClient`, :py:class:`dict` data)
-----------------------------------------------------------------

Called when the voice channel of the voice client is changed.

.. _VC_CHANNEL_EDITED_DATA_STRUCTURE:

Data Structure
~~~~~~~~~~~~~~

================ ===================== ===================================
 Field            Type                  Description
---------------- --------------------- -----------------------------------
 guild_id         int                   The guild id of the voice client
---------------- --------------------- -----------------------------------
 channel_id       int                   The channel id of the voice client
================ ===================== ===================================

putSource(:py:class:`VoiceClient`, :py:class:`dict` data)
---------------------------------------------------------

Called when some sources are put in the queue.

.. _putSource_DATA_STRUCTURE:

Data Structure
~~~~~~~~~~~~~~

================ ===================== ===================================
 Field            Type                  Description
---------------- --------------------- -----------------------------------
 guild_id         int                   The guild id of the voice client
---------------- --------------------- -----------------------------------
 sources          list                  The sources which is put
================ ===================== ===================================

loadSource(:py:class:`VoiceClient`, :py:class:`dict` data)
----------------------------------------------------------

Called when some sources are searched and put in the queue.

.. _loadSource_DATA_STRUCTURE:

Data Structure
~~~~~~~~~~~~~~

================ ======================= =======================================
 Field            Type                    Description
---------------- ----------------------- ---------------------------------------
 guild_id         int                     The guild id of the voice client
---------------- ----------------------- ---------------------------------------
 source           Union[AudioData, list]  The sources which is searched and put
================ ======================= =======================================

REQUIRE_NEXT_SOURCE(:py:class:`VoiceClient`, :py:class:`dict` data)
-------------------------------------------------------------------

Called when the player needs next source to play. If you set ``autoplay`` as ``True``, the related source will be put after this event.

.. _REQUIRE_NEXT_SOURCE_DATA_STRUCTURE:

Data Structure
~~~~~~~~~~~~~~

================ ======================= ==================================================
 Field            Type                    Description
---------------- ----------------------- --------------------------------------------------
 guild_id         int                     The guild id of the voice client
---------------- ----------------------- --------------------------------------------------
 current          AudioSource             The source which the player is currently playing
================ ======================= ==================================================

SOURCE_START(:py:class:`VoiceClient`, :py:class:`dict` data)
------------------------------------------------------------

Called when the player starts to play the source.

.. _SOURCE_START_DATA_STRUCTURE:

Data Structure
~~~~~~~~~~~~~~

================ ======================= ============================================
 Field            Type                    Description
---------------- ----------------------- --------------------------------------------
 guild_id         int                     The guild id of the voice client
---------------- ----------------------- --------------------------------------------
 source           AudioSource             The source which the player starts to play
================ ======================= ============================================

SOURCE_STOP(:py:class:`VoiceClient`, :py:class:`dict` data)
-----------------------------------------------------------

Called when the player stops to play the source.

.. _SOURCE_STOP_DATA_STRUCTURE:

Data Structure
~~~~~~~~~~~~~~

================ ======================= ============================================
 Field            Type                    Description
---------------- ----------------------- --------------------------------------------
 guild_id         int                     The guild id of the voice client
---------------- ----------------------- --------------------------------------------
 source           AudioSource             The source which the player stops to play
================ ======================= ============================================

PLAYER_TRACEBACK(:py:class:`VoiceClient`, :py:class:`dict` data)
----------------------------------------------------------------

Called when the player gets some traceback while trying to send packets to discord server.

.. _PLAYER_TRACEBACK_DATA_STRUCTURE:

Data Structure
~~~~~~~~~~~~~~

================ =============================== ================================================================
 Field            Type                            Description
---------------- ------------------------------- ----------------------------------------------------------------
 guild_id         int                             The guild id of the voice client
---------------- ------------------------------- ----------------------------------------------------------------
 traceback        str                             The traceback information which the player gets
================ =============================== ================================================================

SOURCE_TRACEBACK(:py:class:`VoiceClient`, :py:class:`dict` data)
----------------------------------------------------------------

Called when the player gets some traceback while trying to play the source. That source will be automatically removed from the queue.

.. _SOURCE_TRACEBACK_DATA_STRUCTURE:

Data Structure
~~~~~~~~~~~~~~

================ =============================== ================================================================
 Field            Type                            Description
---------------- ------------------------------- ----------------------------------------------------------------
 guild_id         int                             The guild id of the voice client
---------------- ------------------------------- ----------------------------------------------------------------
 source           Union[AudioData, AudioSource]   The source which the player gets traceback while trying to play
---------------- ------------------------------- ----------------------------------------------------------------
 traceback        str                             The traceback information which the player gets
================ =============================== ================================================================
