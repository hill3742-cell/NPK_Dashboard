from pathlib import Path
from yfpy.query import YahooFantasySportsQuery

# Verified credentials from your Yahoo Developer dashboard
YAHOO_CLIENT_ID = "dj0yJmk9ZVpNYjBQdjhFOUxMJmQ9WVdrOVVUSm9OVTl2WXpRbWNHbzlNQT09JnM9Y29uc3VtZXJzZWNyZXQmc3Y9MCZ4PTkx"
YAHOO_CLIENT_SECRET = "f63ab85ef140c266c3c62cdc87cb40077b40eade"
LEAGUE_ID = "31198"

# Saves generated tokens to .env in your main project folder
env_path = Path(__file__).parent.parent

print(f"Connecting to Yahoo Fantasy API for League ID {LEAGUE_ID}...")

query = YahooFantasySportsQuery(
    league_id=LEAGUE_ID,
    game_code="nfl",
    yahoo_consumer_key=YAHOO_CLIENT_ID,
    yahoo_consumer_secret=YAHOO_CLIENT_SECRET,
    env_file_location=env_path,
    save_token_data_to_env_file=True,
    browser_callback=True,
)

try:
    meta = query.get_league_metadata()
    print(f"\n[SUCCESS] Connected to League: {meta.name}")
    print(f"Season: {meta.season} | Teams: {meta.num_teams} | Current Week: {meta.current_week}")

    print("\nFetching League Standings:")
    standings = query.get_league_standings()
    for team in standings.teams:
        rank = getattr(getattr(team, "team_standings", None), "rank", "-")
        print(f"Rank {rank}: {team.name}")
except Exception as e:
    print(f"\n[ERROR] Failed to query league: {e}")