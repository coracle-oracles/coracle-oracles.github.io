# Coracle website

## Update instructions

This is a simple static website so that it can be deployed on Github pages, but the pages are generated with a build script because I got tired of updating the same stuff (like menus) on multiple pages. To make a change, DON'T change the html files in the repo root. Instead:

1) Modify the files in the `tmpl` directory. `_template.html` contains the stuff shared between all pages.

2) While in the `tmpl` directory, run `./build.py`. This should work on any system with a modern-ish python3 installed.

## Previewing changes

After rebuilding, you can preview the changes by cding to the repo root and running `python3 -m http.server`. Then direct your browser to `localhost:8000`.
