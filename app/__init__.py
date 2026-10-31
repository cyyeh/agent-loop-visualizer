"""The app: what a person sees, on top of the agent.

page.py is the Streamlit page: the chat on the left, the loop on the right, the sidebar's settings, and the background
thread a turn runs in. render.py turns the harness's events into the HTML the page draws, as pure functions, so the
page can redraw any moment of a run, and docs/guide/guide.py, which builds 運作說明 (How it works), uses them too. assets/
holds the stylesheets, the logo and the example files.

Nothing here imports torch or transformers at import time but page.py, through the agent's model backends: render.py
builds with pygments alone, as docs/guide/guide.py does (.github/workflows/pages.yml).
"""
