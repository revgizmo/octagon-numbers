# streamlit_app.py
import streamlit as st

st.title("Octavia: Concentric-Octagon Number System (Base 8)")

tab1, tab2 = st.tabs(["Decimal → Octagon Rings", "Octagon Rings → Decimal"])

with tab1:
    n = st.number_input("Decimal number", min_value=0, value=65, step=1)
    oct_str = format(int(n), "o")  # octal string
    st.write(f"**Octal (base 8):** `{oct_str}`")
    st.write("**Draw these rings (outer → inner):**")
    powers = list(reversed(range(len(oct_str))))
    for p, dchar in zip(powers, oct_str):
        d = int(dchar)
        label = f"8^{p} = {8**p}"
        glyph = "•" if d == 0 else "│" * d  # dot for 0, d vertical ticks for 1–7
        st.write(f"- Ring {label}: {d} tick(s)  {glyph}")

with tab2:
    oct_in = st.text_input("Enter octal digits (0–7), e.g., 521", "101")
    try:
        dec_val = int(oct_in, 8)
        st.write(f"**Decimal:** {dec_val}")
        st.write("**Your rings should be (outer → inner):**")
        powers = list(reversed(range(len(oct_in))))
        for p, dchar in zip(powers, oct_in):
            d = int(dchar)
            label = f"8^{p} = {8**p}"
            glyph = "•" if d == 0 else "│" * d
            st.write(f"- Ring {label}: {d} tick(s)  {glyph}")
    except ValueError:
        st.error("Please enter only digits 0–7.")
