from typing import List

import discord
from discord import *
from discord.ext.commands import Bot
from discord.utils import get

import json

intents = Intents.default()
intents.members = True

with open('config.json') as file:
    config = json.load(file)

client = Bot(command_prefix= config['prefix'], intents=intents)

with open('config.json', 'r') as file:
    config = json.load(file)

@client.event
async def on_ready():
    guild : Guild = client.get_guild(config['id']['guild'])
    members : List[Member] = guild.fetch_members().flatten()
    
    # await guild.create_role(name=role_name, color=0x680680, mentionable=True)
    with open('teams.csv') as file:
        for line in file.readlines():
            sections : List[str] = line.split(';')[1:]
            role_name : str = sections[0]

            role : Role = await guild.create_role(name=role_name, color=0x680680, mentionable=True)

            for name in sections[1:]:
                if name != '' and any(m.display_name == name for m in members):
                    print(name, 'is on server.')
                else:
                    print(name, 'is missing.')


client.run(config['token'])
