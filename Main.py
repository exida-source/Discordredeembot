import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask
import os
import threading

# Set up Flask app
app = Flask(__name__)

# Simple route to keep the web service alive
@app.route('/')
def home():
    return "Bot is running! Good job Exida!"

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
@client.tree.command(name="help", description="Views existing Bot-commands")
async def help(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**Existing commands:**"
  
        "/redeem – redeem rewards in tickets | 👑"
    
        "/kr – redeem Krunker KR in Tickets | 💎"
     
        "/money – redeem money/giftcards in Tickets | 💸"
       
        "/help – View commands | 🤖",
        ephemeral=True
    )

# Run the bot
client.run(os.environ["KEY"])
