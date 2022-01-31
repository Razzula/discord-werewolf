import discord
import random
import math
from operator import truediv

f = open("token.txt", "r")
token = f.read()
f.close()

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

## VARIABLES
setup = False
phase = "null"
round = 0
votes = 0
players = []
voting = []
playerCount = 0
#werewolves
werewolfCount = 1
victim = None
werewolfDone = True
#seer
seerAlive = False
seerDone = True
#doctor
saved = None
doctorAlive = False
doctorDone = True

class Role():
    def __init__(self, name, enabled=False, evil=False, passive=True, min=0, max=None, pct=0, trigger=0, desc=''):
        self.name = name
        self.enabled = enabled
        self.evil = evil
        self.passive = passive
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

    global setup, phase, round, players, voting, votes, playerCount
    global werewolfCount, werewolfDone
    global seerAlive, seerDone
    global saved, doctorAlive, doctorDone

    if message.content.startswith('$start') or message.content.startswith('$begin'):
        if setup == False:
            playerRole = discord.utils.get(message.guild.roles, name="PlayingWerewolf")
            aliveRole = discord.utils.get(message.guild.roles, name="Alive")

            gameChannel = discord.utils.get(message.guild.channels, name="game-room")
            werewolfChannel = discord.utils.get(message.guild.channels, name="werewolf")
            seerChannel = discord.utils.get(message.guild.channels, name="seer")
            doctorChannel = discord.utils.get(message.guild.channels, name="doctor")

            if playerRole == None:
                await message.channel.send("Error: Role 'PlayingWerewolf' does not exist")
            elif playerRole == None:
                await message.channel.send("Error: Role 'Alive' does not exist")
            elif gameChannel == None:
                await message.channel.send("Error: Channel '#game-channel' does not exist")
            elif werewolfChannel == None:
                await message.channel.send("Error: Channel '#werewolf' does not exist")
            elif seerChannel == None:
                await message.channel.send("Error: Channel '#seer' does not exist")
            elif doctorChannel == None:
                await message.channel.send("Error: Channel '#doctor' does not exist")
            else:
                setup = True
                await message.channel.send("Setup complete.")

            return
        else:
            if phase != "null":
                await message.channel.send("Game already in session..")
            else:
                #reset
                playerCount = 0
                votes = 0
                players = []
                voting = []
                saved = None

                #assign roles
                werewolfChannel = discord.utils.get(message.guild.channels, name="werewolf")
                seerChannel = discord.utils.get(message.guild.channels, name="seer")
                doctorChannel = discord.utils.get(message.guild.channels, name="doctor")
                
                playerRole = discord.utils.get(message.guild.roles, name='PlayingWerewolf')
                aliveRole = discord.utils.get(message.guild.roles, name="Alive")
                for player in message.guild.members:
                    if playerRole in player.roles:
                        players.append([player.id, "Villager"])
                        await werewolfChannel.set_permissions(player, view_channel=False)
                        await seerChannel.set_permissions(player, view_channel=False)
                        await doctorChannel.set_permissions(player, view_channel=False)
                        
                        await player.add_roles(aliveRole)
                        playerCount += 1

                #enforce player min.
                if playerCount < 3:
                    await message.channel.send("Too few players are <@&" + str(playerRole.id) + "> (" + str(playerCount) + "/3)")
                    return

                #roles
                f = open('config.txt', 'r')
                config = f.readlines()
                f.close()

                roles = []
                for line in config:
                    if '#' not in line: #ignore comments
                        exec("roles.append(Role(" + line + "))")

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
                                await message.channel.send("Error: Too few players for current config requirements.")
                                setup = False
                                return

                            #assign role
                            for n in range(temp):
                                while True:
                                    i = random.randint(0, len(players)-1)
                                    if players[i][1] == "Villager":
                                        break
                                player = message.guild.get_member(players[i][0])
                                players[i][1] = role.name
                                print(player.name + " : " + role.name)

                                #permissions
                                if "Werewolf" in role.name:
                                    await werewolfChannel.set_permissions(player, view_channel=True)
                                elif role.name == "Seer":
                                    await seerChannel.set_permissions(player, view_channel=True)
                                    seerAlive = True
                                elif role.name == "Doctor":
                                    await doctorChannel.set_permissions(player, view_channel=True)
                                    doctorAlive = True
                            
                for n in range(werewolfCount - wwcounter): #werewolves
                    while True:
                        i = random.randint(0, len(players)-1)
                        if players[i][1] == "Villager":
                            break
                    player = message.guild.get_member(players[i][0])
                    players[i][1] = "Werewolf"
                    print(player.name + " : Werewolf")
                    await werewolfChannel.set_permissions(player, view_channel=True)

                #initialise voting
                for player in message.guild.members:
                    if playerRole in player.roles:
                        voting.append([player.id, 0, False])

                #begin game
                phase = "night"
                round = 1

                gameChannel = discord.utils.get(message.guild.channels, name="game-room")               
                aliveRole = discord.utils.get(message.guild.roles, name="Alive")
                await gameChannel.set_permissions(aliveRole, send_messages=False)

                await gameChannel.send("--------------------------------------------------------\nThe sun sets on the village. A full moon rises. Howling can be heard in the darkness...")
                await werewolfChannel.send("--------------------------------------------------------\nYou are werewolf. To select a target to kill: react.")
                await seerChannel.send("--------------------------------------------------------\nYou are a seer. To see a target's role: react.")
                await doctorChannel.send("--------------------------------------------------------\nYou are a doctor. To protect somebody from the werewolves: react.")               

                for player in players:
                    temp = "<@" + str(player[0]) + ">"
                    await werewolfChannel.send(temp)
                    await seerChannel.send(temp)
                    await doctorChannel.send(temp)

                    try:
                        user = message.guild.get_member(player[0])
                        await user.send("Sshh. You are a " + str(player[1]) + ".")
                    except:
                        print("Cannot message " + str(user.name))

                await werewolfChannel.send("It is night. Select a player to kill.")
                await seerChannel.send("It is night. Select a player to see their role.")
                await doctorChannel.send("It is night. Select a player to protect.")

                werewolfDone = False
                seerDone = False
                doctorDone = False
                return

    if phase == "null":
        return

    #day
    gameChannel = discord.utils.get(message.guild.channels, name="game-room")
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

                if flag == False:
                    try:            
                        await message.add_reaction('<:bonk:798539206901235773>')
                    except:
                        await message.add_reaction('👎')
                    return
                
                #vote
                for i in range(playerCount-1):
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
                                if [id, "Werewolf"] in players:
                                    werewolfCount -= 1
                                elif [id, "Seer"] in players:
                                    seerAlive = False
                                elif [id, "Doctor"] in players:
                                    doctorAlive -= 1
                            round += 1

                            if werewolfCount > 0:
                                if (werewolfCount * 2) >= playerCount:
                                    await gameChannel.send("Werewolves Win!")
                                    phase = "null"
                                    return

                                votes = 0
                                werewolfChannel = discord.utils.get(message.guild.channels, name="werewolf")
                                seerChannel = discord.utils.get(message.guild.channels, name="seer")
                                doctorChannel = discord.utils.get(message.guild.channels, name="doctor")

                                await gameChannel.send(random.choice(msgNight))
                                await werewolfChannel.send("It is night. Select a player to kill.")
                                werewolfDone = False
                                if seerAlive:
                                    await seerChannel.send("It is night. Select a player to see their role.")
                                    seerDone = False
                                if doctorAlive:
                                    await doctorChannel.send("It is night. Select a player to protect.")
                                    doctorDone = False
                            else:
                                await gameChannel.send("Villagers Win!")
                                phase = "null"

