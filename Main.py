import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta
from flask import Flask
import os
import threading
import json

POINTS_FILE = "points.json"
REWARDS_FILE = "rewards.json"

# Helper functions
def load_json(file, fallback):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return fallback
def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

points = load_json(POINTS_FILE, {})
rewards = load_json(REWARDS_FILE, {"Brawl pass": 10000})

def is_owner(interaction):
    return any(role.name == "Owner" for role in interaction.user.roles)




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
        # Debug: send a message when the button is clicked
        guild = interaction.guild
        log_channel = discord.utils.get(guild.text_channels, name="redeem-logs")

        if log_channel:
            await log_channel.send("<@&1360289635363848244> , <@&1360289635363848245> , <@&1360289635363848246> Someone has just redeemed a reward!")

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

        if not log_channel:
            await interaction.followup.send("The 'redeem-logs' channel does not exist!", ephemeral=True)
            return

        # Log the reward redemption
        message = f"**Someone just redeemed a reward!**\nUser: {self.author.mention}"
        await log_channel.send(message)


# Slash command: give points
@client.tree.command(name="give_points", description="Give points to a member")
@app_commands.describe(member="Select the member", amount="Amount of points")
async def give_points(interaction: discord.Interaction, member: discord.Member, amount: int):
    if not is_owner(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    uid = str(member.id)
    points[uid] = points.get(uid, 0) + amount
    save_json(POINTS_FILE, points)
    await interaction.response.send_message(f"Gave {amount} points to {member.mention}.", ephemeral=True)

# Slash command: check your points
@client.tree.command(name="check_points", description="Check your points")
async def check_points(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    user_points = points.get(uid, 0)
    await interaction.response.send_message(f"You have **{user_points}** points.")

# Slash command: point rewards
@client.tree.command(name="point_rewards", description="See all available rewards")
async def point_rewards(interaction: discord.Interaction):
    if not rewards:
        await interaction.response.send_message("No rewards available yet.")
        return
    msg = "**Available Rewards:**\n"
    for reward, price in rewards.items():
        msg += f"- **{reward}** — {price} points\n"
    await interaction.response.send_message(msg)

# Slash command: add a reward (Owner only)
@client.tree.command(name="add_reward", description="Add a new reward")
@app_commands.describe(name="Name of reward", price="Price in points")
async def add_reward(interaction: discord.Interaction, name: str, price: int):
    if not is_owner(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    rewards[name] = price
    save_json(REWARDS_FILE, rewards)
    await interaction.response.send_message(f"Reward **{name}** added for {price} points.", ephemeral=True)

# Slash command: leaderboard
@client.tree.command(name="points_leaderboard", description="Show top 5 users with most points")
async def points_leaderboard(interaction: discord.Interaction):
    top = sorted(points.items(), key=lambda x: x[1], reverse=True)[:5]
    msg = "**Points Leaderboard:**\n"
    for i, (uid, pts) in enumerate(top, start=1):
        user = await client.fetch_user(int(uid))
        msg += f"{i}. {user.name} — {pts} points\n"
    await interaction.response.send_message(msg)

# Slash command: redeem points
@client.tree.command(name="redeem_points", description="Redeem a reward using your points")
async def redeem_points(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    user_points = points.get(uid, 0)

    if not rewards:
        await interaction.response.send_message("No rewards available.", ephemeral=True)
        return

    options = [discord.SelectOption(label=reward, description=f"{price} points") for reward, price in rewards.items()]
    
    class RewardSelect(discord.ui.View):
        @discord.ui.select(placeholder="Choose your reward", options=options)
        async def select_callback(self, select, interaction2):
            reward_name = select.values[0]
            price = rewards[reward_name]

            if user_points < price:
                await interaction2.response.send_message("You don’t have enough points.", ephemeral=True)
                return

            points[uid] = user_points - price
            save_json(POINTS_FILE, points)

            # Log redemption
            log_channel = discord.utils.get(interaction.guild.text_channels, name="redeem-logs")
            if log_channel:
                await log_channel.send(f"{interaction.user.mention} redeemed **{reward_name}**!")

            await interaction2.response.send_message(f"You redeemed **{reward_name}**! Please open a ticket and wait for a moderator.")

    await interaction.response.send_message("Choose a reward to redeem:", view=RewardSelect(), ephemeral=True)


@client.tree.command(name="en", description="Timeout a member for speaking another language.")
@app_commands.describe(member="Select the member to timeout")
async def en(interaction: discord.Interaction, member: discord.Member):
    # Only allow users with certain roles
    allowed_roles = ["Moderator", "Admin", "Owner"]
    user_roles = [role.name for role in interaction.user.roles]

    if not any(role in user_roles for role in allowed_roles):
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    # Timeout for 30 minutes
    try:
        await member.timeout(timedelta(minutes=30), reason="Spoke another language")
        await interaction.response.send_message(f"{member.mention} has been timed out for 30 minutes.", ephemeral=True)

        # Log it
        log_channel = discord.utils.get(interaction.guild.text_channels, name="redeem-logs")
        if log_channel:
            await log_channel.send(f"{member.mention} spoke another language.")

    except Exception as e:
        await interaction.response.send_message(f"Failed to timeout {member.mention}: {e}", ephemeral=True)


        
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
        "Then list any item for me to buy with that amount of KR! When you're done, use the /done command to lock it in!",
        ephemeral=True
    )

@client.tree.command(name="money", description="Redeem money/giftcards")
async def money(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Please enter how you wish to be paid: Paysafe or giftcard - "
        "Available giftcards: Paysafe, Apple, Amazon, Minecraft, Steam, Fortnite... When you're done, use the /dobe command to lock it in",
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
        "/money  – Redeem money/giftcards        | 💸\n"
        "----------------------------------------------\n"
        "/help   – View commands                 | 🤖\n"
        "----------------------------------------------\n"
        "/done   -Finish redeeming a reward      | 😬\n"
        "---------------------------------------------\n"
        "/check_points  -Checks your amount of points \n"
        "------------------------------------------\n"
        "/point_rewards  -View available points rewards\n"
        "-------------------------------------------\n"
        "/points_leaderboard  -Views the points leaderboard\n"
        "------------------------------------------------\n"
        "/redeem_points Redeem a points reward (/point_rewards)\n"
        
        "```"
    )
    await interaction.response.send_message(help_text)

# Run the bot
client.run(os.environ["KEY"])
