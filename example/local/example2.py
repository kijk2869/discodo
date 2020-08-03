"""

This example isn't recommended in production.
Just use it only to learn the structure.
This code is not perfect and can be complex.


Additionally, remote is recommended for efficient performance management.
Just know there is a way to do this.

"""

import logging

import discord
from discord.ext.commands import Bot

import discodo



class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.Audio = discodo.self.AudioManager()

    @commands.Cog.listener()
    async def on_socket_response(self, payload):
        self.Audio.discordDispatch(payload)

    @commands.Cog.listener()
    async def on_ready(self):
        print("bot is now ready.")

    @commands.command(name="join")
    async def _join(self, ctx):
        if not ctx.author.voice:
            return await ctx.send("Join the voice channel first.")

        await self.bot.ws.voice_state(ctx.guild.id, ctx.author.voice.channel.id)
        return await ctx.send(f"Connected to {ctx.author.voice.channel.id}.")

    @commands.command(name="stop")
    async def _stop(self, ctx):
        vc = self.Audio.getVC(ctx.guild.id)

        if not vc:
            return await ctx.send("Please type `!join` first.")

        await vc.destroy()

        return await ctx.send("Player stopped and cleaned the queue.")

    @commands.command(name="play")
    async def _play(self, ctx, music):
        vc = self.Audio.getVC(ctx.guild.id)

        if not vc:
            return await ctx.send("Please type `!join` first.")

        Song = await vc.loadSong(music)

        if isinstance(Song, list):
            return await ctx.send(
                f"{len(Song) - 1} songs except {Song[0].title} added."
            )
        else:
            return await ctx.send(f"{Song.title} added.")

    @commands.command(name="skip")
    async def _skip(self, ctx, offset: int = 1):
        vc = self.Audio.getVC(ctx.guild.id)

        if not vc:
            return await ctx.send("Please type `!join` first.")

        vc.skip(offset)

        return await ctx.send(f"{offset} skipped.")

    @commands.command(name="volume")
    async def _volume(self, ctx, offset: int = 100):
        vc = self.Audio.getVC(ctx.guild.id)

        if not vc:
            return await ctx.send("Please type `!join` first.")

        Volume = vc.setVolume(offset / 100)

        return await ctx.send(f"Set volume to {Volume * 100}%.")

    @commands.command(name="crossfade")
    async def _crossfade(self, ctx, offset: int = 10):
        vc = self.Audio.getVC(ctx.guild.id)

        if not vc:
            return await ctx.send("Please type `!join` first.")

        Crossfade = vc.setCrossfade(offset)

        return await ctx.send(f"Set crossfade seconds to {Crossfade} seconds.")

    @commands.command(name="autoplay")
    async def _autoplay(self, ctx, offset: str = "on"):
        vc = self.Audio.getVC(ctx.guild.id)

        if not vc:
            return await ctx.send("Please type `!join` first.")

        offset = {"on": True, "off": False}.get(offset, True)

        autoplay = vc.setAutoplay(offset)

        return await ctx.send(
            f'Auto related play {"enabled" if autoplay else "disabled"}.'
        )

    @commands.command(name="repeat")
    async def _repeat(self, ctx, offset: str = "on"):
        vc = self.Audio.getVC(ctx.guild.id)

        if not vc:
            return await ctx.send("Please type `!join` first.")

        offset = {"on": True, "off": False}.get(offset, True)

        repeat = vc.setRepeat(offset)

        return await ctx.send(f'Repeat {"enabled" if repeat else "disabled"}.')

    @commands.command(name="np")
    async def _np(self, ctx):
        vc = self.Audio.getVC(ctx.guild.id)

        if not vc:
            return await ctx.send("Please type `!join` first.")

        return await ctx.send(
            f"Now playing: {vc.player.current.title} `{vc.player.current.duration}:{vc.player.current.self.AudioData.duration}`"
        )

    @commands.command(name="shuffle")
    async def _shuffle(self, ctx):
        vc = self.Audio.getVC(ctx.guild.id)

        if not vc:
            return await ctx.send("Please type `!join` first.")

        vc.shuffle()

        return await ctx.send("Shuffle the queue.")

    @commands.command(name="queue")
    async def _queue(self, ctx):
        vc = self.Audio.getVC(ctx.guild.id)

        if not vc:
            return await ctx.send("Please type `!join` first.")

        QueueText = "\n".join(
            [str(vc.Queue.index(Item) + 1) + ". " + Item.title for Item in vc.Queue]
        )

        return await ctx.send(
            f"""
Now playing: {vc.player.current.title} `{vc.player.current.duration}:{vc.player.current.self.AudioData.duration}`

{QueueText}
"""
        )

    @commands.command(name="bassboost")
    async def _bassboost(self, ctx, offset: int = 0):
        vc = self.Audio.getVC(ctx.guild)

        if not vc:
            return await ctx.send("Please type `!join` first.")

        filter = (
            {"anequalizer": discodo.equalizer.bassboost(offset)} if offset != 0 else {}
        )

        vc.setFilter(filter)

        return await ctx.send(f"Set bassboost level {offset}%.")

    @commands.command(name="tempo")
    async def _tempo(self, ctx, offset: float = 1.0):
        vc = self.Audio.getVC(ctx.guild)

        if not vc:
            return await ctx.send("Please type `!join` first.")

        vc.setFilter({"atempo": str(offset)})

        return await ctx.send(f"Set tempo to {offset}.")

    @commands.command(name="seek")
    async def _seek(self, ctx, offset: int = 1):
        vc = self.self.Audio.getVC(ctx.guild)

        if not vc:
            return await ctx.send("Please type `!join` first.")

        vc.seek(offset)

        return await ctx.send(f"Seek to {offset}.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bot = Bot(command_prefix="!")
    bot.add_cog(MusicBot(bot))
    bot.run("SUPERRRSECRETTOKENNNNNN")
