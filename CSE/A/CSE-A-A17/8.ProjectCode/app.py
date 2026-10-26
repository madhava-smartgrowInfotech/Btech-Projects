"""
app.py
--------
Main Streamlit entry point for:

    "Fashion Demand Forecasting Using Machine Learning and Domain Adaptation"

This file ONLY handles UI/navigation and wiring pages together. All actual
data processing / ML logic lives in the `src/` package.

Run locally with:
    streamlit run app.py
"""

from __future__ import annotations

import joblib
import numpy as np
import pandas as pd
import streamlit as st

from src import data_loader, preprocessing, demand_forecasting, feature_engineering
from src import baseline_models, xgboost_model, domain_adaptation, evaluation, visualization, gemini_helper


st.set_page_config(
    page_title="Fashion Demand Forecasting",
    page_icon="👗",
    layout="wide",
)

MODEL_DIR = "models"
BASELINE_MODEL_PATH = f"{MODEL_DIR}/baseline_xgboost.joblib"
ADAPTED_MODEL_PATH = f"{MODEL_DIR}/adapted_xgboost.joblib"
FEATURE_INFO_PATH = f"{MODEL_DIR}/feature_info.joblib"


# ----------------------------------------------------------------------
# Session state initialization -- this is how data/models persist as the
# user clicks between sidebar pages.
# ----------------------------------------------------------------------
for key in [
    "transactions_raw", "articles_raw", "customers_raw",
    "merged", "daily_demand", "feature_table", "feature_mappings",
    "train_df", "test_df",
    "baseline_model", "domain_report",
    "source_model", "adapted_model", "domain_eval",
]:
    if key not in st.session_state:
        st.session_state[key] = None


def sidebar_navigation() -> str:
    st.sidebar.title("👗 Navigation")
    pages = [
        "Home",
        "Data Upload",
        "Data Exploration",
        "Demand Analysis",
        "Feature Engineering",
        "Model Training",
        "Domain Adaptation",
        "Model Evaluation",
        "Demand Forecast",
        "AI Insights",
        "About Project",
    ]
    return st.sidebar.radio("Go to", pages)


# ----------------------------------------------------------------------
# PAGES
# ----------------------------------------------------------------------

def page_home():
    st.title("Fashion Demand Forecasting Using Machine Learning and Domain Adaptation")
    st.subheader("AI-powered fashion demand prediction for changing retail environments")
    st.markdown(
        """
This dashboard walks through a complete demand-forecasting pipeline built
on the H&M Fashion dataset:

1. **Data Upload** — bring your own `customers.csv`, `articles.csv`, `transactions_train.csv`
2. **Data Exploration** — sales trends, top products, category breakdowns
3. **Demand Analysis** — daily/weekly/monthly aggregated demand
4. **Feature Engineering** — time, seasonal, lag & rolling features
5. **Model Training** — baseline vs XGBoost (with tuning)
6. **Domain Adaptation** — instance-weighted adaptation across a chosen domain split
7. **Model Evaluation** — RMSE / MAE / MAPE / R², before vs after adaptation
8. **Demand Forecast** — generate and visualize future predictions
9. **AI Insights** — optional Gemini-powered plain-language explanations

Use the sidebar to move through each stage in order.
        """
    )
    st.info("Start with **Data Upload** to get going.")


