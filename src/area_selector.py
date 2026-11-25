import streamlit as st


# ============================================================
# 1. AREA MAPPING
# ============================================================

WATER_AREAS = {
    1: "Øst",
    2: "Vest",
    3: "Nord"
}


# ============================================================
# 2. INITIALIZE SHARED AREA SELECTION
# ============================================================

def initialize_area_selection():

    if "selected_area_type" not in st.session_state:
        st.session_state["selected_area_type"] = "EL"

    if "selected_area_number" not in st.session_state:
        st.session_state["selected_area_number"] = 3


# ============================================================
# 3. GET SHARED AREA
# ============================================================

def get_selected_area():

    initialize_area_selection()

    return (
        st.session_state["selected_area_type"],
        st.session_state["selected_area_number"]
    )


# ============================================================
# 4. UPDATE SHARED AREA
# ============================================================

def set_selected_area(area_type, area_number):

    st.session_state["selected_area_type"] = area_type
    st.session_state["selected_area_number"] = area_number


# ============================================================
# 5. FORMAT AREA NAME
# ============================================================

def format_area_name(area_type, area_number):

    if area_type == "EL":
        return f"NO{area_number}"

    elif area_type == "NO":
        return "Norway"

    elif area_type == "VASS":
        return WATER_AREAS.get(
            area_number,
            f"Area {area_number}"
        )

    return f"Area {area_number}"


# ============================================================
# 6. SHARED AREA SELECTOR
# ============================================================

def select_area(df):

    initialize_area_selection()

    selected_type, selected_number = get_selected_area()

    # Available area types
    area_types = [
        area_type
        for area_type in ["EL", "NO", "VASS"]
        if area_type in df["omrType"].unique()
    ]

    if selected_type not in area_types:
        st.info(
            "The selected area type is not available "
            "on this page."
        )
        st.stop()

    # Restore area type widget
    st.session_state["_area_type_widget"] = selected_type

    def update_area_type():

        new_type = st.session_state["_area_type_widget"]

        available_numbers = sorted(
            df.loc[
                df["omrType"] == new_type,
                "omrnr"
            ].dropna().unique().tolist()
        )

        current_number = st.session_state[
            "selected_area_number"
        ]

        if current_number not in available_numbers:
            current_number = available_numbers[0]

        set_selected_area(new_type, current_number)

    selected_area = st.radio(
        "Select area type:",
        options=area_types,
        horizontal=True,
        key="_area_type_widget",
        on_change=update_area_type
    )

    # Available area numbers
    area_numbers = sorted(
        df.loc[
            df["omrType"] == selected_area,
            "omrnr"
        ].dropna().unique().tolist()
    )

    if selected_number not in area_numbers:
        st.info(
            "The selected area is not available "
            "on this page."
        )
        st.stop()

    # Restore area number widget
    st.session_state["_area_number_widget"] = selected_number

    def update_area_number():

        set_selected_area(
            selected_area,
            st.session_state["_area_number_widget"]
        )

    selected_number = st.selectbox(
        "Select area number:",
        options=area_numbers,
        format_func=lambda x: format_area_name(
            selected_area, x
        ),
        key="_area_number_widget",
        on_change=update_area_number
    )

    return selected_area, selected_number