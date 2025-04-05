import discord
from discord.ext import commands
from config import LOG_MODERATION_CHANNEL_ID, LOG_WARN_CHANNEL_ID, ROLES_AUTORISES
from database import get_warns, add_warn, remove_warn, remove_all_warns

warns = {}  # Dictionnaire pour stocker les avertissements temporairement

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_log(self, action, moderator, target=None, reason=None, extra_info=None, member_id=None):
        """Envoie un log de modération dans le salon dédié."""
        log_channel = self.bot.get_channel(LOG_MODERATION_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title=f"{action} effectué",
                color=discord.Color.red() if action in ["Ban", "Kick"] else discord.Color.blue()
            )
            embed.add_field(name="Modérateur", value=moderator.mention, inline=False) 
            if target:
                embed.add_field(name="Membre concerné", value=target.mention, inline=False)
                embed.add_field(name="Identifiant", value=target.id, inline=False)
            elif member_id:
                embed.add_field(name="Identifiant", value=str(member_id), inline=False)
            if reason:
                embed.add_field(name="Raison", value=reason, inline=False)
            if extra_info:
                embed.add_field(name="Informations supplémentaires", value=extra_info, inline=False)
            embed.set_footer(text="Action de modération enregistrée")
            await log_channel.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def msg_del(self, ctx, number: int):
        """Supprime un certain nombre de messages dans le canal actuel."""
        if number < 1 or number > 100:
            await ctx.send("Veuillez spécifier un nombre entre 1 et 100.", delete_after=5)
            return
        deleted = await ctx.channel.purge(limit=number + 1)
        await ctx.send(f"J'ai supprimé {len(deleted)} messages.", delete_after=5)
        await self.send_log("Suppression de messages", ctx.author, extra_info=f"{len(deleted)} messages supprimés dans {ctx.channel.mention}")

    @commands.command()
    @commands.has_any_role(ROLES_AUTORISES)
    async def ban(self, ctx, member_id: int, *, reason=None):
        """Permet de bannir un membre en utilisant son identifiant, même s'il n'est plus sur le serveur."""
    
        if member_id == ctx.author.id:
            await ctx.send("Vous ne pouvez pas vous bannir vous-même.", delete_after=5)
            return
        try:
            banned_member = await ctx.guild.fetch_ban(discord.Object(id=member_id))
            await ctx.send(f"Le membre avec l'ID {member_id} est déjà banni.", delete_after=5)
            return
        except discord.NotFound:
            pass
        except discord.Forbidden:
            await ctx.send("Je n'ai pas les permissions pour vérifier les bannissements.", delete_after=5)
            return
        except discord.HTTPException as e:
            await ctx.send(f"Une erreur est survenue lors de la vérification du bannissement: {e}", delete_after=5)
            return
        try:
            await ctx.guild.ban(discord.Object(id=member_id), reason=reason)
            await ctx.send(f"Membre avec l'ID {member_id} a été banni.", delete_after=5)
            await self.send_log("Ban", ctx.author, target=None, reason=reason, member_id=member_id)
        except discord.Forbidden:
            await ctx.send("Je n'ai pas les permissions pour bannir ce membre.", delete_after=5)
        except discord.HTTPException as e:
            await ctx.send(f"Une erreur est survenue lors du bannissement: {e}", delete_after=5)

    @commands.command()
    @commands.has_any_role(ROLES_AUTORISES)
    async def unban(self, ctx, member_id: int, *, reason=None):
        """Permet de débannir un membre en utilisant son identifiant, même s'il n'est plus sur le serveur."""
    
        if member_id == ctx.author.id:
            await ctx.send("Vous ne pouvez pas vous débannir vous-même.", delete_after=5)
            return
        try:
            banned_member = await ctx.guild.fetch_ban(discord.Object(id=member_id))
            await ctx.guild.unban(banned_member.user, reason=reason)
            await ctx.send(f"Membre avec l'ID {member_id} a été débanni.", delete_after=5)
            await self.send_log("Unban", ctx.author, target=None, reason=reason, member_id=member_id)
            return
        except discord.NotFound:
            await ctx.send(f"Aucun membre trouvé avec l'ID {member_id} qui est banni.", delete_after=5)
            return
        except discord.Forbidden:
            await ctx.send("Je n'ai pas les permissions pour vérifier les bannissements ou effectuer le débannissement.", delete_after=5)
            return
        except discord.HTTPException as e:
            await ctx.send(f"Une erreur est survenue lors de la récupération ou du débannissement: {e}", delete_after=5)
            return

    @commands.command()
    @commands.has_any_role(ROLES_AUTORISES)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """Permet d'expulser un membre avec une raison spécifiée."""
        if member == ctx.author:
            await ctx.send("Vous ne pouvez pas vous expulser vous-même.", delete_after=5)
            return
        try:
            await member.kick(reason=reason)
            await ctx.send(f"{member.mention} a été expulsé.", delete_after=5)
            await self.send_log("Kick", ctx.author, target=member, reason=reason)
        except discord.Forbidden:
            await ctx.send("Je n'ai pas les permissions pour expulser ce membre.", delete_after=5)

    @commands.command()
    async def warn(self, ctx, member: discord.Member, *, reason="Aucune raison spécifiée"):
        """Ajoute un avertissement à un membre."""
        if not any(role.name in ROLES_AUTORISES for role in ctx.author.roles):
            await ctx.send("Vous n'avez pas la permission d'exécuter cette commande.", delete_after=5)
            return
        add_warn(member.id)
        warn_count = get_warns(member.id)
        await ctx.send(f"{member.mention} a reçu un avertissement. Il en a maintenant {warn_count}", delete_after=10)
        log_channel = self.bot.get_channel(LOG_WARN_CHANNEL_ID)
        embed = discord.Embed(title="➕ Ajout d'Avertissement",
                            description=f"{member.mention} a reçu 1 avertissement.",
                            color=discord.Color.red())
        embed.add_field(name="Raison", value=reason, inline=False)
        embed.add_field(name="Action réalisée par", value=ctx.author.mention, inline=False)
        embed.add_field(name="Nombre total de warns", value=str(warn_count), inline=False)
        if log_channel:
            await log_channel.send(embed=embed)
        if warn_count >= 3:
            await member.ban(reason="Accumulation de 3 avertissements")
            await log_channel.send(f"{member.mention} a été banni après avoir reçu 3 avertissements.")


    @commands.command()
    async def warn_del(self, ctx, member: discord.Member):
        """Supprime un avertissement d'un membre."""
        if not any(role.name in ROLES_AUTORISES for role in ctx.author.roles):
            await ctx.send("Vous n'avez pas la permission d'exécuter cette commande.", delete_after=5)
            return
        warn_count = get_warns(member.id)
        if warn_count == 0:
            await ctx.send(f"{member.mention} n'a aucun avertissement.", delete_after=5)
            return
        remove_warn(member.id)
        warn_count = get_warns(member.id)
        await ctx.send(f"{member.mention} a 1 avertissement en moins. Il en a maintenant {warn_count}", delete_after=10)
        log_channel = self.bot.get_channel(LOG_WARN_CHANNEL_ID)
        embed = discord.Embed(
            title="➖ Suppression d'Avertissement",
            description=f"{member.mention} a 1 avertissement en moins.",
            color=discord.Color.dark_gold()
        )
        embed.add_field(name="Action réalisée par", value=ctx.author.mention, inline=False)
        embed.add_field(name="Nombre total de warns", value=str(warn_count), inline=False)
        if log_channel:
            await log_channel.send(embed=embed)


    @commands.command()
    async def warn_del_all(self, ctx, member: discord.Member):
        """Supprime tous les avertissements d'un membre."""
        if not any(role.name in ROLES_AUTORISES for role in ctx.author.roles):
            await ctx.send("Vous n'avez pas la permission d'exécuter cette commande.", delete_after=5)
            return
        remove_all_warns(member.id)
        await ctx.send(f"Tous les avertissements de {member.mention} ont été supprimés.", delete_after=10)
        log_channel = self.bot.get_channel(LOG_WARN_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="❌ Suppression de tous les avertissements",
                description=f"Tous les avertissements de {member.mention} ont été supprimés.",
                color=discord.Color.yellow()
            )
            embed.add_field(name="Action réalisée par", value=ctx.author.mention, inline=False)
            await log_channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Moderation(bot))