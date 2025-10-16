import streamlit as st
import random
import matplotlib.pyplot as plt
import statistics

# ===== CONFIG =====
NUM_NODES = 5
BASE_TIME = 1000.0

class Node:
    def __init__(self, node_id, drift=1.0, is_byzantine=False):
        self.node_id = node_id
        self.drift = drift
        self.is_byzantine = is_byzantine
        self.offset = 0.0

    def get_time(self, base_time=BASE_TIME):
        t = base_time * self.drift + self.offset
        return t + 30.0 if self.is_byzantine else t

    def adjust(self, offset):
        self.offset += offset

# ===== ALGORITHMS =====
def berkeley_sync(nodes, use_median=False):
    readings = [n.get_time() for n in nodes]
    central = statistics.median(readings) if use_median else sum(readings) / len(readings)
    for node, r in zip(nodes, readings):
        node.adjust(central - r)

def cristian_sync(clients, server):
    for client in clients:
        server_time = server.get_time()
        if server.is_byzantine:
            server_time += 30.0
        client.adjust(server_time - client.get_time())

# ===== STREAMLIT APP =====
st.set_page_config(page_title="Clock Sync Demo", layout="centered")
st.title("⏱️ Clock Synchronization in Distributed Systems")
st.markdown("""
A college project demonstrating **Berkeley** and **Cristian's** algorithms  
with **manual clock input**, **fault simulation**, and real-time sync status.
""")

# Sidebar
st.sidebar.header("⚙️ Simulation Settings")
algorithm = st.sidebar.selectbox("Algorithm", ["Berkeley", "Cristian"])
fault_type = st.sidebar.selectbox("Fault Type", ["None", "Byzantine Node"])
use_robust = st.sidebar.checkbox("Use Robust Mode (Median for Berkeley)")

# Input method
input_method = st.sidebar.radio("Clock Initialization", ["Random Drift", "Manual Input"])

if input_method == "Manual Input":
    st.sidebar.markdown("### Set Initial Clocks (seconds)")
    manual_times = []
    for i in range(NUM_NODES):
        val = st.sidebar.number_input(f"Node {i}", value=1000.0, step=1.0, key=f"node_{i}")
        manual_times.append(val)
else:
    manual_times = None

# Run Simulation
if st.sidebar.button("▶ Run Simulation"):
    nodes = []
    byzantine_id = 0 if fault_type == "Byzantine Node" else -1

    for i in range(NUM_NODES):
        if manual_times is not None:
            # Manual mode: fixed initial time
            node = Node(i, drift=1.0, is_byzantine=(i == byzantine_id))
            node.offset = manual_times[i] - BASE_TIME
        else:
            # Random drift mode
            drift = random.uniform(0.99, 1.01)
            node = Node(i, drift=drift, is_byzantine=(i == byzantine_id))
        nodes.append(node)

    # Measure before sync
    before_times = [n.get_time() for n in nodes]
    skew_before = max(before_times) - min(before_times)

    # Run selected algorithm
    if algorithm == "Berkeley":
        active_nodes = nodes[1:] if fault_type == "Crash" else nodes
        berkeley_sync(active_nodes, use_median=use_robust)
    else:  # Cristian
        server = nodes[0]
        clients = nodes[1:]
        if fault_type == "Crash":
            clients = nodes[2:]  # skip crashed client
        cristian_sync(clients, server)

    # Measure after sync
    after_times = [n.get_time() for n in nodes]
    skew_after = max(after_times) - min(after_times)

    # ===== FEATURE: SYNCHRONIZATION STATUS =====
    st.subheader("⏱️ Clock Synchronization Status")
    SYNC_THRESHOLD = 0.1  # seconds
    if skew_after < SYNC_THRESHOLD:
        st.success(f"🟢 **SYNCHRONIZED** (Skew: {skew_after:.4f} sec < {SYNC_THRESHOLD}s)")
    else:
        st.error(f"🔴 **UNSYNCHRONIZED** (Skew: {skew_after:.4f} sec ≥ {SYNC_THRESHOLD}s)")

    # Metrics
    col1, col2 = st.columns(2)
    col1.metric("Skew Before Sync", f"{skew_before:.4f} sec")
    col2.metric("Skew After Sync", f"{skew_after:.4f} sec")

    # Plot
    fig, ax = plt.subplots(figsize=(10, 4))
    node_ids = [f"Node {n.node_id}" for n in nodes]
    ax.plot(node_ids, before_times, 'ro-', label='Before Sync')
    ax.plot(node_ids, after_times, 'go-', label='After Sync')
    ax.set_ylabel("Clock Time (seconds)")
    ax.set_title("Clock Values Across Nodes")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    # Explanations
    if fault_type == "Byzantine Node":
        st.info("💡 **Byzantine Node**: Node 0 reports fake time (+30 sec).")
        if algorithm == "Berkeley" and use_robust:
            st.info("🛡️ **Robust Mode**: Median makes Berkeley resistant to lies!")
        elif algorithm == "Cristian":
            st.warning("⚠️ **Cristian fails** if the time server is Byzantine!")

# Footer
st.markdown("---")
st.caption("College Project • Distributed Systems • Streamlit Demo")
