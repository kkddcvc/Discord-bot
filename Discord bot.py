import discord
from discord.ext import commands
import random
import os
import datetime
import asyncio

bot = commands.Bot(command_prefix='.',
                   intents=discord.Intents.all(),
                   help_command=None)

snipe_messages = {}


@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Bot Commands", color=discord.Color.blue())

    mod_commands = """
    `.kick @user` - Kick a user
    `.ban @user` - Ban a user
    `.unban user#1234` - Unban a user
    `.mute @user [minutes]` - Mute a user
    `.unmute @user` - Unmute a user
    `.warn @user` - Warn a user (3 warns = ban)
    `.clear amount` - Clear messages
    `.nuke` - Delete all messages in a channel
    """
    embed.add_field(name="🛡️ Moderation", value=mod_commands, inline=False)

    util_commands = """
    `.ping` - Check bot latency
    `.userinfo [@user]` - Get user info
    `.serverinfo` - Get server info
    `.snipe` - snipes a deleted message
    `.avatar [@user]` - Get user's avatar
    `.servericon` - Get server icon
    `.remind time message` - Set a reminder
    """
    embed.add_field(name="🔧 Utility", value=util_commands, inline=False)

    fun_commands = """
    `.hello` - Get a greeting
    `.roll NdN` - Roll dice
    `.choose option1 option2` - Choose between options
    `.joke` - Get a random joke
    `.countdown seconds` - Start a countdown
    `.poll question opt1 opt2` - Create a poll
    `.giveaway time prize` - Start a giveaway
    """
    embed.add_field(name="🎮 Fun", value=fun_commands, inline=False)

    music_commands = """
    `.play` - Play music
    `.skip` - Skip current track
    """
    embed.add_field(name="🎵 Music", value=music_commands, inline=False)

    await ctx.send(embed=embed)


# Dictionary to store warnings
warnings = {}


@bot.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')


@bot.command()
async def hello(ctx):
    await ctx.send(f'Hello {ctx.author.name}!')


@bot.command()
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f'Cleared {amount} messages.')


@bot.command()
async def kick(ctx, member: discord.Member, *, reason=None):
    if ctx.author.guild_permissions.kick_members:
        await member.kick(reason=reason)
        await ctx.send(f'Kicked {member.name} for {reason}')


@bot.command()
async def ban(ctx, member: discord.Member, *, reason=None):
    if ctx.author.guild_permissions.ban_members:
        await member.ban(reason=reason)
        await ctx.send(f'Banned {member.name} for {reason}')


@bot.command()
async def unban(ctx, *, member):
    if ctx.author.guild_permissions.ban_members:
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member.split('#')
        for ban_entry in banned_users:
            user = ban_entry.user
            if (user.name, user.discriminator) == (member_name,
                                                   member_discriminator):
                await ctx.guild.unban(user)
                await ctx.send(f'Unbanned {user.name}#{user.discriminator}')


@bot.command()
async def mute(ctx, member: discord.Member, time: int = 0):
    if ctx.author.guild_permissions.manage_roles:
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted")
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role,
                                              speak=False,
                                              send_messages=False)
        await member.add_roles(muted_role)
        if time > 0:
            await ctx.send(f'Muted {member.name} for {time} minutes')
            await asyncio.sleep(time * 60)
            await member.remove_roles(muted_role)
            await ctx.send(f'Unmuted {member.name}')
        else:
            await ctx.send(f'Muted {member.name}')


@bot.command()
async def unmute(ctx, member: discord.Member):
    if ctx.author.guild_permissions.manage_roles:
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if muted_role in member.roles:
            await member.remove_roles(muted_role)
            await ctx.send(f'Unmuted {member.name}')


@bot.command()
async def warn(ctx, member: discord.Member, *, reason=None):
    if ctx.author.guild_permissions.kick_members:
        if member.guild.id not in warnings:
            warnings[member.guild.id] = {}
        if member.id not in warnings[member.guild.id]:
            warnings[member.guild.id][member.id] = 1
        else:
            warnings[member.guild.id][member.id] += 1

        warn_count = warnings[member.guild.id][member.id]
        await ctx.send(
            f'⚠️ {member.name} has been warned for: {reason}\nWarning {warn_count}/3'
        )

        if warn_count >= 3:
            await member.ban(reason="Reached 3 warnings")
            await ctx.send(
                f'🔨 {member.name} has been banned for reaching 3 warnings.')
            del warnings[member.guild.id][member.id]


@bot.command()
async def roll(ctx, dice: str):
    try:
        rolls, limit = map(int, dice.split('d'))
        result = [str(random.randint(1, limit)) for r in range(rolls)]
        await ctx.send(', '.join(result))
    except Exception:
        await ctx.send('Format has to be in NdN!')


