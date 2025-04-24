import discord
from discord.ext import commands
from discord.ui import View, Select, Modal, TextInput, Button
from config import LOG_TICKET_CHANNEL_ID, CATEGORY_MAPPINGS, MAX_TICKETS, TICKET_ROLE_ID, STAFF_MANAGER, ILLEGAL_MANAGER, LEGAL_MANAGER, OWNER, PERM_3, MANAGER, ROLES_AUTORISES_RESET_TICKETS, POLE_STAFF, POLE_ILLEGAL, POLE_LEGAL
import sqlite3
import os

ticket_count = {}
old_ticket_names = {}

def create_db():
    conn = sqlite3.connect("ticket_names.db")  # Crée ou ouvre une base de données SQLite
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
    return {row[0]: row[1] for row in rows}  # Renvoie un dictionnaire avec ticket_id et old_name

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
            title="Log Ticket Action",
            description=f"{action} - Ticket {ticket_name}",
            color=discord.Color.blue() if action == "Ouverture" else discord.Color.red()
        )
        embed.add_field(name="Utilisateur", value=user.mention, inline=False)
        embed.add_field(name="Ticket", value=ticket_name, inline=False)
        if category:
            embed.add_field(name="Catégorie", value=category, inline=False)
        if reason:
            embed.add_field(name="Raison", value=reason, inline=False)
        embed.set_footer(text=f"Action effectuée le {user.guild.me.created_at.strftime('%d/%m/%Y à %H:%M:%S')}")
        await log_channel.send(embed=embed)

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=key, value=key) for key in CATEGORY_MAPPINGS.keys()
        ]
        super().__init__(placeholder="Sélectionnez une option", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TicketReasonModal(self.values[0]))

