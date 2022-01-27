from operator import truediv
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
deaths = 0
votes = 0
voting = []
playerCount = 0
werewolfCount = 1

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

    global setup, phase, round, deaths, voting,  votes, playerCount, werewolfCount

    if message.content.startswith('$start') or message.content.startswith('$begin'):
        if setup == False:
            werewolfRole = discord.utils.get(message.guild.roles, name="Werewolf")
            seerRole = discord.utils.get(message.guild.roles, name="Seer")
            playerRole = discord.utils.get(message.guild.roles, name="PlayingWerewolf")

            gameChannel = discord.utils.get(message.guild.channels, name="game-room")
            werewolfChannel = discord.utils.get(message.guild.channels, name="werewolves")
            seerChannel = discord.utils.get(message.guild.channels, name="seer")

            if playerRole == None:
                await message.channel.send("Error: Role 'PlayingWerewolf' does not exist")
            elif werewolfRole == None:
                await message.channel.send("Error: Role 'Werewolf' does not exist")
            elif seerRole == None:
                await message.channel.send("Error: Role 'Seer' does not exist")
            elif gameChannel == None:
                await message.channel.send("Error: Channel '#game-channel' does not exist")
            elif werewolfChannel == None:
                await message.channel.send("Error: Role '#werewolf' does not exist")
            elif seerChannel == None:
                await message.channel.send("Error: Role '#seer' does not exist")
            else:
                setup = True
                await message.channel.send("Setup complete")

            return
        else:
            if phase != "null":
                await message.channel.send("Game already in session")
            else:
                #assign roles
                playerRole = discord.utils.get(message.guild.roles, name='PlayingWerewolf')
                werewolfRole = discord.utils.get(message.guild.roles, name="Werewolf")
                seerRole = discord.utils.get(message.guild.roles, name="Seer")

                userCount = message.guild.member_count - 1

                for user in message.guild.members:
                    if playerRole in user.roles:
                        playerCount += 1

                #werewolves
                for i in range(werewolfCount):
                    player = message.guild.members[random.randint(0, userCount)]
                    while werewolfRole in player.roles or playerRole not in player.roles:
                        player = message.guild.members[random.randint(0, userCount)]

                    await player.add_roles(werewolfRole)
                #seer
                while werewolfRole in player.roles or playerRole not in player.roles:
                    player = message.guild.members[random.randint(0, userCount)]
                await player.add_roles(seerRole)

                #initialise voting
                for player in message.guild.members:
                    if playerRole in player.roles:
                        voting.append([player.id, 0, False])

                #begin game
                phase = "seer"
                round = 1

                gameChannel = discord.utils.get(message.guild.channels, name="game-room")
                werewolfChannel = discord.utils.get(message.guild.channels, name="werewolves")
                seerChannel = discord.utils.get(message.guild.channels, name="seer")
                await gameChannel.send("--------------------------------------------------------")
                await gameChannel.send("Night " + str(round))
                await werewolfChannel.send("--------------------------------------------------------")
                await werewolfChannel.send("You are werewolf. To select a target to kill: tag them.")
                await seerChannel.send("--------------------------------------------------------")
                await seerChannel.send("You are seer. To see a target's role: tag them.")
                await seerChannel.send("Select a player to see their role.")
                return

    #seer
    seerChannel = discord.utils.get(message.guild.channels, name="seer")
    if message.channel == seerChannel:
        if phase == "seer":

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
                werewolfRole = discord.utils.get(message.guild.roles, name="Werewolf")
                seerRole = discord.utils.get(message.guild.roles, name="Seer")
                if playerRole not in player.roles:
                    await message.channel.send("User not playing")
                    return
                if werewolfRole in player.roles:
                    await message.channel.send("That player is a werewolf")
                elif seerRole in player.roles:
                    await message.channel.send("You are the seer... dummy")
                else:
                    await message.channel.send("That player is a villager")
                phase = "werewolf"

                werewolfChannel = discord.utils.get(message.guild.channels, name="werewolves")
                await werewolfChannel.send("Select a player to kill.")

    #werewolf
    werewolfChannel = discord.utils.get(message.guild.channels, name="werewolves")
    if message.channel == werewolfChannel:
        if phase == "werewolf":

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
                werewolfRole = discord.utils.get(message.guild.roles, name="Werewolf")
                if playerRole not in player.roles:
                    await message.channel.send("User not playing")
                elif werewolfRole in player.roles:
                    await message.channel.send("Cannot kill a werewolf")
                else:
                    await player.remove_roles(playerRole)

                    for item in voting:
                        if item[0] == id:
                            voting.remove(item)
                            break

                    gameChannel = discord.utils.get(message.guild.channels, name="game-room")
                    await gameChannel.send("The sun rises")
                    votes = 0
                    await gameChannel.send(player.name + " has died")
                    playerCount -= 1

                    phase = "day"
            return
        else:
            await message.channel.send(":bonk: It is not night.")

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
                        if votes == playerCount or voting[i][1] > (playerCount / 2):
                            phase = "seer"

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
                                werewolfRole = discord.utils.get(message.guild.roles, name="Werewolf")
                                if werewolfRole in player.roles:
                                    werewolfCount -= 1
                            round += 1

                            if werewolfCount > 0:
                                if (werewolfCount * 2) >= playerCount - 1: #change if doctor or witch
                                    await gameChannel.send("Werewolves Win!")
                                    phase = "null"
                                    return
                                await gameChannel.send("Night "+ str(round))
                                await seerChannel.send("Select a player to see their role.")
                            else:
                                await gameChannel.send("Villagers Win!")
                                phase = "null"
                                
                         
                        return

client.run(token)