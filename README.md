# Aaron O'Connell - Data Analytics Portfolio

## Files
- `index.html` - responsive portfolio homepage with About, Projects & Dashboards, Experience, and Contact views.
- `dashboards/football.html` - starter project page for a public-data football dashboard.

## Preview locally
Open `index.html` in a web browser. Keep the `dashboards` folder beside it so project links work.

## Publish online
A straightforward option is GitHub Pages:
1. Create a GitHub repository for the portfolio.
2. Upload `index.html` and the complete `dashboards` folder.
3. In the repository settings, open **Pages** and choose the branch/folder to publish.
4. Open the generated site address to check navigation and project links.

You can also upload the files to any static website host. No server-side code is required.

## Before publishing
- Add your LinkedIn profile URL.
- Decide whether you want your email address publicly visible.
- Replace the football dashboard placeholder with your completed analysis and data-source details.
- Add each new dashboard as its own HTML file in `dashboards/`, then link it from the Projects page in `index.html`.
- Check all claims, links and responsive layouts on desktop and mobile.

The CV-based impact metrics are reproduced from the supplied CV. The dashboard pages are explicitly marked as templates until analysis is added.


## Bank Account Fraud Metric Explorer

Open `baf-metric-explorer.html` in a browser, select the BAF `Base.csv` file, and explore monthly fraud prevalence, feature-level comparisons, segment rates, and documented sentinel-value checks. The CSV is processed locally in the browser and is not uploaded. The page uses Plotly.js and Papa Parse from public CDNs, so an internet connection is required for those libraries.

## Python-powered BAF metric explorer

The dashboard no longer needs the raw dataset in the HTML. Run the analysis locally against the downloaded BAF CSV to produce a small aggregate JSON file:

```bash
pip install pandas numpy
python analyze_baf.py Base.csv
```

This creates `baf-summary.json` with overview metrics, monthly fraud rates, grouped feature summaries, segment rankings, sentinel-value checks and numeric correlations. It exports no application-level rows. Keep `baf-summary.json` beside `baf-metric-explorer.html`.

To preview locally, run `python -m http.server 8000` in the folder and open `http://localhost:8000/`. For GitHub Pages, commit the HTML and generated JSON (not the original CSV). Since the source dataset is synthetic, label it as such in the portfolio.