@client.event
async def on_reaction_add(reaction, user):
    message = reaction.message

    global seerDone, victim, werewolfDone, doctorDone, saved

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

## ROLES ################
# WEREWOLF
async def Werewolf(reaction, user):
    global werewolfDone, victim
    message = reaction.message

    await message.remove_reaction(reaction.emoji, user)
    if werewolfDone == False:

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

                werewolfDone = True
                if seerDone and doctorDone:
                    await NewDay(message)
        return
    else:
        await message.channel.send("<:bonk:798539206901235773> You've already killed.")

# SEER
async def Seer(reaction, user):
    global seerDone
    message = reaction.message

    await message.remove_reaction(reaction.emoji, user)
    if seerDone == False:

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
            
            seerDone = True
            if werewolfDone and doctorDone:
                await NewDay(message)
    else:
        if seerAlive:
            await message.channel.send("<:bonk:798539206901235773> You've already looked at a role.")
        else:
            await message.channel.send("<:bonk:798539206901235773> You are dead.")

# DOCTOR
async def Doctor(reaction, user):
    global doctorDone, saved
    message = reaction.message

    await message.remove_reaction(reaction.emoji, user)
    if doctorDone == False:

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

            doctorDone = True
            if werewolfDone and seerDone:
                await NewDay(message)
    else:
        if doctorAlive:
            await message.channel.send("<:bonk:798539206901235773> You've already protected someone.")
        else:
            await message.channel.send("<:bonk:798539206901235773> You are dead.")

## DAY ################
async def NewDay(message):
    global phase, playerCount, saved, seerAlive, doctorAlive
    gameChannel = discord.utils.get(message.guild.channels, name="game-room")

    phase = "day"
    await gameChannel.send("**Day "+ str(round) + "**\n" + random.choice(msgDay))

    aliveRole = discord.utils.get(message.guild.roles, name="Alive")
    await gameChannel.set_permissions(aliveRole, send_messages=True)

    if victim == saved:
        await gameChannel.send("Nobody has died.")
    else:
        aliveRole = discord.utils.get(message.guild.roles, name="Alive")  
        await victim.remove_roles(aliveRole)
        await gameChannel.send("<@" + str(victim.id) + "> has died." + random.choice(msgDeath))
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
                if item[1] == "Seer":
                    seerAlive = False
                elif item[1] == "Doctor":
                    doctorAlive = False
                    
                break
    
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