import discord
from discord.ext import commands
from discord import app_commands
import os

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

@client.tree.command(name="redeem", description="Beginne mit dem Einlösen deiner Belohnung")
async def redeem(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Please enter the type of reward you want to redeem! /kr or /money ! "
        "(WARNING: Rewards can only be redeemed, if you have won them in a giveaway/event!)",
        ephemeral=True
    )

@client.tree.command(name="kr", description="Krunker KR einlösen")
async def kr(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Please enter your Krunker ingame-name and the amount of KR you wish to redeem. "
        "Then list any item for me to buy with that amount of KR!",
        ephemeral=True
    )

@client.tree.command(name="money", description="Geld einlösen")
async def money(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Please enter how you wish to be paid: Paysafe or giftcard - "
        "Available giftcards: Paysafe, Apple, Amazon, Minecraft, Steam, Fortnite...",
        ephemeral=True
    )
client.run(os.environ["KEY"])

