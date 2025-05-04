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
    return "Bot is running! Host: ExidaBS!"

# Function to run the Flask app in a separate thread
def run_flask():
    app.run(host='0.0.0.0', port=80)

# Start Flask server in a thread
threading.Thread(target=run_flask).start()

# Set up Discord bot
intents = discord.Intents.default()
client = commands.Bot(command_prefix="/", intents=intents)
class RedeemButton(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=None)
        self.author = author
        self.button_clicked = False

    @discord.ui.button(label="Redeem", style=discord.ButtonStyle.green, custom_id="redeem_button")
    async def redeem_button(self, interaction: discord.Interaction, button: discord.ui.Button):
    print("Button clicked!")

        if interaction.user != self.author:
            await interaction.response.send_message("Only the person who used the command can click this button!", ephemeral=True)
            return

        if self.button_clicked:
            await interaction.response.send_message("This button has already been used!", ephemeral=True)
            return

        self.button_clicked = True
        button.disabled = True
        await interaction.response.edit_message(view=self)

        await interaction.followup.send("Your request has been sent to the team.", ephemeral=True)

        guild = interaction.guild
        log_channel = discord.utils.get(guild.text_channels, name="redeem-logs")
        if log_channel is None:
            await interaction.followup.send("The 'redeem-logs' channel does not exist!", ephemeral=True)
            return

        message = f"**Someone just redeemed a reward!**\nUser: {self.author.mention}"
        await log_channel.send(message)



        
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
    await interaction.response.send_message(help_text)

# Run the bot
client.run(os.environ["KEY"])
