import math
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import streamlit as st

st.set_page_config(page_title="Octavia Number System", page_icon="🛡️")

# ---------- normalization ----------
def normalize_octal_str(s: str) -> str:
    """Accepts 0–9, normalizes to canonical base-8 (so '8' -> '10', etc.)."""
    s = "".join(ch for ch in s if ch.isdigit())
    if not s:
        return "0"
    digs = [int(c) for c in s]
    i = len(digs) - 1
    while i >= 0:
        if digs[i] >= 8:
            c = digs[i] // 8
            digs[i] %= 8
            if i == 0:
                digs = [c] + digs
                i += 1
            else:
                digs[i-1] += c
        i -= 1
    # strip leading zeros unless number is 0
    j = 0
    while j < len(digs)-1 and digs[j] == 0:
        j += 1
    digs = digs[j:]
    return "".join(str(d) for d in digs)

# ---------- geometry ----------
def octagon_vertices(radius: float):
    """
    Regular octagon with flat TOP EDGE.
    Vertices ordered CCW starting at 22.5°.
    """
    ang = np.deg2rad(22.5 + 45*np.arange(8))
    x = radius * np.cos(ang)
    y = radius * np.sin(ang)
    return np.c_[x, y]

def octagon_edges_from_top(vertices):
    """
    8 edges starting at the TOP EDGE (v1->v2), then CCW.
    """
    v = vertices
    order = [(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,0),(0,1)]
    return [(v[i], v[j]) for (i,j) in order]

def midpoint(p, q):
    return ((p[0]+q[0])/2, (p[1]+q[1])/2)

# ---------- drawing ----------
def draw_octavia_segments(octal_str: str,
                          base_radius=1.3, dr=0.65,
                          guide_color="#9bb3c7", guide_lw=1.0, guide_alpha=0.2,
                          seg_color="#d24a3a", seg_lw=5.0,
                          dot_color="#333", dot_sz=28):
    """
    For each ring:
      - d>0: draw first d edges CCW starting at the top edge
      - d=0: draw a dot at the midpoint of the top edge
    No text rendered on the figure.
    """
    norm = normalize_octal_str(octal_str)
    digits = [0] if norm == "0" else [int(c) for c in norm]
    k_max = len(digits) - 1

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_aspect("equal"); ax.axis("off")

    for idx, d in enumerate(digits):
        power = k_max - idx
        r = base_radius + power * dr

        # faint outline (closed)
        verts = octagon_vertices(r)
        ax.plot(np.r_[verts[:,0], verts[0,0]],
                np.r_[verts[:,1], verts[0,1]],
                color=guide_color, linewidth=guide_lw, alpha=guide_alpha)

        edges = octagon_edges_from_top(verts)

        if d == 0:
            p, q = edges[0]
            cx, cy = midpoint(p, q)
            ax.scatter([cx], [cy], s=dot_sz, color=dot_color, zorder=5)
        else:
            for k in range(d):
                (p, q) = edges[k]
                ax.plot([p[0], q[0]], [p[1], q[1]],
                        color=seg_color, linewidth=seg_lw, solid_capstyle="round")

    return fig, norm

def render_and_download(octal_str: str):
    fig, norm = draw_octavia_segments(octal_str)
    st.pyplot(fig, use_container_width=False)
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
    st.download_button("Download PNG", data=buf.getvalue(),
                       file_name=f"octavia_{norm}.png", mime="image/png")

# ---------- helpers for kid-friendly ring list ----------
def ring_names_for(oct_str: str):
    """Return outer→inner names like ['64s ring','8s ring','1s ring'] for the digits in oct_str."""
    L = len(oct_str)
    vals = [8**p for p in range(L-1, -1, -1)]  # outer→inner
    names = [f"{v}s ring" for v in vals]
    return names

# ---------- Streamlit UI ----------
st.title("Octavia Number System (Base 8)")
st.caption("Digits fill octagon edges counter-clockwise starting at the top edge. 0 = dot on the top edge. Each outer ring = next place (8s, 64s, 512s, …).")

tab1, tab2 = st.tabs(["Decimal → Octavia", "Octavia (with '8') → Decimal"])

with tab1:
    n = st.number_input("Decimal number", min_value=0, value=65, step=1)
    oct_str = format(int(n), "o")
    st.markdown(f"**Octal (canonical):** `{oct_str}`")

    # Kid-friendly ring list (outer → inner)
    names = ring_names_for(oct_str)
    st.markdown("**Rings (outer → inner):**")
    for name, ch in zip(names, oct_str):
        st.write(f"- **{name}** → digit `{int(ch)}`")

    st.subheader("Drawing")
    render_and_download(oct_str)

with tab2:
    raw = st.text_input("Enter octal digits (0–7; '8' allowed and will normalize)", "14")
    try:
        norm = normalize_octal_str(raw)
        dec_val = int(norm, 8)
        if raw != norm:
            st.info(f"Normalized input: `{raw}` → `{norm}`")
        st.markdown(f"**Decimal:** `{dec_val}`  |  **Octal (canonical):** `{norm}`")

        names = ring_names_for(norm)
        st.markdown("**Rings (outer → inner):**")
        for name, ch in zip(names, norm):
            st.write(f"- **{name}** → digit `{int(ch)}`")

        st.subheader("Drawing")
        render_and_download(norm)
    except ValueError:
        st.error("Please enter only digits 0–9.")
