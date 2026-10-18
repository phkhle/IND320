import streamlit as st
import pandas as pd
import plotly.express as px

from MongoDB_API import get_entsoe_monthly_data


st.title("Electricity Transfers – Norway")

st.info("Currently displaying synthetic test data, not real ENTSO-E observations.")


# 1. Fetch data fra MongoDB
@st.cache_data(ttl=3600)
def load_data():
    return get_entsoe_monthly_data()


df = load_data()

if df.empty:
    st.warning("No data available in MongoDB.")
    st.stop()


# 2. Choose connection

connection = st.selectbox(
    "Select connection",
    sorted(df["connection"].unique())
)

# Find available years for the selected connection
df["year"] = df["month"].str[:4].astype(int)

available_years = sorted(df["year"].unique(), reverse=True)

# Choose year
selected_year = st.radio(
    "Select year",
    options=available_years,
    horizontal=True
)

# Filter on connection and year
df_filtered = df[
    (df["connection"] == connection) &
    (df["year"] == selected_year)
].copy()


# 4. Calculate total import and export for the pie chart
total_import = df_filtered["total_import_mwh"].sum()
total_export = df_filtered["total_export_mwh"].sum()

pie_df = pd.DataFrame({
    "Direction": ["Import", "Export"],
    "MWh": [total_import, total_export]
})

# 5. Pie chart for import vs export
st.subheader(f"Import vs Export – {connection}")

fig = px.pie(
    pie_df,
    names="Direction",
    values="MWh",
    title=f"Electricity transfers: {connection}"
)

st.plotly_chart(fig, use_container_width=True)


# 6. Show datasource
with st.expander("Data source"):
    st.write("Source: MongoDB Atlas – IND320.entsoe_monthly_test")
    st.write("Data type: Synthetic test data")
    st.dataframe(df_filtered)

#------------------------------------------------
# 7. Monthly electricity transfers

st.subheader("Monthly Import and Export")

# Choose months to display
available_months = sorted(df_filtered["month"].unique())

selected_months = st.multiselect(
    "Select months",
    options=available_months,
    default=available_months
)

# Filter data for the selected months
monthly_filtered = df_filtered[
    df_filtered["month"].isin(selected_months)
].copy()

if not monthly_filtered.empty:

    monthly_filtered = monthly_filtered.sort_values("month")

    # Prepare the data for the line chart
    plot_df = monthly_filtered.melt(
        id_vars="month",
        value_vars=["total_import_mwh", "total_export_mwh"],
        var_name="Direction",
        value_name="MWh"
    )

    plot_df["Direction"] = plot_df["Direction"].replace({
        "total_import_mwh": "Import",
        "total_export_mwh": "Export"
    })

    # Line chart
    fig_line = px.line(
        plot_df,
        x="month",
        y="MWh",
        color="Direction",
        markers=True,
        title=f"Monthly Electricity Transfers – {connection}"
    )

    st.plotly_chart(fig_line, use_container_width=True)

else:
    st.info("Please select at least one month.")