import os
import requests
import streamlit as st

API = os.getenv("API_URL", "http://127.0.0.1:8000")
st.title("University IT Ticket Assistant")
ticket = st.text_area("Ticket text")
version = st.selectbox("Prompt version", ["v2", "v1"])
fail = st.checkbox("Simulate backend failure")
if st.button("Analyze"):
    try:
        r = requests.post(f"{API}/analyze", timeout=30,
                          json={"ticket": ticket, "prompt_version": version, "simulate_failure": fail})
        if r.ok:
            d = r.json()
            st.success(f"Category: {d['category']}")
            st.write(f"Summary: {d['summary']}")
            st.caption(f"mode: {d['mode']} | prompt: {d['prompt_version']} | suggestion for human review")
        else:
            st.error(f"Error {r.status_code}: {r.json().get('detail')}")
    except requests.RequestException:
        st.error("Cannot reach the API server.")
