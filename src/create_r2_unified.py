# src/create_r2_unified.py

import pandas as pd
from pathlib import Path
import argparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_r2_unified_dataset(base: Path):
    """Create unified R2 dataset with specified fields"""
    
    # Load R2 data
    r2_dir = base / "data/processed/R2_processed"
    logger.info(f"Loading R2 data from {r2_dir}")
    
    df_matches = pd.read_csv(r2_dir / "R2_all_matches.csv")
    df_maps = pd.read_csv(r2_dir / "R2_all_maps.csv")
    df_players = pd.read_csv(r2_dir / "R2_all_players.csv")
    
    logger.info(f"Loaded - Matches: {len(df_matches)}, Maps: {len(df_maps)}, Players: {len(df_players)}")
    
    # Group map-level info
    logger.info("Aggregating map data...")
    df_map_grouped = (
        df_maps
        .groupby(["team_name", "match_number", "match_url"], as_index=False)
        .agg({
            "map_name":    lambda s: s.tolist(),
            "map_result":  lambda s: s.tolist(),
            "our_score":   lambda s: s.tolist(),
            "their_score": lambda s: s.tolist(),
            "map_number":  'count'  # Total maps played
        })
        .rename(columns={
            "map_name":    "maps_played",
            "map_result":  "map_results",
            "our_score":   "our_scores",
            "their_score": "their_scores",
            "map_number":  "total_maps"
        })
    )
    
    # Add aggregate map statistics
    df_map_grouped['maps_won'] = df_map_grouped['map_results'].apply(lambda x: x.count('W') if isinstance(x, list) else 0)
    df_map_grouped['maps_lost'] = df_map_grouped['map_results'].apply(lambda x: x.count('L') if isinstance(x, list) else 0)
    
    # Group player-level info
    logger.info("Aggregating player data...")
    df_player_grouped = (
        df_players
        .groupby(["match_url"], as_index=False)
        .agg({
            "player_name": lambda s: s.tolist(),
            "team":        lambda s: s.tolist(),
            "rating":      lambda s: s.tolist(),
        })
        .rename(columns={
            "player_name":   "all_players",
            "team":          "all_player_teams",
            "rating":        "all_player_ratings",
        })
    )
    
    # Merge everything
    logger.info("Merging all data...")
    
    # First merge matches with map data
    df_unified = df_matches.merge(
        df_map_grouped,
        on=["team_name", "match_url"],
        how="left",
        suffixes=('_x', '_y')  # This handles match_number appearing in both
    )
    
    # Then merge with player data
    df_unified = df_unified.merge(
        df_player_grouped,
        on=["match_url"],
        how="left"
    )
    
    # Ensure we have all the required columns in the right order
    required_columns = [
        'team_id', 'team_name', 'match_number_x', 'date', 'result', 'score', 
        'opponent', 'tournament', 'match_url', 'match_number_y', 'maps_played', 
        'map_results', 'our_scores', 'their_scores', 'total_maps', 'maps_won', 
        'maps_lost', 'all_players', 'all_player_teams', 'all_player_ratings'
    ]
    
    # Check for missing columns
    missing_columns = [col for col in required_columns if col not in df_unified.columns]
    if missing_columns:
        logger.warning(f"Missing columns: {missing_columns}")
        # Create missing columns with None/empty values
        for col in missing_columns:
            df_unified[col] = None
    
    # Select only the required columns in the specified order
    df_unified = df_unified[required_columns]
    
    # Save the unified dataset
    output_path = r2_dir / "R2_unified_dataset.csv"
    df_unified.to_csv(output_path, index=False)
    
    # Print summary
    print(f"\n✅ Created R2 unified dataset: {output_path}")
    print(f"Total rows: {len(df_unified)}")
    print(f"Unique matches: {df_unified['match_url'].nunique()}")
    print(f"Teams: {df_unified['team_name'].nunique()}")
    print(f"Date range: {df_unified['date'].min()} to {df_unified['date'].max()}")
    
    # Analyze data quality
    analyze_data_quality(df_unified, df_players)
    
    return df_unified

