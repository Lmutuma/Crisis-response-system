"""pages/pg_orgs.py — Response Organizations"""
import streamlit as st
from model_bridge import TYPE_META

STATUS_BADGE = {
    "Available":  ("badge-available", "● Available"),
    "Active":     ("badge-active",    "● Active"),
    "On Standby": ("badge-standby",   "● On Standby"),
}


def show(orgs, alerts, incidents):
    st.markdown("""
    <h1 style='margin-bottom:4px'>Response Organizations</h1>
    <p style='color:#718096;margin-bottom:1.2rem;font-size:15px'>
      Resources matched to predicted incident types
    </p>""", unsafe_allow_html=True)

    avail_n = sum(1 for o in orgs if o["status"]=="Available")
    active_n = sum(1 for o in orgs if o["status"]=="Active")

    c1,c2,c3 = st.columns(3)
    c1.metric("Organizations", len(orgs))
    c2.metric("Available",   avail_n)
    c3.metric("Active",      active_n)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # Show orgs most relevant to current high-confidence predictions first
    dominant_types = set(i["type"] for i in incidents if i["severity"]=="high")
    if dominant_types:
        st.markdown(f"""
        <div style='background:#EBF4FB;border:1px solid #b5d4f4;border-radius:10px;
          padding:12px 18px;margin-bottom:14px;font-size:14px;color:#1a6fa8'>
          [PRED] Current high-severity predictions:
          {' · '.join(f"{TYPE_META[t]['icon']} {t}" for t in dominant_types)}.
          Matching organizations highlighted below.
        </div>""", unsafe_allow_html=True)

    # Filter
    col_f, _ = st.columns([1,2])
    with col_f:
        stat_f = st.multiselect("Status", ["Available","Active","On Standby"],
                                default=["Available","Active","On Standby"])

    filtered = [o for o in orgs if o["status"] in stat_f]

    st.markdown("#### Registered organizations")
    cols = st.columns(2)
    for idx, org in enumerate(filtered):
        badge_cls, badge_txt = STATUS_BADGE.get(org["status"],("badge-available","● Available"))
        resources_html = "".join(f"<li style='margin-bottom:2px'>{r}</li>"
                                  for r in org["resources"])
        # Highlight if responds to a currently active predicted type
        is_relevant = bool(dominant_types & set(org.get("responds_to",[])))
        border_extra = f"box-shadow:0 0 0 2px {org['color']}44;" if is_relevant else ""
        responds_html = " ".join(
            f"<span style='background:{TYPE_META[t]['color']}22;"
            f"color:{TYPE_META[t]['color']};padding:1px 7px;border-radius:10px;"
            f"font-size:11px;font-weight:600'>{TYPE_META[t]['icon']} {t}</span>"
            for t in org.get("responds_to",[])
        )
        with cols[idx % 2]:
            st.markdown(f"""
            <div class="org-card" style="border-left:4px solid {org['color']};{border_extra}">
              <div style="display:flex;align-items:center;
                          justify-content:space-between;margin-bottom:5px">
                <div>
                  <div class="org-name">{org['icon']} {org['name']}</div>
                  <div class="org-type">{org['type']}</div>
                </div>
                <span class="org-badge {badge_cls}">{badge_txt}</span>
              </div>
              <div style="margin-bottom:8px">{responds_html}</div>
              <div style="font-size:13px;color:#444;margin-bottom:8px">
                📞 <b>{org['contact']}</b> &nbsp; ✉ {org['email']}
              </div>
              <div style="font-size:11px;color:#718096;text-transform:uppercase;
                          letter-spacing:.05em;margin-bottom:4px">Resources</div>
              <ul style="font-size:13px;color:#444;padding-left:18px;margin:0">
                {resources_html}
              </ul>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # Resource request form
    st.markdown("#### 📋 Request resources")
    r1, r2 = st.columns(2)
    with r1:
        req_org  = st.selectbox("Organization", [o["name"] for o in orgs])
        req_type = st.selectbox("Resource needed",
                                ["Ambulance","Fire engine","Patrol vehicle",
                                 "Field medics","Emergency shelter",
                                 "Blood supply","Tow truck","Other"])
    with r2:
        req_loc     = st.text_input("Location / Zone",
                                    placeholder="e.g. Central-NW")
        req_urgency = st.selectbox("Urgency",
                                   ["Critical — Deploy immediately",
                                    "High — Within 15 mins",
                                    "Medium — Within 1 hour"])
    req_notes = st.text_area("Additional notes",
                              placeholder="Describe the situation…", height=80)

    if st.button("📤  Submit Request", type="primary"):
        if req_loc.strip():
            st.success(f"✅ Request sent to **{req_org}** for **{req_type}** "
                       f"at **{req_loc}** — {req_urgency.split('—')[0].strip()}")
        else:
            st.warning("Please enter a location.")

    # Critical alerts relevant to orgs
    crit = [a for a in alerts if a["level"]=="critical"]
    if crit:
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.markdown("#### 🔴 Active critical predictions requiring response")
        for a in crit:
            st.markdown(f"""
            <div class="alert-critical">
              <div class="alert-title">{a['icon']} {a['title']}</div>
              <p class="alert-msg">{a['message']}</p>
              <div class="alert-time">🕐 {a['time']}</div>
            </div>""", unsafe_allow_html=True)
