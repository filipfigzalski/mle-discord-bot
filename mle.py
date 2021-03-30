import asyncio
import json
import logging
from typing import Text, List

from discord import *
from discord.ext.commands import Bot, Context, context
from discord.utils import get

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


# loading names and surnames to dictionary
logging.debug('Loading names.')
with open('names.csv', 'r', encoding='UTF-8') as file:
    lst = file.readlines()
    names = {lst[i][:-1]: 1 for i in range(0, len(lst))}

logging.debug('Loading surnames.')
with open('surnames.csv', 'r', encoding='UTF-8') as file:
    lst = file.readlines()
    surnames = {lst[i][:-1]: 1 for i in range(0, len(lst))}

# loading verified ids to dictionary
logging.debug('Loading list of verified ids.')
with open('ids.csv', 'r', encoding='UTF-8') as file:
    lst = file.readlines() 
    ids = {lst[i][:-1]: 1 for i in range(0, len(lst))}
    print('Loaded verified ids.')

# loading config
logging.debug('Loading configuration file.')
with open('config.json') as file:
    config = json.load(file)
    print('Loaded config.')


# defining bot intents
intents = Intents.all()

# creating bot
client = Bot(command_prefix= config['prefix'], intents=intents)


# declarign global variables
guild : Guild

verification_channel : TextChannel
select_role_channel : TextChannel
regulamin_channel : TextChannel
deleted_channel : TextChannel

verified_role : Role
lol_role : Role
csgo_role : Role
permitted_roles : List[Role] = []

regulamin_message : Message
select_role_message : Message

lol_emoji : Emoji
cs_emoji : Emoji

# exception for send_question function
class MemberLeft(Exception):
    pass

async def load_config():
    """Loads configuration file to variables."""
    logging.debug('Loading variables.')
    # importing globals
    global guild, verification_channel, select_role_channel, deleted_channel, regulamin_message, verified_role, lol_role, csgo_role, regulamin_message, select_role_message, lol_emoji, cs_emoji

    # guild
    guild = client.get_guild(config['id']['guild'])

    # channels
    verification_channel = client.get_channel(config['id']['channels']['verification'])
    select_role_channel = client.get_channel(config['id']['channels']['select_role'])
    regulamin_channel = client.get_channel(config['id']['channels']['regulamin'])
    deleted_channel = client.get_channel(config['id']['channels']['deleted'])

    # roles
    verified_role  = get(guild.roles, id=config['id']['roles']['verified'])
    lol_role  = get(guild.roles, id=config['id']['roles']['lol'])
    csgo_role  = get(guild.roles, id=config['id']['roles']['csgo'])
    for role in config['id']['roles']['permitted']:
        permitted_roles.append(get(guild.roles, id=role))

    # messages
    regulamin_message  = await regulamin_channel.fetch_message(config['id']['messages']['regulamin'])
    select_role_message  = await select_role_channel.fetch_message(config['id']['messages']['select_role'])

    # emotes
    lol_emoji = await guild.fetch_emoji(config['id']['emojis']['lol'])
    cs_emoji = await guild.fetch_emoji(config['id']['emojis']['cs'])


async def write_ids():
    """saves ids to file"""
    with open('ids.csv', 'w') as file:
        lines = []
        for line in list(ids.keys()):
            line += '\n'
            lines.append(line)
        file.writelines(lines)
        logging.debug('Ids written succesfully.')

