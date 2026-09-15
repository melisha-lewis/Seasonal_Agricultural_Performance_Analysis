
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

st.set_page_config(
    page_title="Seasonal Agriculture Performance",
    page_icon="🌾",
    layout="wide"
)

st.title("🌾 Seasonal Agricultural Performance Analysis")
st.caption("Interactive frontend based on the uploaded agricultural analysis notebook.")

EXPECTED_COLUMNS = [
    "Farm_ID", "State", "District", "Crop", "Season",
    "Farm_Area_Hectares", "Rainfall_mm", "Avg_Temperature_C",
    "Humidity_pct", "Sunlight_Hours_Day", "Soil_pH", "Soil_Moisture_pct",
    "Nitrogen_kg_ha", "Phosphorus_kg_ha", "Potassium_kg_ha",
    "Irrigation_Method", "Fertilizer_kg_ha", "Pesticide_Litre_ha",
    "Seed_Quality_Score", "Yield_Tonnes_Ha", "Production_Tonnes",
    "Market_Price_INR_Tonne", "Total_Cost_INR", "Revenue_INR", "Profit_INR",
    "Water_Used_m3", "Water_Efficiency_t_per_1000m3",
    "Disease_Pest_Risk_pct"
]

NUMERIC_INPUTS = [
    "Farm_Area_Hectares", "Rainfall_mm", "Avg_Temperature_C",
    "Humidity_pct", "Sunlight_Hours_Day", "Soil_pH", "Soil_Moisture_pct",
    "Nitrogen_kg_ha", "Phosphorus_kg_ha", "Potassium_kg_ha",
    "Fertilizer_kg_ha", "Pesticide_Litre_ha", "Seed_Quality_Score",
    "Market_Price_INR_Tonne", "Total_Cost_INR", "Water_Used_m3",
    "Water_Efficiency_t_per_1000m3", "Disease_Pest_Risk_pct"
]

CATEGORICAL_INPUTS = ["State", "District", "Crop", "Season", "Irrigation_Method"]

# ---------- Sidebar ----------
st.sidebar.header("Data")
uploaded = st.sidebar.file_uploader(
    "Upload agricultural CSV",
    type=["csv"],
    help="Upload the CSV used by the notebook, e.g. seasonal_agriculture_performance_dataset.csv."
)

if uploaded is None:
    st.info("Upload the agricultural CSV from the sidebar to activate the dashboard.")
    st.markdown("""
    ### What this frontend provides
    - User-entered farm conditions
    - Interactive seasonal filtering
    - Average yield, profit, revenue, cost and water analysis
    - Yield prediction using a Random Forest model
    - Model MAE and R² evaluation
    """)
    st.stop()

try:
    df = pd.read_csv(uploaded)
except Exception as e:
    st.error(f"Could not read the CSV: {e}")
    st.stop()

missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
if missing:
    st.warning(
        "The uploaded CSV does not contain all columns expected by the notebook. "
        f"Missing: {', '.join(missing)}"
    )

# Convert likely numeric columns when possible
for col in EXPECTED_COLUMNS:
    if col in df.columns and col not in CATEGORICAL_INPUTS and col != "Farm_ID":
        df[col] = pd.to_numeric(df[col], errors="coerce")

# ---------- KPI section ----------
st.subheader("📊 Dataset Overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows", f"{len(df):,}")
c2.metric("Columns", f"{len(df.columns):,}")
c3.metric("Missing values", f"{int(df.isna().sum().sum()):,}")
if "Season" in df.columns:
    c4.metric("Seasons", df["Season"].nunique())
else:
    c4.metric("Seasons", "N/A")

# ---------- Interactive analysis ----------
st.subheader("🔎 Interactive Analysis")

if "Season" in df.columns:
    seasons = sorted(df["Season"].dropna().astype(str).unique().tolist())
    selected_seasons = st.multiselect(
        "Select season(s)",
        seasons,
        default=seasons
    )
else:
    selected_seasons = []

filtered = df.copy()
if selected_seasons and "Season" in df.columns:
    filtered = df[df["Season"].astype(str).isin(selected_seasons)]

if filtered.empty:
    st.warning("No records match the selected filters.")
    st.stop()

k1, k2, k3, k4 = st.columns(4)
if "Yield_Tonnes_Ha" in filtered:
    k1.metric("Average Yield", f"{filtered['Yield_Tonnes_Ha'].mean():.2f} t/ha")
if "Profit_INR" in filtered:
    k2.metric("Average Profit", f"₹{filtered['Profit_INR'].mean():,.0f}")
if "Revenue_INR" in filtered:
    k3.metric("Average Revenue", f"₹{filtered['Revenue_INR'].mean():,.0f}")
if "Water_Used_m3" in filtered:
    k4.metric("Average Water", f"{filtered['Water_Used_m3'].mean():,.0f} m³")

left, right = st.columns(2)

