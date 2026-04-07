"""pages/pg_map.py — Prediction Map"""
import folium
from folium.plugins import HeatMap
import streamlit as st
from streamlit_folium import st_folium
from model_bridge import TYPE_META

ZONE_COLORS = {
    "MEDICAL": {"color":"#3B8BD4","fillColor":"#3B8BD4","fillOpacity":0.18,"weight":2,"dashArray":""},
    "FIRE":    {"color":"#E24B4A","fillColor":"#E24B4A","fillOpacity":0.20,"weight":2,"dashArray":""},
    "TRAFFIC": {"color":"#EF9F27","fillColor":"#EF9F27","fillOpacity":0.18,"weight":2,"dashArray":"6 4"},
}
SEV_COLORS = {"high":"#E24B4A","medium":"#EF9F27","low":"#639922"}


def show(geo, zones, incidents, heatmap):
    st.markdown("""
    <h1 style='margin-bottom:4px'>🗺 Crisis Prediction Map</h1>
    <p style='color:#718096;margin-bottom:1.2rem;font-size:15px'>
      XGBoost predictions overlaid on real neighbourhood boundaries
    </p>""", unsafe_allow_html=True)

    # Metric bar
    med_n  = sum(1 for i in incidents if i["type"]=="MEDICAL")
    fir_n  = sum(1 for i in incidents if i["type"]=="FIRE")
    trf_n  = sum(1 for i in incidents if i["type"]=="TRAFFIC")
    high_n = sum(1 for i in incidents if i["severity"]=="high")
    avg_conf = sum(i["confidence"] for i in incidents)/len(incidents) if incidents else 0

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Total Predictions", len(incidents))
    c2.metric("Medical",        med_n)
    c3.metric("Fire",           fir_n)
    c4.metric("Traffic",        trf_n)
    c5.metric("Avg Confidence",    f"{avg_conf:.0%}")

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    col_map, col_ctrl = st.columns([3, 1])

    with col_ctrl:
        st.markdown("**Map layers**")
        show_heat  = st.checkbox("Risk heatmap",    value=True)
        show_zones = st.checkbox("Zone predictions", value=True)
        show_incs  = st.checkbox("Incident pins",    value=True)
        st.markdown("**Filter type**")
        show_med   = st.checkbox("Medical",       value=True)
        show_fir   = st.checkbox("Fire",          value=True)
        show_trf   = st.checkbox("Traffic",       value=True)
        st.markdown("**Filter severity**")
        show_high  = st.checkbox("🔴 High",          value=True)
        show_med2  = st.checkbox("🟡 Medium",        value=True)
        show_low   = st.checkbox("🟢 Low",           value=True)

    with col_map:
        south, north, west, east = geo["bbox"]
        m = folium.Map(tiles="CartoDB positron", control_scale=True)
        m.fit_bounds([[south, west], [north, east]])

        # Area boundary
        folium.Rectangle(
            bounds=[[south,west],[north,east]],
            color="#534AB7", weight=2, fill=False, dash_array="8 5",
            tooltip=geo["display_name"],
        ).add_to(m)

        # Heatmap
        if show_heat:
            HeatMap(
                heatmap, min_opacity=0.3, max_val=1.0, radius=22, blur=18,
                gradient={0.2:"#3B8BD4", 0.5:"#EF9F27",
                           0.8:"#E24B4A", 1.0:"#7B0000"},
            ).add_to(m)

        # Zone polygons coloured by dominant prediction
        if show_zones:
            type_filter = []
            if show_med: type_filter.append("MEDICAL")
            if show_fir: type_filter.append("FIRE")
            if show_trf: type_filter.append("TRAFFIC")

            for zone in zones:
                if zone["dominant"] not in type_filter:
                    continue
                s    = ZONE_COLORS[zone["dominant"]]
                meta = TYPE_META[zone["dominant"]]
                dist = zone["type_counts"]
                popup_html = f"""
                <div style='font-family:sans-serif;min-width:200px'>
                  <b style='font-size:14px'>{zone['name']}</b><br>
                  <span style='background:{meta["color"]};color:#fff;
                    padding:2px 9px;border-radius:10px;font-size:12px'>
                    {meta["icon"]} {zone['dominant']}
                  </span>
                  <div style='margin-top:8px;font-size:12px;color:#555'>
                    Medical: {dist.get('MEDICAL',0):.0f}% &nbsp;
                    Fire: {dist.get('FIRE',0):.0f}% &nbsp;
                    Traffic: {dist.get('TRAFFIC',0):.0f}%
                  </div>
                  <small style='color:#aaa'>Risk score: {zone['risk_score']:.0%}</small>
                </div>"""
                folium.Polygon(
                    locations=zone["coords"],
                    color=s["color"], fill_color=s["fillColor"],
                    fill_opacity=s["fillOpacity"], weight=s["weight"],
                    dash_array=s["dashArray"],
                    tooltip=f"{zone['name']} → {zone['dominant']}",
                    popup=folium.Popup(popup_html, max_width=240),
                ).add_to(m)

        # Incident markers
        if show_incs:
            sev_filter = []
            if show_high: sev_filter.append("high")
            if show_med2: sev_filter.append("medium")
            if show_low:  sev_filter.append("low")
            type_filter2 = []
            if show_med: type_filter2.append("MEDICAL")
            if show_fir: type_filter2.append("FIRE")
            if show_trf: type_filter2.append("TRAFFIC")

            for inc in incidents:
                if inc["type"] not in type_filter2: continue
                if inc["severity"] not in sev_filter: continue
                meta = TYPE_META[inc["type"]]
                sc   = SEV_COLORS[inc["severity"]]
                prob = inc["probability"]
                popup_html = f"""
                <div style='font-family:sans-serif;min-width:210px'>
                  <b>{inc['type']} — {inc['id']}</b><br>
                  <span style='font-size:12px;color:#555'>{inc['desc']}</span><br>
                  <div style='margin:6px 0'>
                    <span style='background:{sc};color:#fff;padding:2px 8px;
                      border-radius:10px;font-size:11px'>{inc['severity'].upper()}</span>
                    <span style='font-size:11px;color:#888;margin-left:6px'>
                      Confidence: {inc['confidence']:.0%}
                    </span>
                  </div>
                  <div style='font-size:12px;color:#555'>
                    <b>Probabilities:</b><br>
                    Medical {prob['MEDICAL']:.0%} &nbsp;
                    Fire {prob['FIRE']:.0%} &nbsp;
                    Traffic {prob['TRAFFIC']:.0%}
                  </div>
                  <small style='color:#aaa'>{inc['twp']} · {inc['timestamp']}</small>
                </div>"""
                folium.Marker(
                    location=[inc["lat"], inc["lng"]],
                    icon=folium.Icon(icon=meta["fa_icon"],
                                     prefix="fa", color=meta["fa_color"]),
                    tooltip=f"{meta['icon']} {inc['type']} ({inc['confidence']:.0%})",
                    popup=folium.Popup(popup_html, max_width=260),
                ).add_to(m)

        st_folium(m, width=None, height=560, returned_objects=[])
