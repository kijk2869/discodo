"""

This example isn't recommended in production.
Just use it only to learn the structure.
This code is not perfect and can be complex.


Additionally, remote is recommended for efficient performance management.
Just know there is a way to do this.

"""


import logging

import discord

import discodo

logging.basicConfig(level=logging.INFO)

app = discord.Client()
Audio = discodo.AudioManager()


@app.event
async def on_ready():
    print("bot is now ready.")


@app.event
async def on_socket_response(payload):
    Audio.discordDispatch(payload)


@app.event
async def on_message(message):
    await app.wait_until_ready()

    if message.content.startswith("!join"):
        if not message.author.voice:
            return await message.channel.send("Join the voice channel first.")

        await app.ws.voice_state(message.guild.id, message.author.voice.channel.id)
        return await message.channel.send(
            f"Connected to {message.author.voice.channel.mention}."
        )

    if message.content.startswith("!stop"):
        vc = Audio.getVC(message.guild.id)

        if not vc:
            return await message.channel.send("Please type `!join` first.")

        await vc.destroy()

        return await message.channel.send("Player stopped and cleaned the queue.")

    if message.content.startswith("!play"):
        vc = Audio.getVC(message.guild.id)

        if not vc:
            return await message.channel.send("Please type `!join` first.")

        Song = await vc.loadSong(message.content[5:].strip())

        if isinstance(Song, list):
            return await message.channel.send(
                f"{len(Song) - 1} songs except {Song[0].title} added."
            )
        else:
            return await message.channel.send(f"{Song.title} added.")

    if message.content.startswith("!skip"):
        vc = Audio.getVC(message.guild.id)

        if not vc:
            return await message.channel.send("Please type `!join` first.")

        offset = int(message.content[5:].strip()) if message.content[5:].strip() else 1

        vc.skip(offset)

        return await message.channel.send(f"{offset} skipped.")

    if message.content.startswith("!volume"):
        vc = Audio.getVC(message.guild.id)

        if not vc:
            return await message.channel.send("Please type `!join` first.")

        offset = (
            int(message.content[7:].strip()) if message.content[7:].strip() else 100
        )

        Volume = vc.setVolume(offset / 100)

        return await message.channel.send(f"Set volume to {Volume * 100}%.")

    if message.content.startswith("!crossfade"):
        vc = Audio.getVC(message.guild.id)

        if not vc:
            return await message.channel.send("Please type `!join` first.")

        offset = (
            int(message.content[10:].strip()) if message.content[10:].strip() else 10
        )

        Crossfade = vc.setCrossfade(offset)

        return await message.channel.send(
            f"Set crossfade seconds to {Crossfade} seconds."
        )

    if message.content.startswith("!autoplay"):
        vc = Audio.getVC(message.guild.id)

        if not vc:
            return await message.channel.send("Please type `!join` first.")

        offset = (
            int(message.content[9:].strip()) if message.content[9:].strip() else "on"
        )
        offset = {"on": True, "off": False}.get(offset, True)

        autoplay = vc.setAutoplay(offset)

        return await message.channel.send(
            f'Auto related play {"enabled" if autoplay else "disabled"}.'
        )

    if message.content.startswith("!repeat"):
        vc = Audio.getVC(message.guild.id)

        if not vc:
            return await message.channel.send("Please type `!join` first.")

        offset = (
            int(message.content[7:].strip()) if message.content[7:].strip() else "on"
        )
        offset = {"on": True, "off": False}.get(offset, True)

        repeat = vc.setRepeat(offset)

        return await message.channel.send(
            f'Repeat {"enabled" if repeat else "disabled"}.'
        )

    if message.content.startswith("!np"):
        vc = Audio.getVC(message.guild.id)

        if not vc:
            return await message.channel.send("Please type `!join` first.")

        return await message.channel.send(
            f"Now playing: {vc.player.current.title} `{vc.player.current.duration}:{vc.player.current.AudioData.duration}`"
        )

    if message.content.startswith("!shuffle"):
        vc = Audio.getVC(message.guild.id)

        if not vc:
            return await message.channel.send("Please type `!join` first.")

        await vc.shuffle()

        return await message.channel.send("Shuffle the queue.")

    if message.content.startswith("!queue"):
        vc = Audio.getVC(message.guild.id)

        if not vc:
            return await message.channel.send("Please type `!join` first.")

        QueueText = "\n".join(
            [str(vc.Queue.index(Item) + 1) + ". " + Item.title for Item in vc.Queue]
        )

        return await message.channel.send(
            f"""
Now playing: {vc.player.current.title} `{vc.player.current.duration}:{vc.player.current.AudioData.duration}`

{QueueText}
"""
        )

    if message.content.startswith("!bassboost"):
        vc = Audio.getVC(message.guild)

        if not vc:
            return await message.channel.send("Please type `!join` first.")

        offset = (
            int(message.content[10:].strip()) if message.content[10:].strip() else 0
        )
        filter = (
            {"anequalizer": discodo.equalizer.bassboost(offset)} if offset != 0 else {}
        )

        vc.setFilter(filter)

        return await message.channel.send(f"Set bassboost level {offset}%.")

    if message.content.startswith("!tempo"):
        vc = Audio.getVC(message.guild)

        if not vc:
            return await message.channel.send("Please type `!join` first.")

        offset = (
            float(message.content[6:].strip()) if message.content[6:].strip() else 1.0
        )

        vc.setFilter({"atempo": str(offset)})

        return await message.channel.send(f"Set tempo to {offset}.")

    if message.content.startswith("!seek"):
        vc = Audio.getVC(message.guild)

        if not vc:
            return await message.channel.send("Please type `!join` first.")

        offset = int(message.content[5:].strip()) if message.content[5:].strip() else 1

        vc.seek(offset)

        return await message.channel.send(f"Seek to {offset}.")


app.run("SUPERRRSECRETTOKENNNNNN")