with left:
    if {"Season", "Yield_Tonnes_Ha"}.issubset(filtered.columns):
        season_yield = filtered.groupby("Season")["Yield_Tonnes_Ha"].mean()
        fig, ax = plt.subplots(figsize=(7, 4))
        season_yield.plot(kind="bar", ax=ax)
        ax.set_title("Average Crop Yield by Season")
        ax.set_xlabel("Season")
        ax.set_ylabel("Yield (Tonnes/Ha)")
        plt.xticks(rotation=0)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

with right:
    if {"Season", "Profit_INR"}.issubset(filtered.columns):
        profit_data = filtered.groupby("Season")["Profit_INR"].mean()
        fig, ax = plt.subplots(figsize=(7, 4))
        profit_data.plot(kind="bar", ax=ax)
        ax.set_title("Average Profit by Season")
        ax.set_xlabel("Season")
        ax.set_ylabel("Average Profit (INR)")
        plt.xticks(rotation=0)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

if {"Water_Used_m3", "Yield_Tonnes_Ha"}.issubset(filtered.columns):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.scatter(filtered["Water_Used_m3"], filtered["Yield_Tonnes_Ha"], alpha=0.55)
    ax.set_title("Water Usage vs Crop Yield")
    ax.set_xlabel("Water Used (m³)")
    ax.set_ylabel("Crop Yield (Tonnes/Ha)")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

# ---------- User input prediction ----------
st.subheader("🌱 Enter Farm Details")
st.write("Enter a new farm's conditions below. The model predicts **Yield (Tonnes/Ha)**.")

if "Yield_Tonnes_Ha" not in df.columns:
    st.error("Yield_Tonnes_Ha is required for prediction.")
    st.stop()

# Use available dataset values as dropdown choices
def choices(col, fallback):
    if col in df.columns:
        vals = df[col].dropna().astype(str).unique().tolist()
        if vals:
            return sorted(vals)
    return fallback

with st.form("farm_prediction_form"):
    a, b, c = st.columns(3)

    with a:
        state = st.selectbox("State", choices("State", ["Karnataka"]))
        district = st.selectbox("District", choices("District", ["Bengaluru"]))
        crop = st.selectbox("Crop", choices("Crop", ["Rice", "Wheat", "Maize", "Pulses"]))
        season = st.selectbox("Season", choices("Season", ["Kharif", "Rabi", "Zaid"]))
        irrigation = st.selectbox(
            "Irrigation Method",
            choices("Irrigation_Method", ["Drip", "Sprinkler", "Flood"])
        )
        farm_area = st.number_input("Farm Area (hectares)", min_value=0.01, value=2.0, step=0.1)

    with b:
        rainfall = st.number_input("Rainfall (mm)", min_value=0.0, value=500.0, step=10.0)
        temperature = st.number_input("Average Temperature (°C)", value=25.0, step=0.5)
        humidity = st.number_input("Humidity (%)", min_value=0.0, max_value=100.0, value=65.0, step=1.0)
        sunlight = st.number_input("Sunlight (hours/day)", min_value=0.0, value=7.0, step=0.1)
        soil_ph = st.number_input("Soil pH", min_value=0.0, max_value=14.0, value=6.5, step=0.1)
        soil_moisture = st.number_input("Soil Moisture (%)", min_value=0.0, max_value=100.0, value=50.0, step=1.0)
        nitrogen = st.number_input("Nitrogen (kg/ha)", min_value=0.0, value=80.0, step=1.0)
        phosphorus = st.number_input("Phosphorus (kg/ha)", min_value=0.0, value=40.0, step=1.0)
        potassium = st.number_input("Potassium (kg/ha)", min_value=0.0, value=40.0, step=1.0)

    with c:
        fertilizer = st.number_input("Fertilizer (kg/ha)", min_value=0.0, value=100.0, step=1.0)
        pesticide = st.number_input("Pesticide (L/ha)", min_value=0.0, value=1.0, step=0.1)
        seed_quality = st.number_input(
            "Seed Quality Score", min_value=0.0, max_value=1.0, value=0.85, step=0.01
        )
        market_price = st.number_input(
            "Market Price (INR/tonne)", min_value=0.0, value=30000.0, step=500.0
        )
        total_cost = st.number_input("Total Cost (INR)", min_value=0.0, value=100000.0, step=5000.0)
        water_used = st.number_input("Water Used (m³)", min_value=0.0, value=3000.0, step=100.0)
        water_eff = st.number_input(
            "Water Efficiency (t/1000m³)", min_value=0.0, value=2.0, step=0.1
        )
        risk = st.number_input(
            "Disease/Pest Risk (%)", min_value=0.0, max_value=100.0, value=40.0, step=1.0
        )

    submitted = st.form_submit_button("🚀 Predict Yield", use_container_width=True)

