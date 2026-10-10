"""
Page Replacement Algorithm Simulator
-------------------------------------
Implements FIFO, LRU, and Optimal page replacement algorithms.
"""

from collections import deque
from tabulate import tabulate


def fifo(reference_string, frame_count):
    """Simulate FIFO page replacement. Returns (page_faults, trace)."""
    frames = []
    queue = deque()  # tracks insertion order for eviction
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
    last_used = {}  # page -> index of most recent use
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
            # Evict the frame whose page was used least recently
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
            # For each frame's page, find index of its next use after i.
            # A page with no future use gets "infinity" -> evicted first.
            farthest_index = -1
            victim = None
            for p in frames:
                try:
                    next_use = reference_string.index(p, i + 1)
                except ValueError:
                    next_use = n  # never used again -> best candidate to evict
                if next_use > farthest_index:
                    farthest_index = next_use
                    victim = p
            frames[frames.index(victim)] = page

        trace.append((page, list(frames), True))

    return page_faults, trace


def print_trace(trace, frame_count):
    """Pretty-print the step-by-step frame contents (vertical list)."""
    for page, frames, fault in trace:
        display = frames + ["-"] * (frame_count - len(frames))
        status = "PAGE FAULT" if fault else "no fault"
        print(f"  {page:>3} -> {' '.join(str(x) for x in display):<20} [{status}]")


def print_table(trace, frame_count):
    """Pretty-print the trace as a horizontal table using tabulate.

    Rows: reference string, one row per frame slot, and a fault marker row.
    Columns: one per step in the reference string.
    """
    ref_row = [page for page, _, _ in trace]
    frame_rows = []
    for slot in range(frame_count):
        row = [
            frames[slot] if slot < len(frames) else ""
            for _, frames, _ in trace
        ]
        frame_rows.append(row)
    fault_row = ["F" if fault else "" for _, _, fault in trace]

    headers = [""] + [str(p) for p in ref_row]
    rows = (
        [[f"F{i + 1}"] + row for i, row in enumerate(frame_rows)]
        + [["Fault"] + fault_row]
    )

    print(tabulate(rows, headers=headers, tablefmt="fancy_grid", stralign="center"))


def read_reference_string():
    raw = input("Enter reference string (space-separated numbers): ")
    return [int(x) for x in raw.split()]


def read_frame_count():
    return int(input("Enter number of page frames: "))


ALGORITHMS = {
    "1": ("FIFO", fifo),
    "2": ("LRU", lru),
    "3": ("Optimal", optimal),
}


def main():
    reference_string = None
    frame_count = None

    while True:
        print("\n=== Page Replacement Algorithm Simulator ===")
        print("1. FIFO")
        print("2. LRU")
        print("3. Optimal")
        print("4. Enter/Change reference string and frame size")
        print("5. Exit")
        choice = input("Select an option: ").strip()

        if choice == "4":
            reference_string = read_reference_string()
            frame_count = read_frame_count()

        elif choice in ALGORITHMS:
            if reference_string is None or frame_count is None:
                print("Please enter the reference string and frame size first (option 4).")
                continue
            name, algo = ALGORITHMS[choice]
            faults, trace = algo(reference_string, frame_count)
            print(f"\n--- {name} ---")
            print_table(trace, frame_count)
            print(f"\nTotal page faults: {faults}")
            print(f"Total page hits:   {len(reference_string) - faults}")

        elif choice == "5":
            print("Goodbye!")
            break

        else:
            print("Invalid option, try again.")


if __name__ == "__main__":
    main()
    