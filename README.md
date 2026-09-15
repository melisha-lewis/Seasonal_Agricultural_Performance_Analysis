# Seasonal Agricultural Performance Frontend

This Streamlit frontend is based on the supplied `Seasonal_Agricultural_Performance_Analysis.ipynb`.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then upload the agricultural CSV through the sidebar.

## User input

The frontend provides form fields for:
- State, District, Crop, Season
- Farm area
- Rainfall, temperature, humidity, sunlight
- Soil pH and soil moisture
- Nitrogen, phosphorus and potassium
- Irrigation method
- Fertilizer and pesticide usage
- Seed quality
- Market price and cost
- Water use and water efficiency
- Disease/pest risk

The app trains a Random Forest regression model on the uploaded dataset and predicts `Yield_Tonnes_Ha`.

The notebook itself imports `RandomForestRegressor`, `train_test_split`, `mean_absolute_error`, and `r2_score`; the frontend wires these into an interactive prediction workflow.
