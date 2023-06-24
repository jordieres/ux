#!/bin/bash
streamlit run server.py --server.port=5010 -- -m 138.100.82.180 138.100.82.175 -p apiict00.etsii.upm.es apiict01.etsii.upm.es apiict03.etsii.upm.es --log_mach 138.100.82.180 
