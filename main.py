import discord
import random
import math
from operator import truediv

f = open("token.txt", "r")
token = f.read()
f.close()

intents = discord.Intents.default()
intents.members = True
activity = discord.Game(name="Werewolf")
client = discord.Client(intents=intents, activity=activity)

## VARIABLES
phase = "null"
round = 0
votes = 0
players = []
voting = []
playerCount = 0
roles = []

#<roles>
#werewolves
werewolfCount = 1
victim = None
#doctor
saved = None

class Role():
    def __init__(self, name, job='', enabled=False, evil=False, passive=True, min=0, max=None, pct=0, trigger=0,):
        #gameplay
        self.name = str(name)
        self.job = str(job)
        self.passive = passive
        self.alive = 0
        self.done = True
        #role assignment
        self.enabled = enabled
        self.evil = evil
        self.min = min
        self.max = max
        self.pct = pct
        self.trigger = trigger
        
## NARRATION
msgDay = ["The sun rises.", "Day drops, day rises. Dusk is sweet, the sunrise sweeter.", "A red sun rises. Blood has been spilled this night.", "https://i.gifer.com/embedded/download/P7aO.gif"]
msgNight = ["The sun has set.", "A full moon rises. Howls can be heard in the darkness"]
msgDeath = ["Their body was found, mauled, in the nearby woods", "The body was never found, but their house is covered in claw marks..", ""]


