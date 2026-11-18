# gh-pages

This branch holds only the website files, which GitHub Pages publishes.

- `index.html`: the interactive page for the Nasdaq-100 piecewise straight-line fit. Its data and scripts are all embedded in this one file, with no external dependencies.
  The page is bilingual (English and Chinese), with a switch at the top right. The language is set by the URL alone: no suffix or `#en` gives English, `#zh` gives Chinese.
- `.nojekyll`: makes GitHub Pages publish the static files as they are.

The data and fetch scripts are on the `main` branch.

To enable the site: in the repo go to Settings → Pages → Source, choose "Deploy from a branch", pick the `gh-pages` branch and the `/ (root)` folder, then save.
