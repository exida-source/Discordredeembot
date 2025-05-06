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
LEADERBOARD_FILE = "leaderboard_message.json"

def save_leaderboard_msg_id(data):
    save_json(LEADERBOARD_FILE, data)

def load_leaderboard_msg_id():
    return load_json(LEADERBOARD_FILE, {})

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
intents.members = True  # <-- Add this line


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
        await update_leaderboard()


    uid = str(member.id)
    points[uid] = points.get(uid, 0) + amount
    save_json(POINTS_FILE, points)
    await interaction.response.send_message(f"Gave {amount} points to {member.mention}.")
async def update_leaderboard():
    leaderboard_data_file = "leaderboard_message.json"
    if not os.path.exists(leaderboard_data_file):
        print("Leaderboard message file not found.")
        return

    with open(leaderboard_data_file, "r") as f:
        data = json.load(f)

    channel = client.get_channel(data["channel_id"])
    if not channel:
        print("Leaderboard channel not found.")
        return

    try:
        message = await channel.fetch_message(data["message_id"])
    except discord.NotFound:
        print("Leaderboard message not found.")
        return

    # Build the leaderboard table
    if not points:
        content = "No points data available."
    else:
        sorted_points = sorted(points.items(), key=lambda x: x[1], reverse=True)
        lines = ["**Current Points Leaderboard**"]
        for uid, pts in sorted_points:
            try:
                user = await client.fetch_user(int(uid))
                name = user.name
            except:
                name = f"User ({uid})"
            lines.append(f"- **{name}**: {pts} points")

        content = "\n".join(lines)

    await message.edit(content=content)


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

# Slash command: take points
@client.tree.command(name="take_points", description="Remove points from a user")
@app_commands.describe(member="Member to remove points from", amount="Amount to remove")
async def take_points(interaction: discord.Interaction, member: discord.Member, amount: int):
    if not is_owner(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
        await update_leaderboard()

        
    uid = str(member.id)
    current = points.get(uid, 0)
    points[uid] = max(0, current - amount)
    save_json(POINTS_FILE, points)
    await interaction.response.send_message(f"Removed {amount} points from {member.mention}.", ephemeral=True)

# Slash command: delete reward
@client.tree.command(name="delete_reward", description="Delete a reward from the list")
@app_commands.describe(name="Name of the reward to delete")
async def delete_reward(interaction: discord.Interaction, name: str):
    if not is_owner(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    if name not in rewards:
        await interaction.response.send_message("That reward does not exist.", ephemeral=True)
        return

    del rewards[name]
    save_json(REWARDS_FILE, rewards)
    await interaction.response.send_message(f"Deleted reward **{name}**.", ephemeral=True)

@client.tree.command(name="redeem_points", description="Redeem a reward using your points")
async def redeem_points(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    user_points = points.get(uid, 0)

    if not rewards:
        await interaction.response.send_message("No rewards available.", ephemeral=True)
        return

    class RewardSelect(discord.ui.Select):
        def __init__(self):
            options = [
                discord.SelectOption(label=reward, description=f"{price} points")
                for reward, price in rewards.items()
            ]
            super().__init__(placeholder="Choose your reward", options=options, min_values=1, max_values=1)

        async def callback(self, interaction2: discord.Interaction):
            if interaction2.user.id != interaction.user.id:
                await interaction2.response.send_message("You can't interact with this menu.", ephemeral=True)
                return

            reward_name = self.values[0]
            price = rewards[reward_name]

            if user_points < price:
                await interaction2.response.send_message("You don’t have enough points.", ephemeral=True)
                return

            points[uid] -= price
            save_json(POINTS_FILE, points)
            await update_leaderboard()


            log_channel = discord.utils.get(interaction.guild.text_channels, name="redeem-logs")
            if log_channel:
                await log_channel.send(f"{interaction.user.mention} redeemed **{reward_name}**!")

            await interaction2.response.send_message(
                f"You redeemed **{reward_name}**! Please open a ticket and wait for a moderator.",
                ephemeral=True
            )

    class RewardView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.add_item(RewardSelect())

    await interaction.response.send_message("Choose a reward to redeem:", view=RewardView(), ephemeral=True)

@client.tree.command(name="raw_points", description="View all raw points data")
async def raw_points(interaction: discord.Interaction):
    if not is_owner(interaction):
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    summary = ""
    for uid, pts in points.items():
        try:
            user = await client.fetch_user(int(uid))
            summary += f"{user.name} ({uid}): {pts} points\n"
        except:
            summary += f"Unknown User ({uid}): {pts} points\n"

    if not summary:
        summary = "No points data found."

    await interaction.response.send_message(f"```{summary[:1950]}```", ephemeral=True)


        
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

    # Leaderboard chart setup
    leaderboard_channel = discord.utils.get(client.get_all_channels(), name="owner-only")
    if leaderboard_channel is None:
        print("Channel #owner-only not found.")
        return

    leaderboard_data_file = "leaderboard_message.json"
    if not os.path.exists(leaderboard_data_file):
        # First time: send a new leaderboard message
        msg = await leaderboard_channel.send("Initializing leaderboard...")
        with open(leaderboard_data_file, "w") as f:
            json.dump({"channel_id": msg.channel.id, "message_id": msg.id}, f)
        print("Leaderboard message created and saved.")
        await update_leaderboard()
    else:
        print("Leaderboard message already exists.")


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
async def update_leaderboard_message(guild):
    channel = discord.utils.get(guild.text_channels, name="owner-only")
    if not channel:
        return

    data = load_leaderboard_msg_id()
    msg_id = data.get("message_id")

    leaderboard_text = "**Current Points Table**\n\n"
    sorted_points = sorted(points.items(), key=lambda x: x[1], reverse=True)

    for uid, pts in sorted_points:
        member = guild.get_member(int(uid))
        if member:
            leaderboard_text += f"**{member.display_name}** — {pts} points\n"

    if msg_id:
        try:
            msg = await channel.fetch_message(msg_id)
            await msg.edit(content=leaderboard_text)
        except discord.NotFound:
            msg = await channel.send(leaderboard_text)
            save_leaderboard_msg_id({"message_id": msg.id})
    else:
        msg = await channel.send(leaderboard_text)
        save_leaderboard_msg_id({"message_id": msg.id})

@client.event
async def on_member_join(member):
    await update_leaderboard_message(member.guild)

@client.event
async def on_member_remove(member):
    await update_leaderboard_message(member.guild)
@client.tree.command(name="give_all", description="Give points to all members")
@app_commands.describe(amount="Amount of points to give to everyone")
async def give_all(interaction: discord.Interaction, amount: int):
    if not is_owner(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    updated_count = 0
    for member in interaction.guild.members:
        if not member.bot:
            uid = str(member.id)
            points[uid] = points.get(uid, 0) + amount
            updated_count += 1

    save_json(POINTS_FILE, points)
    await update_leaderboard()

    await interaction.response.send_message(f"Gave **{amount}** points to **{updated_count}** members.")

# Run the bot
client.run(os.environ["KEY"])
