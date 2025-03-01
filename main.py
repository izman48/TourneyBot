from src.tourneyBot import DudeBot
import os
from dotenv import load_dotenv

load_dotenv()
client = DudeBot()
client.run(os.getenv("DISCORD_TOKEN"))