@client.event
async def on_ready():
    print('Logged in as {0.user} (discord-werewolf)\n'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user: #ignore self
        return

    if message.content.startswith('$ping'): #for testing
        await message.channel.send("$pong")
        return

    global phase, round, players, voting, votes, playerCount, roles
    global werewolfCount
    global saved

    if message.content.startswith('$start') or message.content.startswith('$begin'):

        if phase != "null":
            await message.channel.send("Game already in session..")
            return

        #roles
        f = open('config.txt', 'r')
        config = f.readlines()
        f.close()

        roles = []
        for line in config:
            if '#' not in line: #ignore comments
                exec("roles.append(Role(" + line + "))")
 
        playerRole = discord.utils.get(message.guild.roles, name="PlayingWerewolf")
        aliveRole = discord.utils.get(message.guild.roles, name="Alive")
        gameChannel = discord.utils.get(message.guild.channels, name="village")

        flag = True

        if playerRole == None:
            await message.channel.send("Error: Role 'PlayingWerewolf' does not exist")
            flag = False
        if playerRole == None:
            await message.channel.send("Error: Role 'Alive' does not exist")
            flag = False
        if gameChannel == None:
            await message.channel.send("Error: Channel #village does not exist")
            flag = False

        for role in roles:
            if role.passive:
                continue
            roleChannel = discord.utils.get(message.guild.channels, name=role.name.lower())
            if roleChannel == None:
                await message.channel.send("Error: Channel #{} does not exist".format(role.name.lower()))
                flag = False

        roleChannel = discord.utils.get(message.guild.channels, name="werewolf")
        if roleChannel == None:
            await message.channel.send("Error: Channel #werewolf does not exist")
            flag = False

        if flag == False: #exit if there are missing roles and/or channels
            return

        #reset
        playerCount = 0
        votes = 0
        players = []
        voting = []
        saved = None

        #assign roles
        playerRole = discord.utils.get(message.guild.roles, name='PlayingWerewolf')
        aliveRole = discord.utils.get(message.guild.roles, name="Alive")
        for player in message.guild.members:
            if playerRole in player.roles:
                players.append([player.id, "Villager"])
                for role in roles:
                    if role.passive:
                        continue
                    roleChannel = discord.utils.get(message.guild.channels, name=role.name.lower())
                    await roleChannel.set_permissions(player, view_channel=False)
                
                await player.add_roles(aliveRole)
                playerCount += 1

        #enforce player min.
        if playerCount < 3:
            await message.channel.send("Too few players are <@&" + str(playerRole.id) + "> (" + str(playerCount) + "/3)")
            return

        #roles
        werewolfCount = math.floor(playerCount * 1/3)
        counter = 0
        wwcounter = 0

        for role in roles:
            if role.enabled:
                if playerCount >= role.trigger:
                    
                    if role.evil:
                        temp = math.floor(werewolfCount * role.pct)
                    else:
                        temp = math.floor(werewolfCount * role.pct)

                    #bounds contrainst
                    if role.max != None:
                        if temp > role.max:
                            temp = role.max
                    if temp < role.min:
                        temp = role.min
                    
                    if role.evil:
                        wwcounter += temp
                    else:
                        counter += temp
                    if counter + wwcounter > playerCount:
                        await message.channel.send("Too few players are <@&" + str(playerRole.id) + "> for current config requirements.")
                        return

                    role.alive = temp

                    #assign role
                    for n in range(temp):
                        while True:
                            i = random.randint(0, len(players)-1)
                            if players[i][1] == "Villager":
                                break
                        player = message.guild.get_member(players[i][0])
                        players[i][1] = role.name.title()
                        print(player.name + " : " + role.name)

                        #permissions
                        if role.passive == False:
                            roleChannel = discord.utils.get(message.guild.channels, name=role.name.lower())
                            await roleChannel.set_permissions(player, view_channel=True)
                    
        for n in range(werewolfCount - wwcounter): #werewolves
            while True:
                i = random.randint(0, len(players)-1)
                if players[i][1] == "Villager":
                    break
            player = message.guild.get_member(players[i][0])
            players[i][1] = "Werewolf"
            print(player.name + " : Werewolf")
            werewolfChannel = discord.utils.get(message.guild.channels, name="werewolf")
            await werewolfChannel.set_permissions(player, view_channel=True)

        werewolf = Role('Werewolf', job='to kill', passive=False)
        werewolf.done = False
        roles.append(werewolf)

        #initialise voting
        for player in message.guild.members:
            if playerRole in player.roles:
                voting.append([player.id, 0, False])

        #begin game
        round = 1

        gameChannel = discord.utils.get(message.guild.channels, name="village")               
        aliveRole = discord.utils.get(message.guild.roles, name="Alive")
        await gameChannel.set_permissions(aliveRole, send_messages=False)

        await gameChannel.send("--------------------------------------------------------\nThe sun sets on the village. A full moon rises. Howling can be heard in the darkness...")

        for role in roles:
            if role.passive:
                continue

            roleChannel = discord.utils.get(message.guild.channels, name=role.name.lower())
            await roleChannel.send("--------------------------------------------------------\nYou are a {}. To select a target to {}: react.".format(role.name, role.job))

            #list players
            for player in players:
                temp = "<@" + str(player[0]) + ">"
                await roleChannel.send(temp)

            await roleChannel.send("It is night. Select a player to " + role.job)
            role.done = False

        for player in players:
            try:
                user = message.guild.get_member(player[0])
                await user.send("Sshh. You are a " + str(player[1]) + ".")
            except:
                print("Cannot message " + str(user.name))
        
        phase = "night"
        return

    if phase == "null":
        return

    #day
    gameChannel = discord.utils.get(message.guild.channels, name="village")
    if message.channel == gameChannel:
        if phase == "day":

            if '<@' in str(message.content) and '&' not in str(message.content): #if tag
                id = GetPlayerID(message.content)
                player = message.guild.get_member(id)
                if player == None:
                    print("Invalid user tagged: " + str(id))
                    return

                playerRole = discord.utils.get(message.guild.roles, name="PlayingWerewolf")
                aliveRole = discord.utils.get(message.guild.roles, name="Alive")
                if playerRole not in player.roles:
                    await message.channel.send("User not playing")
                    return
                elif aliveRole not in player.roles:
                    await message.channel.send("Player not alive")
                    return
                
                #is user allowed to vote?
                flag = False
                for n in range(playerCount):
                    if voting[n][0] == message.author.id:
                        flag = True
                        if voting[n][2] == False:
                            break
                        else:
                            try:            
                                await message.add_reaction('<:bonk:798539206901235773>')
                            except:
                                await message.add_reaction('👎')
                            return

                #prevent non-players from voting
                if flag == False:
                    try:            
                        await message.add_reaction('<:bonk:798539206901235773>')
                    except:
                        await message.add_reaction('👎')
                    return
                
                #vote
                for i in range(playerCount):
                    if voting[i][0] == id:
                        voting[n][2] = True
                        voting[i][1] += 1
                        votes += 1
                        await message.channel.send(str(votes) + "/" + str(playerCount))

                        if votes == playerCount or voting[i][1] > (playerCount / 2):
                            phase = "night"
                            await gameChannel.set_permissions(aliveRole, send_messages=False)

                            #kill most voted
                            max = 0
                            id = 0
                            item = []
                            tie = False
                            for i in range(playerCount):
                                if voting[i][1] > max:
                                    max = voting[i][1]
                                    item = voting[i]
                                    id = voting[i][0]
                                    tie = False
                                elif voting[i][1] == max:
                                    tie = True
                                voting[i][1] = 0
                            
                            if tie:
                                await gameChannel.send("Voting tied. Nobody was lynched.")
                            else:
                                player = message.guild.get_member(id)
                                await player.remove_roles(aliveRole)
                                await gameChannel.send("<@" + str(player.id) + "> was lynched.")
                                playerCount -= 1
                                voting.remove(item)
                                
                                if [id, 'Werewolf'] in players:
                                    werewolfCount -= 1
                                else:
                                    for role in roles:
                                        if role.passive:
                                            continue
                                        #if deceased was of special role, ensure the life counter is decremented
                                        if [id, role.name.title()] in players:
                                            role.alive -= 1
                            round += 1

                            if werewolfCount > 0:
                                if (werewolfCount * 2) >= playerCount:
                                    await gameChannel.send("Werewolves Win!")
                                    phase = "null"
                                    return

                                votes = 0

                                await gameChannel.send(random.choice(msgNight))
                                #only continue with living roles
                                for role in roles:
                                    if role.passive:
                                        continue
                                    if role.alive > 0 or role.name == "Werewolf":
                                        roleChannel = discord.utils.get(message.guild.channels, name=role.name.lower())
                                        await roleChannel.send("It is night. Select a player to " + role.job + ".")
                                        role.done = False

                            else:
                                await gameChannel.send("Villagers Win!")
                                phase = "null"
                        
                        return

@client.event
async def on_reaction_add(reaction, user):
    message = reaction.message

    #<roles>
    #seer
    seerChannel = discord.utils.get(message.guild.channels, name="seer")
    if message.channel == seerChannel:
        await Seer(reaction, user)

    #werewolf
    werewolfChannel = discord.utils.get(message.guild.channels, name="werewolf")
    if message.channel == werewolfChannel:
        await Werewolf(reaction, user)
        
    #doctor
    doctorChannel = discord.utils.get(message.guild.channels, name="doctor")
    if message.channel == doctorChannel:
        await Doctor(reaction, user)

    ## EXAMPLE OF CUSTOM ROLE
    # import custom.py
    # customChannel = discord.utils.get(message.guild.channels, name="customName")
    # if message.channel == customChannel:
    #     await custom.Custom(reaction, user)

## ROLES ################
# WEREWOLF
async def Werewolf(reaction, user):
    global victim
    message = reaction.message

    await message.remove_reaction(reaction.emoji, user)
    for role in roles:
        if role.name == "Werewolf":
            if role.done== False:

                if '<@' in str(message.content) and '&' not in str(message.content): #if tag
                    id = GetPlayerID(message.content)
                    player = message.guild.get_member(id)
                    if player == None:
                        print("Invalid user tagged: " + str(id))
                        return

                    playerRole = discord.utils.get(message.guild.roles, name="PlayingWerewolf")
                    aliveRole = discord.utils.get(message.guild.roles, name="Alive")
                    if playerRole not in player.roles:
                        await message.channel.send("User not playing.")
                    elif aliveRole not in player.roles:
                        await message.channel.send("Player already dead.")
                    elif [id, "Werewolf"] in players:
                        await message.channel.send("Cannot kill a werewolf..")
                    else:

                        victim = player
                        await message.channel.send("<@" + str(id) + "> has been targeted.")

                        temp = True
                        role.done = True
                        for otherRole in roles:
                            if otherRole.done == False:
                                temp = False
                                break
                        if temp:
                            await NewDay(message)
                return
            else:
                await message.channel.send("<:bonk:798539206901235773> You've already killed.")

# SEER
async def Seer(reaction, user):
    message = reaction.message

    await message.remove_reaction(reaction.emoji, user)
    for role in roles:
        if role.name == "Seer":
            if role.done== False:

                if '<@' in str(message.content) and '&' not in str(message.content): #if tag
                    id = GetPlayerID(message.content)
                    player = message.guild.get_member(id)
                    if player == None:
                        print("Invalid user tagged: " + str(id))
                        return

                    playerRole = discord.utils.get(message.guild.roles, name='PlayingWerewolf')
                    aliveRole = discord.utils.get(message.guild.roles, name="Alive")
                    if playerRole not in player.roles and player.name != victim:
                        await message.channel.send("User not playing")
                        return
                    elif aliveRole not in player.roles:
                        await message.channel.send("Player not alive")
                        return
                    
                    for player in players:
                        if player[0] == id:
                            await message.channel.send("<@" + str(id) + ">  is a " + player[1])
                    
                    temp = True
                    role.done = True
                    for otherRole in roles:
                        if otherRole.done == False:
                            temp = False
                            break
                    if temp:
                        await NewDay(message)
            else:
                if role.alive > 0:
                    await message.channel.send("<:bonk:798539206901235773> You've already looked at a role.")
                else:
                    await message.channel.send("<:bonk:798539206901235773> You are dead.")

# DOCTOR
async def Doctor(reaction, user):
    global saved
    message = reaction.message

    await message.remove_reaction(reaction.emoji, user)
    for role in roles:
        if role.name == "Doctor":
            if role.done== False:

                if '<@' in str(message.content) and '&' not in str(message.content): #if tag
                    id = GetPlayerID(message.content)
                    player = message.guild.get_member(id)
                    if player == None:
                        print("Invalid user tagged: " + str(id))
                        return

                    playerRole = discord.utils.get(message.guild.roles, name="PlayingWerewolf")
                    aliveRole = discord.utils.get(message.guild.roles, name="Alive")
                    if playerRole not in player.roles:
                        await message.channel.send("User not playing")
                        return
                    elif aliveRole not in player.roles:
                        await message.channel.send("Player already dead")
                        return

                    saved = player
                    await message.channel.send("<@" + str(id) + ">  has been protected.")

                    temp = True
                    role.done = True
                    for otherRole in roles:
                        if otherRole.done == False:
                            temp = False
                            break
                    if temp:
                        await NewDay(message)
            else:
                if role.alive > 0:
                    await message.channel.send("<:bonk:798539206901235773> You've already protected someone.")
                else:
                    await message.channel.send("<:bonk:798539206901235773> You are dead.")

## EXAMPLE OF A CUSTOM ROLE
# async def Custom(reaction, user):
#     message = reaction.message

#     await message.remove_reaction(reaction.emoji, user)
#     for role in roles:
#         if role.name == "Custom":
#             if role.done== False:

#                 if '<@' in str(message.content) and '&' not in str(message.content): #if tag
#                     id = GetPlayerID(message.content)
#                     player = message.guild.get_member(id)
#                     if player == None:
#                         print("Invalid user tagged: " + str(id))
#                         return

#                     ## CODE GOES HERE
                    
#                     temp = True
#                     role.done = True
#                     for otherRole in roles:
#                         if otherRole.done == False:
#                             temp = False
#                             break
#                     if temp:
#                         await NewDay(message)
#             else:
#                 if role.alive > 0:
#                     await message.channel.send("<:bonk:798539206901235773> You've already done.")
#                 else:
#                     await message.channel.send("<:bonk:798539206901235773> You are dead.")

## DAY ################
async def NewDay(message):
    global phase, playerCount, saved
    gameChannel = discord.utils.get(message.guild.channels, name="village")

    phase = "day"
    await gameChannel.send("**Day "+ str(round) + "**\n" + random.choice(msgDay))

    aliveRole = discord.utils.get(message.guild.roles, name="Alive")
    await gameChannel.set_permissions(aliveRole, send_messages=True)

    if victim == saved:
        await gameChannel.send("Nobody has died.")
    else:
        await victim.remove_roles(aliveRole)
        await gameChannel.send("<@" + str(victim.id) + "> has died. " + random.choice(msgDeath))
        playerCount -= 1

        if (werewolfCount * 2) >= playerCount:
            await gameChannel.send("Werewolves Win!")
            phase = "null"
            return

        for i in range(len(voting)-1):
            if voting[i][0] == victim.id: #when player found
                voting.remove(voting[i])
            voting[i][2] = False
        for item in players:
            if item[0] == victim.id: #when player found
                #if victim was of
                for role in roles:
                    if role.name == item[1]:
                        role.alive -= 1
                        break                  
                break
    
    #doctor
    saved = None

## COMMON ################
# get a player's ID from a tag in a message
def GetPlayerID(text):
    if '<@!' in str(text):
        keynote = '!'
    else:
        keynote = '@'

    #get tagged user
    msg = str(text)
    temp = ''
    flag = False
    for i in range(len(msg)):
        if msg[i] == keynote:
            flag = True
            continue
        if flag:
            if msg[i] == '>':
                break
            else:
                temp += msg[i]
    id = int(temp)
    return id

client.run(token)