import json

import discord
from discord import *
from discord.ext.commands import Bot, Context
from discord.utils import get


print('Starting up bot.')

# loading names and surnames to dictionary
with open('names.csv', 'r', encoding='UTF-8') as file:
    lst = file.readlines()
    names = {lst[i][:-1]: 1 for i in range(0, len(lst))}
    print('Names loaded.')

with open('surnames.csv', 'r', encoding='UTF-8') as file:
    lst = file.readlines()
    surnames = {lst[i][:-1]: 1 for i in range(0, len(lst))}
    print('Surnames loaded.')

# loading verified ids to dictionary
with open('ids.csv', 'r', encoding='UTF-8') as file:
    lst = file.readlines() 
    ids = {lst[i][:-1]: 1 for i in range(0, len(lst))}
    print('Loaded verified ids.')

# loading config
with open('config.json') as file:
    config = json.load(file)
    print('Loaded config.')


# defining bot intents
intents = Intents.default()
intents.members = True


# creating bot
client = Bot(command_prefix= config['prefix'], intents=intents)


# declarign global variables
guild : Guild

verification_channel : TextChannel
select_role_channel : TextChannel
regulamin_channel : TextChannel

verified_role : Role
lol_role : Role
csgo_role : Role

regulamin_message : Message
select_role_message : Message

lol_emoji : Emoji
cs_emoji : Emoji

async def load_config():
    # importing globals
    global guild, verification_channel, select_role_channel, regulamin_message, verified_role, lol_role, csgo_role, regulamin_message, select_role_message, lol_emoji, cs_emoji

    # guild
    guild = client.get_guild(config['id']['guild'])

    # channels
    verification_channel = client.get_channel(config['id']['channels']['verification'])
    select_role_channel = client.get_channel(config['id']['channels']['select_role'])
    regulamin_channel = client.get_channel(config['id']['channels']['regulamin'])

    # roles
    verified_role  = get(guild.roles, id=config['id']['roles']['verified'])
    lol_role  = get(guild.roles, id=config['id']['roles']['lol'])
    csgo_role  = get(guild.roles, id=config['id']['roles']['csgo'])

    # messages
    regulamin_message  = await regulamin_channel.fetch_message(config['id']['messages']['regulamin'])
    select_role_message  = await select_role_channel.fetch_message(config['id']['messages']['select_role'])

    # emotes
    lol_emoji = await guild.fetch_emoji(config['id']['emojis']['lol'])
    cs_emoji = await guild.fetch_emoji(config['id']['emojis']['cs'])


async def write_ids():
    # saves ids to file
    with open('ids.csv', 'w') as file:
        lines = []
        for line in list(ids.keys()):
            line += '\n'
            lines.append(line)
        file.writelines(lines)
        print('Ids written succesfully.')

async def _verify(member : Member):
    await member.send('Witaj na MLEsports!\nRozpoczniemy teraz weryfikację\nPodaj swoję imię:')

    def check_message(m : Message):
        # checks if message has the same author and was sent in dms
        return m.author == member and isinstance(m.channel, DMChannel)
    
    # asking few simple questions
    message = await client.wait_for('message', check=check_message)
    name = message.content

    await member.send('Podaj swoje nazwisko:')
    message = await client.wait_for('message', check=check_message)
    surname = message.content

    await member.send('W jakim mieście chodzisz do szkoły:')
    message = await client.wait_for('message', check=check_message)
    city = message.content

    await member.send('Jak nazywa się twoja szkoła średnia:')
    message = await client.wait_for('message', check=check_message)
    school = message.content

    message = await member.send('Czy dane się zgadzają?\n - Imię: ' + name + '\n - Nazwisko: ' + surname + '\n - Miasto: ' + city + '\n - Szkoła średnia: ' + school)
    await message.add_reaction('👍')
    await message.add_reaction('👎')

    def check_reaction(r : Reaction, u : User):
        # check if reaction has the same author and was sent in dms
        return u == member and str(r.emoji) in ['👍', '👎'] and isinstance(r.message.channel, DMChannel)

    # waiting for matching reaction
    reaction, user = await client.wait_for('reaction_add', check=check_reaction)

    if str(reaction.emoji) == '👍':
        # sending message to mods channel
        content = member.mention + ' ' + name + ' ' + surname + ' ' +  city + ' ' +  school
        notification : Message = await verification_channel.send(content)
        # checking if name and surname are valid
        if name.upper() in names and surname.upper() in surnames:
            await notification.add_reaction('🚫')

            # changing nickname and giving role 
            nick = name.capitalize() + ' ' + surname.capitalize()
            await member.edit(nick=nick)
            await member.add_roles(verified_role)

            # sending dm
            await member.send('Dziękujemy za weryfikację :3')

        else:
            # adding reactions for easy veryfying
            await notification.add_reaction('✅')
            await notification.add_reaction('❌')

            # sending dm
            await member.send('Hmm...\nDane które podałeś są podejrzane dla naszego bota.\nPoczekaj proszę na weryfikację przez naszych modów.')

            
    elif str(reaction.emoji) == '👎':
        # restart verification process
        await _verify(member)


