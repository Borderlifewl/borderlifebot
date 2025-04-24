import discord
from discord.ext import commands
from discord.utils import get
from config import DOUANIER
import os
from config import LOG_MODERATION_CHANNEL_ID

class Whitelist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_log(self, action, moderator, target=None, reason=None, extra_info=None, member_id=None):
        log_channel = self.bot.get_channel(LOG_MODERATION_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title=f"{action} effectué",
                color=discord.Color.from_rgb(4, 230, 9) if action == "Ouverture" else discord.Color.from_rgb(238, 0, 2)
            )
            embed.add_field(name="Modérateur", value=moderator.mention, inline=False)
            if extra_info:
                embed.add_field(name="Informations supplémentaires", value=extra_info, inline=False)
            embed.set_footer(text="Action enregistrée")
            await log_channel.send(embed=embed)

    @commands.command()
    @commands.has_role(DOUANIER)
    async def openwl(self, ctx):
        nowhitelist = 1342864805559533659
        if ctx.channel.id != 1363157993847521471:
            await ctx.send("Cette commande peut uniquement être exécutée dans un canal spécifique.", delete_after=5)
            return
        
        guild = ctx.guild
        target_channel_id = 1363157993847521471
        channel = guild.get_channel(target_channel_id)

        if channel and isinstance(channel, discord.TextChannel):
            await channel.edit(name="🟢・statut-whitelist")
            await self.send_log("Ouverture de whitelist", ctx.author, target=channel, extra_info=f"Nom du salon modifié en '🟢・statut-whitelist' et image upload dans le salon {ctx.channel.mention}")
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
        if ctx.channel.id != 1363157993847521471:
            await ctx.send("Cette commande peut uniquement être exécutée dans un canal spécifique.", delete_after=5)
            return
        
        guild = ctx.guild
        target_channel_id = 1363157993847521471
        channel = guild.get_channel(target_channel_id)

        if channel and isinstance(channel, discord.TextChannel):
            await channel.edit(name="🔴・statut-whitelist")
            await self.send_log("Fermeture de whitelist", ctx.author, target=channel, extra_info=f"Nom du salon modifié en '🔴・statut-whitelist' et image upload dans le salon {ctx.channel.mention}")
        else:
            await ctx.send("Salon introuvable ou non valide.", delete_after=5)
            return
        
        image_path = os.path.join("images", "Whitelist_Fermé.png")
        if os.path.exists(image_path):
            await ctx.send(f"||<@&{nowhitelist}>||", file=discord.File(image_path))
        else:
            await ctx.send("Image non trouvée.")

async def setup(bot):
    await bot.add_cog(Whitelist(bot))
