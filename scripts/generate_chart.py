"""Generate flagship bar chart for the Medium article."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# Data
providers = ['OpenAI RAG', 'PageIndex\n(multi-doc)', 'CustomGPT.ai RAG', 'Google Gemini\nRAG']
scores = [0.54, 0.69, 0.78, 0.90]
correct = [90, 81, 86, 98]
incorrect = [9, 3, 2, 2]
not_attempted = [1, 16, 12, 0]

# Colors - distinct but professional
colors = ['#4A90D9', '#F5A623', '#7B68EE', '#50C878']

# Create figure
fig, ax = plt.subplots(figsize=(12, 6))

bars = ax.barh(providers, scores, color=colors, height=0.6, edgecolor='white', linewidth=1.5)

# Add score labels on the bars
for bar, score, c, i, n in zip(bars, scores, correct, incorrect, not_attempted):
    # Score label inside bar
    ax.text(bar.get_width() - 0.03, bar.get_y() + bar.get_height()/2,
            f'{score:.2f}',
            ha='right', va='center', fontsize=18, fontweight='bold', color='white')
    # Detail label outside bar
    ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2,
            f'{c} correct · {i} incorrect · {n} skipped',
            ha='left', va='center', fontsize=11, color='#555555')

# Styling
ax.set_xlim(0, 1.18)
ax.set_xlabel('Quality Score  =  (correct − 4 × incorrect) / total', fontsize=12, color='#555555', labelpad=10)
ax.set_title('RAG Provider Benchmark: 100 Questions, ~1000 Documents',
             fontsize=16, fontweight='bold', pad=15, color='#333333')

# Subtitle
ax.text(0.5, 1.02, 'SimpleQA-Verified · 100-question sample · directional results',
        transform=ax.transAxes, ha='center', fontsize=10, color='#999999', style='italic')

# Clean up axes
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_color('#CCCCCC')
ax.spines['left'].set_color('#CCCCCC')
ax.tick_params(axis='y', labelsize=13, colors='#333333')
ax.tick_params(axis='x', labelsize=10, colors='#999999')
ax.xaxis.set_major_formatter(ticker.FormatStrFormatter('%.1f'))
ax.xaxis.grid(True, alpha=0.2, color='#CCCCCC')
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig('/app/article/benchmark_results.png', dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
print("Chart saved to article/benchmark_results.png")