async def _verify(member : Member) -> bool:
    """starts verification process of passed member"""
    logging.info(member.display_name + ' started verification process.')
    try:
        name = await send_question(member, 'Witaj na MLEsports!\nRozpoczniemy teraz weryfikację\nPodaj swoję imię:')
        surname = await send_question(member, 'Podaj swoje nazwisko:')
        city = await send_question(member, 'W jakim mieście chodzisz do szkoły:')
        school = await send_question(member, 'Do jakiej szkoły chodzisz:')
    except MemberLeft:
        logging.info(member.display_name + ' left during verification.')
        return False

    message = await member.send('Czy dane się zgadzają?\n - Imię: ' + name + '\n - Nazwisko: ' + surname + '\n - Miasto: ' + city + '\n - Szkoła średnia: ' + school)
    await message.add_reaction('👍')
    await message.add_reaction('👎')
    while True:
        try:
            def check_reaction(r : Reaction, u : User):
                # check if reaction has the same author and was sent in dms
                return u == member and str(r.emoji) in ['👍', '👎'] and isinstance(r.message.channel, DMChannel)

            # waiting for matching reaction
            reaction, user = await client.wait_for('reaction_add', check=check_reaction, timeout=1)
            break
        except asyncio.TimeoutError:
            # check if member left during verification
            if not str(member.id) in ids:
                logging.info(member.display_name + ' left during verification.')
                return False

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
            logging.info(member.display_name + ' ended verification.')
            return True

        else:
            # adding reactions for easy veryfying
            await notification.add_reaction('✅')
            await notification.add_reaction('❌')

            # sending dm
            await member.send('Hmm...\nDane które podałeś są podejrzane dla naszego bota.\nPoczekaj proszę na weryfikację przez naszych modów.')
            logging.info(member.display_name + ' gave incorrect data.')
            return False

    elif str(reaction.emoji) == '👎':
        # restart verification process
        return await _verify(member)


async def send_question(member : Member, question : str) -> str:
    # sending message
    await member.send(question)
    def check(message : Message):
        # checking if message has the same author and was sent in DMs
        return message.author == member and isinstance(message.channel, DMChannel)
    while True:
        try:
            # wait for reply
            msg = await client.wait_for('message', check=check, timeout=1)
            # return content of reply
            return msg.content
        except asyncio.TimeoutError:
            # check if member left server
            if not str(member.id) in ids:
                raise MemberLeft


def extract_id(id : str) -> int:
    """removes any non-digit characters from string and converts it to integer\n
    f.e. <@123123123> -> 123123123"""
    try:
        return int(''.join(c for c in id if c.isdigit()))
    except ValueError:
        return None

@client.event
async def on_ready():
    # changing presence to -help
    name = client.command_prefix + 'help'
    activity : Activity = Activity(type=ActivityType.listening, name=name)
    await client.change_presence(activity=activity)

    # loading all variables
    await load_config()
    logging.info('Bot ready.')


@client.event
async def on_raw_reaction_add(payload : RawReactionActionEvent):
    # reactions on verification channel
    if payload.channel_id == verification_channel.id and payload.user_id != client.user.id and str(payload.emoji) in ['🚫', '✅', '❌']:
        # loading message
        message : Message = await verification_channel.fetch_message(payload.message_id)
        
        # extracting member id from reacted message
        member_id = extract_id(message.content.split(' ', 1)[0])
        member : Member = guild.get_member(member_id)
        
        if str(payload.emoji) == '🚫':
            # removing role and nickname
            await member.remove_roles(verified_role)
            await member.edit(nick='')
            logging.info('Undone verification for ' + member.display_name)
            await verification_channel.send('🚫 **Cofnięto weryfikacje dla** ' + member.mention)
        elif str(payload.emoji) == '✅':
            await member.add_roles(verified_role)
            
            logging.info('Verification accepted for ' + member.display_name)
            # sending notification to mods with reaction
            content = member.mention + ' został zweryfikowany!'
            notification : Message = await verification_channel.send(content)
            await notification.add_reaction('🚫')

            await member.send('Weryfikacja przyjęta!\nWitamy na **MLEsports**!')
        elif str(payload.emoji) == '❌':
            logging.info('Rejected verification for ' + member.display_name)
            await member.send('Weryfikacja nie przebiegła pomyślnie, spróbuj ponownie.')
            await _verify(member)

    elif payload.message_id == regulamin_message.id:
        member : Member = guild.get_member(payload.user_id)

        # remove reactions
        await regulamin_message.remove_reaction(payload.emoji, member)
        
        # check if reaction is valid and if user didnt start verification earlier
        if str(payload.emoji) == '✅' and not str(payload.user_id) in ids :
            # add id to list of ids
            ids[str(member.id)] = 1
            await write_ids()
            # begin verification process
            await _verify(member)

    # check if reaction is on "select role" message
    elif payload.message_id == select_role_message.id:
        member : Member = guild.get_member(payload.user_id)
        # check if emoji is valid
        if payload.emoji in [cs_emoji, lol_emoji]:
            if payload.emoji == cs_emoji:
                # add role
                await member.add_roles(csgo_role)
                logging.info(member.display_name + ' selected cs_go role.')
            elif payload.emoji == lol_emoji:
                # add role
                await member.add_roles(lol_role)
                logging.info(member.display_name + ' selected lol role.')
        else:
            # remove spam reactions
            await select_role_message.remove_reaction(payload.emoji, member)


