import discord
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive
import os
import asyncio
from database import create_table

create_table()

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

async def load_cogs():
    await bot.load_extension("cogs.convocations")
    await bot.load_extension("cogs.member_join")
    await bot.load_extension("cogs.moderation")
    await bot.load_extension("cogs.tickets")
    await bot.load_extension("cogs.member_leave")
    await bot.load_extension("cogs.whitelist")
    await bot.load_extension("cogs.wlrapide")

keep_alive()

async def main():
    async with bot:
        await load_cogs()
        await bot.start(token)

asyncio.run(main())