@bot.command()
async def choose(ctx, *choices: str):
    await ctx.send(random.choice(choices))

@bot.command()
async def nuke(ctx):
    if ctx.author.guild_permissions.administrator:
        await ctx.send("💣 Channel nuking in progress...")
        await ctx.channel.purge()
        await ctx.send("🎆 Channel has been nuked!")
    else:
        await ctx.send("❌ You need administrator permissions to use this command!")

@bot.command()
async def giveaway(ctx, time: int, *, prize):
    embed = discord.Embed(title="🎉 GIVEAWAY!", 
                         description=f"Prize: **{prize}**\nHosted by: {ctx.author.mention}\nReact with 🎉 to enter!",
                         color=discord.Color.blue())
    embed.set_footer(text=f"Ends in {time} minutes!")
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("🎉")
    
    await asyncio.sleep(time * 60)
    
    new_msg = await ctx.channel.fetch_message(msg.id)
    users = [user async for user in new_msg.reactions[0].users()]
    users.remove(bot.user)
    
    if len(users) == 0:
        await ctx.send("No one entered the giveaway 😔")
        return
        
    winner = random.choice(users)
    await ctx.send(f"🎉 Congratulations {winner.mention}! You won: **{prize}**!")


@bot.command()
async def serverinfo(ctx):
    guild = ctx.guild
    await ctx.send(f'Server Name: {guild.name}\nMembers: {guild.member_count}')


@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(f'Username: {member.name}\nJoined at: {member.joined_at}')


@bot.command()
async def play(ctx):
    await ctx.send("🎵 Would play music if configured!")


@bot.command()
async def skip(ctx):
    await ctx.send("⏭️ Would skip current track if configured!")


@bot.command()
async def joke(ctx):
    jokes = [
        "Why don't dragons tell jokes? They're afraid of dragon on!",
        "What do you call a bear with no teeth? A gummy bear!"
    ]
    await ctx.send(random.choice(jokes))


@bot.command()
async def countdown(ctx, time: str):
    try:
        if time.lower().endswith('s'):
            seconds = int(time[:-1])
        elif time.lower().endswith('m'):
            seconds = int(time[:-1]) * 60
        elif time.lower().endswith('h'):
            seconds = int(time[:-1]) * 3600
        elif time.lower().endswith('d'):
            seconds = int(time[:-1]) * 86400
        else:
            seconds = int(time)
            
        if seconds > 86400:
            await ctx.send("Please choose a shorter time (max 1 day)!")
            return
            
        msg = await ctx.send(f"Countdown: {seconds}s")
        while seconds > 0:
            seconds -= 1
            await asyncio.sleep(1)
            await msg.edit(content=f"Countdown: {seconds}s")
        await msg.edit(content="Time's up! ⏰")
    except ValueError:
        await ctx.send("Please use a valid format! Examples: 30s, 5m, 1h, 1d")


@bot.command()
async def poll(ctx, question, *options):
    if len(options) > 5:
        await ctx.send("Maximum 5 options allowed!")
        return
    emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']
    description = []
    for i, opt in enumerate(options):
        description.append(f"{emojis[i]} {opt}")
    embed = discord.Embed(title=question, description="\n".join(description))
    msg = await ctx.send(embed=embed)
    for i in range(len(options)):
        await msg.add_reaction(emojis[i])


@bot.command()
async def remind(ctx, time: int, *, reminder):
    await ctx.send(f"I'll remind you about '{reminder}' in {time} minutes!")
    await asyncio.sleep(time * 60)
    await ctx.send(f"🔔 Reminder {ctx.author.mention}: {reminder}")


@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(member.avatar.url)


@bot.command()
async def servericon(ctx):
    await ctx.send(ctx.guild.icon.url if ctx.guild.icon else "No server icon!")


@bot.event
async def on_message_delete(message):
    if not message.author.bot:
        snipe_messages[message.channel.id] = {
            'content': message.content,
            'author': message.author,
            'created_at': message.created_at
        }


@bot.command()
async def snipe(ctx):
    channel = ctx.channel
    if channel.id in snipe_messages:
        msg = snipe_messages[channel.id]
        embed = discord.Embed(description=msg['content'],
                              color=discord.Color.purple(),
                              timestamp=msg['created_at'])
        embed.set_author(name=msg['author'].name,
                         icon_url=msg['author'].avatar.url)
        embed.set_footer(text="Deleted Message")
        await ctx.send(embed=embed)
    else:
        await ctx.send("No recently deleted messages found!")


TOKEN =("DISCORD_TOKEN")
if not TOKEN:
    print("Error: DISCORD_TOKEN environment variable not set")
    exit(1)

bot.run(TOKEN)