class TicketReasonModal(Modal, title="Raison du ticket"):
    def __init__(self, category):
        super().__init__()
        self.category = category
        self.reason = TextInput(label="Décrivez la raison de votre ticket", style=discord.TextStyle.paragraph)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        user_tickets = ticket_count.get(interaction.user.id, 0)
        if user_tickets >= MAX_TICKETS:
            await interaction.response.send_message("Vous avez atteint le nombre maximum de tickets.", ephemeral=True)
            return
        
        category_id = CATEGORY_MAPPINGS[self.category]
        category = discord.utils.get(interaction.guild.categories, id=category_id)
        if category is None:
            await interaction.response.send_message("Catégorie introuvable.", ephemeral=True)
            return
        
        ticket_name_map = {
            "Besoin d'aide": "bda",
            "Reprise Entreprise": "re",
            "Reprise Groupe Criminel": "rgc",
            "Glitch/Bug": "gb",
            "Recrutement Staff": "rs",
            "Demande de Wype": "dw",
            "Dossier Mort RP": "mrp"
        }

        ticket_prefix = ticket_name_map.get(self.category, "ticket")
        ticket_channel = await interaction.guild.create_text_channel(
            name=f"{ticket_prefix}-{interaction.user.name}", category=category
        )
    
        ticket_count[interaction.user.id] = user_tickets + 1

        await ticket_channel.set_permissions(interaction.guild.default_role, read_messages=False)
        await ticket_channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        if self.category == "Besoin d'aide":
            allowed_roles = [TICKET_ROLE_ID]
        elif self.category == "Reprise Entreprise":
            allowed_roles = [POLE_LEGAL, LEGAL_MANAGER, OWNER, PERM_3, MANAGER]
        elif self.category == "Reprise Groupe Criminel":
            allowed_roles = [POLE_ILLEGAL, ILLEGAL_MANAGER, OWNER, PERM_3, MANAGER]
        elif self.category == "Glitch/Bug":
            allowed_roles = [TICKET_ROLE_ID]
        elif self.category == "Recrutement Staff":
            allowed_roles = [POLE_STAFF, STAFF_MANAGER, MANAGER, OWNER, PERM_3]    
        elif self.category == "Demande de Wype":
            allowed_roles = [TICKET_ROLE_ID]
        elif self.category == "Dossier Mort RP":
            allowed_roles = [TICKET_ROLE_ID]
        else:
            allowed_roles = []

        # Ajoute les rôles autorisés
        for role_id in allowed_roles:
            role = discord.utils.get(interaction.guild.roles, id=role_id)
            if role:
                await ticket_channel.set_permissions(role, read_messages=True, send_messages=True)

        ticket_type = self.category
        if ticket_type == "Besoin d'aide":
            embed = discord.Embed(
            title="<:ticket:1349849004837572608> **- Ticket Ouvert**",
            description=f"Merci de suivre les instructions si dessous.",
            color=discord.Color.from_rgb(88, 20, 147)
            )
            embed.set_thumbnail(url="https://www.dropbox.com/scl/fi/aeb93t3low78cezb3eip4/Logo2.png?rlkey=og0puob6i1ner9jszous6txg4&st=lteug4o8&dl=0&raw=1")
            embed.add_field(
                name="Description de votre problème :", 
                value="- Merci de décrire votre problème en détails",
                inline=False
            )
            embed.add_field(name="Sujet", value=self.category, inline=True)
            embed.add_field(name="Raison", value=self.reason.value, inline=True)
            embed.add_field(name="Date et Heure", value=f"{interaction.created_at.strftime('%d/%m/%Y à %H:%M:%S')}", inline=True)
            embed.set_footer(text="Merci de patienter, un membre du staff vous répondra rapidement !", icon_url="https://www.dropbox.com/scl/fi/aeb93t3low78cezb3eip4/Logo2.png?rlkey=og0puob6i1ner9jszous6txg4&st=lteug4o8&dl=0&raw=1")
        elif ticket_type == "Reprise Entreprise":
            embed = discord.Embed(
            title="<:ticket:1349849004837572608> **- Ticket Ouvert**",
            description=f"Merci de suivre les instructions si dessous.",
            color=discord.Color.from_rgb(88, 20, 147)
            )
            embed.set_thumbnail(url="https://www.dropbox.com/scl/fi/aeb93t3low78cezb3eip4/Logo2.png?rlkey=og0puob6i1ner9jszous6txg4&st=lteug4o8&dl=0&raw=1")
            embed.add_field(
                name="Votre dossier de Reprise d'Entreprise' doit contenir :", 
                value="- Une présentation de l'entreprise\n"
                      "- L'histoire de l'entreprise\n"
                      "- Vos motivations\n"
                      "- Une présentation de votre personnage\n"
                      "- La Hiérarchie de l'entreprise\n"
                      "- D'autres informations pour compléter votre dossier, qui pourraient bonifier notre décision\n"
                      "- Une fois terminé, merci de joindre ici même votre dossier ",
                inline=False
            )
            embed.add_field(name="Sujet", value=self.category, inline=True)
            embed.add_field(name="Raison", value=self.reason.value, inline=True)
            embed.add_field(name="Date et Heure", value=f"{interaction.created_at.strftime('%d/%m/%Y à %H:%M:%S')}", inline=True)
            embed.set_footer(text="Merci de patienter, un membre du staff vous répondra rapidement !", icon_url="https://www.dropbox.com/scl/fi/aeb93t3low78cezb3eip4/Logo2.png?rlkey=og0puob6i1ner9jszous6txg4&st=lteug4o8&dl=0&raw=1")
        elif ticket_type == "Reprise Groupe Criminel":
            embed = discord.Embed(
            title="<:ticket:1349849004837572608> **- Ticket Ouvert**",
            description=f"Merci de suivre les instructions si dessous.",
            color=discord.Color.from_rgb(88, 20, 147)
            )
            embed.set_thumbnail(url="https://www.dropbox.com/scl/fi/aeb93t3low78cezb3eip4/Logo2.png?rlkey=og0puob6i1ner9jszous6txg4&st=lteug4o8&dl=0&raw=1")
            embed.add_field(
                name="Votre dossier de Reprise de Groupe Criminel doit contenir :", 
                value="- Une présentation du groupe\n"
                      "- L'histoire du groupe\n"
                      "- Vos motivations\n"
                      "- Une présentation de votre personnage\n"
                      "- La Hiérarchie du groupe\n"
                      "- D'autres informations pour compléter votre dossier, qui pourraient bonifier notre décision\n"
                      "- Une fois terminé, merci de joindre ici même votre dossier ",
                inline=False
            )
            embed.add_field(name="Sujet", value=self.category, inline=True)
            embed.add_field(name="Raison", value=self.reason.value, inline=True)
            embed.add_field(name="Date et Heure", value=f"{interaction.created_at.strftime('%d/%m/%Y à %H:%M:%S')}", inline=True)
            embed.set_footer(text="Merci de patienter, un membre du staff vous répondra rapidement !", icon_url="https://www.dropbox.com/scl/fi/aeb93t3low78cezb3eip4/Logo2.png?rlkey=og0puob6i1ner9jszous6txg4&st=lteug4o8&dl=0&raw=1")
        elif ticket_type == "Glitch/Bug":
            embed = discord.Embed(
            title="<:ticket:1349849004837572608> **- Ticket Ouvert**",
            description=f"Merci de suivre les instructions si dessous.",
            color=discord.Color.from_rgb(88, 20, 147)
            )
            embed.set_thumbnail(url="https://www.dropbox.com/scl/fi/aeb93t3low78cezb3eip4/Logo2.png?rlkey=og0puob6i1ner9jszous6txg4&st=lteug4o8&dl=0&raw=1")
            embed.add_field(
                name="Glitch ou Bug à signaler", 
                value="- Merci de décrire le glitch ou le bug en détails, avec si possible des recs ou des photos à l'appui",
                inline=False
            )
            embed.add_field(name="Sujet", value=self.category, inline=True)
            embed.add_field(name="Raison", value=self.reason.value, inline=True)
            embed.add_field(name="Date et Heure", value=f"{interaction.created_at.strftime('%d/%m/%Y à %H:%M:%S')}", inline=True)
            embed.set_footer(text="Merci de patienter, un membre du staff vous répondra rapidement !", icon_url="https://www.dropbox.com/scl/fi/aeb93t3low78cezb3eip4/Logo2.png?rlkey=og0puob6i1ner9jszous6txg4&st=lteug4o8&dl=0&raw=1")
        elif ticket_type == "Recrutement Staff":
            embed = discord.Embed(
            title="<:ticket:1349849004837572608> **- Ticket Ouvert**",
            description=f"Merci de suivre les instructions si dessous.",
            color=discord.Color.from_rgb(88, 20, 147)
            )
            embed.set_thumbnail(url="https://www.dropbox.com/scl/fi/aeb93t3low78cezb3eip4/Logo2.png?rlkey=og0puob6i1ner9jszous6txg4&st=lteug4o8&dl=0&raw=1")
            embed.add_field(
                name="Votre dossier de Recrutement Staff doit contenir :", 
                value="- Vos Motivations\n"
                      "- Votre âge\n"
                      "- Vos disponibilités\n"
                      "- Plusieurs lignes pour vous présenter\n"
                      "- Une ou plusieurs chose(s) sur vous pour bonifier notre décision\n"
                      "- Une fois terminé, merci de joindre ici même votre dossier ",
                inline=False
            )
            embed.add_field(name="Sujet", value=self.category, inline=True)
            embed.add_field(name="Raison", value=self.reason.value, inline=True)
            embed.add_field(name="Date et Heure", value=f"{interaction.created_at.strftime('%d/%m/%Y à %H:%M:%S')}", inline=True)
            embed.set_footer(text="Merci de patienter, un membre du staff vous répondra rapidement !", icon_url="https://www.dropbox.com/scl/fi/aeb93t3low78cezb3eip4/Logo2.png?rlkey=og0puob6i1ner9jszous6txg4&st=lteug4o8&dl=0&raw=1")
        elif ticket_type == "Demande de Wype":
            embed = discord.Embed(
            title="<:ticket:1349849004837572608> **- Ticket Ouvert**",
            description=f"Merci de suivre les instructions si dessous.",
            color=discord.Color.from_rgb(88, 20, 147)
            )
            embed.set_thumbnail(url="https://www.dropbox.com/scl/fi/aeb93t3low78cezb3eip4/Logo2.png?rlkey=og0puob6i1ner9jszous6txg4&st=lteug4o8&dl=0&raw=1")
            embed.add_field(
                name="Votre Dossier de Demande de Wype doit contenir", 
                value="- Votre Nom et Prénom RP \n"
                      "- Raison de la demande \n"
                      "- Autre(s) information(s) à donner",
                inline=False
            )
            embed.add_field(name="Sujet", value=self.category, inline=True)
            embed.add_field(name="Raison", value=self.reason.value, inline=True)
            embed.add_field(name="Date et Heure", value=f"{interaction.created_at.strftime('%d/%m/%Y à %H:%M:%S')}", inline=True)
            embed.set_footer(text="Merci de patienter, un membre du staff vous répondra rapidement !", icon_url="https://www.dropbox.com/scl/fi/aeb93t3low78cezb3eip4/Logo2.png?rlkey=og0puob6i1ner9jszous6txg4&st=lteug4o8&dl=0&raw=1")
        elif ticket_type == "Dossier Mort RP":
            embed = discord.Embed(
            title="<:ticket:1349849004837572608> **- Ticket Ouvert**",
            description=f"Merci de suivre les instructions si dessous.",
            color=discord.Color.from_rgb(88, 20, 147)
            )
            embed.set_thumbnail(url="https://www.dropbox.com/scl/fi/aeb93t3low78cezb3eip4/Logo2.png?rlkey=og0puob6i1ner9jszous6txg4&st=lteug4o8&dl=0&raw=1")
            embed.add_field(
                name="Votre Dossier de Mort RP doit contenir :", 
                value="- Votre Nom et Prénom RP \n"
                      "- Nom et Prénom RP du membre concerné \n"
                      "- Pseudo du membre concerné \n"
                      "- Raison de la demande \n"
                      "- Preuve(s) à fournir \n"
                      "- Autre(s) information(s) à donner",
                inline=False
            )
            embed.add_field(
                name="<a:informationbl2:1344049716765134878>  Attention, sans raison ou sans preuve, le dossier se fera\n" 
                     "        immédiatement refuser", 
                value="** **", 
                inline=False
            )
            embed.add_field(name="Sujet", value=self.category, inline=True)
            embed.add_field(name="Raison", value=self.reason.value, inline=True)
            embed.add_field(name="Date et Heure", value=f"{interaction.created_at.strftime('%d/%m/%Y à %H:%M:%S')}", inline=True)
            embed.set_footer(text="Merci de patienter, un membre du staff vous répondra rapidement !", icon_url="https://www.dropbox.com/scl/fi/aeb93t3low78cezb3eip4/Logo2.png?rlkey=og0puob6i1ner9jszous6txg4&st=lteug4o8&dl=0&raw=1")

        closeandclaim_view = CloseandClaimTicketView(ticket_channel, interaction.user.id)
        await ticket_channel.send(embed=embed, content=f"<@&{TICKET_ROLE_ID}> {interaction.user.mention}", view=closeandclaim_view)
        
        await log_ticket_action("Ouverture", interaction.user, ticket_channel.name, self.category, self.reason.value)
        
        await interaction.response.send_message(f"Votre ticket a été ouvert : {ticket_channel.mention}", ephemeral=True)

        await interaction.message.edit(view=TicketView())