@client.event
async def on_raw_reaction_remove(payload : RawReactionActionEvent):
    # check if reaction was removed on select role message
    if payload.message_id == select_role_message.id:
            member : Member = guild.get_member(payload.user_id)
            # check if emoji is valid
            if payload.emoji in [cs_emoji, lol_emoji]:
                if payload.emoji == cs_emoji:
                    # add selected role
                    await member.remove_roles(csgo_role)
                    logging.info(member.display_name + ' removed cs_go role.')
                elif payload.emoji == lol_emoji:
                    # add selected role
                    await member.remove_roles(lol_role)
                    logging.info(member.display_name + ' removed lol role.')


@client.event
async def on_member_remove(member : Member):
    logging.info(member.display_name + ' left server.')
    # update ids
    ids.pop(str(member.id))
    await write_ids()

@client.event
async def on_raw_message_delete(payload : RawMessageDeleteEvent):
    
    content = payload.cached_message.author.mention + ' ' + payload.cached_message.channel.mention + '\n'
    content += payload.cached_message.content
    await deleted_channel.send(content)

@client.command()
async def verify(ctx : Context, *args):
    if isinstance(ctx.channel, DMChannel):
        await ctx.send('Ta komenda działa tylko na serwerze.')
        logging.info(ctx.author.display_name + ' tried to use verify command in DMs.')
        return
    # check if author has permissions
    if any(x in permitted_roles for x in ctx.author.roles):
        if (len(args) != 1):
            await ctx.send('Ta komenda wymaga jednego argumentu.')
            return
        member : Member = guild.get_member(extract_id(args[0]))
        await _verify(member)
        logging.info(ctx.author.display_name + ' stared verification process for ' + member.display_name)
    else:
        await ctx.send('Nie masz odpowiedniej roli, żeby to zrobić.')
        logging.info(ctx.author.display_name + ' tried to use verify command without right role.')

@client.command()
async def say(ctx : Context, *args : str):
    if isinstance(ctx.channel, DMChannel):
        await ctx.send('Ta komenda działa tylko na serwerze.')
        logging.info(ctx.author.display_name + ' tried to use say command in DMs.')
        return
    if any(x in permitted_roles for x in ctx.author.roles):
        # check if author has on of permitted roles
        if (len(args) != 1):
            # check if exactly one parameter was passed
            logging.info(ctx.author.display_name + ' passed wrong amount of arguments to say command.')
            await ctx.send('Ta komenda wymaga jednego argumentu.')
            return
        channel : TextChannel = guild.get_channel(extract_id(args[0]))
        if channel is None:
            # check if getting channel was succesfull
            logging.info(ctx.author.display_name + ' passed wrong channel to say command.')
            await ctx.send('Podałeś niepoprawny kanał.')
            return
        await ctx.send('Co mam napisać na kanale ' + channel.mention + ':\n(Napisz **"ANULUJ"** aby anulować komendę)')
        def check(message : Message):
            return message.author == ctx.author and message.channel == ctx.channel
        try:
            # wait for message (max 15 minutes)
            message : Message = await client.wait_for('message', check=check, timeout=900)
            # add reaction
            await message.add_reaction('👌')
            if message.content == 'ANULUJ':
                return
            # send exact copy of passed message
            logging.info(ctx.author.display_name + ' sent message using say command.')
            await channel.send(message.content)
        except asyncio.TimeoutError:
            await ctx.send('Czas upłynął.')
    else:
        await ctx.send('Nie masz odpowiedniej roli, żeby to zrobić.')
        logging.info(ctx.author.display_name + ' tried to use say command without right role.')

client.run(config['token'])