def page_data_upload():
    st.title("📂 Data Upload")
    st.write("Upload your H&M dataset files below. Only Transactions and Articles are required.")

    sample_limit = st.number_input(
        "Max transaction rows to load (for performance / experimentation). Set 0 for no limit.",
        min_value=0, value=200_000, step=50_000,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        transactions_file = st.file_uploader("Transactions CSV", type="csv", key="up_txn")
    with col2:
        articles_file = st.file_uploader("Articles CSV", type="csv", key="up_art")
    with col3:
        customers_file = st.file_uploader("Customers CSV (optional)", type="csv", key="up_cust")

    if st.button("Load & Process Data", type="primary"):
        try:
            nrows = None if sample_limit == 0 else int(sample_limit)

            if transactions_file is None:
                st.error("Please upload the transaction dataset.")
                return
            if articles_file is None:
                st.error("Please upload the article dataset.")
                return

            transactions_raw = data_loader.load_transactions(transactions_file, sample_rows=nrows)
            articles_raw = data_loader.load_articles(articles_file)
            customers_raw = data_loader.load_customers(customers_file) if customers_file else pd.DataFrame()

            with st.spinner("Cleaning data..."):
                cleaned_txn = preprocessing.clean_transactions(transactions_raw)
                cleaned_art = preprocessing.clean_articles(articles_raw)
                cleaned_cust = preprocessing.clean_customers(customers_raw)
                merged = preprocessing.merge_datasets(cleaned_txn, cleaned_art, cleaned_cust)

            st.session_state.transactions_raw = cleaned_txn
            st.session_state.articles_raw = cleaned_art
            st.session_state.customers_raw = cleaned_cust
            st.session_state.merged = merged

            report = preprocessing.data_quality_report(transactions_raw, cleaned_txn, merged)
            st.success("Data loaded and cleaned successfully!")
            render_data_quality_report(report)

        except data_loader.DataValidationError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Something went wrong while processing your files: {e}")

    elif st.session_state.merged is not None:
        st.info("Data already loaded for this session. Upload new files above to replace it.")
        report = preprocessing.data_quality_report(
            st.session_state.transactions_raw, st.session_state.transactions_raw, st.session_state.merged
        )
        render_data_quality_report(report)


def render_data_quality_report(report: dict):
    st.subheader("📊 Data Quality Report")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Transactions", f"{report['num_transactions']:,}")
    c2.metric("Customers", f"{report['num_customers']:,}")
    c3.metric("Products", f"{report['num_products']:,}")
    c4.metric("Columns", report["columns"])

    c5, c6, c7 = st.columns(3)
    c5.metric("Missing Values", f"{report['missing_values_total']:,}")
    c6.metric("Duplicate Rows", f"{report['duplicate_rows']:,}")
    c7.metric("Rows Removed in Cleaning", f"{report['rows_removed']:,}")

    if report["date_min"] is not None:
        st.write(f"**Date range:** {report['date_min'].date()} → {report['date_max'].date()}")


def page_data_exploration():
    st.title("🔍 Data Exploration")
    if st.session_state.merged is None:
        st.warning("Please upload and process data first (Data Upload page).")
        return

    if st.session_state.daily_demand is None:
        with st.spinner("Aggregating daily demand..."):
            st.session_state.daily_demand = demand_forecasting.aggregate_daily_demand(st.session_state.merged)

    daily = st.session_state.daily_demand

    st.plotly_chart(visualization.plot_daily_trend(daily), use_container_width=True)
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(visualization.plot_monthly_demand(daily), use_container_width=True)
    with col2:
        st.plotly_chart(visualization.plot_weekly_demand(daily), use_container_width=True)

    st.plotly_chart(visualization.plot_top_products(daily), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        for cat_col in ["department_name", "colour_group_name"]:
            if cat_col in daily.columns:
                st.plotly_chart(visualization.plot_categorical_demand(daily, cat_col), use_container_width=True)
    with col4:
        if "sales_channel_id" in daily.columns:
            st.plotly_chart(visualization.plot_categorical_demand(daily, "sales_channel_id"), use_container_width=True)
        st.plotly_chart(visualization.plot_price_distribution(daily), use_container_width=True)


def page_demand_analysis():
    st.title("📈 Demand Analysis")
    if st.session_state.daily_demand is None:
        st.warning("Please visit Data Exploration first to compute daily demand.")
        return

    daily = st.session_state.daily_demand
    st.write("Aggregated daily demand table (date + article_id → demand):")
    st.dataframe(daily.head(200), use_container_width=True)

    st.markdown(
        """
**Note on data leakage:** This table is built by counting transactions
that occurred *on that exact date* for *that exact product* — no future
information is used in the aggregation itself. Leakage risk only enters
later, in feature engineering, which is why lag/rolling features are
computed with a strict `.shift()` before any rolling window.
        """
    )


def page_feature_engineering():
    st.title("⚙️ Feature Engineering")
    if st.session_state.daily_demand is None:
        st.warning("Please visit Data Exploration first.")
        return

    if st.button("Build Feature Table", type="primary"):
        with st.spinner("Filling missing dates and engineering features..."):
            filled = demand_forecasting.fill_missing_dates_per_article(st.session_state.daily_demand)
            feature_table, mappings = feature_engineering.build_feature_table(filled)
            st.session_state.feature_table = feature_table
            st.session_state.feature_mappings = mappings
        st.success("Feature table built.")

    if st.session_state.feature_table is not None:
        ft = st.session_state.feature_table
        st.write(f"Feature table shape: **{ft.shape[0]:,} rows × {ft.shape[1]} columns**")
        st.dataframe(ft.head(50), use_container_width=True)

        feature_cols = feature_engineering.get_feature_columns(ft)
        st.write("**Model input features:**")
        st.code(", ".join(feature_cols))


def page_model_training():
    st.title("🤖 Model Training")
    if st.session_state.feature_table is None:
        st.warning("Please build the feature table first (Feature Engineering page).")
        return

    ft = st.session_state.feature_table
    train_fraction = st.slider("Training data fraction (chronological)", 0.5, 0.95, 0.8, 0.05)

    train_df, test_df = baseline_models.chronological_split(ft, train_fraction=train_fraction)
    summary = baseline_models.split_summary(train_df, test_df)

    st.subheader("Chronological Train/Test Split")
    st.markdown(
        """
We split by **date**, not randomly — the model is trained on earlier
dates and tested on later dates, mirroring how it will actually be used
in production (you never have next week's data when forecasting this week).
A random split would leak future information into training and produce
overly optimistic, misleading metrics.
        """
    )
    c1, c2 = st.columns(2)
    c1.write(f"**Train:** {summary['train_start'].date()} → {summary['train_end'].date()} ({summary['train_rows']:,} rows)")
    c2.write(f"**Test:** {summary['test_start'].date()} → {summary['test_end'].date()} ({summary['test_rows']:,} rows)")

    st.session_state.train_df = train_df
    st.session_state.test_df = test_df

    feature_cols = feature_engineering.get_feature_columns(ft)
    X_train, y_train = train_df[feature_cols], train_df["demand"]
    X_test, y_test = test_df[feature_cols], test_df["demand"]

    st.subheader("Baseline: Historical Moving Average")
    if st.button("Run Moving Average Baseline"):
        preds = baseline_models.moving_average_forecast(train_df, test_df)
        metrics = evaluation.evaluate_model(y_test, preds)
        st.json(metrics)
        st.session_state.setdefault("results", {})
        st.session_state.results = st.session_state.get("results", {})
        st.session_state.results["Moving Average"] = metrics

    st.subheader("XGBoost Model")
    tune = st.checkbox("Run hyperparameter tuning (slower, more accurate)")
    if st.button("Train XGBoost", type="primary"):
        with st.spinner("Training XGBoost..."):
            if tune:
                model, best_params = xgboost_model.tune_xgboost(X_train, y_train, n_iter=10, cv_splits=3)
                st.write("Best parameters found:", best_params)
            else:
                model = xgboost_model.train_xgboost(X_train, y_train)

            preds = model.predict(X_test)
            metrics = evaluation.evaluate_model(y_test, preds)

        st.session_state.baseline_model = model
        st.session_state.setdefault("results", {})
        st.session_state.results = st.session_state.get("results", {})
        st.session_state.results["XGBoost"] = metrics
        st.success("XGBoost trained.")
        st.json(metrics)

        joblib.dump(model, BASELINE_MODEL_PATH)
        joblib.dump({"feature_cols": feature_cols}, FEATURE_INFO_PATH)

    if st.button("Load Existing XGBoost Model"):
        try:
            st.session_state.baseline_model = joblib.load(BASELINE_MODEL_PATH)
            st.success("Loaded saved model.")
        except FileNotFoundError:
            st.error("No saved model found yet — train one first.")

    if "results" in st.session_state and st.session_state.results:
        st.subheader("Model Comparison So Far")
        comp = evaluation.compare_models(st.session_state.results)
        st.dataframe(comp, use_container_width=True)
        st.plotly_chart(visualization.plot_model_comparison(comp, "RMSE"), use_container_width=True)


def page_domain_adaptation():
    st.title("🔀 Domain Adaptation")
    if st.session_state.feature_table is None:
        st.warning("Please build the feature table first.")
        return

    ft = st.session_state.feature_table
    st.markdown(
        """
We train on a **source domain** and test on a **target domain** that may
have a different data distribution (different price points, product mix,
seasonal pattern, etc.) — this is called *distribution shift*. Below, we
first measure that shift, then attempt to correct for it using
**instance-weighted domain adaptation**.
        """
    )

    domain_options = [c for c in ["sales_channel_id", "product_group_name", "department_name"] if c in ft.columns]
    if not domain_options:
        st.error("No suitable domain-split column found (expected sales_channel_id, product_group_name, or department_name).")
        return

    domain_col = st.selectbox("Domain-defining column", domain_options)
    unique_vals = sorted(ft[domain_col].dropna().unique().tolist())
    if len(unique_vals) < 2:
        st.error(f"Column '{domain_col}' does not have at least 2 distinct values to split source/target.")
        return

    source_val = st.selectbox("Source domain value", unique_vals, index=0)
    target_val = st.selectbox("Target domain value", unique_vals, index=min(1, len(unique_vals) - 1))

    if source_val == target_val:
        st.error("Source and target values must be different.")
        return

    if st.button("Run Domain Shift Analysis & Adaptation", type="primary"):
        # Exclude the domain-defining column itself from the feature set --
        # otherwise the domain classifier (and the model) would trivially
        # "cheat" by reading the domain label directly off a feature.
        feature_cols = [c for c in feature_engineering.get_feature_columns(ft) if c != domain_col]
        source_df, target_df = domain_adaptation.split_domains(ft, domain_col, source_val, target_val)

        if source_df.empty or target_df.empty:
            st.error("One of the domains has no data. Choose different values.")
            return

        source_X, source_y = source_df[feature_cols], source_df["demand"]
        target_train, target_test = baseline_models.chronological_split(target_df, train_fraction=0.5)
        target_test_X, target_test_y = target_test[feature_cols], target_test["demand"]

        with st.spinner("Training source-domain model (no adaptation)..."):
            source_model = xgboost_model.train_xgboost(source_X, source_y)
            preds_before = source_model.predict(target_test_X)
            metrics_before = evaluation.evaluate_model(target_test_y, preds_before)

        st.subheader("Domain Shift Analysis")
        classifier, clf_acc = domain_adaptation.train_domain_classifier(source_X, target_df[feature_cols])
        st.metric("Domain Classifier Accuracy", f"{clf_acc:.2%}",
                   help="Close to 50% = domains look similar. Close to 100% = domains are very different.")

        shift_summary = domain_adaptation.domain_shift_summary(source_X, target_df[feature_cols])
        st.dataframe(shift_summary.head(15), use_container_width=True)

        top_shift_feature = shift_summary.iloc[0]["feature"]
        st.plotly_chart(
            visualization.plot_domain_shift_histogram(source_X[top_shift_feature], target_df[top_shift_feature], top_shift_feature),
            use_container_width=True,
        )
        st.plotly_chart(
            visualization.plot_domain_shift_boxplot(source_X[top_shift_feature], target_df[top_shift_feature], top_shift_feature),
            use_container_width=True,
        )

        with st.spinner("Computing instance weights and training adapted model..."):
            weights = domain_adaptation.compute_instance_weights(classifier, source_X)
            adapted_model = domain_adaptation.train_adapted_model(source_X, source_y, weights)
            preds_after = adapted_model.predict(target_test_X)
            metrics_after = evaluation.evaluate_model(target_test_y, preds_after)

        st.session_state.source_model = source_model
        st.session_state.adapted_model = adapted_model
        st.session_state.domain_eval = (metrics_before, metrics_after)

        joblib.dump(adapted_model, ADAPTED_MODEL_PATH)

        st.subheader("Before vs After Adaptation")
        report = evaluation.before_after_adaptation_report(metrics_before, metrics_after)
        st.dataframe(report, use_container_width=True)
        st.caption("Improvement percentages reflect the actual experiment above — not a claimed or assumed result.")


def page_model_evaluation():
    st.title("📏 Model Evaluation")
    if "results" in st.session_state and st.session_state.results:
        st.subheader("Baseline vs XGBoost")
        comp = evaluation.compare_models(st.session_state.results)
        st.dataframe(comp, use_container_width=True)
        for metric in ["RMSE", "MAE", "MAPE (%)"]:
            st.plotly_chart(visualization.plot_model_comparison(comp, metric), use_container_width=True)
    else:
        st.info("Train models on the Model Training page first.")

    if st.session_state.domain_eval is not None:
        st.subheader("Domain Adaptation: Before vs After")
        before, after = st.session_state.domain_eval
        report = evaluation.before_after_adaptation_report(before, after)
        st.dataframe(report, use_container_width=True)

    if st.session_state.baseline_model is not None and st.session_state.feature_table is not None:
        st.subheader("Feature Importance")
        feature_cols = feature_engineering.get_feature_columns(st.session_state.feature_table)
        pairs = xgboost_model.get_feature_importance(st.session_state.baseline_model, feature_cols, top_n=20)
        st.plotly_chart(visualization.plot_feature_importance(pairs), use_container_width=True)


def page_demand_forecast():
    st.title("🔮 Demand Forecast")
    if st.session_state.baseline_model is None or st.session_state.feature_table is None:
        st.warning("Please train the XGBoost model first (Model Training page).")
        return

    ft = st.session_state.feature_table
    article_ids = sorted(ft["article_id"].unique().tolist())
    article_id = st.selectbox("Select Article", article_ids)
    horizon = st.selectbox("Forecast Horizon (days)", [7, 14, 30])

    if st.button("Generate Forecast", type="primary"):
        model = st.session_state.baseline_model
        feature_cols = feature_engineering.get_feature_columns(ft)

        article_history = ft[ft["article_id"] == article_id].sort_values("t_dat")
        if len(article_history) < 5:
            st.error("Not enough historical data to create lag features for this product.")
            return

        last_row = article_history.iloc[-1].copy()
        last_date = last_row["t_dat"]
        recent_demand = article_history["demand"].tolist()

        forecast_rows = []
        for step in range(1, horizon + 1):
            future_date = last_date + pd.Timedelta(days=step)
            row = last_row.copy()
            row["t_dat"] = future_date

            # Recompute time features for the future date
            row["year"] = future_date.year
            row["month"] = future_date.month
            row["day"] = future_date.day
            row["day_of_week"] = future_date.dayofweek
            row["is_weekend"] = int(future_date.dayofweek >= 5)
            row["month_sin"] = np.sin(2 * np.pi * future_date.month / 12)
            row["month_cos"] = np.cos(2 * np.pi * future_date.month / 12)
            row["dow_sin"] = np.sin(2 * np.pi * future_date.dayofweek / 7)
            row["dow_cos"] = np.cos(2 * np.pi * future_date.dayofweek / 7)

            # Update lag features from the running recent_demand history
            for lag in [1, 7, 14, 28]:
                row[f"lag_{lag}"] = recent_demand[-lag] if len(recent_demand) >= lag else 0

            for window in [7, 14, 28]:
                row[f"rolling_mean_{window}"] = np.mean(recent_demand[-window:])
            for window in [7, 28]:
                row[f"rolling_std_{window}"] = np.std(recent_demand[-window:]) if len(recent_demand) > 1 else 0

            X_future = pd.DataFrame([row[feature_cols]])
            pred = max(0, float(model.predict(X_future)[0]))

            forecast_rows.append({"t_dat": future_date, "predicted_demand": pred})
            recent_demand.append(pred)

        forecast_df = pd.DataFrame(forecast_rows)
        st.session_state["last_forecast"] = forecast_df

        st.dataframe(forecast_df, use_container_width=True)
        st.plotly_chart(
            visualization.plot_forecast(article_history.tail(60), forecast_df), use_container_width=True
        )


def page_ai_insights():
    st.title("🧠 AI Insights (Optional — Gemini)")

    if not gemini_helper.is_gemini_available():
        st.info(
            "AI Insights is optional and not currently configured. Add a `GEMINI_API_KEY` "
            "to `.streamlit/secrets.toml` to enable it. Every other page works without this."
        )

    question = st.text_input("Ask a question about your model/results (e.g. 'Why did demand increase?')")

    if st.button("Get AI Explanation"):
        metrics = st.session_state.results if "results" in st.session_state else None
        feature_importance = None
        if st.session_state.baseline_model is not None and st.session_state.feature_table is not None:
            feature_cols = feature_engineering.get_feature_columns(st.session_state.feature_table)
            feature_importance = xgboost_model.get_feature_importance(
                st.session_state.baseline_model, feature_cols, top_n=10
            )

        context = gemini_helper.build_context_summary(metrics=metrics, feature_importance=feature_importance)
        with st.spinner("Asking Gemini..."):
            answer = gemini_helper.get_ai_explanation(question or "Summarize the model results.", context)
        st.markdown(answer)

    if "last_forecast" in st.session_state and st.button("Summarize Latest Forecast"):
        feature_importance = None
        if st.session_state.baseline_model is not None and st.session_state.feature_table is not None:
            feature_cols = feature_engineering.get_feature_columns(st.session_state.feature_table)
            feature_importance = xgboost_model.get_feature_importance(
                st.session_state.baseline_model, feature_cols, top_n=10
            )
        with st.spinner("Summarizing..."):
            summary = gemini_helper.get_forecast_summary(st.session_state["last_forecast"], feature_importance)
        st.markdown(summary)


def page_about():
    st.title("ℹ️ About This Project")
    st.markdown(
        """
**Title:** Fashion Demand Forecasting Using Machine Learning and Domain Adaptation

**Goal:** Forecast fashion product demand using historical sales data,
while demonstrating how a model trained on one domain (e.g. a sales
channel) can be adapted to perform better on a different, related domain
with a shifted data distribution.

**Techniques used:**
- XGBoost regression for demand forecasting
- Chronological (time-aware) train/test splitting
- Lag & rolling-window features computed per-product, leakage-free
- Domain adaptation via logistic-regression-based instance weighting
- Safe MAPE calculation (zero-demand-aware)

See the project README for full setup, deployment, and methodology details.
        """
    )


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------

PAGE_FUNCTIONS = {
    "Home": page_home,
    "Data Upload": page_data_upload,
    "Data Exploration": page_data_exploration,
    "Demand Analysis": page_demand_analysis,
    "Feature Engineering": page_feature_engineering,
    "Model Training": page_model_training,
    "Domain Adaptation": page_domain_adaptation,
    "Model Evaluation": page_model_evaluation,
    "Demand Forecast": page_demand_forecast,
    "AI Insights": page_ai_insights,
    "About Project": page_about,
}


def main():
    selected_page = sidebar_navigation()
    PAGE_FUNCTIONS[selected_page]()


if __name__ == "__main__":
    main()
