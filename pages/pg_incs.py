"""pages/pg_incs.py — Incident Predictions"""
import streamlit as st
import plotly.express as px
import pandas as pd
from model_bridge import TYPE_META

SEV_COLORS = {"high":"#E24B4A","medium":"#EF9F27","low":"#639922"}
TYPE_COLORS = {"MEDICAL":"#3B8BD4","FIRE":"#E24B4A","TRAFFIC":"#EF9F27"}


def confidence_bar(pct, color):
    return (f"<div class='conf-bar-wrap'>"
            f"<div class='conf-bar' style='width:{pct:.0%};background:{color}'></div>"
            f"</div>")


def show(incidents):
    st.markdown("""
    <h1 style='margin-bottom:4px'>Incident Predictions</h1>
    <p style='color:#718096;margin-bottom:1.2rem;font-size:15px'>
      XGBoost 3-class predictions — MEDICAL · FIRE · TRAFFIC
    </p>""", unsafe_allow_html=True)

    # Metrics
    med_n  = sum(1 for i in incidents if i["type"]=="MEDICAL")
    fir_n  = sum(1 for i in incidents if i["type"]=="FIRE")
    trf_n  = sum(1 for i in incidents if i["type"]=="TRAFFIC")
    high_n = sum(1 for i in incidents if i["severity"]=="high")
    avg_c  = sum(i["confidence"] for i in incidents)/len(incidents) if incidents else 0

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Total",         len(incidents))
    c2.metric("Medical",    med_n)
    c3.metric("Fire",       fir_n)
    c4.metric("Traffic",    trf_n)
    c5.metric("Avg Confidence",f"{avg_c:.0%}")

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # Filters
    f1, f2, f3 = st.columns(3)
    with f1:
        type_f = st.multiselect("Type", ["MEDICAL","FIRE","TRAFFIC"],
                                default=["MEDICAL","FIRE","TRAFFIC"])
    with f2:
        sev_f = st.multiselect("Severity", ["high","medium","low"],
                               default=["high","medium","low"])
    with f3:
        stat_f = st.multiselect("Status", ["Predicted","Active","Resolved"],
                                default=["Predicted","Active","Resolved"])

    filtered = [i for i in incidents
                if i["type"] in type_f
                and i["severity"] in sev_f
                and i["status"] in stat_f]

    st.markdown(f"<div style='font-size:13px;color:#718096;margin-bottom:12px'>"
                f"Showing {len(filtered)} of {len(incidents)} predictions</div>",
                unsafe_allow_html=True)

    # High-confidence critical cards
    critical = [i for i in filtered if i["severity"]=="high"]
    if critical:
        st.markdown("#### 🔴 High-severity predictions")
        cols = st.columns(min(len(critical), 3))
        for idx, inc in enumerate(critical):
            meta = TYPE_META[inc["type"]]
            with cols[idx % 3]:
                prob = inc["probability"]
                bar_html = ""
                for t, c in [("MEDICAL","#3B8BD4"),("FIRE","#E24B4A"),("TRAFFIC","#EF9F27")]:
                    bar_html += (f"<div style='font-size:11px;color:#718096;margin-top:4px'>"
                                 f"{TYPE_META[t]['icon']} {t} {prob[t]:.0%}</div>"
                                 f"{confidence_bar(prob[t], c)}")

                st.markdown(f"""
                <div class='pred-card' style='border-left:4px solid {meta["color"]}'>
                  <div style='font-weight:700;font-size:14px;margin-bottom:3px'>
                    {meta['icon']} {inc['id']} — {inc['type']}
                  </div>
                  <div style='font-size:12px;color:#444;margin-bottom:6px'>{inc['desc']}</div>
                  <div style='font-size:12px;color:#718096;margin-bottom:6px'>
                    📍 {inc['twp']} · 🕐 {inc['timestamp']}
                  </div>
                  <div style='font-size:11px;font-weight:600;color:{SEV_COLORS[inc["severity"]]}'>
                    {inc['severity'].upper()} · Confidence {inc['confidence']:.0%}
                  </div>
                  {bar_html}
                </div>""", unsafe_allow_html=True)

    # Full table
    st.markdown("#### All predictions")
    df = pd.DataFrame([{
        "ID":          i["id"],
        "Type":        f"{TYPE_META[i['type']]['icon']} {i['type']}",
        "Description": i["desc"],
        "Severity":    i["severity"].title(),
        "Confidence":  f"{i['confidence']:.0%}",
        "Township":    i["twp"],
        "Status":      i["status"],
        "Time":        i["timestamp"],
        "Lat":         i["lat"],
        "Lng":         i["lng"],
    } for i in filtered])
    st.dataframe(df, use_container_width=True, hide_index=True, height=360)

    # Charts
    ch1, ch2 = st.columns(2)
    with ch1:
        st.markdown("#### Predictions by type")
        tc = pd.Series([i["type"] for i in filtered]).value_counts()
        fig = px.bar(x=tc.index, y=tc.values,
                     color=tc.index,
                     color_discrete_map=TYPE_COLORS,
                     labels={"x":"","y":"Count"})
        fig.update_layout(showlegend=False, height=260,
                          margin=dict(t=10,b=10,l=10,r=10),
                          paper_bgcolor="white", plot_bgcolor="#f4f7f9",
                          font_family="Space Grotesk")
        st.plotly_chart(fig, use_container_width=True)

    with ch2:
        st.markdown("#### Confidence distribution")
        fig2 = px.histogram(
            x=[i["confidence"] for i in filtered], nbins=15,
            color_discrete_sequence=["#534AB7"],
            labels={"x":"Model Confidence","y":"Count"},
        )
        fig2.update_layout(height=260,
                           margin=dict(t=10,b=10,l=10,r=10),
                           paper_bgcolor="white", plot_bgcolor="#f4f7f9",
                           font_family="Space Grotesk", bargap=0.08)
        fig2.update_xaxes(range=[0,1], tickformat=".0%")
        st.plotly_chart(fig2, use_container_width=True)
