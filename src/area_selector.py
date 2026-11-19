
import streamlit as st


def select_area(df):
    """
    Shared area selector for NVE reservoir data.

    Stores the selected area type and area number
    in Streamlit session state.
    """

    # Initialize persistent selections
    if "selected_area_type" not in st.session_state:
        st.session_state["selected_area_type"] = "EL"

    if "selected_area_number" not in st.session_state:
        st.session_state["selected_area_number"] = 3

    # Restore area type widget
    st.session_state["_area_type_widget"] = (
        st.session_state["selected_area_type"]
    )

    def update_area_type():
        st.session_state["selected_area_type"] = (
            st.session_state["_area_type_widget"]
        )

    selected_area = st.radio(
        "Select area type:",
        options=["EL", "NO", "VASS"],
        horizontal=True,
        key="_area_type_widget",
        on_change=update_area_type
    )

    # Find available area numbers
    area_numbers = sorted(
        df.loc[
            df["omrType"] == selected_area,
            "omrnr"
        ].unique().tolist()
    )

    if not area_numbers:
        st.warning("No areas available.")
        st.stop()

    # Validate persistent area number
    if st.session_state["selected_area_number"] not in area_numbers:
        st.session_state["selected_area_number"] = area_numbers[0]

    # Restore area number widget
    st.session_state["_area_number_widget"] = (
        st.session_state["selected_area_number"]
    )

    def update_area_number():
        st.session_state["selected_area_number"] = (
            st.session_state["_area_number_widget"]
        )

    selected_number = st.selectbox(
        "Select area number:",
        options=area_numbers,
        format_func=lambda x: (
            f"NO{x}" if selected_area == "EL"
            else f"Area {x} – { {1: 'Øst', 2: 'Vest', 3: 'Nord'}[x] }" # according to NVEs
            if selected_area == "VASS" and x in (1, 2, 3)
            else f"Area {x}"
        ),
        key="_area_number_widget",
        on_change=update_area_number
    )

    return selected_area, selected_number
