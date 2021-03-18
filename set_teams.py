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
    members : List[Member] = await guild.fetch_members().flatten()
    
    # await guild.create_role(name=role_name, color=0x680680, mentionable=True)
    with open('teams.csv', encoding='cp1250') as file:
        for line in file.readlines():
            sections : List[str] = line.split(';')[1:]
            role_name : str = sections[0]

            role : Role = await guild.create_role(name=role_name, color=0x680680, mentionable=True)
            
            for name in sections[1:]:
                nname = ' '.join(name.split())
                if nname and any(m.display_name == nname for m in members):
                    member = guild.get_member_named(nname)
                    await member.add_roles(role)
                    print(nname, role_name, member.id)
                else:
                    print(nname, role_name, 'is missing.')


client.run(config['token'])
