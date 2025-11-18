#!/bin/bash
set -e
cd ~/FreeMobileApp
source venv/bin/activate
streamlit run streamlit_app/app.py --server.port 8502 --server.address 0.0.0.0 --server.headless true
