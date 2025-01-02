import discord
from discord.ext import commands
from discord.ext import tasks
from discord import app_commands
from pytrends.request import TrendReq
import asyncio
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import io
import seaborn as sns
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)

# Initialize Discord bot with commands and PyTrends
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=commands.when_mentioned, intents=intents)
pytrends = TrendReq(hl='en-US', tz=360)

# Constants
CHANNEL_ID = 1319290513114796032
INTERVAL_HOURS = 8
EMBED_COLOR = 0x2F3136  # Discord dark theme color

# Country code mapping
COUNTRY_CODES = {
    'united_states': 'US',
    'india': 'IN',
    'brazil': 'BR',
    'united_kingdom': 'GB',
    'germany': 'DE',
    'france': 'FR',
    'canada': 'CA',
    'australia': 'AU',
    'spain': 'ES',
    'italy': 'IT',
    'russia': 'RU',
    'mexico': 'MX',
    'south_korea': 'KR',
    'netherlands': 'NL',
    'turkey': 'TR',
    'indonesia': 'ID',
    'switzerland': 'CH',
    'sweden': 'SE',
    'poland': 'PL',
    'belgium': 'BE',
    'norway': 'NO',
    'argentina': 'AR',
    'austria': 'AT',
    'denmark': 'DK',
    'singapore': 'SG',
    'ireland': 'IE',
    'greece': 'GR',
    'portugal': 'PT',
    'new_zealand': 'NZ',
    'finland': 'FI',
    'malaysia': 'MY',
    'israel': 'IL',
    'philippines': 'PH',
    'south_africa': 'ZA',
    'thailand': 'TH',
    'vietnam': 'VN'
}

# Suppress pandas future warnings
import warnings
import io
warnings.simplefilter(action='ignore', category=FutureWarning)

async def create_trend_charts(trends_data, country_name="Global"):
    """Create visualizations of trend data with DejaVu Sans font and dark theme."""
    # Set the dark theme and background color
    sns.set_style("darkgrid")
    plt.rcParams['axes.facecolor'] = '#2F3136'
    plt.rcParams['figure.facecolor'] = '#2F3136'
    plt.rcParams['savefig.facecolor'] = '#2F3136'

    # Set the font to DejaVu Sans
    plt.rcParams['font.family'] = 'DejaVu Sans'

    # Adjust font colors to contrast the dark background
    title_color = 'white'
    label_color = 'white'
    tick_color = 'white'

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))

    # Plot 1: Interest Over Time
    trends = [t['trend'] for t in trends_data[:10]]
    values = [t['interest'] for t in trends_data[:10]]

    sns.barplot(x=values, y=trends, palette='coolwarm', ax=ax1)
    ax1.set_title(f'Top 10 Trends by Interest - {country_name}', fontsize=14, pad=20, color=title_color)
    ax1.set_xlabel('Interest Score', fontsize=12, color=label_color)
    ax1.set_ylabel('Trends', fontsize=12, color=label_color)
    ax1.tick_params(axis='x', colors=tick_color)
    ax1.tick_params(axis='y', colors=tick_color)

    # Plot 2: Growth Rates
    growth_rates = [t['growth_rate'] for t in trends_data[:10]]

    # Create color mapping based on growth rates
    colors = ['#2ecc71' if x >= 0 else '#e74c3c' for x in growth_rates]
    sns.barplot(x=growth_rates, y=trends, palette=colors, ax=ax2)
    ax2.set_title(f'Growth Rates of Top 10 Trends - {country_name}', fontsize=14, pad=20, color=title_color)
    ax2.set_xlabel('Growth Rate (%)', fontsize=12, color=label_color)
    ax2.set_ylabel('Trends', fontsize=12, color=label_color)
    ax2.tick_params(axis='x', colors=tick_color)
    ax2.tick_params(axis='y', colors=tick_color)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight',
                facecolor=fig.get_facecolor(), edgecolor='none')
    buf.seek(0)
    plt.close()

    return discord.File(buf, filename='trend_analysis.png')

