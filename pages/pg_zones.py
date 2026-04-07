"""pages/pg_zones.py — Zone Analysis"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from model_bridge import TYPE_META

TYPE_COLORS = {"MEDICAL":"#3B8BD4","FIRE":"#E24B4A","TRAFFIC":"#EF9F27"}


def show(geo, zones):
    city = st.session_state.get("city_name", "the area")
    st.markdown(f"""
    <h1 style='margin-bottom:4px'>Zone Analysis</h1>
    <p style='color:#718096;margin-bottom:1.2rem;font-size:15px'>
      Predicted incident type per neighbourhood — <b>{city}</b>
    </p>""", unsafe_allow_html=True)

    med_n = sum(1 for z in zones if z["dominant"]=="MEDICAL")
    fir_n = sum(1 for z in zones if z["dominant"]=="FIRE")
    trf_n = sum(1 for z in zones if z["dominant"]=="TRAFFIC")

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Zones",       len(zones))
    c2.metric("Medical zones",  med_n)
    c3.metric("Fire zones",     fir_n)
    c4.metric("Traffic zones",  trf_n)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # Charts row
    ch1, ch2 = st.columns(2)

    with ch1:
        st.markdown("#### Dominant prediction by zone")
        fig = px.pie(
            values=[med_n, fir_n, trf_n],
            names=["MEDICAL","FIRE","TRAFFIC"],
            color=["MEDICAL","FIRE","TRAFFIC"],
            color_discrete_map=TYPE_COLORS,
            hole=0.5,
        )
        fig.update_traces(textposition="outside", textinfo="percent+label", textfont=dict(color="black"))
        fig.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=290,
                          showlegend=False, paper_bgcolor="white",
                          font_family="Space Grotesk", font=dict(color="black"))
        st.plotly_chart(fig, use_container_width=True)

    with ch2:
        st.markdown("#### Risk score distribution")
        fig2 = px.histogram(
            x=[z["risk_score"] for z in zones], nbins=20,
            color_discrete_sequence=["#534AB7"],
            labels={"x":"Risk Score","y":"Zones"},
        )
        fig2.update_layout(margin=dict(t=10,b=30,l=10,r=10), height=290,
                           paper_bgcolor="white", plot_bgcolor="#f4f7f9",
                           font_family="Space Grotesk", font=dict(color="black"), bargap=0.1)
        fig2.update_xaxes(tickfont=dict(color="black"))
        fig2.update_yaxes(tickfont=dict(color="black"))
        fig2.update_xaxes(range=[0,1])
        st.plotly_chart(fig2, use_container_width=True)

    # Stacked bar — incident type breakdown per zone (top 12)
    st.markdown("#### Incident type breakdown per zone (top 12 by risk score)")
    top12 = sorted(zones, key=lambda z: z["risk_score"], reverse=True)[:12]
    names = [z["name"][:20] for z in top12]
    med_v = [z["type_counts"].get("MEDICAL",0) for z in top12]
    fir_v = [z["type_counts"].get("FIRE",0)    for z in top12]
    trf_v = [z["type_counts"].get("TRAFFIC",0) for z in top12]

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(name="Medical", x=names, y=med_v,
                           marker_color="#3B8BD4", textfont=dict(color="white")))
    fig3.add_trace(go.Bar(name="Fire",    x=names, y=fir_v,
                           marker_color="#E24B4A", textfont=dict(color="white")))
    fig3.add_trace(go.Bar(name="Traffic", x=names, y=trf_v,
                           marker_color="#EF9F27", textfont=dict(color="white")))
    fig3.update_layout(
        barmode="stack",
        height=340,
        margin=dict(t=10,b=60,l=10,r=10),
        paper_bgcolor="white", plot_bgcolor="#f4f7f9",
        yaxis_title="Predicted % split",
        font_family="Space Grotesk",
        font=dict(color="black"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="black")),
    )
    fig3.update_xaxes(tickangle=45, tickfont=dict(color="black"))
    fig3.update_yaxes(tickfont=dict(color="black"))
    st.plotly_chart(fig3, use_container_width=True)

    # Zone table
    st.markdown("#### All zones")
    table_html = "<table style='width:100%; border-collapse:collapse; font-family:Space Grotesk; font-size:14px;'>"
    table_html += "<tr style='background:#f4f7f9;'><th style='padding:8px; text-align:left; border-bottom:1px solid #e2e8f0;'>Zone</th><th style='padding:8px; text-align:left; border-bottom:1px solid #e2e8f0;'>Dominant Type</th><th style='padding:8px; text-align:left; border-bottom:1px solid #e2e8f0;'>Medical %</th><th style='padding:8px; text-align:left; border-bottom:1px solid #e2e8f0;'>Fire %</th><th style='padding:8px; text-align:left; border-bottom:1px solid #e2e8f0;'>Traffic %</th><th style='padding:8px; text-align:left; border-bottom:1px solid #e2e8f0;'>Risk Score</th></tr>"
    for zone in zones:
        dominant = zone["dominant"]
        if dominant == "MEDICAL":
            badge = "<span class='badge-medical'>MEDICAL</span>"
        elif dominant == "FIRE":
            badge = "<span class='badge-fire'>FIRE</span>"
        elif dominant == "TRAFFIC":
            badge = "<span class='badge-traffic'>TRAFFIC</span>"
        else:
            badge = dominant
        med_pct = zone["type_counts"].get("MEDICAL", 0) * 100
        fire_pct = zone["type_counts"].get("FIRE", 0) * 100
        traffic_pct = zone["type_counts"].get("TRAFFIC", 0) * 100
        table_html += f"<tr><td style='padding:8px; border-bottom:1px solid #f0f0f0;'>{zone['name']}</td><td style='padding:8px; border-bottom:1px solid #f0f0f0;'>{badge}</td><td style='padding:8px; border-bottom:1px solid #f0f0f0;'>{med_pct:.1f}%</td><td style='padding:8px; border-bottom:1px solid #f0f0f0;'>{fire_pct:.1f}%</td><td style='padding:8px; border-bottom:1px solid #f0f0f0;'>{traffic_pct:.1f}%</td><td style='padding:8px; border-bottom:1px solid #f0f0f0;'>{zone['risk_score']:.3f}</td></tr>"
    table_html += "</table>"
    st.markdown(table_html, unsafe_allow_html=True)
