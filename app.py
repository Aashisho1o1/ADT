"""Alumni Disaster Tracker: which alumni are near an active natural disaster?"""
import html

import folium
import streamlit as st
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

import core

st.set_page_config(page_title="Alumni Disaster Tracker", page_icon="🌍", layout="wide")


@st.cache_data(ttl=900)
def get_events():
    return core.fetch_events()


@st.cache_data
def get_alumni():
    return core.load_alumni()


def build_map(alumni, events, radius_km):
    m = folium.Map(location=[20, 0], zoom_start=2)
    cluster = MarkerCluster().add_to(m)
    for a in alumni.itertuples():
        folium.CircleMarker(
            [a.lat, a.lon], radius=6, color="#1f77b4", fill=True,
            popup=html.escape(f"{a.name}, {a.city}"),
        ).add_to(cluster)
    for e in events.itertuples():
        folium.Circle([e.lat, e.lon], radius=radius_km * 1000, color="#d62728", weight=1, fill=True, fill_opacity=0.08).add_to(m)
        folium.CircleMarker(
            [e.lat, e.lon], radius=7, color="#d62728", fill=True,
            popup=html.escape(f"{e.title} ({e.category}, {e.date})"),
        ).add_to(m)
    return m


events, is_live = get_events()
alumni = get_alumni()

with st.sidebar:
    st.header("Filters")
    categories = sorted(events["category"].unique())
    selected = st.multiselect("Event types", categories, default=categories)
    radius_km = st.slider("Alert radius (km)", 50, 1000, 300, step=50)

events = events[events["category"].isin(selected)]
nearby = core.find_nearby(alumni, events, radius_km)

st.title("🌍 Alumni Disaster Tracker")
st.caption("Open natural-disaster events from NASA EONET (last 30 days), matched against alumni locations.")
if not is_live:
    st.warning("NASA EONET is unreachable, so this is a saved snapshot.")

c1, c2, c3 = st.columns(3)
c1.metric("Active events", len(events))
c2.metric("Alumni", len(alumni))
c3.metric("Alumni near an event", nearby["name"].nunique())

map_col, list_col = st.columns([3, 2])
with map_col:
    st_folium(build_map(alumni, events, radius_km), height=550, use_container_width=True, returned_objects=[])
with list_col:
    st.subheader(f"Within {radius_km} km")
    if nearby.empty:
        st.success("No alumni near an active event.")
    else:
        st.dataframe(nearby, hide_index=True)
