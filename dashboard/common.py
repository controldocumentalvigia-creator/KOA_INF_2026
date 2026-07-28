import streamlit as st
import plotly.express as px

def chart(fig, key=None):
    st.plotly_chart(fig, use_container_width=True, key=key)

def table(df, formats=None):
    styled = df.style.format(formats or {})
    st.dataframe(styled, hide_index=True, use_container_width=True)
