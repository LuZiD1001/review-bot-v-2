import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

TOKEN    = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

intents = discord.Intents.default()
intents.members         = True
intents.message_content = True
intents.guilds          = True

bot = commands.Bot(command_prefix="!", intents=intents)

COGS = ["cogs.reviews"]

async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"[REVIEW] ✅ Loaded cog: {cog}")
        except Exception as e:
            print(f"[REVIEW] ❌ Failed to load {cog}: {e}")

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"[REVIEW] ⚡ Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"[REVIEW] Sync error: {e}")

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="die Reviews ⭐"
        )
    )
    print(f"[REVIEW] 🚀 Online als {bot.user}")

@bot.event
async def on_guild_join(guild):
    if GUILD_ID and guild.id != GUILD_ID:
        print(f"[REVIEW] 🚫 Unerlaubter Server — verlasse: {guild.name}")
        await guild.leave()

async def main():
    async with bot:
        await load_cogs()
        if not TOKEN:
            raise ValueError("[REVIEW] DISCORD_TOKEN ist nicht in .env gesetzt!")
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