def analyze_data_quality(df_unified: pd.DataFrame, df_players: pd.DataFrame):
    """Analyze data quality and report issues"""
    
    print("\n=== Data Quality Analysis ===")
    
    # Clean player data first
    df_players_clean = df_players.copy()
    df_players_clean['player_name'] = df_players_clean['player_name'].str.strip()
    df_players_clean['match_url'] = df_players_clean['match_url'].str.strip()
    
    # Remove any empty player names
    df_players_clean = df_players_clean[df_players_clean['player_name'] != '']
    
    # Check player counts per match
    player_counts = df_players_clean.groupby('match_url')['player_name'].count().reset_index()
    player_counts.columns = ['match_url', 'player_count']
    
    # Group by player count to see distribution
    count_distribution = player_counts['player_count'].value_counts().sort_index()
    print("\nPlayer count distribution:")
    for count, num_matches in count_distribution.items():
        print(f"  {count} players: {num_matches} matches")
    
    # Find matches with incorrect player counts (not 10 or 20)
    # 10 = one team perspective, 20 = both team perspectives
    incorrect_counts = player_counts[(player_counts['player_count'] != 10) & (player_counts['player_count'] != 20)].sort_values('player_count')
    
    if len(incorrect_counts) > 0:
        print(f"\nMatches with unusual player counts ({len(incorrect_counts)} total):")
        # Show a sample of each count type
        for count in sorted(incorrect_counts['player_count'].unique()):
            matches_with_count = incorrect_counts[incorrect_counts['player_count'] == count]
            print(f"\n  {count} players ({len(matches_with_count)} matches):")
            for _, row in matches_with_count.head(3).iterrows():
                print(f"    {row['match_url']}")
            if len(matches_with_count) > 3:
                print(f"    ... and {len(matches_with_count) - 3} more")
    
    # Check for missing data in unified dataset
    print(f"\n=== Missing Data in Unified Dataset ===")
    print(f"Rows with missing player data: {df_unified['all_players'].isna().sum()}")
    print(f"Rows with missing map data: {df_unified['maps_played'].isna().sum()}")
    print(f"Rows with missing team_id: {df_unified['team_id'].isna().sum()}")
    
    # Check for duplicate team-match combinations
    duplicates = df_unified[df_unified.duplicated(subset=['team_name', 'match_url'], keep=False)]
    if len(duplicates) > 0:
        print(f"\nWARNING: Found {len(duplicates)} duplicate team-match combinations")
        print("Example duplicates:")
        print(duplicates[['team_name', 'match_url']].head(10))
    
    # Analyze match perspectives
    match_perspectives = df_unified.groupby('match_url')['team_name'].count()
    print(f"\n=== Match Perspectives Analysis ===")
    print(f"Matches with 1 team perspective: {(match_perspectives == 1).sum()}")
    print(f"Matches with 2 team perspectives: {(match_perspectives == 2).sum()}")
    print(f"Matches with >2 team perspectives: {(match_perspectives > 2).sum()}")
    
    # Cross-check: matches with 20 players but only 1 perspective
    matches_20_players = set(player_counts[player_counts['player_count'] == 20]['match_url'])
    matches_1_perspective = set(match_perspectives[match_perspectives == 1].index)
    weird_matches = matches_20_players.intersection(matches_1_perspective)
    if weird_matches:
        print(f"\nWARNING: {len(weird_matches)} matches have 20 players but only 1 team perspective!")
        for match in list(weird_matches)[:3]:
            print(f"  {match}")
    
    return incorrect_counts

def main():
    parser = argparse.ArgumentParser(
        description="Create R2 unified dataset with specified fields"
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Project root directory"
    )
    args = parser.parse_args()
    
    # Create the unified dataset
    create_r2_unified_dataset(args.base_dir)

if __name__ == "__main__":
    main()