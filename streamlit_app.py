import math
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import streamlit as st

st.set_page_config(page_title="Octavia Number System", page_icon="🛡️")

# ---------- normalization ----------
def normalize_octal_str(s: str) -> str:
    """Accept '8' or '9' and normalize to canonical base-8 string."""
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
    j = 0
    while j < len(digs)-1 and digs[j] == 0:
        j += 1
    digs = digs[j:]
    return "".join(str(d) for d in digs)

def ring_label(power: int) -> str:
    return f"Ring {power} = 8^{power} = {8**power}"

# ---------- geometry ----------
def octagon_vertices(radius: float):
    """
    Regular octagon with flat TOP EDGE.
    Vertices ordered CCW starting at angle 22.5°.
    """
    ang = np.deg2rad(22.5 + 45*np.arange(8))
    x = radius * np.cos(ang)
    y = radius * np.sin(ang)
    return np.c_[x, y]  # shape (8,2)

def octagon_edges_from_top(vertices):
    """
    Return 8 edges (pairs of points) starting at the TOP EDGE,
    then CCW around. Top edge = v1->v2.
    """
    v = vertices
    order = [(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,0),(0,1)]
    return [(v[i], v[j]) for (i,j) in order]

def midpoint(p, q):
    return ((p[0]+q[0])/2, (p[1]+q[1])/2)

# ---------- drawing ----------
def draw_octavia_segments(octal_str: str,
                          base_radius=1.3, dr=0.65,
                          guide_color="#9bb3c7", guide_lw=1.5,
                          seg_color="#d24a3a", seg_lw=5.0,
                          dot_color="#333", dot_sz=28):
    """
    For each ring:
      - d>0: draw first d edges CCW starting at the top edge
      - d=0: draw a dot at the midpoint of the top edge
    """
    norm = normalize_octal_str(octal_str)
    digits = [0] if norm == "0" else [int(c) for c in norm]
    k_max = len(digits) - 1

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(f"Octavia Numeral: {norm}₈", fontsize=14)

    for idx, d in enumerate(digits):
        power = k_max - idx
        r = base_radius + power * dr

        # outline
        verts = octagon_vertices(r)
        ax.plot(np.r_[verts[:,0], verts[0,0]],
                np.r_[verts[:,1], verts[0,1]],
                color=guide_color, linewidth=guide_lw)

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

        # label near right side, stagger a little by power
        label_r = r * 0.82
        label_theta = math.radians(340 - 6*power)
        lx, ly = label_r*math.cos(label_theta), label_r*math.sin(label_theta)
        ax.text(lx, ly, ring_label(power),
                fontsize=10, ha="left", va="center", color="#000")

    return fig, norm

def render_and_download(octal_str: str):
    fig, norm = draw_octavia_segments(octal_str)
    st.pyplot(fig)
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
    st.download_button("Download PNG", data=buf.getvalue(),
                       file_name=f"octavia_{norm}.png", mime="image/png")

# ---------- Streamlit UI ----------
st.title("Octavia Number System (Base 8)")
st.caption("Digits fill octagon edges CCW from the top. 0 = dot on the top edge. Each outer ring = next power of 8.")

tab1, tab2 = st.tabs(["Decimal → Octavia", "Octavia (with '8') → Decimal"])

with tab1:
    n = st.number_input("Decimal number", min_value=0, value=65, step=1)
    oct_str = format(int(n), "o")
    st.markdown(f"**Octal (canonical):** `{oct_str}`")
    powers = list(reversed(range(len(oct_str))))
    st.markdown("**Rings (outer → inner):**")
    for p, ch in zip(powers, oct_str):
        d = int(ch)
        st.write(f"- {ring_label(p)} → digit {d}")
    st.subheader("Drawing")
    render_and_download(oct_str)

with tab2:
    raw = st.text_input("Enter octal digits (0–7, '8' allowed, will normalize)", "101")
    try:
        norm = normalize_octal_str(raw)
        dec_val = int(norm, 8)
        if raw != norm:
            st.info(f"Normalized input: `{raw}` → `{norm}`")
        st.markdown(f"**Decimal:** `{dec_val}`  |  **Octal (canonical):** `{norm}`")
        powers = list(reversed(range(len(norm))))
        st.markdown("**Rings (outer → inner):**")
        for p, ch in zip(powers, norm):
            d = int(ch)
            st.write(f"- {ring_label(p)} → digit {d}")
        st.subheader("Drawing")
        render_and_download(norm)
    except ValueError:
        st.error("Please enter only digits 0–9.")
