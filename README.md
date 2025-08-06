# Valorant Match Prediction: Machine Learning Analysis of Professional Esports

This project develops a predictive model for professional Valorant match outcomes using historical performance data spanning 2021-2025. The final model achieves 60.5% test accuracy on 1,300 competitive matches, demonstrating meaningful predictive capability in the esports domain.

## Research Motivation

Traditional sports analytics has well-established frameworks for performance prediction, but competitive esports presents unique challenges. Unlike traditional sports with decades of statistical history, Valorant's competitive scene is relatively young and rapidly evolving. This creates an interesting research question: how do we build reliable predictive models in a domain where the underlying game mechanics, competitive meta, and player skill distributions are constantly shifting?

My approach focuses on identifying stable patterns in team performance while accounting for the temporal dynamics inherent to competitive gaming.

## Key Findings

The most significant discovery involves the temporal evolution of predictability in competitive Valorant. The model shows markedly better performance on recent matches (60.5% accuracy) compared to historical data (55.7% training accuracy). This suggests that as the competitive ecosystem matures, team hierarchies become more established and matchup outcomes more predictable.

Through systematic experimentation, I identified 20-day rolling windows as optimal for feature calculation. This finding has implications beyond just this dataset - it suggests there's a natural time horizon for meaningful performance trends in tactical FPS games.

The model also demonstrates strong feature synergy effects. Individual features achieve modest performance (52-57% accuracy), but their combination reaches 60.5%, indicating positive interactions when multiple performance indicators align.

## Dataset and Preprocessing

The dataset originates from 2,100+ professional Valorant matches across major VCT tournaments. All data was scraped personally from VLR.gg's website using a custom selenium scraper, and a painful amount of regular expressions. 

After applying data quality controls and feature engineering requirements, 1,300 matches remained with complete feature coverage. This reduction primarily stems from many matches scraped lacking an available R2, or, Rating 2.0 score for their players. Rating 2.0 is similar to KDA or ACS, a general rating score for how the player performed given a specific game, but more nuanced, and is calculated by VLR.GG. 
For more information on R2 Scores:
https://www.vlr.gg/381456/vlr-rating-2-0-update

The final dataset covers 43 tier-1 organizations competing between November 2021 and July 2025, providing both geographical diversity (Americas, EMEA, Pacific regions) and temporal depth for analysis.

Data preprocessing involved standardizing team identifiers across tournaments, parsing nested match results (maps and round scores), and implementing temporal validation safeguards to prevent data leakage.

## Methodology

### Feature Engineering

I developed four predictive features based on different aspects of competitive performance:

**1. Team Skill Differential (r2_advantage)**  
Quantifies fundamental skill gaps using 20-day rolling averages of individual player ratings. This captures baseline team strength while adapting to roster changes and form fluctuations.

**2. Historical Dominance Patterns (rolling_round_diff)**  
Measures teams' tendencies to win decisively versus playing close matches. Some teams consistently dominate weaker opponents while others have closer contests regardless of skill gap - a pattern that tends to persist over time.

**3. Recent Competitive Form (recent_form)**  
Win rate across the most recent 5 matches within a 30-day window. This feature captures momentum effects, meta adaptation, and short-term roster chemistry while avoiding stale data from extended periods without competition.

**4. Head-to-Head Historical Performance (h2h_advantage)**  
Win rate against specific opponents based on direct historical matchups. Through empirical testing, I determined that requiring minimum 2 previous encounters optimizes the reliability-coverage tradeoff. Matchups with insufficient history default to neutral (0.5).

### Model Architecture

I selected logistic regression as the primary algorithm for several reasons: interpretability of coefficients, exceptional performance with the available sample size, and established precedent in the sports analytics domain.

The model architecture prioritizes temporal validity through strict chronological validation. All rolling calculations employ `.shift(1)` operations to ensure historical data only, and the 80/20 train-test split maintains temporal ordering.

### Validation Framework

