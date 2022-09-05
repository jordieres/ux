import streamlit as st
import sys
import os, subprocess
import streamlit as st
import numpy as np 
import pandas as pd 
import time
import ast
import tempfile
import json

def _tabs(tabs_data = {}, default_active_tab=0):
        tab_titles = list(tabs_data.keys())
        if not tab_titles:
            return None
        active_tab = st.radio("", tab_titles, index=default_active_tab)
        child = tab_titles.index(active_tab)+1
        st.markdown("""  
            <style type="text/css">
            div[role=radiogroup] > label > div:first-of-type {
               display: none
            }
            div[role=radiogroup] {
                flex-direction: unset
            }
            div[role=radiogroup] label {             
                border: 1px solid #999;
                background: #EEE;
                padding: 4px 12px;
                border-radius: 4px 4px 0 0;
                position: relative;
                top: 1px;
                }
            div[role=radiogroup] label:nth-child(""" + str(child) + """) {    
                background: #FFF !important;
                border-bottom: 1px solid transparent;
            }            
            </style>
        """,unsafe_allow_html=True)        
        return tabs_data[active_tab]

def _show_video():
    st.title("Russia – Ukraine conflict / crisis Explained")
    st.video("https://www.youtube.com/watch?v=h2P9AmGcMdM")

def _fake_df():
    N = 50
    rand = pd.DataFrame()
    rand['a'] = np.arange(N)
    rand['b'] = np.random.rand(N)
    rand['c'] = np.random.rand(N)    
    return rand

def do_tabs():
    st.markdown("Tab example found at [Multiple tabs in streamlit](https://discuss.streamlit.io/t/multiple-tabs-in-streamlit/1100/19?u=wgong27514)")
    tab_content = _tabs({
            "Tab html": "<h2> Hello Streamlit, <br/> what a cool tool! </h2>",
            "Tab video": _show_video, 
            "Tab df": _fake_df()
        })
    if callable(tab_content):
        tab_content()
    elif type(tab_content) == str:
        st.markdown(tab_content, unsafe_allow_html=True)
    else:
        st.write(tab_content)

do_tabs()


