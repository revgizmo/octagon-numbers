# streamlit_app.py
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import streamlit as st

st.set_page_config(page_title="Octavia Ring Numerals (Base 8)", page_icon="🛡️")

# ---------- Octal normalization ----------
def normalize_octal_str(s: str) -> str:
    s = "".join(ch for ch in s if ch.isdigit())
    if not s:
        return "0"
    digs = [int(c) for c in s]  # MSB->LSB (outer->inner)
    i = len(digs) - 1
    while i >= 0:
        if digs[i] >= 8:
            carry = digs[i] // 8
            digs[i] %= 8
            if i == 0:
                digs = [carry] + digs
                i += 1
            else:
                digs[i-1] += carry
        i -= 1
    j = 0
    while j < len(digs)-1 and digs[j] == 0:
        j += 1
    digs = digs[j:]
    return "".join(str(d) for d in digs)

# ---------- Canonical vs Compact counts ----------
def to_counts_canonical(octal_str: str):
    """Per-ring counts outer→inner (0..7). '0' -> [0] meaning 1s ring dot."""
    if octal_str == "0":
        return [0]
    return [int(c) for c in octal_str]

def to_counts_compact(octal_str: str):
    """
    Compact rule (simple & correct):
    While there exists an adjacent pair (outer >= 1, inner == 0), move exactly 1
    from the outer ring into the inner ring (+8). Scan outer→inner until stable.
    Then drop any leading zero ring created.
    Returns per-ring counts outer→inner where 0=dot, 1..7=segments, 8=full ring.
    """
    if octal_str == "0":
        return [0]
    d = [int(c) for c in octal_str]  # outer→inner

    changed = True
    while changed:
        changed = False
        # work from second-innermost outward (so we fill inner holes first)
        for i in range(len(d) - 2, -1, -1):
            if d[i] >= 1 and d[i+1] == 0:
                d[i] -= 1
                d[i+1] = 8
                changed = True
        # remove any newly-empty outer ring
        while len(d) > 1 and d[0] == 0:
            d.pop(0)
            changed = True

    # clamp to 0..8 for drawing (values are already 0 or 8 or 1..7)
    d = [min(max(0, x), 8) for x in d]
    return d

def ring_names_for_counts(counts):
    L = len(counts)
    vals = [8**p for p in range(L-1, -1, -1)]
    return [f"{v}s ring" for v in vals]

# ---------- Geometry / drawing ----------
def octagon_vertices(radius: float):
    ang = np.deg2rad(22.5 + 45*np.arange(8))  # flat top
    x = radius * np.cos(ang); y = radius * np.sin(ang)
    return np.c_[x, y]

def octagon_edges_from_top(vertices):
    v = vertices
    order = [(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,0),(0,1)]  # start at top, CCW
    return [(v[i], v[j]) for (i,j) in order]

def midpoint(p, q):
    return ((p[0]+q[0])/2.0, (p[1]+q[1])/2.0)

SEG_COLOR   = "#d24a3a"
GUIDE_COLOR = "#9bb3c7"

def draw_rings(counts, base_radius=1.3, dr=0.65,
               guide_lw=1.0, guide_alpha=0.18,
               seg_lw=5.0, dot_color="#333", dot_sz=40):
    fig = plt.figure(figsize=(6, 7.2))
    ax = fig.add_axes([0.08, 0.22, 0.84, 0.74])
    ax.set_aspect("equal"); ax.axis("off")

    if counts == [0]:
        # faint 1s ring + dot at its top edge
        r = base_radius
        verts = octagon_vertices(r)
        ax.plot(np.r_[verts[:,0], verts[0,0]], np.r_[verts[:,1], verts[0,1]],
                color=GUIDE_COLOR, linewidth=1.0, alpha=guide_alpha)
        top_edge = octagon_edges_from_top(verts)[0]
        cx, cy = midpoint(*top_edge)
        ax.scatter([cx], [cy], s=dot_sz, color=dot_color, zorder=5)
        return fig

    L = len(counts)
    for idx, c in enumerate(counts):
        power = L - 1 - idx
        r = base_radius + power * dr
        verts = octagon_vertices(r)
        edges = octagon_edges_from_top(verts)

        ax.plot(np.r_[verts[:,0], verts[0,0]], np.r_[verts[:,1], verts[0,1]],
                color=GUIDE_COLOR, linewidth=1.0, alpha=guide_alpha)

        if c == 0:
            p, q = edges[0]; cx, cy = midpoint(p, q)
            ax.scatter([cx], [cy], s=dot_sz, color=dot_color, zorder=5)
        else:
            for k in range(min(int(c), 8)):
                (p, q) = edges[k]
                ax.plot([p[0], q[0]], [p[1], q[1]],
                        color=SEG_COLOR, linewidth=seg_lw, solid_capstyle="round")
    return fig

def render_and_download(octal_str: str, dec_val: int, counts):
    fig = draw_rings(counts)
    caption = f"Octal Number {octal_str} = Integer Number {dec_val}"
    fig.text(0.5, 0.06, caption, ha="center", va="center", fontsize=12)
    st.pyplot(fig, use_container_width=False)

    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
    st.download_button("Download PNG", data=buf.getvalue(),
                       file_name=f"octavia_{octal_str}_{dec_val}.png", mime="image/png")

# ---------- UI ----------
st.title("Octavia Ring Numerals (Base 8)")
st.caption(
    "A **ring** is the faint octagon for a place value (…64s, 8s, 1s). "
    "0 = dot; 1–7 = that many contiguous segments (from the top, CCW); 8 = full ring.  "
    "**Compact**: move 1 from an outer ring into the next inner ring **only when that inner ring is 0** "
    "(adds +8 there). Repeat outer→inner until stable; drop any empty outer ring."
)

mode = st.radio("View", ["Compact (preferred)", "Canonical (literal base-8)"], index=0)
is_compact = mode.startswith("Compact")

tab1, tab2 = st.tabs(["Decimal → Rings", "Rings (with '8' allowed) → Decimal"])

with tab1:
    n = st.number_input("Decimal number", min_value=0, value=16, step=1)
    norm = format(int(n), "o")
    counts = to_counts_compact(norm) if is_compact else to_counts_canonical(norm)

    names = ring_names_for_counts(counts)
    st.markdown(f"**Octal (canonical):** `{norm}`")
    st.markdown("**Rings shown (outer → inner):**")
    for nm, c in zip(names, counts):
        txt = "dot" if c == 0 else ("full ring (8 segments)" if c == 8 else f"{c} segment(s)")
        st.write(f"- **{nm}** → {txt}")

    st.subheader("Drawing")
    render_and_download(norm, int(n), counts)

with tab2:
    raw = st.text_input("Enter octal digits (0–7; '8'/'9' allowed and will be normalized)", "20")
    try:
        norm = normalize_octal_str(raw)
        dec_val = int(norm, 8)
        counts = to_counts_compact(norm) if is_compact else to_counts_canonical(norm)

        names = ring_names_for_counts(counts)
        st.markdown(f"**Decimal:** `{dec_val}`  |  **Octal (canonical):** `{norm}`")
        st.markdown("**Rings shown (outer → inner):**")
        for nm, c in zip(names, counts):
            txt = "dot" if c == 0 else ("full ring (8 segments)" if c == 8 else f"{c} segment(s)")
            st.write(f"- **{nm}** → {txt}")

        st.subheader("Drawing")
        render_and_download(norm, dec_val, counts)
    except ValueError:
        st.error("Please enter only digits 0–9.")
