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

        return await message.channel.send(
            f"I connected to {message.author.voice.channel.mention}"
        )

    if message.content.startswith("!play"):
        VC = codo.getVC(message.guild, safe=True)

        if not VC:
            return await message.channel.send("Please type `!join` first.")

        if not hasattr(VC, "channel"):
            VC.channel = message.channel

        source = await VC.loadSource(message.content[5:].strip())

        if isinstance(source, list):
            return await message.channel.send(
                f"{len(source) - 1} songs except {source[0].title} added."
            )
        else:
            return await message.channel.send(f"{source.title} added.")

    if message.content.startswith("!stop"):
        VC = codo.getVC(message.guild, safe=True)

        if not VC:
            return await message.channel.send(
                "I'm not connected to any voice channel now."
            )

        await VC.destroy()

        return await message.channel.send("I stopped the player and cleaned the queue.")


codo.registerNode()
app.run("your discord bot token here")
