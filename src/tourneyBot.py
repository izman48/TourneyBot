import os
import discord
from tournament import tournamentCreator, InvalidTournamentException
from dotenv import load_dotenv


class MyClient(discord.Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot_id = ""

    async def on_ready(self):
        print(f"Logged on as {self.user}!")
        self.bot_id = self.user.id

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.mentions:
            if message.mentions[0].id == self.bot_id:
                words = message.content.split()
                if words[1] == "help":
                    await message.channel.send(
                        "I'm a bot that can help you create teams for a tournament if you have more than 8 people. Just type @tourney create in a voice channel and I'll take care of the rest."
                    )
                elif words[1] == "create":
                    await message.channel.send("Creating Teams...")
                    self.players = [
                        member.name for member in message.author.voice.channel.members
                    ]
                    try:
                        tournament = tournamentCreator(self.players)
                        await message.channel.send(f"Teams: {tournament}")
                    except InvalidTournamentException as e:
                        await message.channel.send(f"Error: {e}")
                else:
                    await message.channel.send("I'm not sure what you want me to do.")
        print(f"Message from {message.author}: {message.content}")


def main():
    intents = discord.Intents.default()
    client = MyClient(intents=intents)
    client.run(token=TOKEN)


if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.environ["DISCORD_TOKEN"]
    main()
