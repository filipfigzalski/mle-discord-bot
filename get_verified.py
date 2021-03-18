from typing import List

import discord
from discord import *
from discord.ext.commands import Bot
from discord.utils import get

intents = Intents.default()
intents.members = True

client = Bot(command_prefix= '-', intents=intents)

@client.event
async def on_ready():
    guild : Guild = client.get_guild(789972608539426846)
    role : Role = guild.get_role(789992127769477121)
    ids = []
    members : List[Member] = guild.members
    for member in members:
        if role in member.roles:
            ids.append(str(member.id) + '\n')
    with open('ids.csv', 'w') as file:
        file.writelines(ids)
    print('done')

client.run('ODE5OTU5NDY3MTAwODY0NTEz.YEuMww.6Oq7LQ7YdOZQMpXyJlyDcR0f5GY')

