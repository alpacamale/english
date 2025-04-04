import streamlit as st

title = "Shadow Home"

st.set_page_config(
    page_icon="🦜",
    page_title=title,
)
st.markdown(
    f"""
    # {title}

    Welcome, stranger!

    This app built for improove your english skill!

    You can learn english using audio or video source from your favorate youtuber, podcast, documentary, etc.

    To proceed, upload the media or input youtube url.
    """
)
