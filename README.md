# Upland Racing Ledger Bot 🏎️

A Discord bot designed to manage race rewards and crew stakes within the Upland metaverse. 

## Features
* **Project Management**: Create specific race projects with custom reward pools.
* **Stake Tracking**: Add crew members and their respective stakes to calculate fair payouts.
* **Live Ledger**: Generate a detailed breakdown of UPX distribution.

## Slash Commands
* `/setrace`: Initialize a race project and its UPX pool.
* `/addcrew`: Add a participant and their stake.
* `/ledger`: View the current distribution of rewards.
* `/calculate`: Quick math for manual stake checks.

## Setup
1. Invite the bot to your server with `applications.commands` and `bot` scopes.
2. Set your `DISCORD_TOKEN` as an environment variable.
3. Run `python main.py`.