async def get_trends(country=None):
    try:
        if country:
            country = country.lower().replace(' ', '_')
            if country not in COUNTRY_CODES:
                raise ValueError(f"Country '{country}' not supported")
            trending_searches = pytrends.trending_searches(pn=country)
        else:
            trending_searches = pytrends.trending_searches(pn='united_states')  # Default to global/US trends
            
        top_20_trends = trending_searches.head(20).values.flatten().tolist()
        current_time = datetime.utcnow()
        
        trends_data = []
        for trend in top_20_trends:
            growth_rate = get_trend_growth(trend)
            trends_data.append({
                'trend': trend,
                'growth_rate': growth_rate,
                'timestamp': current_time,
                'interest': 100 - top_20_trends.index(trend) * 5
            })
        
        country_name = country.replace('_', ' ').title() if country else "Global"
        
        # Main embed with cleaner formatting
        main_embed = discord.Embed(
            title=f"{country_name} Trend Analysis 📈",
            description=f"Current trending topics in {country_name}",
            color=EMBED_COLOR,
            timestamp=current_time
        )
        
        # Split trends into 4 groups of 5
        trend_groups = []
        for i in range(0, 20, 5):
            group_text = ""
            for idx, trend_info in enumerate(trends_data[i:i+5], start=i+1):
                growth_indicator = "+" if trend_info['growth_rate'] > 0 else "-" if trend_info['growth_rate'] < 0 else "="
                group_text += f"`{idx:02d}` **{trend_info['trend']}**\n"
                group_text += f"      {growth_indicator} {abs(trend_info['growth_rate']):.1f}% | Interest: {trend_info['interest']}\n"
            trend_groups.append(group_text)

        # Add fields in 2x2 grid without group labels
        for i, group in enumerate(trend_groups):
            main_embed.add_field(
                name="\u200b",
                value=group,
                inline=True
            )
            # Add empty field after odd-numbered groups to create 2x2 layout
            if i % 2 == 0:
                main_embed.add_field(name="\u200b", value="\u200b", inline=True)
        
        # Analytics embed with cleaner design
        analytics_embed = discord.Embed(
            title=f"{country_name} Analytics Overview",
            color=EMBED_COLOR,
            timestamp=current_time
        )
        
        avg_growth = sum(t['growth_rate'] for t in trends_data) / len(trends_data)
        positive_growth = sum(1 for t in trends_data if t['growth_rate'] > 0)
        top_growers = sorted(trends_data, key=lambda x: x['growth_rate'], reverse=True)[:3]
        
        analytics_text = (
            f"**Growth Metrics**\n"
            f"Average Growth Rate: {avg_growth:.1f}%\n"
            f"Positive Trending: {positive_growth}/20\n\n"
            f"**Top Momentum**\n"
            f"1. {top_growers[0]['trend']} (+{top_growers[0]['growth_rate']:.1f}%)\n"
            f"2. {top_growers[1]['trend']} (+{top_growers[1]['growth_rate']:.1f}%)\n"
            f"3. {top_growers[2]['trend']} (+{top_growers[2]['growth_rate']:.1f}%)"
        )
        
        analytics_embed.description = analytics_text
        
        # Styling
        main_embed.set_footer(text=f"Powered by Google Trends")
        
        return main_embed, analytics_embed, await create_trend_charts(trends_data, country_name)
        
    except Exception as e:
        error_embed = discord.Embed(
            title="Error",
            description=f"Failed to fetch trends: {str(e)}",
            color=0xe74c3c
        )
        return error_embed, None, None

def get_trend_growth(keyword):
    """Calculate growth rate for a specific keyword"""
    try:
        pytrends.build_payload([keyword], timeframe='now 7-d')
        interest_over_time = pytrends.interest_over_time()
        
        if not interest_over_time.empty:
            first_value = interest_over_time[keyword].iloc[0]
            last_value = interest_over_time[keyword].iloc[-1]
            if first_value > 0:
                growth_rate = ((last_value - first_value) / first_value) * 100
                return growth_rate
        return 0
    except:
        return 0

@tasks.loop(hours=INTERVAL_HOURS)
async def send_trends():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        main_embed, analytics_embed, chart = await get_trends()
        if analytics_embed:
            await channel.send(file=chart)
            await channel.send(embed=main_embed)
            await channel.send(embed=analytics_embed)
        else:
            await channel.send(embed=main_embed)

@bot.tree.command(name="trends", description="Get trending topics for a specific country")
async def trends_command(interaction: discord.Interaction, country: str = None):
    """Get trending topics for a specific country"""
    await interaction.response.defer(ephemeral=False)
    try:
        # Get user's DM channel
        dm_channel = await interaction.user.create_dm()
        
        # Get trends data
        main_embed, analytics_embed, chart = await get_trends(country)
        
        if analytics_embed:
            await dm_channel.send(file=chart)
            await dm_channel.send(embed=main_embed)
            await dm_channel.send(embed=analytics_embed)
        else:
            await dm_channel.send(embed=main_embed)
            
        confirmation_embed = discord.Embed(
            title="Trends Sent",
            description="Trends data has been sent to your DMs!",
            color=EMBED_COLOR
        )
        await interaction.followup.send(embed=confirmation_embed)
    except discord.Forbidden:
        await interaction.followup.send("I couldn't send you a DM. Please enable DMs from server members.", ephemeral=True)
    except Exception as e:
        logging.error(f"Error in trends_command: {str(e)}")
        await interaction.followup.send("An error occurred while fetching trends.", ephemeral=True)

@bot.tree.command(name="countries", description="List all available countries")
async def list_countries(interaction: discord.Interaction):
    """List all available countries"""
    countries = [country.replace('_', ' ').title() for country in COUNTRY_CODES.keys()]
    columns = 3
    countries_list = '\n'.join(
        ' | '.join(countries[i:i + columns]) for i in range(0, len(countries), columns)
    )
    embed = discord.Embed(
        title="Available Countries",
        description=countries_list,
        color=EMBED_COLOR
    )
    await interaction.response.send_message(embed=embed)

@bot.event
async def on_error(event, *args, **kwargs):
    logging.error(f"Error in {event}: {str(args[0])}")

@bot.event
async def on_ready():
    logging.info(f'Bot logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        logging.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logging.error(f"Failed to sync commands: {e}")
    send_trends.start()

# Add reconnect logic
async def start_bot():
    while True:
        try:
            await bot.start(TOKEN)
        except (discord.ConnectionClosed, discord.GatewayNotFound, discord.HTTPException) as e:
            logging.error(f"Connection error: {str(e)}")
            await asyncio.sleep(5)
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            await asyncio.sleep(5)

# Replace with your bot token
TOKEN = 'YOUR_DISCORD_BOT_TOKEN'

# Modify the bot run line
if __name__ == "__main__":
    asyncio.run(start_bot())