@client.event
async def on_ready():
    # changing presence to -help
    name = client.command_prefix + 'help'
    activity : Activity = Activity(type=ActivityType.listening, name=name)
    await client.change_presence(activity=activity)

    # loading all variables
    await load_config()

    # console message
    print('Bot ready.')


@client.event
async def on_raw_reaction_add(payload : RawReactionActionEvent):
    # reactions on verification channel
    if payload.channel_id == verification_channel.id and payload.user_id != client.user.id and str(payload.emoji) in ['🚫', '✅', '❌']:
        # fetching message
        message : Message = await verification_channel.fetch_message(payload.message_id)
        
        # extracting member id from reacted message
        member_id =  int(''.join(c for c in message.content.split(' ', 1)[0] if c.isdigit()))
        member : Member = guild.get_member(member_id)
        
        if str(payload.emoji) == '🚫':
            # removing role and nickname
            await member.remove_roles(verified_role)
            await member.edit(nick='')
            await verification_channel.send('🚫 **Cofnięto weryfikacje dla** ' + member.mention)
        elif str(payload.emoji) == '✅':
            await member.add_roles(verified_role)
            
            # sending notification to mods with reaction
            content = member.mention + ' został zweryfikowany!'
            notification : Message = await verification_channel.send(content)
            await notification.add_reaction('🚫')

            await member.send('Weryfikacja przyjęta!\nWitamy na **MLEsports**!')
        elif str(payload.emoji) == '❌':
            await member.send('Weryfikacja nie przebiegła pomyślnie, spróbuj ponownie')
            await _verify(member)

    elif payload.message_id == regulamin_message.id:
        member : Member = guild.get_member(payload.user_id)

        # remove reactions
        await regulamin_message.remove_reaction(payload.emoji, member)
        
        if str(payload.emoji) == '✅' and not str(payload.user_id) in ids :
            print(member.display_name + ' started verification process.')

            # add id to list of ids
            ids[str(member.id)] = 1
            await write_ids()
            # begin verification process
            await _verify(member)
            print(member.display_name + ' ended verification process.')


    elif payload.message_id == select_role_message.id:
        member : Member = guild.get_member(payload.user_id)
        if payload.emoji in [cs_emoji, lol_emoji]:
            if payload.emoji == cs_emoji:
                await member.add_roles(csgo_role)
                print(member.display_name + ' selected cs_go role.')
            elif payload.emoji == lol_emoji:
                await member.add_roles(lol_role)
                print(member.display_name + ' selected lol role.')

        else:
            # remove spam reactions
            await select_role_message.remove_reaction(payload.emoji, member)


@client.event
async def on_raw_reaction_remove(payload : RawReactionActionEvent):
    if payload.message_id == select_role_message.id:
            member : Member = guild.get_member(payload.user_id)
            if payload.emoji in [cs_emoji, lol_emoji]:
                if payload.emoji == cs_emoji:
                    await member.remove_roles(csgo_role)
                    print(member.display_name + ' removed cs_go role.')
                elif payload.emoji == lol_emoji:
                    await member.remove_roles(lol_role)
                    print(member.display_name + ' removed lol role.')


@client.event
async def on_member_remove(member : Member):
    print(member.display_name + ' left server.')
    ids.pop(str(member.id))
    await write_ids()

@client.command()
async def verify(ctx : Context, arg):
    author = await guild.fetch_member(ctx.author.id)
    if author.guild_permissions.manage_roles:
        member_id = arg[3:-1]
        member : Member = await guild.fetch_member(member_id)
        await _verify(member)
    else:
        await ctx.send('You don\'t have permission to do this!')

client.run(config['token'])

