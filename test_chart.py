import sys
sys.path.insert(0, 'smart_data_system')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd

# Load actual sample data
df = pd.read_csv('smart_data_system/data/sample_data.csv')
print(f"Loaded data: {df.shape}")
print(f"Columns: {df.columns.tolist()}")

# Get numeric columns
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()[:4]
print(f"Numeric columns: {numeric_cols}")

# Calculate stats
stats_data = {}
for col in numeric_cols:
    stats_data[col] = df[col].mean()

print(f"Stats: {stats_data}")

# Create chart
fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor('white')
ax.set_facecolor('#f8f9fa')

cols = list(stats_data.keys())
values = list(stats_data.values())

colors = ['#6C63FF', '#FF6584', '#43D399', '#F5A623']
bars = ax.bar(cols, values, color=colors[:len(cols)], edgecolor='#333', linewidth=1.5, width=0.6, alpha=0.85)

ax.set_title('Test Data Chart', color='#000', fontsize=14, fontweight='bold', pad=15)
ax.set_ylabel('Mean Values', color='#333', fontsize=11)
ax.tick_params(colors='#333', labelsize=10)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#ccc')
ax.spines['bottom'].set_color('#ccc')
ax.grid(axis='y', color='#ddd', linewidth=0.8, alpha=0.5)
ax.set_axisbelow(True)

for bar, val in zip(bars, values):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width() / 2, height,
            f'{val:.2f}', ha='center', va='bottom', color='#000', fontsize=10, fontweight='bold')

plt.xticks(rotation=45, ha='right', color='#333')
plt.tight_layout()

fpath = 'smart_data_system/static/charts/test_real_data.png'
print(f'\nSaving to {fpath}...')
plt.savefig(fpath, dpi=100, bbox_inches='tight', facecolor='white')
plt.close(fig)

if os.path.exists(fpath):
    size = os.path.getsize(fpath)
    print(f'SUCCESS! Chart saved: {size} bytes')
    with open(fpath, 'rb') as f:
        header = f.read(8)
    print(f'PNG signature valid: {header.hex()}')
else:
    print('ERROR: File not saved')
