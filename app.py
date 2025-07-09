pip install matplotlib
# Streamlit Dashboard: Bakery Supply Chain Inventory Simulator with Service Levels and Lead Times
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- Parameters ---
n_periods = 365
unit_cost = {
    'store': 20,
    'hub': 18,
    'bakery': 15
}

store_demand_mean = 100
store_demand_std = store_demand_mean * 0.2

# --- Streamlit UI ---
st.title("🍞 Bakery Supply Chain Inventory Simulator")
st.markdown("This dashboard simulates inventory cost and service level for different replenishment frequencies at store and hub levels.")

store_days = st.slider("Replenishment Frequency: Store (days)", 1, 7, 1)
hub_days = st.slider("Replenishment Frequency: Hub (days)", 3, 14, 7)

# Cost sliders
st.subheader("💲 Holding Cost per Unit")
h_store = st.slider("Store Holding Cost ($)", 1, 100, 20)
h_hub = st.slider("Hub Holding Cost ($)", 1, 100, 18)
h_bakery = st.slider("Bakery Holding Cost ($)", 1, 100, 15)

# Lead time sliders (min threshold 1 day for all)
st.subheader("🚛 Lead Time (Days)")
lt_store = st.slider("Lead Time to Store", 1, 5, 1)
lt_hub = st.slider("Lead Time to Hub", 1, 7, 2)
lt_bakery = st.slider("Lead Time to Bakery", 1, 10, 3)

# --- Simulation Function ---
def simulate_inventory_cost(store_days, hub_days, lead_var=0.2):
    store_inv = []
    hub_inv = []
    bakery_inv = []

    store_inventory = 0
    hub_inventory = 0
    bakery_inventory = 0

    total_demand = 0
    fulfilled_demand = 0
    stockout_days = 0
    leadtime_variation = lambda base: max(1, int(np.round(np.random.normal(base, base * lead_var))))

    for day in range(n_periods):
        demand = max(0, np.random.normal(store_demand_mean, store_demand_std))
        total_demand += demand

        fulfilled = min(store_inventory, demand)
        fulfilled_demand += fulfilled

        if store_inventory < demand:
            stockout_days += 1

        store_inventory -= fulfilled

        if day % store_days == 0:
            store_lead = leadtime_variation(lt_store)
            qty = store_demand_mean * store_lead
            if hub_inventory >= qty:
                store_inventory += qty
                hub_inventory -= qty

        if day % hub_days == 0:
            hub_lead = leadtime_variation(lt_hub)
            qty = store_demand_mean * hub_lead
            bakery_inventory -= qty
            hub_inventory += qty

        if day % hub_days == 0:
            bakery_lead = leadtime_variation(lt_bakery)
            bakery_inventory += store_demand_mean * bakery_lead

        store_inv.append(max(0, store_inventory))
        hub_inv.append(max(0, hub_inventory))
        bakery_inv.append(max(0, bakery_inventory))

    store_val = np.mean(store_inv) * h_store
    hub_val = np.mean(hub_inv) * h_hub
    bakery_val = np.mean(bakery_inv) * h_bakery

    service_level = fulfilled_demand / total_demand
    stockout_risk = stockout_days / n_periods

    return store_val, hub_val, bakery_val, service_level, stockout_risk, total_demand

# --- Run Simulation ---
store_val, hub_val, bakery_val, service_level, stockout_risk, total_demand = simulate_inventory_cost(store_days, hub_days)
total_val = store_val + hub_val + bakery_val

# --- Display Results ---
st.subheader("📊 Inventory Cost Breakdown")
st.metric("Store", f"${store_val:,.2f}")
st.metric("Hub", f"${hub_val:,.2f}")
st.metric("Bakery", f"${bakery_val:,.2f}")
st.metric("Total", f"${total_val:,.2f}")

st.subheader("📈 Service Level Metrics")
st.metric("Fill Rate", f"{service_level*100:.2f}%")
st.metric("Stockout Risk (Days with Shortage)", f"{stockout_risk*100:.2f}%")
st.metric("Total Demand (Units)", f"{total_demand:,.0f}")

# --- Plot Inventory Distribution ---
fig, ax = plt.subplots(1, 2, figsize=(14, 5))
labels = ['Store', 'Hub', 'Bakery']
values = [store_val, hub_val, bakery_val]
ax[0].bar(labels, values, color=['orange', 'skyblue', 'plum'])
ax[0].set_ylabel("Inventory Value ($)")
ax[0].set_title("Inventory Allocation by Node")
ax[0].grid(True, axis='y')

# --- Plot Service Level vs Total Cost ---
simulation_points = list(range(1, 8))
costs = []
levels = []
for freq in simulation_points:
    s, h, b, level, _, _ = simulate_inventory_cost(freq, hub_days)
    costs.append(s + h + b)
    levels.append(level * 100)

ax[1].plot(levels, costs, marker='o', color='darkgreen')
ax[1].set_title("Service Level vs Total Cost")
ax[1].set_xlabel("Fill Rate (%)")
ax[1].set_ylabel("Total Inventory Cost ($)")
ax[1].grid(True)

st.pyplot(fig)
# --- Find Optimal Setting for 95% Fill Rate ---
target_fill = 0.95
best_setting = None
min_gap = float('inf')

for store_day in range(1, 8):
    s, h, b, level, _, _ = simulate_inventory_cost(store_day, hub_days)
    gap = abs(level - target_fill)
    if gap < min_gap:
        min_gap = gap
        best_setting = {
            'Store Repl. Freq (days)': store_day,
            'Fill Rate (%)': level * 100,
            'Total Cost ($)': s + h + b
        }

# Display Optimal Settings
st.subheader("🎯 Optimal Setting for ~95% Fill Rate")
st.write(f"**Store Replenishment Frequency:** {best_setting['Store Repl. Freq (days)']} days")
st.write(f"**Achieved Fill Rate:** {best_setting['Fill Rate (%)']:.2f}%")
st.write(f"**Total Inventory Cost:** ${best_setting['Total Cost ($)']:,.2f}")

# --- Footer ---
st.caption("Simulated for 1 year of daily demand with 20% variability. Lead time includes variability. Service level reflects fill rate.")
