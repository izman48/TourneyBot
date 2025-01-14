from src.tourneyBot import MyClient
import os
from dotenv import load_dotenv

load_dotenv()
client = MyClient()
client.run(os.getenv("DISCORD_TOKEN"))
