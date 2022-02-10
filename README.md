# discord-werewolf

A Discord bot for hosting the classic social deduction game: Werewolf. Features roles such as Werewolf, Seer, Doctor, Drunk, and Alpha Werewolf, with suporrt for easily-added custom roles. A bot running this code will only be able to host a single game on a single server, at any given time, as use over multiple servers was not a requirement for its original purpose.

## Getting Started

### Prerequisites

This project was written for Python 3.10
- [discord.py](https://github.com/Rapptz/discord.py) will be required

The bot will require several permissions to function:

- Server Members Intent
- Manage Roles
- Manage Channels
- Read Messages/View Channels
- Send Messages
- Manage Messages
- Add Reactions

### Installing

Download the repository, and enter your bot's token into `token.txt`

### Using

To run the bot, run the `main.py` file (this will display players' roles, and so it is recommended to not have the console visible whilst playing, unless debugging)

To begin the game simply message `$start`  or `$begin` to a channel

The bot will create any required server roles that are missing, and will inform you of any missing channels, though cannot create them, so will require a  server admin to do so.  Any permission-errors will be visible in the console. If a category exists with same name as one of the game channels, this may lead to fatal errors, causing the program to crash.

### Adding Custom Roles

The bot has support for custom roles. To implement a custom role:

1. Add your role to the `config.txt` file. For example:
```
name, job='', enabled=True, evil=False, passive=True, min=0, max=None, pct=0, trigger=0
```
This will add the role to the bot

* name - name of the role
* job - verb of what the role does (for example, werewolf:'kill', doctor:'protect'). This is used in the narration messages.
* enabled - should the bot use this role?
* evil - is this role on the werewolves' team?
* passive - does this role have code to run (False) like a seer? or is it just a soft-role (True) like the drunk?
* min - mininum number required of this role
* max - maximum number required of this role
* pct - percentage of players that should be this role (e.g. 0.5 would be half of the players)
* trigger - how many players are required before this role is used?

If the role is **not** passive, then you will also need to:

2. Create a function that carries out the role's job. A template can be found in the code called `Custom()`

3. If required, alter the `NewDay()` function (if the new role influences any deaths), and add any global variables underneath the `#<roles>` header

4. In the `on_reaction_add()` function, add a call for the new function (an example can be found already in the function)

## License

Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)