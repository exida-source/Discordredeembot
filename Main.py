import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask
import os
import threading


class RedeemButton(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=None)
        self.author = author

    @discord.ui.button(label="Redeem", style=discord.ButtonStyle.green)
    async def redeem_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("Only the person who used the command can click this button!", ephemeral=True)
            return

        await interaction.response.send_message("Your request has been sent to the moderators and owners.", ephemeral=True)

        guild = interaction.guild
        roles_to_notify = ["Moderator", "Owner"]
        message = f"{self.author.mention} just redeemed their reward!"

        for member in guild.members:
            if any(role.name in roles_to_notify for role in member.roles):
                try:
                    await member.send(message)
                except:
                    print(f"Could not DM {member.name}")

@client.tree.command(name="done", description="Redeem your reward (notifies mods)")
async def done(interaction: discord.Interaction):
    view = RedeemButton(interaction.user)
    await interaction.response.send_message(
        "**Did you give all needed information to redeem your reward?**\n"
        "Then click the button below. This will contact Moderators and Owners, who will then get you the reward.\n\n"
        "**By clicking the button, you state that you are allowed to receive the reward (won a giveaway, etc.). "
        "If not, you will face a timeout!**",
        view=view
    )

# Set up Flask app
app = Flask(__name__)

# Simple route to keep the web service alive
@app.route('/')
def home():
    return "Bot is running! Host: ExidaBS!"

# Function to run the Flask app in a separate thread
def run_flask():
    app.run(host='0.0.0.0', port=80)

# Start Flask server in a thread
threading.Thread(target=run_flask).start()

# Set up Discord bot
intents = discord.Intents.default()
client = commands.Bot(command_prefix="/", intents=intents)

@client.event
async def on_ready():
    print(f"Bot ist online als {client.user}")
    try:
        synced = await client.tree.sync()
        print(f"Slash-Befehle synchronisiert: {len(synced)}")
    except Exception as e:
        print(f"Fehler beim Synchronisieren der Befehle: {e}")

@client.tree.command(name="redeem", description="Guides you step by step to redeem your reward")
async def redeem(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Please enter the type of reward you want to redeem! /kr or /money ! "
        "(WARNING: Rewards can only be redeemed, if you have won them in a giveaway/event!)",
        ephemeral=True
    )

@client.tree.command(name="kr", description="redeem Krunker KR")
async def kr(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Please enter your Krunker ingame-name and the amount of KR you wish to redeem. "
        "Then list any item for me to buy with that amount of KR!",
        ephemeral=True
    )

@client.tree.command(name="money", description="Redeem money/giftcards")
async def money(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Please enter how you wish to be paid: Paysafe or giftcard - "
        "Available giftcards: Paysafe, Apple, Amazon, Minecraft, Steam, Fortnite...",
        ephemeral=True
    )

@client.tree.command(name="help", description="View available commands")
async def help(interaction: discord.Interaction):
    help_text = (
        "```"
        "/redeem – Redeem rewards in tickets     | 👑\n"
        "----------------------------------------------\n"
        "/kr     – Redeem Krunker KR in tickets  | 💎\n"
        "----------------------------------------------\n"
        "/money  – Redeem money/giftcards         | 💸\n"
        "----------------------------------------------\n"
        "/help   – View commands                            | 🤖"
        "```"
    )
    await interaction.response.send_message(help_text, ephemeral=True)

# Run the bot
client.run(os.environ["KEY"])
