# ML Project: Valorant Match Prediction

## TL;DR
Built a machine learning model to predict professional Valorant match outcomes:
- **Dataset**: ~1,300 professional matches (2021-2025) scraped from VLR.gg
- **Accuracy**: 60.5% (vs 50.2% random baseline)
- **Method**: Logistic regression with 4 engineered features
- **Key Finding**: 20-day window optimal for performance assessment
- **Interesting Insight**: Competitive scenes become more predictable as they mature

## Skills Demonstrated
- Web scraping (Selenium, regex parsing)
- Data cleaning & feature engineering  
- ML model development & validation
- Statistical analysis & interpretation


## Model Performance

![Accuracy Over Time](notebooks/accuracy_over_time.png)

*Model accuracy increases from 56.2% to 60.5% as the competitive scene matures, consistently beating the baseline.*


## Project Structure
```
├── data/              # Raw and processed match data
├── notebooks/         # Data exploration & refining, feature engineering & visualization
├── src/              # Web scraping & feature engineering code
├── PROJECT_REPORT.md  # Full research paper with methodology
├── README.md         # This file
└── requirements.txt  # Python dependencies
```

## Installation
```bash
git clone https://github.com/zaza-op/valorant-match-predictor
cd valorant-match-predictor
pip install -r requirements.txt
```

## Full Analysis
See [PROJECT_REPORT.md](PROJECT_REPORT.md) for complete methodology, results, and findings.

## Contact
z.nimer@outlook.com - Seeking research opportunities in data analytics/ML