class CloseandClaimTicketView(View):
    def __init__(self, channel, user_id):
        super().__init__(timeout=None)
        self.channel = channel
        self.user_id = user_id

    @discord.ui.button(label="Fermer le ticket", style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(CloseTicketModal(self.channel, self.user_id))

    @discord.ui.button(label="Claim Ticket", style=discord.ButtonStyle.success)
    async def claim_ticket(self, interaction: discord.Interaction, button: Button):
        if any(role.id == TICKET_ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message(f"{interaction.user.mention} a claim ce ticket.", ephemeral=False)
        else:
            await interaction.response.send_message("Vous n'avez pas la permission de claim ce ticket.", ephemeral=True)


class CloseTicketModal(Modal, title="Raison de la fermeture du ticket"):
    def __init__(self, channel, user_id):
        super().__init__()
        self.channel = channel
        self.user_id = user_id
        self.reason = TextInput(label="Pourquoi fermez-vous ce ticket ?", style=discord.TextStyle.paragraph)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id == self.user_id or any(role.id == TICKET_ROLE_ID for role in interaction.user.roles):
            ticket_name = self.channel.name
            await interaction.response.defer()
            await log_ticket_action("Fermeture", interaction.user, ticket_name, reason=self.reason.value)
            ticket_count[self.user_id] = max(0, ticket_count.get(self.user_id, 0) - 1)
            await self.channel.delete()
        else:
            await interaction.response.send_message("Vous n'avez pas la permission de fermer ce ticket.", ephemeral=True)

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        create_db()  # Créer la base de données si elle n'existe pas
        self.old_ticket_names = get_old_ticket_names()  # Charger les anciens noms depuis la DB

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def panel(self, ctx):
        embed = discord.Embed(
            title="<:borderlife:1344046660463890504> - Ouvrir un Ticket",
            description="Sélectionnez une option ci-dessous pour ouvrir un ticket. Un membre de l'équipe staff vous contactera rapidement.",
            color=discord.Color.purple()
        )
        embed.set_thumbnail(url="https://www.dropbox.com/scl/fi/aeb93t3low78cezb3eip4/Logo2.png?rlkey=og0puob6i1ner9jszous6txg4&st=lteug4o8&dl=0&raw=1")
        embed.add_field(
            name="<:purplepin:1345831132226388090> **- Comment ça fonctionne**",
            value="Choisissez l'option qui correspond à votre besoin. Un ticket sera créé dans la catégorie appropriée, et un membre de notre staff interviendra rapidement.",
            inline=False
        )
        embed.add_field(
            name="<:ticket:1349849004837572608> **- Options de tickets**",
            value="<a:purplearrow:1345827190541123675> **Besoin d'aide** ➜ Pour toute question ou problème.\n"
                  "<a:purplearrow:1345827190541123675> **Reprise Entreprise** ➜ Pour récupérer une entreprise.\n"
                  "<a:purplearrow:1345827190541123675> **Reprise Groupe Criminel** ➜ Pour récupérer un groupe criminel.\n"
                  "<a:purplearrow:1345827190541123675> **Glitch/Bug** ➜ Si vous rencontrez/découvrez un Bug ou un Glitch.\n"
                  "<a:purplearrow:1345827190541123675> **Recrutement Staff** ➜ Si vous souhaitez rejoindre l'équipe staff du serveur.\n"
                  "<a:purplearrow:1345827190541123675> **Demande de Wype** ➜ Si vous souhaitez vous faire wype.\n"
                  "<a:purplearrow:1345827190541123675> **Dossier de Mort RP** ➜ Si vous souhaitez déposer un dossier de mort RP",
            inline=False
        )
        embed.set_footer(text="Nous sommes là pour vous aider !", icon_url="https://www.dropbox.com/scl/fi/aeb93t3low78cezb3eip4/Logo2.png?rlkey=og0puob6i1ner9jszous6txg4&st=lteug4o8&dl=0&raw=1")

        await ctx.send(embed=embed, view=TicketView())

    @commands.command()
    @commands.has_role(TICKET_ROLE_ID)
    async def ticket_add(self, ctx, member: discord.Member):
        if ctx.channel.name.startswith("ticket-") or ctx.channel.name.startswith("bda-") or ctx.channel.name.startswith("re-") or ctx.channel.name.startswith("rgc-") or ctx.channel.name.startswith("gb-") or ctx.channel.name.startswith("rs-") or ctx.channel.name.startswith("dw-") or ctx.channel.name.startswith("mrp-") or ctx.channel.id in self.old_ticket_names:
            await ctx.channel.set_permissions(member, read_messages=True, send_messages=True)
            await ctx.send(f"{member.mention} a été ajouté au ticket.")
        else:
            await ctx.send("Cette commande ne peut être utilisée que dans un ticket.")

    @commands.command()
    @commands.has_role(TICKET_ROLE_ID)
    async def ticket_remove(self, ctx, member: discord.Member):
        if ctx.channel.name.startswith("ticket-") or ctx.channel.name.startswith("bda-") or ctx.channel.name.startswith("re-") or ctx.channel.name.startswith("rgc-") or ctx.channel.name.startswith("gb-") or ctx.channel.name.startswith("rs-") or ctx.channel.name.startswith("dw-") or ctx.channel.name.startswith("mrp-") or ctx.channel.id in self.old_ticket_names:
            await ctx.channel.set_permissions(member, overwrite=None)
            await ctx.send(f"{member.mention} a été retiré du ticket.")
        else:
            await ctx.send("Cette commande ne peut être utilisée que dans un ticket.")

    @commands.command()
    @commands.has_any_role(ROLES_AUTORISES_RESET_TICKETS)
    async def ticket_number_del(self, ctx, member: discord.Member):
        if member.id in ticket_count and ticket_count[member.id] > 0:
            ticket_count[member.id] -= 1
            await ctx.send(f"Un ticket a été retiré à {member.mention}. Le nombre de tickets restants est {ticket_count[member.id]}.")
        else:
            await ctx.send(f"{member.mention} n'a pas de tickets ou le nombre est déjà à zéro.")
    
    @commands.command()
    @commands.has_any_role(ROLES_AUTORISES_RESET_TICKETS)
    async def ticket_number_reset(self, ctx, member: discord.Member):
        ticket_count[member.id] = 0
        await ctx.send(f"Le nombre de tickets de {member.mention} a été remis à zéro.")

    @commands.command()
    @commands.has_role(TICKET_ROLE_ID)
    async def ticket_rename(self, ctx, new_name: str):
        if ctx.channel.name.startswith("ticket-") or ctx.channel.name.startswith("bda-") or ctx.channel.name.startswith("re-") or ctx.channel.name.startswith("rgc-") or ctx.channel.name.startswith("gb-") or ctx.channel.name.startswith("rs-") or ctx.channel.name.startswith("dw-") or ctx.channel.name.startswith("mrp-") or ctx.channel.id in self.old_ticket_names:
            await ctx.channel.edit(name=new_name)
            self.old_ticket_names[ctx.channel.id] = new_name  # Mise à jour de l'historique des anciens noms
            save_old_ticket_name(ctx.channel.id, new_name)  # Sauvegarder dans la DB
            await ctx.send(f"Le ticket a été renommé en : {new_name}")
        else:
            await ctx.send("Cette commande peut seulement être utilisée dans un canal de ticket.")

    @commands.command()
    @commands.has_any_role(TICKET_ROLE_ID)
    async def ticket_close(self, ctx, *, reason: str = "Aucune raison spécifiée"):
        """Ferme un ticket manuellement avec une raison optionnelle."""
        if ctx.channel.category and ctx.channel.category.id in CATEGORY_MAPPINGS.values():
            # Enregistrer l'action dans les logs
            opened_by = ticket_authors.get(ctx.channel.id)
            await log_ticket_action("Fermeture (commande)", ctx.author, ctx.channel.name, reason=reason, opened_by=opened_by)

            # Mettre à jour le compteur de tickets de l'utilisateur
            user_id = ticket_authors.get(ctx.channel.id).id if ctx.channel.id in ticket_authors else None
            if user_id and user_id in ticket_count:
                ticket_count[user_id] = max(0, ticket_count.get(user_id, 0) - 1)

            # Générer et envoyer le transcript
            log_channel = discord.utils.get(ctx.guild.text_channels, id=LOG_TICKET_CHANNEL_ID)
            if log_channel:
                transcript_file = await generate_transcript(ctx.channel)
                await log_channel.send(file=transcript_file)

            # Supprimer l'auteur du ticket de la liste
            if ctx.channel.id in ticket_authors:
                del ticket_authors[ctx.channel.id]

            # Supprimer le canal
            await ctx.send("Le ticket sera fermé dans quelques secondes...")
            await asyncio.sleep(3)
            await ctx.channel.delete()
        else:
            await ctx.send("❌ Cette commande doit être utilisée dans un ticket.")

async def setup(bot):
    await bot.add_cog(Tickets(bot))
