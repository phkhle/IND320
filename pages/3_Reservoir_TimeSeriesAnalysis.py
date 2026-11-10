import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from area_selector import select_area

from NVE_API import get_nve_data
from analysis import (
    plot_filling_stl,
    plot_filling_spectrogram
)


# ============================================================
# 1. PAGE TITLE
# ============================================================

st.title("Reservoir Filling Analysis")

st.write(
    "Explore seasonal patterns and frequency characteristics "
    "of Norwegian reservoir filling levels."
)


# ============================================================
# 2. LOAD NVE DATA
# ============================================================

@st.cache_data(ttl=3600)
def load_data():
    return get_nve_data()


df = load_data()
df["dato_Id"] = pd.to_datetime(df["dato_Id"])


# ============================================================
# 3. SHARED AREA SELECTION
# ============================================================

selected_area, selected_number = select_area(df)

# ============================================================
# 4. FILTER WEEKLY DATA
# ============================================================

df_filtered = (
    df.loc[
        (df["omrType"] == selected_area) &
        (df["omrnr"] == selected_number),
        ["dato_Id", "fyllingsgrad"]
    ]
    .sort_values("dato_Id")
    .reset_index(drop=True)
)

st.caption(
    f"Observations: {len(df_filtered)} | "
    f"Period: {df_filtered['dato_Id'].min().date()} "
    f"to {df_filtered['dato_Id'].max().date()}"
)


# ============================================================
# 5. ANALYSIS TABS
# ============================================================

tab1, tab2 = st.tabs([
    "STL Decomposition",
    "Spectrogram"
])


# ============================================================
# 6. STL TAB
# ============================================================

with tab1:

    st.subheader("STL Decomposition")

    st.write(
        "Decompose reservoir filling degree into "
        "trend, seasonal and residual components."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        seasonal = st.slider(
            "Seasonal smoother",
            min_value=7,
            max_value=51,
            value=13,
            step=2
        )

    with col2:
        trend = st.slider(
            "Trend smoother",
            min_value=55,
            max_value=209,
            value=105,
            step=2
        )

    with col3:
        robust = st.checkbox(
            "Robust STL",
            value=True
        )

    if len(df_filtered) >= 104:

        fig, summary = plot_filling_stl(
            df=df_filtered,
            date_col="dato_Id",
            value_col="fyllingsgrad",
            period=52,
            seasonal=seasonal,
            trend=trend,
            robust=robust
        )

        st.pyplot(fig)
        plt.close(fig)

        with st.expander("STL Summary"):
            st.json(summary)

    else:
        st.warning(
            "At least two years of weekly data "
            "are recommended for STL analysis."
        )


# ============================================================
# 7. SPECTROGRAM TAB
# ============================================================

with tab2:

    st.subheader("Spectrogram")

    st.write(
        "Explore how periodic patterns in reservoir "
        "filling degree change over time."
    )

    window_length = st.slider(
        "Window length (weeks)",
        min_value=52,
        max_value=260,
        value=156,
        step=26
    )

    overlap = st.slider(
        "Overlap (weeks)",
        min_value=0,
        max_value=window_length - 1,
        value=min(130, window_length - 1)
    )

    if len(df_filtered) >= window_length:

        fig, summary = plot_filling_spectrogram(
            df=df_filtered,
            date_col="dato_Id",
            value_col="fyllingsgrad",
            window_length=window_length,
            overlap=overlap
        )

        st.pyplot(fig)
        plt.close(fig)

        with st.expander("Spectrogram Summary"):
            st.json(summary)

    else:
        st.warning(
            "Not enough observations for "
            "the selected window length."
        )
