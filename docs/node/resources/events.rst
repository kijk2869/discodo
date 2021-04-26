.. _node_events:

Event Reference
===============

This section outlines the different types of events dispatched by discodo node with websocket.

.. note::
    If you are using :py:class:`DPYClient`, the events that you get will have something different. See this :ref:`client_events`.

STATUS
------

Called when the client requests system information by ``getStatus``. the unit is mega bytes or percent.

================= ===================== ==================================
 Field             Type                  Description
----------------- --------------------- ----------------------------------
 UsedMemory        integer               The process memory usage
----------------- --------------------- ----------------------------------
 TotalMemory       integer               The system memory usage
----------------- --------------------- ----------------------------------
 ProcessLoad       integer               The process cpu usage
----------------- --------------------- ----------------------------------
 TotalLoad         integer               The system cpu usage
----------------- --------------------- ----------------------------------
 Cores             integer               The cpu core count
----------------- --------------------- ----------------------------------
 Threads           integer               The process thread count
----------------- --------------------- ----------------------------------
 NetworkInbound    integer               The network inbound counters
----------------- --------------------- ----------------------------------
 NetworkOutbound   integer               The network outbound counters
================= ===================== ==================================

HEARTBEAT_ACK
-------------

Called when the client send ``HEARTBEAT`` payload. The data of this event is payload data.

IDENTIFIED
----------

Called when the new voice client has successfully created. This is not the same as the client being fully connected.

================ ===================== ==================================
 Field            Type                  Description
---------------- --------------------- ----------------------------------
 guild_id         int                   The guild id of the voice client
---------------- --------------------- ----------------------------------
 id               str                   The id of the voice client
================ ===================== ==================================

VC_DESTROYED
------------

Called when the voice client has successfully destroyed.

.. note::
    This does not mean that the bot have disconnected from the voice channel. When the client receives this event, it should disconnect from the voice channel.

================ ===================== ====================================================
 Field            Type                  Description
---------------- --------------------- ----------------------------------------------------
 guild_id         int                   The guild id of the voice client that is destroyed
================ ===================== ====================================================

QUEUE_EVENT
-----------

Called when there is something changed in the queue of the voice client.

================ ===================== ==================================
 Field            Type                  Description
---------------- --------------------- ----------------------------------
 guild_id         int                   The guild id of the voice client
---------------- --------------------- ----------------------------------
 name             str                   The name of the method
---------------- --------------------- ----------------------------------
 args             list                  The arguments of the method
================ ===================== ==================================

VC_CHANNEL_EDITED
-----------------

Called when the voice channel of the voice client is changed.

================ ===================== ===================================
 Field            Type                  Description
---------------- --------------------- -----------------------------------
 guild_id         int                   The guild id of the voice client
---------------- --------------------- -----------------------------------
 channel_id       int                   The channel id of the voice client
================ ===================== ===================================

putSource
---------

Called when some sources are put in the queue.

================ ===================== ===================================
 Field            Type                  Description
---------------- --------------------- -----------------------------------
 guild_id         int                   The guild id of the voice client
---------------- --------------------- -----------------------------------
 sources          list                  The sources which is put
================ ===================== ===================================

loadSource
----------

Called when some sources are searched and put in the queue.

================ ======================= =======================================
 Field            Type                    Description
---------------- ----------------------- ---------------------------------------
 guild_id         int                     The guild id of the voice client
---------------- ----------------------- ---------------------------------------
 source           list or AudioData       The sources which is searched and put
================ ======================= =======================================

REQUIRE_NEXT_SOURCE
-------------------

Called when the player needs next source to play. If you set ``autoplay`` as ``True``, the related source will be put after this event.

================ ======================= ==================================================
 Field            Type                    Description
---------------- ----------------------- --------------------------------------------------
 guild_id         int                     The guild id of the voice client
---------------- ----------------------- --------------------------------------------------
 current          AudioSource             The source which the player is currently playing
================ ======================= ==================================================

SOURCE_START
------------

Called when the player starts to play the source.

================ ======================= ============================================
 Field            Type                    Description
---------------- ----------------------- --------------------------------------------
 guild_id         int                     The guild id of the voice client
