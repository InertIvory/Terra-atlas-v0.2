# Terra Atlas 🌍

An interactive 3D-style globe for exploring Earth's countries and major river systems. Built with Python, Streamlit and Plotly.

## Features in version 0.2

- Everything from version 0.1.
- Regional 3D terrain explorer with named presets (Himalayas, Drakensberg, Cape Fold Mountains, Andes, Alps, Grand Canyon and East African Rift).
- Custom terrain coordinates, adjustable area width, sample resolution, colour palette and vertical exaggeration.
- Elevation samples from the Copernicus DEM GLO-90 through the Open-Meteo Elevation API.

## Features in version 0.1

- Interactive globe using an orthographic projection.
- Rotate by dragging and zoom with the mouse wheel / map controls.
- Switch between Orthographic, Natural Earth and Equirectangular projections.
- Show or hide major rivers and country labels.
- Select a country to highlight it and inspect geographic and source-dataset statistics.
- Three map appearances.

## Run locally

Python 3.10+ is recommended.

```bash
# 1. Create and activate a virtual environment (optional but recommended)
python -m venv .venv

# Windows:
.venv\Scripts\activate

# macOS / Linux:
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the app
streamlit run app.py
```

Streamlit will print a local address, usually `http://localhost:8501`.

## Deploy with GitHub + Streamlit Community Cloud

1. Create a new GitHub repository, for example `terra-atlas`.
2. Upload `app.py`, `requirements.txt`, `README.md` and `.gitignore` to the repository root.
3. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with GitHub.
4. Choose **Create app**, select your repository and branch, and set the main file path to `app.py`.
5. Deploy.

The app downloads the Natural Earth GeoJSON datasets at runtime and caches them for 24 hours. The first load therefore requires an internet connection.

## Data sources

- Country boundaries: [Natural Earth — Admin 0 countries](https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-admin-0-countries/)
- Major rivers: [Natural Earth — Rivers and lake centerlines](https://www.naturalearthdata.com/downloads/110m-physical-vectors/)
- GeoJSON distribution: [nvkelso/natural-earth-vector](https://github.com/nvkelso/natural-earth-vector)

Natural Earth data is public domain. The 1:110m scale is suitable for global context, but omits many small islands, local waterways and fine boundary details. This is an educational atlas, not a legal or navigation map.

## Roadmap

### Version 0.3 — Better geographic detail
- Higher-resolution 1:50m and 1:10m country and river layers.
- Searchable rivers, lakes, mountain ranges, deserts and major cities.
- Country profiles with more reliable, dated indicators.

### Version 0.4 — Earth systems
- Climate zones, biomes, elevation and tectonic plates.
- Watersheds and river-basin exploration.
- Population density and migration datasets with dates, definitions and source notes.

### Version 0.5 — Time dimension (4D)
- Time slider for dated datasets.
- Historical borders and population change.
- Animated migration and environmental change, with clear separation between observed data and illustrative scenarios.

## Important distinction

The current globe is interactive 3D-style geographic visualization, not a physically accurate 3D terrain model. The planned time dimension will be added later using time-stamped datasets; it will not imply that all historical or migration data is equally complete.


## Elevation attribution

Terrain elevation is based on the Copernicus DEM GLO-90 (Copernicus Programme, ESA)
and retrieved using the Open-Meteo Elevation API. See
https://open-meteo.com/en/docs/elevation-api and
https://doi.org/10.5270/ESA-c5d3d65.
