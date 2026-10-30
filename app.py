import math
import requests
import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.set_page_config(
    page_title="Terra Atlas | Explore Earth",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

COUNTRIES_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    "master/geojson/ne_110m_admin_0_countries.geojson"
)
RIVERS_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    "master/geojson/ne_110m_rivers_lake_centerlines.geojson"
)
ELEVATION_URL = "https://api.open-meteo.com/v1/elevation"

st.markdown("""
<style>
    .block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
    .hero {padding: 1.15rem 1.35rem; border: 1px solid rgba(128,128,128,.25);
           border-radius: 14px; margin-bottom: 1rem;}
    .hero h1 {margin: 0 0 .25rem 0; letter-spacing: -.04em;}
    .muted {opacity: .72; font-size: .92rem;}
    div[data-testid="stMetric"] {border: 1px solid rgba(128,128,128,.22);
        padding: .75rem; border-radius: 12px;}
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=86400, show_spinner="Loading geographic datasets…")
def load_geojson(url: str):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def feature_name(feature):
    props = feature.get("properties", {})
    return (
        props.get("ADMIN") or props.get("NAME") or
        props.get("name") or props.get("NAME_EN") or "Unknown"
    )


def river_parts(geometry):
    if not geometry:
        return
    kind = geometry.get("type")
    coords = geometry.get("coordinates", [])
    if kind == "LineString":
        yield coords
    elif kind == "MultiLineString":
        yield from coords
    elif kind == "GeometryCollection":
        for item in geometry.get("geometries", []):
            yield from river_parts(item)


def build_map(countries, rivers, selected_name, show_rivers, show_labels,
              projection, map_theme):
    features = countries.get("features", [])
    locations, names, regions, populations, gdp = [], [], [], [], []
    selected_iso = None

    for feature in features:
        p = feature.get("properties", {})
        iso = p.get("ADM0_A3") or p.get("SOV_A3") or p.get("ISO_A3")
        if not iso or iso == "-99":
            continue
        name = feature_name(feature)
        locations.append(iso)
        names.append(name)
        regions.append(p.get("REGION_UN", ""))
        populations.append(p.get("POP_EST"))
        gdp.append(p.get("GDP_MD"))
        if name == selected_name:
            selected_iso = iso

    if map_theme == "Dark":
        land, ocean, border, river_color, text_color = "#17232d", "#08131e", "#718391", "#48b9d6", "#edf5f8"
    elif map_theme == "Satellite-inspired":
        land, ocean, border, river_color, text_color = "#34483d", "#101e2c", "#8b9b87", "#63c9ed", "#f4f5e9"
    else:
        land, ocean, border, river_color, text_color = "#e5e1d5", "#c7dce5", "#657782", "#2688b7", "#1b2930"

    fig = go.Figure()
    fig.add_trace(go.Choropleth(
        geojson=countries, locations=locations, z=[1] * len(locations),
        featureidkey="properties.ADM0_A3",
        customdata=list(zip(names, regions, populations, gdp)),
        colorscale=[[0, "#789b83"], [1, "#789b83"]],
        showscale=False, marker_line_color=border, marker_line_width=0.45,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>Region: %{customdata[1]}<br>"
            "Estimated population: %{customdata[2]:,.0f}<br>"
            "GDP (US$ millions): %{customdata[3]:,.0f}<extra></extra>"
        ), name="Countries",
    ))

    if selected_iso:
        fig.add_trace(go.Choropleth(
            geojson=countries, locations=[selected_iso], z=[1],
            featureidkey="properties.ADM0_A3",
            colorscale=[[0, "#f0b44d"], [1, "#f0b44d"]],
            showscale=False, marker_line_color="#fff2d4",
            marker_line_width=1.15, hoverinfo="skip",
            name="Selected country",
        ))

    if show_rivers:
        for feature in rivers.get("features", []):
            props = feature.get("properties", {})
            river_name = props.get("name") or props.get("NAME") or props.get("name_en") or "Unnamed river"
            lons, lats = [], []
            for part in river_parts(feature.get("geometry")):
                for point in part:
                    if len(point) >= 2:
                        lons.append(point[0])
                        lats.append(point[1])
                lons.append(None)
                lats.append(None)
            if lons:
                fig.add_trace(go.Scattergeo(
                    lon=lons, lat=lats, mode="lines",
                    line=dict(width=1.15, color=river_color),
                    text=[river_name] * len(lons),
                    hovertemplate="<b>%{text}</b><extra>River / drainage</extra>",
                    showlegend=False,
                ))

    if show_labels:
        label_lons, label_lats, label_names = [], [], []
        for feature in features:
            p = feature.get("properties", {})
            x, y = p.get("LABEL_X"), p.get("LABEL_Y")
            if x is not None and y is not None:
                label_lons.append(x)
                label_lats.append(y)
                label_names.append(feature_name(feature))
        fig.add_trace(go.Scattergeo(
            lon=label_lons, lat=label_lats, text=label_names,
            mode="text", textfont=dict(size=8, color=text_color),
            hoverinfo="skip", showlegend=False,
        ))

    fig.update_geos(
        projection_type=projection.lower(),
        showland=True, landcolor=land, showocean=True, oceancolor=ocean,
        showcountries=True, countrycolor=border,
        showcoastlines=True, coastlinecolor=border,
        showlakes=True, lakecolor=ocean, showrivers=False,
        showframe=False, bgcolor="rgba(0,0,0,0)",
        lataxis_showgrid=True, lataxis_gridcolor="rgba(130,150,160,.22)",
        lonaxis_showgrid=True, lonaxis_gridcolor="rgba(130,150,160,.22)",
    )
    fig.update_layout(
        height=660, margin=dict(l=0, r=0, t=5, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=text_color), dragmode="pan",
        uirevision="terra-atlas-map",
    )
    return fig


@st.cache_data(ttl=604800, show_spinner="Sampling terrain elevation…")
def get_elevation_grid(lat_min, lat_max, lon_min, lon_max, resolution):
    """Fetch a regular elevation grid in batches of at most 100 points."""
    latitudes = np.linspace(lat_min, lat_max, resolution)
    longitudes = np.linspace(lon_min, lon_max, resolution)
    lon_grid, lat_grid = np.meshgrid(longitudes, latitudes)
    flat_lats = lat_grid.ravel()
    flat_lons = lon_grid.ravel()
    elevations = []

    with requests.Session() as session:
        for start in range(0, len(flat_lats), 100):
            batch_lats = flat_lats[start:start + 100]
            batch_lons = flat_lons[start:start + 100]
            response = session.get(
                ELEVATION_URL,
                params={
                    "latitude": ",".join(f"{v:.5f}" for v in batch_lats),
                    "longitude": ",".join(f"{v:.5f}" for v in batch_lons),
                },
                timeout=45,
            )
            response.raise_for_status()
            payload = response.json()
            if "elevation" not in payload:
                raise ValueError(payload.get("reason", "Elevation service returned no elevation array."))
            elevations.extend(payload["elevation"])

    z = np.asarray(elevations, dtype=float).reshape(resolution, resolution)
    z[~np.isfinite(z)] = np.nan
    return longitudes, latitudes, z


PRESETS = {
    "Himalayas — Mount Everest": (27.9881, 86.9250, 1.8),
    "Drakensberg — Southern Africa": (-29.35, 29.35, 2.2),
    "Cape Fold Mountains — South Africa": (-33.65, 19.35, 1.0),
    "Andes — Aconcagua": (-32.6532, -70.0109, 2.0),
    "Alps — Mont Blanc": (45.8326, 6.8652, 1.1),
    "Grand Canyon — USA": (36.1069, -112.1129, 1.0),
    "East African Rift": (-2.5, 36.0, 3.0),
    "Custom coordinates": (-29.0, 25.0, 2.0),
}


def terrain_figure(lons, lats, elevations, exaggeration, palette):
    z_plot = elevations * exaggeration
    colors = {
        "Earth": "earth",
        "Viridis": "viridis",
        "Terrain": "terrain",
        "Hot": "hot",
    }
    fig = go.Figure(data=[go.Surface(
        x=lons, y=lats, z=z_plot,
        surfacecolor=elevations,
        colorscale=colors.get(palette, "earth"),
        colorbar=dict(title="Elevation<br>(m)", thickness=14),
        hovertemplate=(
            "Longitude: %{x:.3f}°<br>Latitude: %{y:.3f}°"
            "<br>Displayed height: %{z:,.0f} m"
            "<extra>Terrain grid</extra>"
        ),
        connectgaps=False,
    )])
    fig.update_layout(
        height=650,
        margin=dict(l=0, r=0, t=10, b=0),
        scene=dict(
            xaxis_title="Longitude (°)",
            yaxis_title="Latitude (°)",
            zaxis_title=f"Elevation × {exaggeration:.1f} (m)",
            aspectmode="manual",
            aspectratio=dict(x=1.25, y=1, z=0.55),
            camera=dict(eye=dict(x=1.55, y=1.55, z=1.15)),
        ),
    )
    return fig


st.markdown("""
<div class="hero">
  <h1>🌍 Terra Atlas</h1>
  <div class="muted">An interactive field guide to our planet — countries, rivers,
  topography and the systems that connect them.</div>
</div>
""", unsafe_allow_html=True)

tab_globe, tab_terrain = st.tabs(["🌐 World globe", "⛰️ Terrain explorer"])

with tab_globe:
    with st.sidebar:
        st.header("Globe controls")
        projection = st.selectbox(
            "Globe projection",
            ["Orthographic", "Natural Earth", "Equirectangular"],
            help="Drag to rotate; use the scroll wheel or map controls to zoom.",
        )
        map_theme = st.selectbox("Map appearance", ["Atlas", "Dark", "Satellite-inspired"])
        show_rivers = st.toggle("Show major rivers", value=True)
        show_labels = st.toggle("Show country labels", value=False)
        st.divider()
        st.subheader("Find a country")
        st.caption("Choose a country to highlight it and inspect available facts.")

    try:
        countries = load_geojson(COUNTRIES_URL)
        rivers = load_geojson(RIVERS_URL)
    except Exception as exc:
        st.error("The geographic datasets could not be loaded. Check your internet connection and refresh the app.")
        st.code(str(exc))
        st.stop()

    country_features = countries.get("features", [])
    country_names = sorted({feature_name(f) for f in country_features})
    default_index = country_names.index("South Africa") if "South Africa" in country_names else 0
    with st.sidebar:
        selected_name = st.selectbox("Country", country_names, index=default_index)

    selected_feature = next((f for f in country_features if feature_name(f) == selected_name), None)
    selected_props = selected_feature.get("properties", {}) if selected_feature else {}

    left, right = st.columns([3.25, 1], gap="large")
    with left:
        st.subheader("Explore the globe")
        st.caption("Drag to rotate • Scroll to zoom • Hover over countries and rivers for information")
        figure = build_map(
            countries, rivers, selected_name, show_rivers, show_labels,
            projection, map_theme
        )
        st.plotly_chart(
            figure, use_container_width=True,
            config={
                "scrollZoom": True, "displayModeBar": True,
                "modeBarButtonsToRemove": ["lasso2d", "select2d"],
                "displaylogo": False, "responsive": True,
            },
        )

    with right:
        st.subheader(selected_name)
        if selected_props:
            region = selected_props.get("REGION_UN") or "Not listed"
            subregion = selected_props.get("SUBREGION") or "Not listed"
            population = selected_props.get("POP_EST")
            area = selected_props.get("AREA")
            gdp = selected_props.get("GDP_MD")
            st.metric("World region", region)
            st.write(f"**Subregion:** {subregion}")
            if isinstance(population, (int, float)):
                st.metric("Estimated population", f"{population:,.0f}")
            if isinstance(area, (int, float)):
                st.metric("Land area", f"{area:,.0f} km²")
            if isinstance(gdp, (int, float)):
                st.metric("GDP estimate", f"${gdp:,.0f} million")
            st.caption("Country statistics are Natural Earth estimates and may be dated or generalized.")
        st.divider()
        st.markdown("**What am I looking at?**")
        st.write(
            "Country polygons show generalized national boundaries. Blue lines represent "
            "major mapped rivers and drainage centerlines. Small rivers and local waterways "
            "are not included at this global map scale."
        )

    st.divider()
    st.subheader("A planet to investigate")
    topic1, topic2, topic3 = st.columns(3)
    with topic1:
        st.markdown("#### 🌊 Hydrology")
        st.write("Trace river systems from source regions to deltas. Explore how water links mountains, farms, cities and oceans.")
    with topic2:
        st.markdown("#### 🏔️ Physical geography")
        st.write("Compare continents, coastlines, deserts, mountain systems and the major physical features of Earth.")
    with topic3:
        st.markdown("#### 🧭 Human geography")
        st.write("Use the map as a foundation for studying population, migration, borders, trade and urbanization.")

with tab_terrain:
    st.subheader("Explore Earth's surface in 3D")
    st.write(
        "Choose a mountain system or region to sample its terrain. Drag to orbit the surface, "
        "scroll to zoom, and hover over the grid to inspect coordinates and elevation."
    )
    preset_name = st.selectbox("Region", list(PRESETS.keys()))
    default_lat, default_lon, default_span = PRESETS[preset_name]
    custom = preset_name == "Custom coordinates"

    c1, c2, c3 = st.columns(3)
    with c1:
        center_lat = st.number_input(
            "Centre latitude", min_value=-85.0, max_value=85.0,
            value=float(default_lat), step=0.1, format="%.4f",
            disabled=not custom, key=f"lat_{preset_name}",
        )
    with c2:
        center_lon = st.number_input(
            "Centre longitude", min_value=-180.0, max_value=180.0,
            value=float(default_lon), step=0.1, format="%.4f",
            disabled=not custom, key=f"lon_{preset_name}",
        )
    with c3:
        span = st.slider(
            "Area width (approx. degrees)", 0.5, 5.0,
            float(default_span), 0.1,
            help="Larger areas show more terrain but less local detail.",
        )

    c4, c5, c6 = st.columns(3)
    with c4:
        resolution = st.select_slider("Terrain detail", options=[15, 21, 31, 41], value=31)
    with c5:
        exaggeration = st.slider("Vertical exaggeration", 1.0, 5.0, 2.0, 0.5)
    with c6:
        palette = st.selectbox("Elevation palette", ["Earth", "Viridis", "Terrain", "Hot"])

    if st.button("Generate 3D terrain", type="primary", use_container_width=True):
        lat_min = max(-89.0, center_lat - span / 2)
        lat_max = min(89.0, center_lat + span / 2)
        lon_min = max(-179.0, center_lon - span / 2)
        lon_max = min(179.0, center_lon + span / 2)
        try:
            lons, lats, elevation_grid = get_elevation_grid(
                round(lat_min, 4), round(lat_max, 4),
                round(lon_min, 4), round(lon_max, 4),
                int(resolution),
            )
            st.session_state["terrain_result"] = {
                "lons": lons, "lats": lats, "z": elevation_grid,
                "region": preset_name, "lat": center_lat, "lon": center_lon,
                "span": span,
            }
        except Exception as exc:
            st.error("Terrain data could not be retrieved. Please try again.")
            st.code(str(exc))

    terrain = st.session_state.get("terrain_result")
    if terrain:
        st.markdown(f"### {terrain['region']}")
        grid = terrain["z"]
        valid = grid[np.isfinite(grid)]
        if valid.size:
            m1, m2, m3 = st.columns(3)
            m1.metric("Highest sampled point", f"{np.nanmax(grid):,.0f} m")
            m2.metric("Lowest sampled point", f"{np.nanmin(grid):,.0f} m")
            m3.metric("Relief in sampled area", f"{np.nanmax(grid)-np.nanmin(grid):,.0f} m")
            fig = terrain_figure(
                terrain["lons"], terrain["lats"], grid,
                exaggeration, palette,
            )
            st.plotly_chart(
                fig, use_container_width=True,
                config={"scrollZoom": True, "displaylogo": False, "responsive": True},
            )
            st.caption(
                "The vertical exaggeration changes the displayed shape, not the measured elevation. "
                "The summary statistics use sampled points only; they are not guaranteed regional maxima or minima."
            )
        else:
            st.warning("No valid elevation samples were returned for this area.")
    else:
        st.info("Choose a region and select **Generate 3D terrain** to load its elevation surface.")

    with st.expander("How the terrain layer works"):
        st.markdown("""
        - Elevation is sampled from the **Copernicus DEM GLO-90**, a global digital elevation model.
        - The source dataset has a nominal 90-metre grid, but this app samples a much coarser display grid to keep the interactive 3D surface responsive.
        - Each terrain grid uses up to 41 × 41 sample locations. The API accepts up to 100 coordinate pairs per request, so the app automatically batches requests.
        - The 3D surface is a regional terrain view, not a full-resolution survey model. Fine ridges, cliffs and small valleys may be smoothed or missed.
        - Vertical exaggeration is a visual aid and must not be mistaken for true slope or height proportions.
        """)

st.divider()
st.caption(
    "Terra Atlas • Version 0.2 • Streamlit + Plotly + Natural Earth + Copernicus DEM via Open-Meteo. "
    "Elevation data attribution: Copernicus Programme and Open-Meteo."
)