**Temporal Split Validation**: 80% chronological training (pre-April 2025), 20% testing (April-July 2025)  
**Cross-Validation**: 5-fold time-series CV yielding 55.8% ± 1.7% mean accuracy  
**Bootstrap Analysis**: 100 iterations confirming 60.3% ± 1.2% stability  
**Feature Ablation**: Individual feature contributions validated through solo performance testing

## Results and Analysis

### Model Performance
The final model achieves 60.5% test accuracy with 55.7% training accuracy, indicating healthy generalization without overfitting. This represents an 8.5 percentage point improvement over random baseline on test data.

Cross-validation across temporal folds shows consistent performance, validating the model's stability across different competitive periods. Bootstrap resampling confirms result reliability within tight confidence intervals.

### Feature Analysis
Individual feature performance reveals interesting patterns:
- **r2_advantage**: 55.2% (fundamental skill predictor)
- **rolling_round_diff**: 56.7% (strongest individual feature)
- **recent_form**: 54.4% (momentum indicator) 
- **h2h_advantage**: 53.6% (contextual modifier)

The gap between individual (52-57%) and combined (60.5%) performance demonstrates positive feature interactions. When multiple indicators align - skill advantage, recent form, favorable matchup history, and dominance patterns - prediction confidence increases substantially.

### Temporal Analysis
The performance difference between training and test periods provides evidence for the competitive scene maturation hypothesis. Several factors likely contribute:
- **Established team hierarchies**: Skill gaps become more consistent
- **Strategic depth**: Teams develop reliable tactical systems  
- **Reduced upset frequency**: Random factors matter less as competition matures

### Feature Engineering Insights
The 20-day optimal window discovery has broader implications for esports analytics. This timeframe balances several competing factors:
- **Recency**: Captures current form without including stale data
- **Stability**: Sufficient sample size for reliable averages
- **Meta relevance**: Aligns with typical patch cycles and strategic adaptation periods

## Technical Implementation

The implementation emphasizes reproducibility and temporal validity:

```python
# Example: Temporal rolling average with data leakage prevention
def calculate_rolling_features(df, window_days=20):
    df_sorted = df.sort_values(['team_id', 'date'])
    for team in df['team_id'].unique():
        team_data = df_sorted[df_sorted['team_id'] == team]
        rolling_avg = team_data['rating'].rolling(f'{window_days}D').mean().shift(1)
        df.loc[df['team_id'] == team, 'rolling_rating'] = rolling_avg
    return df
```

The pipeline handles missing values through principled exclusion rather than imputation, maintaining data integrity at the cost of sample size.

## Academic and Practical Implications

### Research Contributions
This work contributes to several research domains:
- **Sports Analytics**: Demonstrates temporal optimization principles for performance prediction
- **Esports Studies**: Provides quantitative evidence for competitive scene evolution
- **Machine Learning**: Documents feature synergy effects in temporal prediction tasks

### Practical Applications
The methodology has direct applications in tournament prediction, team performance analysis, and strategic planning. The 60.5% accuracy level provides actionable insights while acknowledging the inherent uncertainty in competitive outcomes.

### Future Directions
Several extensions could strengthen this work:
- **Cross-game validation**: Testing temporal optimization findings on other competitive titles
- **Advanced feature engineering**: Incorporating map-specific performance, agent selection patterns, and micro-game statistics
- **Causal inference**: Moving beyond correlation to understand causal relationships between features and outcomes

## Limitations and Considerations

The analysis focuses exclusively on tier-1 professional play, potentially limiting generalizability to other competitive levels. The model also doesn't capture certain potentially important factors like roster changes, coaching impacts, or tournament-specific pressure effects.

Feature selection prioritizes interpretability over maximum predictive power - more complex ensemble methods might achieve higher accuracy at the cost of explainability.

## Conclusion

This project demonstrates that competitive esports outcomes can be predicted with meaningful accuracy through careful feature engineering and temporal modeling. The discovery of optimal prediction windows and evidence for competitive scene maturation provide valuable insights for both academic research and practical applications.

The methodology successfully balances predictive performance with interpretability, creating a framework that could extend to other competitive gaming domains while maintaining scientific rigor.
