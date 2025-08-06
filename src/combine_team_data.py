# src/save_r2_with_duplicates.py

### USED TO COMBINE THREE SEPARATE CSV FILES PER TEAM INTO ONE BIG CSV FILE EACH ###

import pandas as pd
from pathlib import Path
import argparse
import logging
from typing import List, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_all_teams(base: Path) -> List[str]:
    """Extract all unique team names from the data directory"""
    teams = set()
    
    # Check maps directory for team files
    maps_dir = base / "data/raw/vlr_data/maps"
    if maps_dir.exists():
        for file in maps_dir.glob("*_maps.csv"):
            team_name = file.stem.replace("_maps", "")
            teams.add(team_name)
    
    return sorted(list(teams))

def load_team_data(team: str, base: Path) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load all three CSV files for a given team"""
    maps_file    = base / "data/raw/vlr_data/maps"    / f"{team}_maps.csv"
    matches_file = base / "data/raw/vlr_data/matches" / f"{team}_matches.csv"
    players_file = base / "data/raw/vlr_data/players" / f"{team}_players.csv"
    
    try:
        df_maps    = pd.read_csv(maps_file)
        df_matches = pd.read_csv(matches_file)
        df_players = pd.read_csv(players_file)
        return df_maps, df_matches, df_players
    except FileNotFoundError as e:
        logger.warning(f"Missing file for team {team}: {e}")
        return None, None, None

def main():
    parser = argparse.ArgumentParser(
        description="Save R2 data - filter out matches without player data"
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Project root directory"
    )
    args = parser.parse_args()
    
    # Load all data
    all_maps = []
    all_matches = []
    all_players = []
    
    teams = get_all_teams(args.base_dir)
    logger.info(f"Found {len(teams)} teams to process")
    
    for team in teams:
        logger.info(f"Processing team: {team}")
        df_maps, df_matches, df_players = load_team_data(team, args.base_dir)
        
        if df_maps is not None:
            all_maps.append(df_maps)
            all_matches.append(df_matches)
            all_players.append(df_players)
    
    # Combine all dataframes
    logger.info("Combining all dataframes...")
    combined_maps = pd.concat(all_maps, ignore_index=True)
    combined_matches = pd.concat(all_matches, ignore_index=True)
    combined_players = pd.concat(all_players, ignore_index=True)
    
    # Get URLs that have player data
    urls_with_players = set(combined_players['match_url'].unique())
    
    # Filter everything to only include matches with player data
    filtered_matches = combined_matches[combined_matches['match_url'].isin(urls_with_players)]
    filtered_maps = combined_maps[combined_maps['match_url'].isin(urls_with_players)]
    
    # Save to R2_processed folder
    output_dir = args.base_dir / "data/processed/R2_processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filtered_matches.to_csv(output_dir / "R2_all_matches.csv", index=False)
    filtered_maps.to_csv(output_dir / "R2_all_maps.csv", index=False)
    combined_players.to_csv(output_dir / "R2_all_players.csv", index=False)
    
    # Print summary
    print(f"\n Saved R2 data to {output_dir}")
    print(f"Matches: {len(filtered_matches)} rows")
    print(f"Maps: {len(filtered_maps)} rows")
    print(f"Players: {len(combined_players)} rows")
    print(f"Unique matches: {filtered_matches['match_url'].nunique()}")

if __name__ == "__main__":
    main()