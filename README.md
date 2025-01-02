# Trends Bot

Trends Bot is a Discord bot that fetches and displays trending topics from Google Trends. It provides visualizations and analytics for the top trends in various countries.

## Features

- Fetches trending topics from Google Trends
- Provides visualizations of trend data
- Supports multiple countries
- Sends trend updates at regular intervals
- Commands to get trends and list available countries

## Requirements

- Python 3.8+
- Discord bot token

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/pythontooth/trendsdiscordbot.git
    cd TRENDS_BOT
    ```

2. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

3. Replace the placeholder token in `bot.py` with your Discord bot token:
    ```python
    TOKEN = 'YOUR_DISCORD_BOT_TOKEN'
    ```

## Usage

1. Run the bot:
    ```sh
    python bot.py
    ```

2. Invite the bot to your Discord server using the OAuth2 URL with the necessary permissions.

## Commands

- `/trends [country]`: Get trending topics for a specific country. If no country is specified, it defaults to the United States.
- `/countries`: List all available countries.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any changes.

## License

This project is licensed under the MIT License.
