import os
import asyncio
import discord
from tournament import tournamentCreator, InvalidTournamentException
from dotenv import load_dotenv


class MyClient(discord.Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot_id = ""
        self.my_emojis = ["🔁", "✅"]
        self.current_team_message = None

    async def on_ready(self):
        print(f"Logged on as {self.user}!")
        self.bot_id = self.user.id

    async def on_reaction_add(self, reaction, user):
        if user == self.user:
            return
        if (
            reaction.emoji == "🔁"
            and self.current_team_message is not None
            and reaction.message.id == self.current_team_message.id
        ):
            await self.current_team_message.delete()
            teams = tournamentCreator(self.players)
            teams_message = "\n".join(
                [f"Team {i+1}: {' '.join(players)}" for i, players in enumerate(teams)]
            )

            created_message = await reaction.message.channel.send(
                f"```{teams_message}```"
            )
            self.current_team_message = created_message
            for emoji in self.my_emojis:
                await created_message.add_reaction(emoji)
        if (
            reaction.emoji == "✅"
            and self.current_team_message is not None
            and reaction.message.id == self.current_team_message.id
        ):
            self.current_team_message = None

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.mentions:
            if message.mentions[0].id == self.bot_id:
                words = message.content.split()
                if len(words) != 2:
                    return
                if words[1] == "help":
                    await message.channel.send(
                        "```I'm a bot that can help you create teams for a tournament if you have more than 8 people. Just type @tourney create in a voice channel and I'll take care of the rest.```"
                    )
                elif words[1] == "create":
                    self.players = [
                        member.name
                        for member in message.author.voice.channel.members
                        if message.author.voice.channel
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
                        teams = tournamentCreator(self.players)
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
