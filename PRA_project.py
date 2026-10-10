"""
Page Replacement Algorithm Simulator — Streamlit UI
-----------------------------------------------------
Flow (per the app flowchart):
  Launch app -> user selects algorithm -> user inputs reference string &
  frame count -> backend executes chosen algorithm -> calculate faults/hits
  + generate step-by-step trace -> render results & tables -> user can
  adjust inputs to dynamically re-run (Streamlit reruns automatically on
  any widget change, so this happens for free).
"""

from collections import deque

import pandas as pd
import streamlit as st

# --------------------------------------------------------------------------
# Core algorithms (unchanged logic from the CLI version)
# --------------------------------------------------------------------------


def fifo(reference_string, frame_count):
    """Simulate FIFO page replacement. Returns (page_faults, trace)."""
    frames = []
    queue = deque()
    page_faults = 0
    trace = []

    for page in reference_string:
        if page in frames:
            trace.append((page, list(frames), False))
            continue

        page_faults += 1
        if len(frames) < frame_count:
            frames.append(page)
            queue.append(page)
        else:
            oldest = queue.popleft()
            frames[frames.index(oldest)] = page
            queue.append(page)

        trace.append((page, list(frames), True))

    return page_faults, trace


def lru(reference_string, frame_count):
    """Simulate Least Recently Used page replacement."""
    frames = []
    last_used = {}
    page_faults = 0
    trace = []

    for i, page in enumerate(reference_string):
        if page in frames:
            last_used[page] = i
            trace.append((page, list(frames), False))
            continue

        page_faults += 1
        if len(frames) < frame_count:
            frames.append(page)
        else:
            lru_page = min(frames, key=lambda p: last_used[p])
            frames[frames.index(lru_page)] = page

        last_used[page] = i
        trace.append((page, list(frames), True))

    return page_faults, trace


def optimal(reference_string, frame_count):
    """Simulate Optimal (Belady's) page replacement."""
    frames = []
    page_faults = 0
    trace = []
    n = len(reference_string)

    for i, page in enumerate(reference_string):
        if page in frames:
            trace.append((page, list(frames), False))
            continue

        page_faults += 1
        if len(frames) < frame_count:
            frames.append(page)
        else:
            farthest_index = -1
            victim = None
            for p in frames:
                try:
                    next_use = reference_string.index(p, i + 1)
                except ValueError:
                    next_use = n
                if next_use > farthest_index:
                    farthest_index = next_use
                    victim = p
            frames[frames.index(victim)] = page

        trace.append((page, list(frames), True))

    return page_faults, trace


ALGORITHMS = {
    "FIFO": fifo,
    "LRU": lru,
    "Optimal": optimal,
}

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def trace_to_dataframe(trace, frame_count):
    """Turn a trace into a horizontal DataFrame: rows = Ref/F1../Fault,
    columns = one per reference-string step."""
    ref_row = [str(page) for page, _, _ in trace]
    data = {"": ["Ref"] + [f"F{i + 1}" for i in range(frame_count)] + ["Fault"]}

    for step, (page, frames, fault) in enumerate(trace):
        col = [str(page)]
        col += [str(frames[s]) if s < len(frames) else "" for s in range(frame_count)]
        col += ["F" if fault else ""]
        data[str(step + 1)] = col

    df = pd.DataFrame(data).set_index("")
    return df


def highlight_faults(df):
    """Style the 'Fault' row so faults stand out in the rendered table."""

    def _style(row):
        if row.name == "Fault":
            return [
                "background-color: #ffd6d6; font-weight: bold;" if v == "F" else ""
                for v in row
            ]
        return ["" for _ in row]

    return df.style.apply(_style, axis=1)


def parse_reference_string(raw: str):
    try:
        return [int(x) for x in raw.split()]
    except ValueError:
        return None


# --------------------------------------------------------------------------
# Streamlit UI
# --------------------------------------------------------------------------

st.set_page_config(page_title="Page Replacement Simulator", layout="wide")

st.title("🗂️ Page Replacement Algorithm Simulator")
st.caption("FIFO · LRU · Optimal — enter a reference string and watch the frames fill up.")

# --- User selects algorithm -----------------------------------------------
st.subheader("1. Select Algorithm")
mode = st.radio(
    "Choose one algorithm, or compare all three:",
    options=["FIFO", "LRU", "Optimal", "Compare All"],
    horizontal=True,
)

# --- User inputs reference string & frame count ----------------------------
st.subheader("2. Provide Inputs")
col1, col2 = st.columns([3, 1])
with col1:
    raw_ref = st.text_input(
        "Reference string (space-separated page numbers)",
        value="7 0 1 2 0 3 0 4 2 3 0 3 2",
    )
with col2:
    frame_count = st.number_input("Number of frames", min_value=1, max_value=10, value=3, step=1)

reference_string = parse_reference_string(raw_ref)

if reference_string is None:
    st.error("Please enter only whole numbers separated by spaces (e.g. `7 0 1 2 0 3`).")
    st.stop()

if not reference_string:
    st.info("Enter a reference string above to run the simulation.")
    st.stop()

# --- Backend executes chosen algorithm(s) -----------------------------------
st.subheader("3. Results")

if mode == "Compare All":
    summary_rows = []
    for name, algo in ALGORITHMS.items():
        faults, trace = algo(reference_string, frame_count)
        hits = len(reference_string) - faults
        summary_rows.append({"Algorithm": name, "Page Faults": faults, "Page Hits": hits})

    summary_df = pd.DataFrame(summary_rows).set_index("Algorithm")

    st.markdown("**Comparison summary**")
    st.dataframe(summary_df, use_container_width=True)
    st.bar_chart(summary_df["Page Faults"])

    for name, algo in ALGORITHMS.items():
        faults, trace = algo(reference_string, frame_count)
        with st.expander(f"{name} — step-by-step trace ({faults} faults)", expanded=False):
            df = trace_to_dataframe(trace, frame_count)
            st.dataframe(highlight_faults(df), use_container_width=True)

else:
    algo = ALGORITHMS[mode]
    faults, trace = algo(reference_string, frame_count)
    hits = len(reference_string) - faults

    m1, m2, m3 = st.columns(3)
    m1.metric("Algorithm", mode)
    m2.metric("Page Faults", faults)
    m3.metric("Page Hits", hits)

    st.markdown("**Step-by-step trace**")
    df = trace_to_dataframe(trace, frame_count)
    st.dataframe(highlight_faults(df), use_container_width=True)

# --- User can adjust inputs to dynamically re-run ---------------------------
st.caption(
    "Change the algorithm, reference string, or frame count above — "
    "the simulation re-runs automatically."
)