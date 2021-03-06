.. currentmodule:: discodo

High-level API
==============

This section outlines the API of discodo.

.. note::

    This module uses the Python logging module to log diagnostic and errors
    in an output independent way. If the logging module is not configured,
    logs will not be output anywhere. See :ref:`logging_setup` for
    more information.

Client
------

.. autoclass:: discodo.DPYClient
    :members:

Utils
-----

.. autoclass:: discodo.utils.EventDispatcher
    :members:

.. automodule:: discodo.utils.status
    :members:

.. autoclass:: discodo.utils.CallbackList
    :members:

.. automethod:: discodo.utils.tcp.getFreePort

Node
----

.. autoclass:: discodo.Node
    :members:

.. autoclass:: discodo.Nodes
    :members:

VoiceClient
-----------

.. autoclass:: discodo.VoiceClient
    :members:

AudioData
---------

.. autoclass:: discodo.models.AudioData
    :members:

AudioSource
-----------

.. autoclass:: discodo.models.AudioSource
    :members:

Errors
------

.. autoexception:: discodo.DiscodoException

.. autoexception:: discodo.EncryptModeNotReceived

.. autoexception:: discodo.NotPlaying

.. autoexception:: discodo.VoiceClientNotFound

.. autoexception:: discodo.NoSearchResults

.. autoexception:: discodo.OpusLoadError

.. autoexception:: discodo.HTTPException

.. autoexception:: discodo.Forbidden

.. autoexception:: discodo.TooManyRequests

.. autoexception:: discodo.NotSeekable

.. autoexception:: discodo.NodeException

.. autoexception:: discodo.NodeNotConnected
