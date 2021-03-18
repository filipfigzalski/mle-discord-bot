from typing import List

import discord
from discord import *
from discord.ext.commands import Bot
from discord.utils import get

intents = Intents.default()
intents.members = True

client = Bot(command_prefix= '-', intents=intents)

with open('config.json', 'r') as file:
    config = file.json()

@client.event
async def on_ready():
    guild : Guild = client.get_guild(config['id']['guild'])
    role : Role = guild.get_role(config['id']['role']['verified'])
    ids = []
    members : List[Member] = guild.members
    for member in members:
        if role in member.roles:
            ids.append(str(member.id) + '\n')
    with open('ids.csv', 'w') as file:
        file.writelines(ids)
    print('done')

client.run(config['token'])
