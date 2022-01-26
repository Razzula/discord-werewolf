import discord
import random

f = open("token.txt", "r")
token = f.read()
f.close()

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print('Logged in as {0.user} (main)\n'.format(client))

@client.event
async def on_message(message):
    print(message.content)

client.run(token)