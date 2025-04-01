import discord
import aiohttp
import io
from discord.ext import commands
from discord.utils import get
from config import DOUANIER

class Whitelist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_role(DOUANIER)
    async def openwl(self, ctx):
        nowhitelist = 1342864805559533659
        if ctx.channel.id != 1342859770893172788:
            await ctx.send("Cette commande peut uniquement être exécutée dans un canal spécifique.", delete_after=5)
            return
        guild = ctx.guild
        channel = get(guild.text_channels, name="🔴・statut-whitelist")
        if channel:
            await channel.edit(name="🟢・statut-whitelist")
        image_wlo_url = "https://www.dropbox.com/scl/fi/gn0xopnfuz0ba2adeoq7u/Whitelist_Ouverte.png?rlkey=o2ymy8c4kp39r3efljdg3aju2&st=vrr17obm&dl=0&raw=1"
        async with aiohttp.ClientSession() as session:
            async with session.get(image_wlo_url) as response:
                if response.status == 200:
                    image = await response.read()
                    await ctx.send(f"||<@&{nowhitelist}>||", file=discord.File(io.BytesIO(image), filename="whitelist_ouverte.png"))
                else:
                    await ctx.send("Impossible de récupérer l'image.")
        await message.delete(delay=5)

    @commands.command()
    @commands.has_role(DOUANIER)
    async def closewl(self, ctx):
        nowhitelist = 1342864805559533659
        if ctx.channel.id != 1342859770893172788:
            await ctx.send("Cette commande peut uniquement être exécutée dans un canal spécifique.", delete_after=5)
            return
        guild = ctx.guild
        channel = get(guild.text_channels, name="🟢・statut-whitelist")
        if channel:
            await channel.edit(name="🔴・statut-whitelist")
        image_wlf_url = "https://www.dropbox.com/scl/fi/85yw5b3ia57kpk5xk28qe/Whitelist_Ferm.png?rlkey=xl0es5j3gspv2op0cn4olpshv&st=11jg65ar&dl=0&raw=1"
        async with aiohttp.ClientSession() as session:
            async with session.get(image_wlf_url) as response:
                if response.status == 200:
                    image = await response.read()
                    await ctx.send(f"||<@&{nowhitelist}>||", file=discord.File(io.BytesIO(image), filename="whitelist_fermee.png"))
                else:
                    await ctx.send("Impossible de récupérer l'image.")
        await message.delete(delay=5)

# Setup de la cog
async def setup(bot):
    await bot.add_cog(Whitelist(bot))
