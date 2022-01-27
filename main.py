from operator import truediv
from xmlrpc.server import ServerHTMLDoc
import discord
import random

f = open("token.txt", "r")
token = f.read()
f.close()

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

setup = False
phase = "null"
round = 0
votes = 0
players = []
voting = []
playerCount = 0
werewolfCount = 1
victim = None
saved = None
seerAlive = False
doctorAlive = False

werewolfDone = True
seerDone = True
doctorDone = True

@client.event
async def on_ready():
    print('Logged in as {0.user} (main)\n'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user: #ignore self
        return

    if message.content.startswith('$ping'):
        await message.channel.send("$pong")
        return

    global setup, phase, round, players, voting, votes, playerCount, werewolfCount, seerAlive, doctorAlive, werewolfDone, seerDone, doctorDone

    if message.content.startswith('$start') or message.content.startswith('$begin'):
        if setup == False:
            playerRole = discord.utils.get(message.guild.roles, name="PlayingWerewolf")

            gameChannel = discord.utils.get(message.guild.channels, name="game-room")
            werewolfChannel = discord.utils.get(message.guild.channels, name="werewolves")
            seerChannel = discord.utils.get(message.guild.channels, name="seer")
            doctorChannel = discord.utils.get(message.guild.channels, name="dcotor")

            if playerRole == None:
                await message.channel.send("Error: Role 'PlayingWerewolf' does not exist")
            elif gameChannel == None:
                await message.channel.send("Error: Channel '#game-channel' does not exist")
            elif werewolfChannel == None:
                await message.channel.send("Error: Channel '#werewolf' does not exist")
            elif seerChannel == None:
                await message.channel.send("Error: Channel '#seer' does not exist")
            elif seerChannel == None:
                await message.channel.send("Error: Channel '#doctor' does not exist")
            else:
                setup = True
                await message.channel.send("Setup complete")

            return
        else:
            if phase != "null":
                await message.channel.send("Game already in session")
            else:
                #reset
                playerCount = 0
                votes = 0
                players = []
                voting = []
                saved = None

                #assign roles
                werewolfChannel = discord.utils.get(message.guild.channels, name="werewolves")
                seerChannel = discord.utils.get(message.guild.channels, name="seer")
                doctorChannel = discord.utils.get(message.guild.channels, name="doctor")
                
                playerRole = discord.utils.get(message.guild.roles, name='PlayingWerewolf')
                for player in message.guild.members:
                    if playerRole in player.roles:
                        players.append([player.id, "Villager"])
                        await werewolfChannel.set_permissions(player, view_channel=False)
                        await seerChannel.set_permissions(player, view_channel=False)
                        await doctorChannel.set_permissions(player, view_channel=False)
                        playerCount += 1

                userCount = message.guild.member_count - 1

                roles = ["Werewolf", "Seer", "Doctor"]
                for role in roles:
                    i = random.randint(0, len(players)-1)
                    while players[i][1] != "Villager":
                        i = random.randint(0, len(players)-1)
                    player = message.guild.get_member(players[i][0])

                    if role == "Werewolf":
                        await werewolfChannel.set_permissions(player, view_channel=True)
                    elif role == "Seer":
                        await seerChannel.set_permissions(player, view_channel=True)
                        seerAlive = True
                    elif role == "Doctor":
                        await doctorChannel.set_permissions(player, view_channel=True)
                        doctorAlive = True
                    players[i][1] = role
                    print(player.name + " : " + role)

                #initialise voting
                for player in message.guild.members:
                    if playerRole in player.roles:
                        voting.append([player.id, 0, False])

                #begin game
                phase = "night"
                round = 1

                gameChannel = discord.utils.get(message.guild.channels, name="game-room")
                await gameChannel.send("--------------------------------------------------------")
                await gameChannel.send("Night " + str(round))
                await werewolfChannel.send("--------------------------------------------------------")
                await werewolfChannel.send("You are werewolf. To select a target to kill: tag them.")
                await seerChannel.send("--------------------------------------------------------")
                await seerChannel.send("You are a seer. To see a target's role: tag them.")
                await doctorChannel.send("--------------------------------------------------------")
                await doctorChannel.send("You are a doctor. To protect somebody from the werewolves: tag them.")
                

                for player in players:
                    await werewolfChannel.send("<@" + str(player[0]) + ">")
                    await seerChannel.send("<@" + str(player[0]) + ">")
                    await doctorChannel.send("<@" + str(player[0]) + ">")

                await werewolfChannel.send("Select a player to kill.")
                await seerChannel.send("Select a player to see their role.")
                await doctorChannel.send("Select a player to protect.")

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
                if '<@!' in str(message.content):
                    keynote = '!'
                else:
                    keynote = '@'

                #get tagged user
                msg = str(message.content)
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
                player = message.guild.get_member(id)
                if player == None:
                    print("Invalid user tagged: " + str(id))
                    return

                playerRole = discord.utils.get(message.guild.roles, name="PlayingWerewolf")
                if playerRole not in player.roles:
                    await message.channel.send("User not playing")
                    return
                
                for i in range(playerCount):
                    if voting[i][0] == id:
                        voting[i][1]  += 1
                        votes += 1
                        await message.channel.send(str(votes) + "/" + str(playerCount))

                        if votes == playerCount or voting[i][1] > (playerCount / 2):
                            phase = "night"

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
                                await player.remove_roles(playerRole)
                                await gameChannel.send(player.name + " was lynched.")
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
                                werewolfChannel = discord.utils.get(message.guild.channels, name="werewolves")
                                seerChannel = discord.utils.get(message.guild.channels, name="seer")
                                doctorChannel = discord.utils.get(message.guild.channels, name="doctor")

                                await gameChannel.send("Night "+ str(round))
                                await werewolfChannel.send("Select a player to kill.")
                                werewolfDone = False
                                if seerAlive:
                                    await seerChannel.send("Select a player to see their role.")
                                    seerDone = False
                                if doctorAlive:
                                    await doctorChannel.send("Select a player to protect.")
                                    doctorDone = False
                            else:
                                await gameChannel.send("Villagers Win!")
                                phase = "null"
                                
                         
                        return

@client.event
async def on_reaction_add(reaction, user):
    message = reaction.message

    global seerDone, victim, werewolfDone, doctorDone, saved

    #seer
    seerChannel = discord.utils.get(message.guild.channels, name="seer")
    if message.channel == seerChannel:
        await message.remove_reaction(reaction.emoji, user)
        if seerDone == False:

            if '<@' in str(message.content) and '&' not in str(message.content): #if tag
                if '<@!' in str(message.content):
                    keynote = '!'
                else:
                    keynote = '@'

                #get tagged user
                msg = str(message.content)
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
                player = message.guild.get_member(id)
                if player == None:
                    print("Invalid user tagged: " + str(id))
                    return

                playerRole = discord.utils.get(message.guild.roles, name='PlayingWerewolf')
                if playerRole not in player.roles and player.name != victim:
                    await message.channel.send("User not playing")
                    return
                
                for player in players:
                    if player[0] == id:
                        await message.channel.send("<@" + str(id) + ">  is a " + player[1])
                
                seerDone = True
                if werewolfDone and doctorDone:
                    await NewDay(message)
        else:
            if seerAlive:
                await message.channel.send(":bonk: You've already looked at a role.")
            else:
                await message.channel.send(":bonk: You are dead.")

    #werewolf
    werewolfChannel = discord.utils.get(message.guild.channels, name="werewolves")
    if message.channel == werewolfChannel:
        await message.remove_reaction(reaction.emoji, user)
        if werewolfDone == False:

            if '<@' in str(message.content) and '&' not in str(message.content): #if tag
                if '<@!' in str(message.content):
                    keynote = '!'
                else:
                    keynote = '@'

                #get tagged user
                msg = str(message.content)
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
                player = message.guild.get_member(id)
                if player == None:
                    print("Invalid user tagged: " + str(id))
                    return

                playerRole = discord.utils.get(message.guild.roles, name="PlayingWerewolf")
                if playerRole not in player.roles:
                    await message.channel.send("User not playing")
                elif [id, "Werewolf"] in players:
                    await message.channel.send("Cannot kill a werewolf")
                else:

                    victim = player
                    await message.channel.send("<@" + str(id) + "> has been targeted.")

                    werewolfDone = True
                    if seerDone and doctorDone:
                        await NewDay(message)
            return
        else:
            await message.channel.send(":bonk: You've already killed.")

    #doctor
    doctorChannel = discord.utils.get(message.guild.channels, name="doctor")
    if message.channel == doctorChannel:
        await message.remove_reaction(reaction.emoji, user)
        if doctorDone == False:

            if '<@' in str(message.content) and '&' not in str(message.content): #if tag
                if '<@!' in str(message.content):
                    keynote = '!'
                else:
                    keynote = '@'

                #get tagged user
                msg = str(message.content)
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
                player = message.guild.get_member(id)
                if player == None:
                    print("Invalid user tagged: " + str(id))
                    return

                playerRole = discord.utils.get(message.guild.roles, name="PlayingWerewolf")
                if playerRole not in player.roles:
                    await message.channel.send("User not playing")
                    return

                saved = player
                await message.channel.send("<@" + str(id) + ">  has been protected.")

                doctorDone = True
                if werewolfDone and seerDone:
                    await NewDay(message)
        else:
            if doctorAlive:
                await message.channel.send(":bonk: You've already protected someone.")
            else:
                await message.channel.send(":bonk: You are dead.")

async def NewDay(message):
    global phase, playerCount, saved, seerAlive, doctorAlive
    gameChannel = discord.utils.get(message.guild.channels, name="game-room")
    playerRole = discord.utils.get(message.guild.roles, name="PlayingWerewolf")

    phase = "day"
    await gameChannel.send("The sun rises")

    if victim == saved:
        await gameChannel.send("Nobody has died")
    else:  
        await gameChannel.send(victim.name + " has died")
        await victim.remove_roles(playerRole)
        playerCount -= 1

        if (werewolfCount * 2) >= playerCount:
            await gameChannel.send("Werewolves Win!")
            phase = "null"
            return

        for item in voting:
            if item[0] == victim.id: #when player found
                voting.remove(item)
                break
        for item in players:
            if item[0] == victim.id: #when player found
                if item[1] == "Seer":
                    seerAlive = False
                elif item[1] == "Doctor":
                    doctorAlive = False
                    
                break
    
    saved = None

client.run(token)