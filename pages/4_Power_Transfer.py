import streamlit as st
import pandas as pd
import plotly.express as px

from src.MongoDB_API import (
    get_entsoe_monthly_data,
    get_entsoe_daily_data,
)


# ============================================================
# 1. PAGE TITLE
# ============================================================

st.title("Electricity Transfers – Norway")

st.write(
    "Explore electricity imports and exports between Norway "
    "and neighboring countries using ENTSO-E data from 2024–2025."
)


# ============================================================
# 2. FETCH DATA FROM MONGODB
# ============================================================

@st.cache_data(ttl=3600)
def load_monthly_data():
    """Load monthly ENTSO-E data from MongoDB Atlas."""
    return get_entsoe_monthly_data()


@st.cache_data(ttl=3600)
def load_daily_data():
    """Load daily ENTSO-E data from MongoDB Atlas."""
    return get_entsoe_daily_data()


df_monthly = load_monthly_data()
df_daily = load_daily_data()

if df_monthly.empty or df_daily.empty:
    st.warning("Monthly or daily ENTSO-E data is missing in MongoDB.")
    st.stop()


# ============================================================
# 3. PREPARE DATA
# ============================================================

df_monthly["month"] = pd.to_datetime(
    df_monthly["month"], format="%Y-%m"
)

df_daily["date"] = pd.to_datetime(
    df_daily["date"], format="%Y-%m-%d"
)

df_monthly["year"] = df_monthly["month"].dt.year
df_daily["year"] = df_daily["date"].dt.year
df_daily["month_number"] = df_daily["date"].dt.month

for df in [df_monthly, df_daily]:

    df["total_import_mwh"] = pd.to_numeric(
        df["total_import_mwh"], errors="coerce"
    )

    df["total_export_mwh"] = pd.to_numeric(
        df["total_export_mwh"], errors="coerce"
    )


# ============================================================
# 4. FILTERS
# ============================================================

st.subheader("Filter Electricity Transfers")

filter_col1, filter_col2, filter_col3 = st.columns(
    [2, 1, 2],
    gap="medium"
)

with filter_col1:

    connection = st.selectbox(
        "Select connection",
        options=sorted(df_monthly["connection"].unique())
    )

connection_df = df_monthly[
    df_monthly["connection"] == connection
]

available_years = sorted(
    connection_df["year"].unique(),
    reverse=True
)

with filter_col2:

    selected_year = st.selectbox(
        "Select year",
        options=available_years
    )


daily_filtered = df_daily[
    (df_daily["connection"] == connection) &
    (df_daily["year"] == selected_year)
].copy()

month_names = {
    1: "Jan", 2: "Feb", 3: "Mar",
    4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep",
    10: "Oct", 11: "Nov", 12: "Dec"
}

available_months = sorted(
    daily_filtered["month_number"].unique()
)

month_options = [
    month_names[month] for month in available_months
]

with filter_col3:

    selected_month_labels = st.multiselect(
        "Select months (daily chart)",
        options=month_options,
        default=month_options[:1],
        placeholder="Select months"
    )

selected_month_numbers = [
    month for month, name in month_names.items()
    if name in selected_month_labels
]


# ============================================================
# 5. ANNUAL SUMMARY
# ============================================================

annual_df = connection_df[
    connection_df["year"] == selected_year
].copy()

total_import = annual_df["total_import_mwh"].sum()
total_export = annual_df["total_export_mwh"].sum()
net_import = total_import - total_export

st.divider()

st.subheader(f"Annual Summary – {connection} ({selected_year})")

metric_col1, metric_col2, metric_col3 = st.columns(3)

with metric_col1:

    st.metric(
        "Total Import (MWh)",
        f"{total_import:,.0f}"
    )

with metric_col2:

    st.metric(
        "Total Export (MWh)",
        f"{total_export:,.0f}"
    )

with metric_col3:

    st.metric(
        "Net Import (MWh)",
        f"{net_import:,.0f}"
    )

st.caption(
    "Annual totals are calculated for the selected connection "
    "and year, independently of the selected months."
)

st.divider()


