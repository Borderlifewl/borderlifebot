import discord
from discord.ext import commands
from discord.ui import View, Select, Modal, TextInput, Button
from config import LOG_TICKET_CHANNEL_ID, CATEGORY_CONVOCATIONS_MAPPINGS, ROLES_CONVOCATIONS_ID, MAX_CONVOCATIONS
import sqlite3

ticket_count = {}
old_ticket_names = {}

def create_db():
    conn = sqlite3.connect("ticket_names.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id INTEGER PRIMARY KEY,
            old_name TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_old_ticket_names():
    conn = sqlite3.connect("ticket_names.db")
    cursor = conn.cursor()
    cursor.execute("SELECT ticket_id, old_name FROM tickets")
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def save_old_ticket_name(ticket_id, old_name):
    conn = sqlite3.connect("ticket_names.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO tickets (ticket_id, old_name) VALUES (?, ?)", (ticket_id, old_name))
    conn.commit()
    conn.close()


async def log_ticket_action(action, user, ticket_name, category=None, reason=None):
    log_channel = discord.utils.get(user.guild.text_channels, id=LOG_TICKET_CHANNEL_ID)
    if log_channel:
        embed = discord.Embed(
            title="Log Convocation Action",
            description=f"{action} - Convocation {ticket_name}",
            color=discord.Color.from_rgb(88, 20, 147) if action == "Ouverture" else discord.Color.from_rgb(88, 20, 147)
        )
        embed.add_field(name="Utilisateur", value=user.mention, inline=False)
        embed.add_field(name="Convocation", value=ticket_name, inline=False)
        if category:
            embed.add_field(name="Catégorie", value=category, inline=False)
        if reason:
            embed.add_field(name="Raison", value=reason, inline=False)
        embed.set_footer(text=f"Action effectuée le {user.guild.me.created_at.strftime('%d/%m/%Y à %H:%M:%S')}")
        await log_channel.send(embed=embed)

class ConvocationView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ConvocationSelect())

class ConvocationSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=key, value=key) for key in CATEGORY_CONVOCATIONS_MAPPINGS.keys()
        ]
        super().__init__(placeholder="Sélectionnez une option", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ConvocationReasonModal(self.values[0]))

class ConvocationReasonModal(Modal, title="Raison de la convocation"):
    def __init__(self, category):
        super().__init__()
        self.category = category
        self.reason = TextInput(label="Décrivez la raison de votre convocation", style=discord.TextStyle.paragraph)
        self.member_mention = TextInput(label="ID du membre à convoquer", style=discord.TextStyle.short)
        self.add_item(self.reason)
        self.add_item(self.member_mention)

    async def on_submit(self, interaction: discord.Interaction):
        user_tickets = ticket_count.get(interaction.user.id, 0)
        if user_tickets >= MAX_CONVOCATIONS:
            await interaction.response.send_message("Vous avez atteint le nombre maximum de convocations.", ephemeral=True)
            return
        
        category_id = CATEGORY_CONVOCATIONS_MAPPINGS[self.category]
        category = discord.utils.get(interaction.guild.categories, id=category_id)
        if category is None:
            await interaction.response.send_message("Catégorie introuvable.", ephemeral=True)
            return
        
        ticket_name_map = {
            "Convocations": "convoc"
        }

        ticket_prefix = ticket_name_map.get(self.category, "ticket")
        member = None
        if self.member_mention.value:
            if "<@" in self.member_mention.value:
                member_id = int(self.member_mention.value[2:-1])
            else:
                try:
                    member_id = int(self.member_mention.value)
                except ValueError:
                    member_id = None
            if member_id:
                member = interaction.guild.get_member(member_id)

        if member:
            ticket_channel_name = f"{ticket_prefix}-({member.display_name})"
        else:
            ticket_channel_name = f"{ticket_prefix}-{interaction.user.name}"
        ticket_channel = await interaction.guild.create_text_channel(
            name=ticket_channel_name, category=category
        )
    
        ticket_count[interaction.user.id] = user_tickets + 1

        await ticket_channel.set_permissions(interaction.guild.default_role, read_messages=False)
        await ticket_channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        await ticket_channel.set_permissions(discord.utils.get(interaction.guild.roles, id=ROLES_CONVOCATIONS_ID), read_messages=True, send_messages=True)  # Ajoute le staff

        if member:
            await ticket_channel.set_permissions(member, read_messages=True, send_messages=True)

        embed = discord.Embed(
        title="Convocation Ouverte",
        description="Si vous êtes convoqué par un staff, merci de suivre ses indications sous peine de sanction(s).",
        color=discord.Color.from_rgb(88, 20, 147)
        )
        embed.set_thumbnail(url="https://www.dropbox.com/scl/fi/lp1vk9tp2dxe4rdrz7nm1/Logo.png?rlkey=jmb78m9bs2x83gyi59k0wx0yc&st=kkbfwwam&dl=0&raw=1")
        embed.add_field(name="Sujet", value=self.category, inline=True)
        embed.add_field(name="Raison", value=self.reason.value, inline=True)
        embed.add_field(name="Date et Heure", value=f"{interaction.created_at.strftime('%d/%m/%Y à %H:%M:%S')}", inline=True)
        embed.set_footer(text="Tout message offensant ou haineux entraînera une ou plusieurs sanctions !", icon_url="https://www.dropbox.com/scl/fi/lp1vk9tp2dxe4rdrz7nm1/Logo.png?rlkey=jmb78m9bs2x83gyi59k0wx0yc&st=kkbfwwam&dl=0&raw=1")

        mention_text = f"{interaction.user.mention}"
        if member:
            mention_text += f" {member.mention}"
        
        closeandclaim_view = CloseConvocationView(ticket_channel, interaction.user.id)
        await ticket_channel.send(embed=embed, content=f"<@&{ROLES_CONVOCATIONS_ID}> {mention_text}", view=closeandclaim_view)
        
        await log_ticket_action("Ouverture", interaction.user, ticket_channel.name, self.category, self.reason.value)
        
        await interaction.response.send_message(f"Votre convocation a été ouvert : {ticket_channel.mention}", ephemeral=True)

        await interaction.message.edit(view=ConvocationView())

class CloseConvocationView(View):
    def __init__(self, channel, user_id):
        super().__init__(timeout=None)
        self.channel = channel
        self.user_id = user_id

    @discord.ui.button(label="Fermer la convocation", style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        if any(role.id == ROLES_CONVOCATIONS_ID for role in interaction.user.roles):
            await interaction.response.send_modal(CloseConvocationModal(self.channel, self.user_id))
        else:
            await interaction.response.send_message("Vous n'avez pas la permission de fermer ce ticket.", ephemeral=True)

class CloseConvocationModal(Modal, title="Raison de la fermeture de la convocation"):
    def __init__(self, channel, user_id):
        super().__init__()
        self.channel = channel
        self.user_id = user_id
        self.reason = TextInput(label="Pourquoi fermez-vous cette convocation ?", style=discord.TextStyle.paragraph)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        if any(role.id == ROLES_CONVOCATIONS_ID for role in interaction.user.roles):
            ticket_name = self.channel.name
            await interaction.response.defer()
            await log_ticket_action("Fermeture", interaction.user, ticket_name, reason=self.reason.value)
            ticket_count[self.user_id] = max(0, ticket_count.get(self.user_id, 0) - 1)
            await self.channel.delete()
        else:
            await interaction.response.send_message("Vous n'avez pas la permission de fermer cette convocation.", ephemeral=True)

class Convocations(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        create_db()  # Créer la base de données si elle n'existe pas
        self.old_ticket_names = get_old_ticket_names()  # Charger les anciens noms depuis la DB

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def panel_convocations(self, ctx):
        embed = discord.Embed(
            title="Créer une convocation",
            description="Si vous souhaitez convoquer un membre du serveur merci d'ouvrir une convocation à l'aide de ce panel et d'éxecuter dans la convocation ouverte la commande !convocation_add @",
            color=discord.Color.from_rgb(88, 20, 147)
        )
        embed.set_thumbnail(url="https://www.dropbox.com/scl/fi/lp1vk9tp2dxe4rdrz7nm1/Logo.png?rlkey=jmb78m9bs2x83gyi59k0wx0yc&st=kkbfwwam&dl=0&raw=1")
        embed.set_footer(text="Convocations - Borderlife", icon_url="https://www.dropbox.com/scl/fi/lp1vk9tp2dxe4rdrz7nm1/Logo.png?rlkey=jmb78m9bs2x83gyi59k0wx0yc&st=kkbfwwam&dl=0&raw=1")

        await ctx.send(embed=embed, view=ConvocationView())

    @commands.command()
    @commands.has_role(ROLES_CONVOCATIONS_ID)
    async def convocation_add(self, ctx, member: discord.Member):
        if ctx.channel.name.startswith("ticket-") or ctx.channel.name.startswith("convoc-") or ctx.channel.id in self.old_ticket_names:
            await ctx.channel.set_permissions(member, read_messages=True, send_messages=True)
            await ctx.send(f"{member.mention} a été ajouté au ticket.")
        else:
            await ctx.send("Cette commande ne peut être utilisée que dans un ticket.")

    @commands.command()
    @commands.has_role(ROLES_CONVOCATIONS_ID)
    async def convocation_remove(self, ctx, member: discord.Member):
        if ctx.channel.name.startswith("ticket-") or ctx.channel.name.startswith("convoc-") or ctx.channel.id in self.old_ticket_names:
            await ctx.channel.set_permissions(member, overwrite=None)
            await ctx.send(f"{member.mention} a été retiré du convocation.")
        else:
            await ctx.send("Cette commande ne peut être utilisée que dans un convocation.")

    @commands.command()
    @commands.has_role(ROLES_CONVOCATIONS_ID)
    async def convocation_rename(self, ctx, new_name: str):
        if ctx.channel.name.startswith("ticket-") or ctx.channel.name.startswith("convoc-") or ctx.channel.id in self.old_ticket_names:
            await ctx.channel.edit(name=new_name)
            self.old_ticket_names[ctx.channel.id] = new_name  # Mise à jour de l'historique des anciens noms
            save_old_ticket_name(ctx.channel.id, new_name)  # Sauvegarder dans la DB
            await ctx.send(f"La convocation a été renommé en : {new_name}")
        else:
            await ctx.send("Cette commande peut seulement être utilisée dans un canal de convocation.")

async def setup(bot):
    await bot.add_cog(Convocations(bot))