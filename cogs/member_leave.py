import discord
from discord.ext import commands
from config import GUILD_ID, LEAVE_CHANNEL_ID
from datetime import datetime
import pytz

class MemberLeave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.guild.id != GUILD_ID:
            return
        
        log_channel = self.bot.get_channel(LEAVE_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="👤 Un membre a quitté",
                description=f"Un utilisateur a quitté le serveur.",
                color=discord.Color.red()
            )

            avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
            embed.set_thumbnail(url=avatar_url)

            embed.add_field(name="Identifiant", value=f"{member.id}", inline=False)
            embed.add_field(name="Nom d'utilisateur", value=member.name, inline=False)
            embed.add_field(name="Pseudo sur le serveur", value=member.display_name, inline=False)
            embed.add_field(name="Création du compte", value=member.created_at.strftime('%d/%m/%Y à %H:%M:%S'), inline=False)
            paris_tz = pytz.timezone('Europe/Paris')
            joined_at_paris = member.joined_at.astimezone(paris_tz) if member.joined_at else None
            embed.add_field(name="Date d'arrivée", value=joined_at_paris.strftime('%d/%m/%Y à %H:%M:%S') if joined_at_paris else "Non disponible", inline=False)
            left_at_paris = datetime.now(paris_tz)
            embed.add_field(name="Date de départ du membre", value=left_at_paris.strftime('%d/%m/%Y à %H:%M:%S'), inline=False)
            embed.add_field(name="Discord du joueur", value=member.mention, inline=False)
            roles = [role.mention for role in member.roles if role != member.guild.default_role]
            roles_str = ", ".join(roles) if roles else "Aucun rôle"
            embed.add_field(name="Rôles", value=roles_str, inline=False)
            embed.add_field(name="Lien du profil", value=f"[Clique ici](https://discord.com/users/{member.id})", inline=False)

            embed.set_footer(text=f"Information du Joueur, pour toute erreur contacter un fondateur ou co-fondateur")

            await log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MemberLeave(bot))
