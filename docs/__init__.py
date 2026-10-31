"""The project's documentation: the pages in this folder, each in English and, as .zh-TW.md, in Traditional Chinese,
and guide/, which builds 運作說明 (How it works), the static page on GitHub Pages.

It is a package so that the guide builds with `python -m docs.guide` and tests/test_guide.py can import it. Like
app/__init__.py, it imports nothing: the Pages workflow builds the guide with pygments alone.
"""
