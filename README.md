# Raytown Construction Racing Ledger 🏎️

A specialized Discord bot for the Upland Metaverse to calculate and track crew rewards based on Spark hours and UPX rates.

## Features
- **Dynamic Payouts**: Automatically calculates reward pools using `Spark Hours * UPX Rate`.
- **Stake Tracking**: Manage crew member contributions for specific projects.
- **Visual Ledgers**: Professional Discord Embeds for payout transparency.

## Setup
1. Clone this repository.
2. Install dependencies: `pip install -r requirements.txt`.
3. Set your `DISCORD_TOKEN` in your environment variables.
4. Run `python main.py`.

## Commands
- `/setrace`: Define project metrics (Spark/UPX).
- `/ledger`: Generate the payout breakdown.
- `/addcrew`: Add a participant's stake.