# ============================================================
# 6. SHARED CHART SETTINGS
# ============================================================

direction_colors = {
    "Import": "#0068C9",
    "Export": "#83C9FF"
}

chart_height = 420

left_col, right_col = st.columns(
    [2, 3],
    gap="large"
)


# ============================================================
# 7. LEFT COLUMN - ANNUAL IMPORT AND EXPORT
# ============================================================

with left_col:

    st.subheader("Annual Import and Export")

    st.caption(f"{connection} | Full year {selected_year}")

    pie_df = pd.DataFrame({
        "Direction": ["Import", "Export"],
        "MWh": [total_import, total_export]
    })

    if pie_df["MWh"].sum() > 0:

        fig_pie = px.pie(
            pie_df,
            names="Direction",
            values="MWh",
            hole=0.3,
            color="Direction",
            color_discrete_map=direction_colors
        )

        fig_pie.update_traces(
            textposition="inside",
            textinfo="percent",
            hovertemplate=(
                "%{label}<br>"
                "%{value:,.0f} MWh<br>"
                "%{percent}"
                "<extra></extra>"
            )
        )

        fig_pie.update_layout(
            height=chart_height,

            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",

            margin=dict(
                l=15,
                r=15,
                t=20,
                b=60
            ),

            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.05,
                xanchor="center",
                x=0.5,
                title_text=""
            )
        )

        st.plotly_chart(
            fig_pie,
            use_container_width=True,
            theme="streamlit"
        )

    else:

        st.info(
            "No electricity transfers for this period."
        )


# ============================================================
# 8. RIGHT COLUMN - DAILY ELECTRICITY TRANSFERS
# ============================================================

with right_col:

    st.subheader("Daily Electricity Transfers")

    months_text = ", ".join(selected_month_labels)

    st.caption(
        f"{connection} | {months_text} {selected_year}"
    )

    plot_daily = daily_filtered[
        daily_filtered["month_number"].isin(
            selected_month_numbers
        )
    ].copy()

    if not plot_daily.empty:

        plot_daily = plot_daily.sort_values("date")

        plot_df = plot_daily.melt(
            id_vars=["date"],
            value_vars=[
                "total_import_mwh",
                "total_export_mwh"
            ],
            var_name="Direction",
            value_name="MWh"
        )

        plot_df["Direction"] = plot_df["Direction"].replace({
            "total_import_mwh": "Import",
            "total_export_mwh": "Export"
        })

        fig_line = px.line(
            plot_df,
            x="date",
            y="MWh",
            color="Direction",
            color_discrete_map=direction_colors,
            labels={
                "date": "Date",
                "MWh": "Electricity (MWh)"
            }
        )

        fig_line.update_traces(
            line=dict(width=2)
        )

        fig_line.update_layout(
            height=chart_height,

            hovermode="x unified",

            xaxis_title="Date",
            yaxis_title="Electricity (MWh)",

            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",

            margin=dict(
                l=20,
                r=15,
                t=20,
                b=60
            ),

            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.25,
                xanchor="center",
                x=0.5,
                title_text=""
            )
        )

        st.plotly_chart(
            fig_line,
            use_container_width=True,
            theme="streamlit"
        )

    else:

        st.info(
            "Select at least one month to display daily data."
        )


# ============================================================
# 9. DATA SOURCE AND OBSERVATIONS
# ============================================================

st.divider()

with st.expander("Data source and observations"):

    st.write("**Source:** ENTSO-E Transparency Platform")
    st.write("**Storage:** Apache Cassandra and MongoDB Atlas")
    st.write("**Processing:** Apache Spark")
    st.write("**Collections:** IND320.entsoe_monthly, IND320.entsoe_daily")
    st.write("**Period:** January 2024 – December 2025")
    st.write("**Unit:** MWh")

    st.write(
        "Electricity transfer observations are aggregated into "
        "monthly and daily totals. Daily dates are based on "
        "the Europe/Oslo time zone."
    )

    st.subheader("Monthly observations")

    st.dataframe(
        annual_df[
            [
                "connection",
                "month",
                "total_import_mwh",
                "total_export_mwh"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )