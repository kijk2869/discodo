import discord
import discodo
import logging

logging.basicConfig(level=logging.INFO)


app = discord.Client()
manager = discodo.ClientManager()


@app.event
async def on_socket_response(*args, **kwargs):
    manager.discordDispatch(*args, **kwargs)


@app.event
async def on_ready():
    print("ready")


@app.event
async def on_message(message):
    if message.content == "!join":
        await app.ws.voice_state(message.guild.id, message.author.voice.channel.id)


app.run("NTAyNDczMzI1OTY1MjEzNzE4.W8iKwA.ySZVUtZ2tlSPg4QrcEWwPFaxQoo")
