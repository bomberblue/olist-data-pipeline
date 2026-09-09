# visualizations.py
"""
Simplified visualizations for Olist star schema.
Creates summary visualizations of the data.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os
from queries import *
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create output directory
os.makedirs("output", exist_ok=True)

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12


def create_visualizations():
    """Generate summary visualizations."""
    
    print("📊 Generating Summary Visualizations...")
    print("=" * 60)
    
    # 1. Row Counts Bar Chart
    print("  📊 Creating Table Row Counts Chart...")
    try:
        counts = get_table_row_counts()
        
        # Sort by row count
        sorted_counts = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))
        
        fig, ax = plt.subplots(figsize=(12, 8))
        bars = ax.bar(sorted_counts.keys(), sorted_counts.values(), alpha=0.7)
        ax.set_xlabel('Table Name')
        ax.set_ylabel('Row Count')
        ax.set_title('Table Row Counts', fontsize=14)
        ax.grid(True, axis='y')
        plt.xticks(rotation=45, ha='right')
        
        # Add value labels on bars
        for bar, count in zip(bars, sorted_counts.values()):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 100,
                    f'{count:,}', ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        plt.savefig('output/table_row_counts.png', dpi=300, bbox_inches='tight')
        plt.close()
        logger.info("  ✅ Saved: output/table_row_counts.png")
        
    except Exception as e:
        print(f"  ❌ Error creating row counts chart: {e}")
    
    # 2. Table Overview Table (as image)
    print("  📋 Creating Table Overview Chart...")
    try:
        counts = get_table_row_counts()
        
        # Create a summary table
        df = pd.DataFrame(list(counts.items()), columns=['Table Name', 'Row Count'])
        df = df.sort_values('Row Count', ascending=False)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.axis('tight')
        ax.axis('off')
        
        table = ax.table(cellText=df.values,
                         colLabels=df.columns,
                         cellLoc='center',
                         loc='center',
                         colWidths=[0.3, 0.2])
        
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1.2, 1.5)
        
        ax.set_title('Table Overview - Row Counts', fontsize=14, pad=20)
        
        plt.tight_layout()
        plt.savefig('output/table_overview.png', dpi=300, bbox_inches='tight')
        plt.close()
        logger.info("  ✅ Saved: output/table_overview.png")
        
    except Exception as e:
        print(f"  ❌ Error creating table overview: {e}")
    
    print("\n✅ All visualizations saved to: output/")


if __name__ == "__main__":
    create_visualizations()