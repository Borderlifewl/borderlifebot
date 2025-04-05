import discord
from discord.ext import commands

staff = 1342561371065286667

class WLrapide(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mentioned_users = set()  # Pour garder une trace des utilisateurs déjà mentionnés

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # Remplacez 'whitelist - de 1 heure' par le nom exact de votre rôle
        role_name = '・Whitelist -1H'
        staff_channel_id = 1357782780863447080  # Remplacez par l'ID de votre canal staff

        # Vérifiez si le rôle a été ajouté
        if any(role.name == role_name for role in after.roles) and not any(role.name == role_name for role in before.roles):
            # Vérifiez si l'utilisateur a déjà été mentionné
            if after.id not in self.mentioned_users:
                staff_channel = self.bot.get_channel(staff_channel_id)
                if staff_channel:
                    await staff_channel.send(f"||<@&{staff}>|| {after.mention}, veut se faire Whitelist dans moins d'1 heure")
                    self.mentioned_users.add(after.id)  # Ajoutez l'utilisateur à la liste des mentionnés

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reset_mentions(self, ctx):
        """Commande pour réinitialiser la liste des utilisateurs mentionnés (pour les tests)"""
        self.mentioned_users.clear()
        await ctx.send("La liste des utilisateurs mentionnés a été réinitialisée.")

async def setup(bot):
    await bot.add_cog(WLrapide(bot))