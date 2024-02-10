import os
import discord
from tournament import teamCreator, InvalidTournamentException
from dotenv import load_dotenv


class MyClient(discord.Client):
    """
    A custom client class for the tournament bot.

    Attributes:
        bot_id (str): The ID of the bot user.
        my_emojis (list): A list of emojis used by the bot.
        current_team_message (discord.Message): The current team message.

    Methods:
        on_ready(): Called when the bot is ready and logged in.
        on_reaction_add(reaction, user): Called when a reaction is added to a message.
        on_message(message): Called when a message is received.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot_id = ""
        self.my_emojis = ["🔁", "✅"]
        self.current_team_message = None

    async def on_ready(self):
        """
        Called when the bot is ready and logged in.
        """
        print(f"Logged on as {self.user}!")
        self.bot_id = self.user.id

    async def on_reaction_add(self, reaction, user):
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
        ):
            await self.current_team_message.delete()
            teams = teamCreator(self.players)
            teams_message = "\n".join(
                [f"Team {i+1}: {' '.join(players)}" for i, players in enumerate(teams)]
            )

            created_message = await reaction.message.channel.send(
                f"```{teams_message}```"
            )
            self.current_team_message = created_message
            for emoji in self.my_emojis:
                await self.current_team_message.add_reaction(emoji)
        if (
            reaction.emoji == "✅"
            and self.current_team_message is not None
            and reaction.message.id == self.current_team_message.id
        ):
            for emoji in self.my_emojis:
                await self.current_team_message.remove_reaction(emoji, self.user)
            self.current_team_message = None

    async def on_message(self, message):
        """
        Called when a message is received.

        Args:
            message (discord.Message): The message that was received.
        """
        if message.mentions:
            if message.mentions[0].id == self.bot_id:
                words = message.content.split()
                if len(words) != 2:
                    return
                if words[1] == "help":
                    await message.channel.send(
                        "```I'm a bot that can help you create teams for a tournament if you have more than 8 people in a voice channel. Just type @tourney create while in the voice channel and I'll take care of the rest.```"
                    )
                elif words[1] == "create" and not message.author.voice is None:
                    self.players = [
                        member.name for member in message.author.voice.channel.members
                    ]
                    # Use this for testing
                    # self.players = [
                    #     "Player1",
                    #     "Player2",
                    #     "Player3",
                    #     "Player4",
                    #     "Player5",
                    #     "Player6",
                    #     "Player7",
                    #     "Player8",
                    # ]
                    try:
                        teams = teamCreator(self.players)
                        teams_message = "\n".join(
                            [
                                f"Team {i+1}: {' '.join(players)}"
                                for i, players in enumerate(teams)
                            ]
                        )

                        created_message = await message.channel.send(
                            f"```{teams_message}```"
                        )
                        self.current_team_message = created_message
                        for emoji in self.my_emojis:
                            await created_message.add_reaction(emoji)
                    except InvalidTournamentException as e:
                        await message.channel.send(f"```Error: {e}```")
        print(f"Message from {message.author}: {message.content}")


def main():
    intents = discord.Intents.default()
    client = MyClient(intents=intents)
    client.run(TOKEN)


if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.environ["DISCORD_TOKEN"]
    main()