if submitted:
    feature_cols = [c for c in EXPECTED_COLUMNS if c in df.columns and c not in ["Yield_Tonnes_Ha", "Farm_ID"]]
    X = df[feature_cols].copy()
    y = pd.to_numeric(df["Yield_Tonnes_Ha"], errors="coerce")

    valid = y.notna()
    X = X.loc[valid]
    y = y.loc[valid]

    if len(X) < 10:
        st.error("At least 10 valid training rows are recommended for prediction.")
        st.stop()

    categorical = [c for c in feature_cols if c in CATEGORICAL_INPUTS]
    numeric = [c for c in feature_cols if c not in categorical]

    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median"))
    ])
    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore"))
    ])

    preprocessor = ColumnTransformer([
        ("num", numeric_pipeline, numeric),
        ("cat", categorical_pipeline, categorical)
    ])

    model = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", RandomForestRegressor(
            n_estimators=250,
            random_state=42,
            n_jobs=-1
        ))
    ])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    with st.spinner("Training model and generating prediction..."):
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        mae = mean_absolute_error(y_test, predictions)
        r2 = r2_score(y_test, predictions)

        input_row = {
            "State": state,
            "District": district,
            "Crop": crop,
            "Season": season,
            "Farm_Area_Hectares": farm_area,
            "Rainfall_mm": rainfall,
            "Avg_Temperature_C": temperature,
            "Humidity_pct": humidity,
            "Sunlight_Hours_Day": sunlight,
            "Soil_pH": soil_ph,
            "Soil_Moisture_pct": soil_moisture,
            "Nitrogen_kg_ha": nitrogen,
            "Phosphorus_kg_ha": phosphorus,
            "Potassium_kg_ha": potassium,
            "Irrigation_Method": irrigation,
            "Fertilizer_kg_ha": fertilizer,
            "Pesticide_Litre_ha": pesticide,
            "Seed_Quality_Score": seed_quality,
            "Market_Price_INR_Tonne": market_price,
            "Total_Cost_INR": total_cost,
            "Water_Used_m3": water_used,
            "Water_Efficiency_t_per_1000m3": water_eff,
            "Disease_Pest_Risk_pct": risk,
        }

        # The original notebook has derived output columns. We don't ask the
        # user to enter those because they are outputs, not independent inputs.
        for col in feature_cols:
            if col not in input_row:
                if pd.api.types.is_numeric_dtype(df[col]):
                    input_row[col] = float(df[col].median())
                else:
                    input_row[col] = str(df[col].mode(dropna=True).iloc[0])

        new_data = pd.DataFrame([input_row])[feature_cols]
        predicted_yield = float(model.predict(new_data)[0])

    p1, p2, p3 = st.columns(3)
    p1.metric("Predicted Yield", f"{predicted_yield:.2f} t/ha")
    p2.metric("MAE", f"{mae:.2f}")
    p3.metric("R² Score", f"{r2:.3f}")

    st.success(f"Estimated crop yield: **{predicted_yield:.2f} tonnes/hectare**")

# ---------- Season summary ----------
st.subheader("📋 Season Summary")
summary_cols = {}
if {"Season", "Yield_Tonnes_Ha"}.issubset(df.columns):
    summary_cols["Average Yield"] = df.groupby("Season")["Yield_Tonnes_Ha"].mean()
if {"Season", "Profit_INR"}.issubset(df.columns):
    summary_cols["Average Profit"] = df.groupby("Season")["Profit_INR"].mean()
if {"Season", "Water_Used_m3"}.issubset(df.columns):
    summary_cols["Average Water"] = df.groupby("Season")["Water_Used_m3"].mean()
if {"Season", "Revenue_INR"}.issubset(df.columns):
    summary_cols["Average Revenue"] = df.groupby("Season")["Revenue_INR"].mean()
if {"Season", "Total_Cost_INR"}.issubset(df.columns):
    summary_cols["Average Cost"] = df.groupby("Season")["Total_Cost_INR"].mean()
if {"Season", "Disease_Pest_Risk_pct"}.issubset(df.columns):
    summary_cols["Average Risk"] = df.groupby("Season")["Disease_Pest_Risk_pct"].mean()

if summary_cols:
    season_summary = pd.DataFrame(summary_cols).round(2)
    st.dataframe(season_summary, use_container_width=True)

    if not season_summary.empty:
        best_yield = season_summary["Average Yield"].idxmax() if "Average Yield" in season_summary else None
        best_profit = season_summary["Average Profit"].idxmax() if "Average Profit" in season_summary else None
        highest_water = season_summary["Average Water"].idxmax() if "Average Water" in season_summary else None
        highest_risk = season_summary["Average Risk"].idxmax() if "Average Risk" in season_summary else None

        insights = []
        if best_yield:
            insights.append(f"Best average yield: **{best_yield}**")
        if best_profit:
            insights.append(f"Best average profit: **{best_profit}**")
        if highest_water:
            insights.append(f"Highest water usage: **{highest_water}**")
        if highest_risk:
            insights.append(f"Highest disease/pest risk: **{highest_risk}**")
        st.markdown(" | ".join(insights))

st.subheader("🧾 Filtered Data")
st.dataframe(filtered.head(500), use_container_width=True)
