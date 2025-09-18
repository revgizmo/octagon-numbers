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
    digs = [int(c) for c in s]
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

# ---------- Canonical / Compact ----------
def to_counts_canonical(octal_str: str):
    if octal_str == "0":
        return [0]
    return [int(c) for c in octal_str]

def compact_once(d):
    changed = False
    for i in range(len(d) - 2, -1, -1):
        if d[i] >= 1 and d[i+1] == 0:
            d[i] -= 1
            d[i+1] = 8
            changed = True
    while len(d) > 1 and d[0] == 0:
        d.pop(0)
        changed = True
    return changed

def to_counts_compact(octal_str: str):
    if octal_str == "0":
        return [0]
    d = [int(c) for c in octal_str]
    while compact_once(d):
        pass
    return d

# ---------- Drawing ----------
def octagon_vertices(radius: float):
    ang = np.deg2rad(22.5 + 45*np.arange(8))
    x = radius * np.cos(ang); y = radius * np.sin(ang)
    return np.c_[x, y]

def octagon_edges_from_top(vertices):
    v = vertices
    order = [(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,0),(0,1)]
    return [(v[i], v[j]) for (i,j) in order]

def midpoint(p, q):
    return ((p[0]+q[0])/2.0, (p[1]+q[1])/2.0)

SEG_COLOR   = "#d24a3a"
GUIDE_COLOR = "#9bb3c7"

def draw_rings(counts, base_radius=1.3, dr=0.65,
               guide_lw=1.0, guide_alpha=0.18,
               seg_lw=5.0, dot_color="#333", dot_sz=40,
               title_text=None):
    fig = plt.figure(figsize=(6, 7.6))
    if title_text:
        fig.suptitle(title_text, fontsize=13)
    ax = fig.add_axes([0.08, 0.22, 0.84, 0.70])
    ax.set_aspect("equal"); ax.axis("off")

    if counts == [0]:
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

def render_and_download(octal_str: str, dec_val: int, counts, *, key: str):
    title = f"Octal Number {octal_str} = [{', '.join(str(c) for c in counts)}] = Integer Number {dec_val}"
    fig = draw_rings(counts, title_text=title)
    st.pyplot(fig, width="content")

    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
    st.download_button(
        "Download PNG",
        data=buf.getvalue(),
        file_name=f"octavia_{octal_str}_{dec_val}.png",
        mime="image/png",
        key=key,
    )

# ---------- UI ----------
st.title("Octavia Ring Numerals (Base 8)")

mode = st.radio("View", ["Compact (preferred)", "Canonical (literal base-8)"], index=0)

tab1, tab2 = st.tabs(["Decimal → Rings", "Rings (with '8' allowed) → Decimal"])

with tab1:
    n = st.number_input("Decimal number", min_value=0, value=16, step=1)
    norm = format(int(n), "o")
    counts = to_counts_compact(norm) if mode.startswith("Compact") else to_counts_canonical(norm)

    st.subheader("Drawing")
    render_and_download(norm, int(n), counts, key=f"dl1-{mode}-{norm}-{n}")

with tab2:
    raw = st.text_input("Enter octal digits (0–7; '8'/'9' allowed and will be normalized)", "20")
    try:
        norm = normalize_octal_str(raw)
        dec_val = int(norm, 8)
        counts = to_counts_compact(norm) if mode.startswith("Compact") else to_counts_canonical(norm)

        st.subheader("Drawing")
        render_and_download(norm, dec_val, counts, key=f"dl2-{mode}-{norm}-{dec_val}")
    except ValueError:
        st.error("Please enter only digits 0–9.")
