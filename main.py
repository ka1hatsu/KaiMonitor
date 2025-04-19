import discord
import asyncio
import aiohttp
from datetime import datetime
from bs4 import BeautifulSoup
import os
from discord.ext import commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

tracked_accounts = {}

# Check if Instagram account exists and get follower count
async def check_instagram(username):
    url = f"https://www.instagram.com/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            text = await resp.text()

            # Detect "page not available" message
            if (
                "Sorry, this page isn't available." in text or
                "The link you followed may be broken" in text or
                "page may have been removed" in text
            ):
                return False, None  # Still banned

            # Try to extract followers
            try:
                soup = BeautifulSoup(text, "html.parser")
                scripts = soup.find_all("script", type="application/ld+json")
                for script in scripts:
                    if '"@type": "Person"' in script.text:
                        data = script.text
                        if '"interactionCount":"' in data:
                            followers_str = data.split('"interactionCount":"')[1].split('"')[0]
                            followers = int(followers_str.replace("UserFollowers:", ""))
                            return True, followers
                return True, "Unknown"
            except:
                return True, "Unknown"

# Background monitor task
async def monitor_username(username, channel):
    while True:
        is_online, followers = await check_instagram(username)

        if is_online:
            end_time = datetime.utcnow()
            start_time = tracked_accounts[username]["start_time"]
            delta = end_time - start_time
            days = delta.days
            hours, rem = divmod(delta.seconds, 3600)
            minutes, seconds = divmod(rem, 60)

            time_taken = f"{days} days {hours} hours {minutes} minutes {seconds} seconds"

            await channel.send(
                f"**Account Recovered** | @{username} | Time Taken: {time_taken} | Followers: {followers}"
            )
            del tracked_accounts[username]
            break

        await asyncio.sleep(600)  # Check every 10 minutes

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Add one username
@bot.slash_command(name="addmonitor", description="Add a single Instagram username to monitor.")
async def addmonitor(ctx, username: str):
    username = username.lower()

    if username in tracked_accounts:
        await ctx.respond(f"@{username} is already being monitored.")
        return

    tracked_accounts[username] = {
        "start_time": datetime.utcnow(),
        "channel": ctx.channel
    }

    await ctx.respond(f"Started monitoring @{username}...")
    asyncio.create_task(monitor_username(username, ctx.channel))

# Add multiple usernames
@bot.slash_command(name="addmonitors", description="Add multiple Instagram usernames to monitor (comma separated).")
async def addmonitors(ctx, usernames: str):
    names = [name.strip().lower() for name in usernames.split(",")]
    added = []
    already_tracking = []

    for username in names:
        if username in tracked_accounts:
            already_tracking.append(username)
        else:
            tracked_accounts[username] = {
                "start_time": datetime.utcnow(),
                "channel": ctx.channel
            }
            added.append(username)
            asyncio.create_task(monitor_username(username, ctx.channel))

    response = ""
    if added:
        response += "**Started monitoring:** " + ", ".join(f"@{u}" for u in added) + "\n"
    if already_tracking:
        response += "**Already being monitored:** " + ", ".join(f"@{u}" for u in already_tracking)

    await ctx.respond(response)

# List all monitored usernames
@bot.slash_command(name="listmonitored", description="List all currently monitored Instagram usernames.")
async def listmonitored(ctx):
    if not tracked_accounts:
        await ctx.respond("No usernames are currently being monitored.")
        return

    response = "**Currently Monitored Accounts:**\n"
    now = datetime.utcnow()

    for username, info in tracked_accounts.items():
        delta = now - info["start_time"]
        days = delta.days
        hours, rem = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        time_monitored = f"{days}d {hours}h {minutes}m {seconds}s"

        response += f"- @{username} (for {time_monitored})\n"

    await ctx.respond(response)

# Start the bot
bot.run(os.getenv("MTM2MzAyODM4NTIxMDgzMDg0OA.GJiIw4.0hiSNHPH-qgfYY30RyxcE2qXCTzd5L2ymNiMYI"))
