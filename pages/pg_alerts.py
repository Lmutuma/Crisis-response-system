"""pages/pg_alerts.py — Alerts & Warnings"""
import streamlit as st
from model_bridge import TYPE_META


def show(alerts, zones, incidents):
    st.markdown("""
    <h1 style='margin-bottom:4px'>Alerts & Warnings</h1>
    <p style='color:#718096;margin-bottom:1.2rem;font-size:15px'>
      Model-generated alerts for responders, residents, and partner organizations
    </p>""", unsafe_allow_html=True)

    crit_n = sum(1 for a in alerts if a["level"]=="critical")
    warn_n = sum(1 for a in alerts if a["level"]=="warning")
    info_n = sum(1 for a in alerts if a["level"]=="info")

    c1,c2,c3 = st.columns(3)
    c1.metric("Critical", crit_n)
    c2.metric("Warnings", warn_n)
    c3.metric("Info",     info_n)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # Filter
    col_f, _ = st.columns([1,2])
    with col_f:
        level_f = st.multiselect("Filter level", ["critical","warning","info"],
                                 default=["critical","warning","info"])

    level_class = {"critical":"alert-critical","warning":"alert-warning","info":"alert-info"}

    st.markdown("#### Live prediction alerts")
    for a in [x for x in alerts if x["level"] in level_f]:
        cls = level_class.get(a["level"], "alert-info")
        st.markdown(f"""
        <div class="{cls}">
          <div class="alert-title">{a['icon']} {a['title']}</div>
          <p class="alert-msg">{a['message']}</p>
          <div class="alert-time">{a['time']}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # Public broadcast panel
    st.markdown("#### Broadcast warning to residents & organizations")
    st.markdown("""
    <div style='background:#fffbf0;border:1px solid #f0c040;border-radius:10px;
      padding:14px 18px;margin-bottom:14px;font-size:14px;color:#7a5800'>
      Send prediction-based warnings to residents and registered organizations
      in the affected zone.
    </div>""", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        warn_zone = st.selectbox("Target zone",
                                 [z["name"] for z in zones] + ["All zones"])
        warn_type = st.selectbox("Predicted incident type",
                                 ["MEDICAL","FIRE","TRAFFIC","All types"])
        warn_level = st.selectbox("Alert level",
                                  ["Critical — Immediate danger",
                                   "Warning — High predicted risk",
                                   "Advisory — Stay alert"])
    with col_b:
        warn_msg = st.text_area("Warning message",
                                placeholder="e.g. High probability of medical "
                                "emergencies predicted in this zone. "
                                "Ambulances pre-positioned.",
                                height=116)

    notify = st.multiselect(
        "Notify via",
        ["SMS to residents", "Email to organizations",
         "In-app notification", "Radio broadcast"],
        default=["SMS to residents", "In-app notification"],
    )

    if st.button("Send Warning Now", type="primary"):
        if warn_msg.strip():
            st.success(f"Warning sent to **{warn_zone}** via: {', '.join(notify)}")
            st.info(f"**Message:** {warn_msg}")
        else:
            st.warning("Please enter a warning message.")

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # High-risk zone quick buttons
    high_zones = sorted(zones, key=lambda z: z["risk_score"], reverse=True)[:5]
    st.markdown("#### Quick-send warnings for top predicted zones")
    for zone in high_zones:
        meta = TYPE_META[zone["dominant"]]
        col1, col2 = st.columns([4,1])
        with col1:
            st.markdown(f"""
            <div style='background:white;border:1px solid #e2e8f0;
              border-left:4px solid {meta["color"]};border-radius:0 10px 10px 0;
              padding:10px 14px;margin-bottom:6px'>
              <b style='font-size:13px'>{meta["icon"]} {zone["name"]}</b>
              <span style='color:#999;font-size:12px'>
                — dominant: {zone["dominant"]} · risk {zone["risk_score"]:.0%}
              </span>
            </div>""", unsafe_allow_html=True)
        with col2:
            if st.button("Send", key=f"qsend_{zone['name']}"):
                st.toast(f"⚠ Warning sent for {zone['name']}!", icon="🔔")
