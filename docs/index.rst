.. discodo documentation master file, created by
   sphinx-quickstart on Sun Feb 28 13:00:50 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to discodo's documentation!
===================================

Discodo is an enhanced audio player for discord.

Features
--------

- Standalone Audio Node
- Youtube Related Video Autoplay
- Crossfade and Audio effects
- Synced Youtube Video Subtitle

Supported sources
-----------------

- All sources that can be extracted from youtube-dl_
- All formats that can be demuxed by libav_

.. _youtube-dl: https://github.com/ytdl-org/youtube-dl
.. _libav: https://libav.org/

Client libraries
----------------

- discodo_ (Python_)
- discodo.js_ (Node.js_)

.. _Python: https://www.python.org/
.. _Node.js: https://nodejs.org/
.. _discodo: https://github.com/kijk2869/discodo
.. _discodo.js: https://github.com/kijk2869/discodo.js


.. toctree::
   :caption: Introduction
   :maxdepth: 1

   introduction/installation.rst
   introduction/quickstart.rst
   introduction/logging.rst

.. toctree::
   :caption: Node
   :maxdepth: 1

   node/connection.rst
   node/resources/voice_client.rst
   node/resources/source.rst
   node/resources/events.rst

.. toctree::
   :caption: API Reference
   :maxdepth: 1

   high_api.rst
   events.rst
