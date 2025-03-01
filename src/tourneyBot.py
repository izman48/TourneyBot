import discord
from discord import app_commands
from discord.interactions import Interaction
from src.tournament import teamCreator, tournamentGenerator, InvalidTournamentException
from typing import Set, List, Optional

# Constants for setup command
SETUP_ROLE_ID = 759395917924139038
ADMIN_ROLE_IDS: Set[int] = {858401896930082868, 480422236243623936}
TOURNAMENT_EMOJIS = ["🔁", "✅"]
MAX_NICKNAME_LENGTH = 32


class DudeBot(discord.Client):
    """
    A custom client class for the tournament bot.

    Attributes:
        bot_id (str): The ID of the bot user.
        tournament_emojis (list): A list of emojis used by the bot.
        current_team_message (discord.Message): The current team message.
        tree (app_commands.CommandTree): The command tree for slash commands.
    """

    def __init__(self, *args, **kwargs):
        # Set up intents for the required permissions
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.reactions = True
        kwargs["intents"] = intents
        super().__init__(*args, **kwargs)

        self.bot_id: str = ""
        self.tournament_emojis: List[str] = TOURNAMENT_EMOJIS
        self.current_team_message: Optional[discord.Message] = None
        self.teams: List[List[str]] = []
        self.tournament_creator: int = 0
        self.players: List[str] = []

        # Set up command tree for slash commands
        self.tree = app_commands.CommandTree(self)

        # Register the setup command
        @self.tree.command()
        @app_commands.checks.has_any_role(*ADMIN_ROLE_IDS)
        async def setup(
            interaction: Interaction,
            member: discord.Member,
            first_name: str,
            last_initial: str,
        ):
            """
            Setup a user by changing their nickname and removing the setup role.

            Parameters
            ----------
            member : The member to setup
            first_name : The member's first name
            last_initial : The member's last initial (single letter)
            """
            try:
                # Check if the user has already been setup
                guild = interaction.guild
                if guild is None:
                    await interaction.response.send_message(
                        "This command can only be used in a server.",
                        ephemeral=True,
                    )
                    return

                setup_role = guild.get_role(SETUP_ROLE_ID)
                is_already_setup = (
                    setup_role not in member.roles
                    and member.nick is not None
                    and member.nick != member.name
                )

                if is_already_setup:
                    await interaction.response.send_message(
                        f"{member.mention} has already been set up.",
                        ephemeral=True,
                    )
                    return

                # Get current nickname or username if no nickname
                current_name = member.name

                # Format the new nickname: FirstName "CurrentName" LastInitial
                # Calculate how much space we have for the middle part
                # Format is: FirstName + space + quote + CurrentName + quote + space + LastInitial
                # So we need 5 extra characters (2 spaces, 2 quotes, and a buffer of 1)
                extras_length = len(first_name) + 5 + len(last_initial)
                available_space = MAX_NICKNAME_LENGTH - extras_length

                # Truncate the current name if needed
                if len(current_name) > available_space:
                    truncated_name = current_name[: available_space - 3] + "..."
                else:
                    truncated_name = current_name

                # Create the new nickname
                new_nickname = f'{first_name} "{truncated_name}" {last_initial}'

                # Final check to ensure we're within limits
                if len(new_nickname) > MAX_NICKNAME_LENGTH:
                    # If still too long, reduce the first name or use initials
                    new_nickname = (
                        f'{first_name[:1]}. "{truncated_name}" {last_initial}'
                    )

                await member.edit(nick=new_nickname)

                # Remove setup role if they have it
                guild = interaction.guild
                if guild is None:
                    return

                setup_role = guild.get_role(SETUP_ROLE_ID)
                if setup_role in member.roles:
                    await member.remove_roles(setup_role)

                await interaction.response.send_message(
                    f"Successfully set up {member.mention}:\n"
                    f"• Changed nickname to: {new_nickname}\n"
                    f"• Removed setup role",
                    ephemeral=True,
                )
            except discord.Forbidden:
                await interaction.response.send_message(
                    "I don't have permission to modify this user's nickname or roles.",
                    ephemeral=True,
                )
            except Exception as e:
                await interaction.response.send_message(
                    f"An error occurred: {str(e)}", ephemeral=True
                )

        @setup.error
        async def setup_error(
            interaction: Interaction, error: app_commands.AppCommandError
        ):
            if isinstance(error, app_commands.MissingAnyRole):
                await interaction.response.send_message(
                    "You don't have permission to use this command.", ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"An error occurred: {str(error)}", ephemeral=True
                )

    async def setup_hook(self):
        """
        Called when the bot is setting up. Used to sync the command tree.
        """
        await self.tree.sync()

    async def on_ready(self):
        """
        Called when the bot is ready and logged in.
        """
        print(f"Logged on as {self.user}!")
        self.bot_id = self.user.id

    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        """
        Called when a reaction is added to a message.

        Args:
            reaction (discord.Reaction): The reaction that was added.
            user (discord.User): The user who added the reaction.
        """
        if user == self.user:
            return
        if (
            reaction.emoji == "🔁"
            and self.current_team_message is not None
            and reaction.message.id == self.current_team_message.id
            and user.id == self.tournament_creator
        ):
            await self.current_team_message.delete()
            teams = teamCreator(self.players)
            self.teams = teams
            teams_message = "\n".join(
                [
                    f"Team {i + 1}: {' '.join(players)}"
                    for i, players in enumerate(teams)
                ]
            )

            created_message = await reaction.message.channel.send(
                f"```{teams_message}```"
            )
            self.current_team_message = created_message
            for emoji in self.tournament_emojis:
                await self.current_team_message.add_reaction(emoji)
        if (
            reaction.emoji == "✅"
            and self.current_team_message is not None
            and reaction.message.id == self.current_team_message.id
            and user.id == self.tournament_creator
        ):
            for emoji in self.tournament_emojis:
                await self.current_team_message.remove_reaction(emoji, self.user)
            await self.current_team_message.channel.send(
                f"```{tournamentGenerator(self.teams)}```"
            )
            self.current_team_message = None

    async def on_message(self, message: discord.Message):
        """
        Called when a message is received.

        Args:
            message (discord.Message): The message that was received.
        """
        if not message.mentions or message.mentions[0].id != self.bot_id:
            return

        command_parts = message.content.split()
        if len(command_parts) != 2:
            return

        command = command_parts[1].lower()

        if command == "help":
            await message.channel.send(
                "```I'm a bot that can help you create teams for a tournament "
                "if you have more than 8 people in a voice channel. "
                "Just type @tourney create while in the voice channel and I'll take care of the rest.```"
            )
        elif command == "create":
            # Check if author has voice state and is in a voice channel
            if not isinstance(message.author, discord.Member):
                await message.channel.send(
                    "```Error: Command must be used in a server.```"
                )
                return

            if not message.author.voice or not message.author.voice.channel:
                await message.channel.send(
                    "```Error: You must be in a voice channel to use this command.```"
                )
                return

            voice_channel = message.author.voice.channel

            # Check if the voice channel is a type that has members
            if not hasattr(voice_channel, "members"):
                await message.channel.send(
                    "```Error: Cannot get members from this type of voice channel.```"
                )
                return

            self.players = [member.name for member in voice_channel.members]

            try:
                teams = teamCreator(self.players)
                self.teams = teams
                teams_message = "\n".join(
                    [
                        f"Team {i + 1}: {' '.join(players)}"
                        for i, players in enumerate(teams)
                    ]
                )

                created_message = await message.channel.send(f"```{teams_message}```")
                self.current_team_message = created_message
                self.tournament_creator = message.author.id

                for emoji in self.tournament_emojis:
                    await created_message.add_reaction(emoji)
            except InvalidTournamentException as e:
                await message.channel.send(f"```Error: {e}```")