---------------- ----------------------- --------------------------------------------
 source           AudioSource             The source which the player starts to play
================ ======================= ============================================

SOURCE_STOP
-----------

Called when the player stops to play the source.

================ ======================= ============================================
 Field            Type                    Description
---------------- ----------------------- --------------------------------------------
 guild_id         int                     The guild id of the voice client
---------------- ----------------------- --------------------------------------------
 source           AudioSource             The source which the player stops to play
================ ======================= ============================================

getState
--------

Called when the client requests the player state by ``getState``.

================ =============================== ================================================
 Field            Type                            Description
---------------- ------------------------------- ------------------------------------------------
 guild_id         str                             The guild id of the voice client
---------------- ------------------------------- ------------------------------------------------
 channel_id       str                             The channel id of the voice client
---------------- ------------------------------- ------------------------------------------------
 state            str                             Current state of the voice client
---------------- ------------------------------- ------------------------------------------------
 current          AudioSource                     Current source of the player
---------------- ------------------------------- ------------------------------------------------
 duration         float                           Current duration of the source that is playing
---------------- ------------------------------- ------------------------------------------------
 position         float                           Current position of the source that is playing
---------------- ------------------------------- ------------------------------------------------
 remain           float                           (duration value) - (position value)
---------------- ------------------------------- ------------------------------------------------
 remainQueue      int                             Current queue length of the player
---------------- ------------------------------- ------------------------------------------------
 options          JSON                            Current options of the player
================ =============================== ================================================

getQueue
--------

Called when the client requests the player queue by ``getQueue``.

================ =============================== =================================
 Field            Type                            Description
---------------- ------------------------------- ---------------------------------
 guild_id         int                             The guild id of the voice client
---------------- ------------------------------- ---------------------------------
 entries          list                            The entries of the queue
================ =============================== =================================

requestSubtitle
---------------

Called when the client requests synced subtitles by ``requestSubtitle``.

================ =============================== =================================
 Field            Type                            Description
---------------- ------------------------------- ---------------------------------
 guild_id         int                             The guild id of the voice client
---------------- ------------------------------- ---------------------------------
 identify         str                             The id to identify the subtitle
---------------- ------------------------------- ---------------------------------
 url              str                             The url of the subtitle
================ =============================== =================================

Subtitle
--------

This event is for sending the sync subtitle. This event is sent according to the player's position.

================ =============================== =================================
 Field            Type                            Description
---------------- ------------------------------- ---------------------------------
 guild_id         int                             The guild id of the voice client
---------------- ------------------------------- ---------------------------------
 identify         str                             The id to identify the subtitle
---------------- ------------------------------- ---------------------------------
 previous         str                             The content of previous subtitle
---------------- ------------------------------- ---------------------------------
 current          str                             The content of current subtitle
---------------- ------------------------------- ---------------------------------
 next             str                             The content of next subtitle
================ =============================== =================================

subtitleDone
------------

Called when the subtitle is done.

================ =============================== =================================
 Field            Type                            Description
---------------- ------------------------------- ---------------------------------
 guild_id         int                             The guild id of the voice client
---------------- ------------------------------- ---------------------------------
 identify         str                             The id to identify the subtitle
================ =============================== =================================

PLAYER_TRACEBACK
----------------

Called when the player gets some traceback while trying to send packets to discord server.

================ =============================== ================================================================
 Field            Type                            Description
---------------- ------------------------------- ----------------------------------------------------------------
 guild_id         int                             The guild id of the voice client
---------------- ------------------------------- ----------------------------------------------------------------
 traceback        str                             The traceback information which the player gets
================ =============================== ================================================================

SOURCE_TRACEBACK
----------------

Called when the player gets some traceback while trying to play the source. That source will be automatically removed from the queue.

================ =============================== ================================================================
 Field            Type                            Description
---------------- ------------------------------- ----------------------------------------------------------------
 guild_id         int                             The guild id of the voice client
---------------- ------------------------------- ----------------------------------------------------------------
 source           Union[AudioData, AudioSource]   The source which the player gets traceback while trying to play
---------------- ------------------------------- ----------------------------------------------------------------
 traceback        str                             The traceback information which the player gets
================ =============================== ================================================================
