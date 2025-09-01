#!/usr/bin/env python3
"""
Simple test for Enter key functionality
"""

import streamlit as st

st.title("Enter Key Test")

# Initialize session state
if 'enter_pressed' not in st.session_state:
    st.session_state.enter_pressed = False

# Text input
query = st.text_area("Enter your query:", key="test_query")

# Process button with smaller width
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🚀 Process", key="test_button"):
        st.success(f"Processed: {query}")

# Handle Enter key
if st.session_state.get('enter_pressed', False):
    st.success(f"Enter pressed! Query: {query}")
    st.session_state.enter_pressed = False

# Show current state
st.write("Session state:", st.session_state)
