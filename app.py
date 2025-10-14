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
    central = statistics.median(readings) if use_median else sum(readings)/len(readings)
    for node, r in zip(nodes, readings):
        node.adjust(central - r)

def cristian_sync(clients, server):
    for client in clients:
        server_time = server.get_time()
        if server.is_byzantine:
            server_time += 30.0
        client.adjust(server_time - client.get_time())

# ===== STREAMLIT UI =====
st.set_page_config(page_title="Clock Sync Demo", layout="centered")
st.title("⏱️ Clock Synchronization in Distributed Systems")
st.markdown("""
A college project demonstrating **Berkeley** and **Cristian's** algorithms  
with support for **Byzantine faults** and **clock drift**.
""")

# Sidebar options
st.sidebar.header("Simulation Settings")
algorithm = st.sidebar.selectbox("Algorithm", ["Berkeley", "Cristian"])
fault_type = st.sidebar.selectbox("Fault Type", ["None", "Byzantine Node"])
use_robust = st.sidebar.checkbox("Use Robust Mode (Median for Berkeley)")

if st.sidebar.button("🔄 Reset"):
    st.cache_data.clear()  # Clears cached results
    st.rerun()

if st.sidebar.button("▶ Run Simulation"):
    # Create nodes with random drift
    nodes = []
    byzantine_id = 0 if fault_type == "Byzantine Node" else -1
    for i in range(NUM_NODES):
        drift = random.uniform(0.99, 1.01)  # ±1% drift
        is_byz = (i == byzantine_id)
        nodes.append(Node(i, drift, is_byz))

    # Measure before
    before_times = [n.get_time() for n in nodes]
    skew_before = max(before_times) - min(before_times)

    # Run algorithm
    if algorithm == "Berkeley":
        berkeley_sync(nodes, use_median=use_robust)
    else:  # Cristian
        server = nodes[0]
        clients = nodes[1:]
        cristian_sync(clients, server)

    # Measure after
    after_times = [n.get_time() for n in nodes]
    skew_after = max(after_times) - min(after_times)

    # Display results
    st.success(f"✅ **{algorithm} Algorithm** completed!")
    col1, col2 = st.columns(2)
    col1.metric("Skew Before Sync", f"{skew_before:.4f} sec")
    col2.metric("Skew After Sync", f"{skew_after:.4f} sec")

    # Plot
    fig, ax = plt.subplots(figsize=(10, 4))
    node_ids = [f"Node {n.node_id}" for n in nodes]
    ax.plot(node_ids, before_times, 'ro-', label='Before Sync')
    ax.plot(node_ids, after_times, 'go-', label='After Sync')
    ax.set_ylabel("Clock Time")
    ax.set_title("Clock Values Across Nodes")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    # Explanation
    if fault_type == "Byzantine Node":
        st.info("💡 **Byzantine Node**: Node 0 reports fake time (+30 sec).")
        if algorithm == "Berkeley" and use_robust:
            st.info("🛡️ **Robust Mode**: Median makes Berkeley resistant to lies!")
        elif algorithm == "Cristian":
            st.warning("⚠️ **Cristian fails** if the time server is Byzantine!")

# Footer
st.markdown("---")
st.caption("College Project • Clock Synchronization • Berkeley vs Cristian")
