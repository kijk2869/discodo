"""

This example isn't recommended in production.
Just use it only to learn the structure.
This code is not perfect and can be complex.

"""
import logging
import re

import discord

import discodo

logging.basicConfig(level=logging.INFO)

app = discord.Client()
Audio = discodo.DPYClient(app)
Audio.register_local_node()

URL_REGEX = re.compile(
    r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
)


@app.event
async def on_ready():
    print("bot is now ready.")


@Audio.event("SOURCE_START")
async def sendPlaying(VC, Data):
    await VC.channel.send(f'playing {Data["source"]["title"]}')


@Audio.event("SOURCE_END")
async def sendStopped(VC, Data):
    await VC.channel.send(f'{Data["source"]["title"]} Done')


@app.event
async def on_message(message):
    await app.wait_until_ready()

    if message.content.startswith("!join"):
        if not message.author.voice:
            return await message.channel.send("Join the voice channel first.")

        await Audio.connect(message.author.voice.channel)
        return await message.channel.send(
            f"connected to {message.author.voice.channel.mention}."
        )

    if message.content.startswith("!stop"):
        vc = Audio.getVC(message.guild)

        if not vc:
            return await message.channel.send("Please type `!join` first.")

        await vc.destroy()

        return await message.channel.send(f"player stopped and cleaned the queue.")

    if message.content.startswith("!play"):
        vc = Audio.getVC(message.guild)

        if not vc:
            return await message.channel.send("Please type `!join` first.")

        if not hasattr(vc, "channel"):
            vc.channel = message.channel

        Source = await vc.loadSource(message.content[5:].strip())

        if isinstance(Source, list):
            return await message.channel.send(
                f'{len(Source) - 1} songs except {Source[0]["title"]} added.'
            )
        else:
            return await message.channel.send(f'{Source["data"]["title"]} added.')

    if message.content.startswith("!skip"):
        vc = Audio.getVC(message.guild)

        if not vc:
            return await message.channel.send("Please type `!join` first.")

        offset = int(message.content[5:].strip()) if message.content[5:].strip() else 1

        Remain = await vc.skip(offset)

        return await message.channel.send(f"{offset} skipped. {Remain}songs remain")

    if message.content.startswith("!remove"):
        vc = Audio.getVC(message.guild)

        if not vc:
            return await message.channel.send("Please type `!join` first.")

        offset = int(message.content[7:].strip()) if message.content[7:].strip() else 1

        Data = await vc.remove(offset)

        return await message.channel.send(f'{Data["removed"]["title"]} removed.')

    if message.content.startswith("!volume"):
        vc = Audio.getVC(message.guild)

        if not vc:
            return await message.channel.send("Please type `!join` first.")

        offset = (
            int(message.content[7:].strip()) if message.content[7:].strip() else 100
        )

        Volume = await vc.setVolume(offset / 100)

        return await message.channel.send(f"set volume to {Volume}%.")

    if message.content.startswith("!crossfade"):
        vc = Audio.getVC(message.guild)

        if not vc:
            return await message.channel.send("Please type `!join` first.")

        offset = (
            int(message.content[10:].strip()) if message.content[10:].strip() else 10
        )

        Crossfade = await vc.setCrossfade(offset)

        return await message.channel.send(
            f"set crossfade seconds to {Crossfade} seconds."
        )

    if message.content.startswith("!autoplay"):
        vc = Audio.getVC(message.guild)

        if not vc:
            return await message.channel.send("Please type `!join` first.")

        offset = (
            int(message.content[9:].strip()) if message.content[9:].strip() else "on"
        )
        offset = {"on": True, "off": False}.get(offset, True)

        autoplay = await vc.setAutoplay(offset)

        return await message.channel.send(
            f'auto related play {"enabled" if autoplay else "disabled"}.'
        )

    if message.content.startswith("!np"):
        vc = Audio.getVC(message.guild)

        if not vc:
            return await message.channel.send("Please type `!join` first.")

        Data = await vc.getState()

        return await message.channel.send(
            f'Now playing: {Data["current"]["title"]} `{Data["position"]}:{Data["duration"]}`'
        )

    if message.content.startswith("!shuffle"):
        vc = Audio.getVC(message.guild)

        if not vc:
            return await message.channel.send("Please type `!join` first.")

        await vc.shuffle()

        return await message.channel.send("shuffle the queue.")

    if message.content.startswith("!queue"):
        vc = Audio.getVC(message.guild)

        if not vc:
            return await message.channel.send("Please type `!join` first.")

        State = await vc.getState()
        Queue = await vc.getQueue()
        QueueText = "\n".join(
            [str(Queue.index(Item) + 1) + ". " + Item["title"] for Item in Queue]
        )

        return await message.channel.send(
            f"""
Now playing: {State["current"]["title"]} `{State["position"]}:{State["duration"]}`

{QueueText}
"""
        )

    if message.content.startswith("!seek"):
        vc = Audio.getVC(message.guild)

        if not vc:
            return await message.channel.send("Please type `!join` first.")

        offset = int(message.content[5:].strip()) if message.content[5:].strip() else 1

        await vc.seek(offset)

        return await message.channel.send(f"seek to {offset}.")

    if message.content.startswith("!subtitle"):
        vc = Audio.getVC(message.guild)

        if not vc:
            return await message.channel.send("Please type `!join` first.")

        language = message.content[9:].strip() if message.content[9:].strip() else None
        if not language:
            return await message.channel.send("Please type language.")

        if URL_REGEX.match(language):
            url, language = language, None
        else:
            url = None

        class SubtitleCallback:
            def __init__(self):
                self._msg = None

            async def callback(self, subtitle):
                if not self._msg or message.channel.last_message.id != self._msg.id:
                    if self._msg:
                        await self._msg.delete()
                    self._msg = await message.channel.send(subtitle["current"])
                else:
                    await self._msg.edit(content=subtitle["current"])

        Data = await vc.getSubtitle(
            lang=language, url=url, callback=SubtitleCallback().callback
        )


app.run("SUPERRRSECRETTOKENNNNNN")
