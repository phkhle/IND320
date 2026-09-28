import streamlit as st

#####################################
# Home page for the IND320 project
#####################################

st.set_page_config(
    page_title="IND320 Reservoir Project",
    layout="wide"
)

st.title("IND320 Reservoir Project")

st.write(
    """
    Welcome to my IND320 project.

    This application explores reservoir data using Python, Pandas, and Streamlit.
    """
)

st.header("About the project")

st.write(
    """
    The project uses reservoir data from a CSV file.
    The data can be explored in table form and visualized interactively using the pages in the sidebar.
    """
)

st.header("Navigation")

st.write(
    """
    Use the sidebar on the left to navigate between:

    - Data — explore the reservoir data
    - Table — view the data in a table format
    - Plot — create interactive plots
    """
)