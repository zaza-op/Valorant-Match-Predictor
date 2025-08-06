# Dataset Documentation

## Overview
Professional Valorant competitive match data spanning November 2021 to July 2025, covering major VCT tournaments and tier-1 competitive play.

## Data Sources
- VLR.gg Website

## Dataset Characteristics
- **Total Matches**: 1298, (after cleaning)
- **Teams Covered**: 43 tier-1 organizations
- **Time Period**: 2021-11-04 to 2025-07-13

## Data Schema

### DataSets
Raw dataset: data/raw
Combined dataset: data/processed/all_teams
Datasets with R2 Scores only: data/processed/R2_processed
Final Dataset: notebooks/processed_valorant_dataset.cs

### Match-Level Features
| Column | Type | Description |
|--------|------|-------------|
| match_number | int | Unique match identifier |
| date | datetime | Match date (YYYY-MM-DD) |
| result | string | Match outcome ('W'/'L') |
| team_name | string | Team name (standardized) |
| opponent | string | Opponent team name |
| tournament | string | Tournament/event name |
| maps_played | list | Maps in match |
| our_scores | list | Rounds won per map |
| their_scores | list | Opponent rounds won per map |

### Player Performance Features  
| Column | Type | Description |
|--------|------|-------------|
| all_players | list | Player names in match |
| all_player_teams | list | Team affiliations |
| all_player_ratings | list | Individual R2 performance ratings |

### Engineered Features
| Column | Type | Description |
|--------|------|-------------|
| mean_my_rating | float | Team average rating for match |
| mean_opp_rating | float | Opponent average rating |
| rolling_20d_my | float | 20-day rolling average (own team) |  (large variety, ranging 15d-200d)
| rolling_20d_opp | float | 20-day rolling average (opponent) | (large variety, raniging 15d-200d)
| r2_advantage | float | Skill differential feature |
| rolling_round_diff | float | Historical dominance pattern |
| recent_form | float | Win rate in last 5 games |
| h2h_advantage | float | Head-to-head historical record |

## Data Quality
- **Missing Values**: <2% across all features (handled via dropna)
- **Temporal Coverage**: Even distribution across time periods
- **Team Balance**: 50.2% overall win rate (well-balanced)
- **Validation**: Comprehensive data integrity checks performed

## Preprocessing Steps
1. **Team Standardization**: Mapped team abbreviations to full names
2. **Date Parsing**: Converted to datetime objects for temporal analysis  
3. **Rating Extraction**: Parsed individual player ratings from match data
4. **Feature Engineering**: Generated rolling averages and derived metrics
5. **Quality Filtering**: Removed matches with insufficient historical context