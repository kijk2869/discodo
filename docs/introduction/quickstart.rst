Quickstart
==========

A Minimal Bot with discord.py_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. _discord.py: https://github.com/Rapptz/discord.py

Let’s make a bot which uses local node feature.

It looks like this:

.. code-block:: python3

    import discord
    import discodo

    client = discord.Client()
    codo = discodo.DPYClient(client)

    @client.event
    async def on_ready():
        print(f"I logged in as {client.user} (client.user.id)")

    @codo.event("SOURCE_START")
    async def sendPlaying(VC, Data):
        await VC.channel.send(f"I'm now playing {Data['source']['title']}")

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        if message.content.startswith("!join"):
            if not message.author.voice:
                return await message.channel.send("Join the voice channel first.")

            await codo.connect(message.author.voice.channel)

            return await message.channel.send(f"I connected to {message.author.voice.channel.mention}")

        if message.content.startswith("!play"):
            VC = codo.getVC(message.guild, safe=True)

            if not VC:
                return await message.channel.send("Please type `!join` first.")

            if not hasattr(VC, "channel"):
                VC.channel = message.channel

            source = await VC.loadSource(message.content[5:].strip())

            if isinstance(source, list):
                return await message.channel.send(f"{len(source) - 1} songs except {source[0].title} added.")
            else:
                return await message.channel.send(f"{source.title} added.")

        if message.content.startswith("!stop"):
            VC = codo.getVC(message.guild, safe=True)

            if not VC:
                return await message.channel.send("I'm not connected to any voice channel now.")

            await VC.destroy()

            return await message.channel.send("I stopped the player and cleaned the queue.")

    codo.registerNode()
    app.run("your discord bot token here")


Let's name this file ``simple_musicbot.py``

Assume you know how to use discord.py_, and I will explain the discodo_ code step by step.

.. _discodo: https://github.com/kijk2869/discodo

1. We create an instance of :py:class:`DPYClient`. This client will manage voice connections to Discord.
2. After ``on_ready`` event, we use the :py:attr:`DPYClient.event()` decorator to register an event like discord.py_ . In this case, ``SOURCE_START`` will be called when the music starts playing.
3. When the ``!join`` command is excuted, we check if the :py:attr:`discord.Message.author` is connected to the voice channel. If it is, then we connected to the channel using :py:func:`DPYClient.connect()`
4. When the ``!play`` command runs, set the VC.channel to the current message channel to send messages during playback, search for queries and add them to the list.
5. If the ``!stop`` command is excuted, we destroy the voice client via :py:func:`VoiceClient.destroy()`
6. Finally, we set local nodes to be used by not giving host argument to :py:func:`DPYClient.registerNode()`

Now that we've made a simple music bot, we have to run this. Just as you do when you run a discord.py_ Bot

.. code-block:: console

    $ python simple_musicbot.py

Now you can try playing around with your basic musicbot.
