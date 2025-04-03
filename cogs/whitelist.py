import discord
from discord.ext import commands
from discord.utils import get
from config import DOUANIER
import os

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
        target_channel_id = 1342859770893172788
        channel = guild.get_channel(target_channel_id)
        if channel and isinstance(channel, discord.TextChannel):
            await channel.edit(name="🟢・statut-whitelist")
        else:
            await ctx.send("Salon introuvable ou non valide.", delete_after=5)
            return
        image_path = os.path.join("images", "Whitelist_Ouverte.png")
        if os.path.exists(image_path):
            await ctx.send(f"||<@&{nowhitelist}>||", file=discord.File(image_path))
        else:
            await ctx.send("Image non trouvée.")

    @commands.command()
    @commands.has_role(DOUANIER)
    async def closewl(self, ctx):
        nowhitelist = 1342864805559533659
        if ctx.channel.id != 1342859770893172788:
            await ctx.send("Cette commande peut uniquement être exécutée dans un canal spécifique.", delete_after=5)
            return
        guild = ctx.guild
        target_channel_id = 1342859770893172788
        channel = guild.get_channel(target_channel_id)
        if channel and isinstance(channel, discord.TextChannel):
            await channel.edit(name="🔴・statut-whitelist")
        else:
            await ctx.send("Salon introuvable ou non valide.", delete_after=5)
            return
        image_path = os.path.join("images", "Whitelist_Fermé.png")
        if os.path.exists(image_path):
            await ctx.send(f"||<@&{nowhitelist}>||", file=discord.File(image_path))
        else:
            await ctx.send("Image non trouvée.")

# Setup de la cog
async def setup(bot):
    await bot.add_cog(Whitelist(bot))
