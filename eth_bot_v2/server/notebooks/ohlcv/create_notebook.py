#!/usr/bin/env python
"""
Create OHLCV Jupyter Notebooks
This script generates all notebook files with proper markdown and code cells
"""

import json
import os
from pathlib import Path

def create_notebook(cells, filename):
    """Create a Jupyter notebook from cells list"""
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {
                    "name": "ipython",
                    "version": 3
                },
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.10.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    
    # Ensure directory exists
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    
    # Write notebook
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=2, ensure_ascii=False)
    print(f"✅ Created: {filename}")

# ====================================================================
# BASE IMPORT CELL (Works for all notebook locations)
# ====================================================================

def get_base_imports():
    """Base imports that work for all notebooks"""
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# ====================================================================",
            "# 📦 IMPORTS AND SETUP",
            "# ====================================================================",
            "",
            "import pandas as pd",
            "import numpy as np",
            "import matplotlib.pyplot as plt",
            "import seaborn as sns",
            "from pathlib import Path",
            "import sys",
            "import os",
            "import warnings",
            "warnings.filterwarnings('ignore')",
            "",
            "# Set plotting style",
            "plt.style.use('seaborn-v0_8-darkgrid')",
            "sns.set_palette(\"husl\")",
            "%matplotlib inline",
            "",
            "# ====================================================================",
            "# 🔧 PATH CONFIGURATION - Find utils folder",
            "# ====================================================================",
            "",
            "# Get notebook location",
            "notebook_dir = Path(os.getcwd()).resolve()",
            "",
            "def find_ohlcv_root(start_path):",
            "    current = start_path",
            "    for _ in range(5):",
            "        if (current / 'utils').exists() and (current / 'utils' / 'data_loader.py').exists():",
            "            return current",
            "        current = current.parent",
            "    return None",
            "",
            "# Find ohlcv root",
            "ohlcv_root = find_ohlcv_root(notebook_dir)",
            "",
            "if ohlcv_root:",
            "    utils_path = ohlcv_root / 'utils'",
            "    if str(utils_path) not in sys.path:",
            "        sys.path.insert(0, str(utils_path))",
            "    print(f\"✅ OHLCV root: {ohlcv_root}\")",
            "    print(f\"✅ Utils path: {utils_path}\")",
            "else:",
            "    print(\"⚠️  Could not find ohlcv root. Trying relative path...\")",
            "    for rel_path in ['../../utils', '../../../utils', '../../../../utils']:",
            "        test_path = (notebook_dir / rel_path).resolve()",
            "        if test_path.exists() and (test_path / 'data_loader.py').exists():",
            "            if str(test_path) not in sys.path:",
            "                sys.path.insert(0, str(test_path))",
            "            print(f\"✅ Found utils at: {test_path}\")",
            "            break",
            "",
            "# ====================================================================",
            "# 📦 IMPORT UTILITIES",
            "# ====================================================================",
            "",
            "try:",
            "    from data_loader import DataLoader",
            "    from visualizations import TradingVisualizer",
            "    from trading_helpers import TradingHelpers",
            "    print(\"✅ All utilities imported successfully!\")",
            "except ImportError as e:",
            "    print(f\"❌ Import error: {e}\")",
            "    print(\"⚠️  Please ensure utils folder exists with required files.\")",
            "    raise",
            "",
            "print(\"\\n\" + \"=\" * 60)",
            "print(\"✅ SETUP COMPLETE\")",
            "print(\"=\" * 60)"
        ]
    }

# ====================================================================
# NOTEBOOK CELL DEFINITIONS
# ====================================================================

def get_data_overview_cells():
    """Cells for 01_data_overview.ipynb"""
    return [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# Data Overview\n",
                "## OHLCV Price Data Analysis\n",
                "\n",
                "### Objectives:\n",
                "- Load and examine ETH/USD OHLCV data\n",
                "- Understand data structure and types\n",
                "- Check for missing values and data quality\n",
                "- Initial statistical summary\n",
                "- Data range and frequency analysis\n",
                "\n",
                "### Data Sources:\n",
                "- CSV file: `../../../data/Eth_OHLCV.csv`\n",
                "- JSON file: `../../../data/Eth_OHLCV.json`\n",
                "- SQLite DB: `../../../data/ETH.db`"
            ]
        },
        get_base_imports(),
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Initialize data loader\n",
                "loader = DataLoader()\n",
                "\n",
                "# Load data from CSV\n",
                "df = loader.load_from_csv()\n",
                "\n",
                "if df.empty:\n",
                "    print(\"CSV not found, trying JSON...\")\n",
                "    df = loader.load_from_json()\n",
                "\n",
                "if df.empty:\n",
                "    print(\"JSON not found, trying database...\")\n",
                "    df = loader.load_from_db()\n",
                "\n",
                "print(f\"\\n✅ Data loaded successfully!\")\n",
                "print(f\"📊 Shape: {df.shape}\")\n",
                "print(f\"📅 Date range: {df.index.min()} to {df.index.max()}\")\n",
                "print(f\"📈 Total periods: {len(df)}\")\n",
                "df.head(10)"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Data info\n",
                "print(\"=\" * 60)\n",
                "print(\"📋 DATA INFORMATION\")\n",
                "print(\"=\" * 60)\n",
                "df.info()\n",
                "\n",
                "print(\"\\n\" + \"=\" * 60)\n",
                "print(\"📊 DATA TYPES\")\n",
                "print(\"=\" * 60)\n",
                "print(df.dtypes)\n",
                "\n",
                "print(\"\\n\" + \"=\" * 60)\n",
                "print(\"🔍 NULL VALUES\")\n",
                "print(\"=\" * 60)\n",
                "print(df.isnull().sum())"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Statistical summary\n",
                "print(\"=\" * 60)\n",
                "print(\"📈 STATISTICAL SUMMARY\")\n",
                "print(\"=\" * 60)\n",
                "df.describe()"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Data quality check\n",
                "print(\"=\" * 60)\n",
                "print(\"🔍 DATA QUALITY CHECK\")\n",
                "print(\"=\" * 60)\n",
                "\n",
                "# Check for zero or negative values\n",
                "for col in ['open', 'high', 'low', 'close', 'volume']:\n",
                "    if col in df.columns:\n",
                "        invalid = (df[col] <= 0).sum()\n",
                "        print(f\"{col}: {invalid} invalid values (<=0)\")\n",
                "\n",
                "# Check OHLC logic\n",
                "invalid_ohlc = ((df['high'] < df['low']) | \n",
                "               (df['high'] < df['open']) | \n",
                "               (df['high'] < df['close']) |\n",
                "               (df['low'] > df['open']) | \n",
                "               (df['low'] > df['close'])).sum()\n",
                "print(f\"\\n⚠️ Invalid OHLC relationships: {invalid_ohlc}\")\n",
                "\n",
                "if invalid_ohlc > 0:\n",
                "    print(\"\\nInvalid rows:\")\n",
                "    invalid_mask = ((df['high'] < df['low']) | \n",
                "                   (df['high'] < df['open']) | \n",
                "                   (df['high'] < df['close']) |\n",
                "                   (df['low'] > df['open']) | \n",
                "                   (df['low'] > df['close']))\n",
                "    print(df[invalid_mask].head())"
            ]
        }
    ]

def get_statistical_analysis_cells():
    """Cells for 02_statistical_analysis.ipynb"""
    return [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# Statistical Analysis\n",
                "## OHLCV Price Statistics\n",
                "\n",
                "### Objectives:\n",
                "- Distribution analysis of prices and returns\n",
                "- Skewness and kurtosis examination\n",
                "- Outlier detection using IQR and Z-score methods\n",
                "- Rolling statistics analysis\n",
                "- Volatility and return distribution patterns"
            ]
        },
        get_base_imports(),
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Load data\n",
                "loader = DataLoader()\n",
                "df = loader.load_from_csv()\n",
                "\n",
                "if df.empty:\n",
                "    df = loader.load_from_db()\n",
                "\n",
                "print(f\"✅ Data loaded: {len(df)} rows\")\n",
                "\n",
                "# Calculate returns\n",
                "df['returns'] = df['close'].pct_change() * 100\n",
                "df['log_returns'] = np.log(df['close'] / df['close'].shift(1)) * 100\n",
                "df['range'] = df['high'] - df['low']\n",
                "df['range_pct'] = (df['high'] - df['low']) / df['close'] * 100\n",
                "\n",
                "# Price changes\n",
                "df['price_change'] = df['close'] - df['open']\n",
                "df['price_change_pct'] = (df['close'] - df['open']) / df['open'] * 100\n",
                "\n",
                "df.head()"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Distribution analysis\n",
                "fig, axes = plt.subplots(2, 2, figsize=(15, 10))\n",
                "\n",
                "# Price distribution\n",
                "df['close'].hist(bins=50, ax=axes[0, 0], edgecolor='black')\n",
                "axes[0, 0].set_title('ETH Price Distribution', fontsize=14, fontweight='bold')\n",
                "axes[0, 0].set_xlabel('Price ($)')\n",
                "axes[0, 0].set_ylabel('Frequency')\n",
                "\n",
                "# Returns distribution\n",
                "df['returns'].dropna().hist(bins=50, ax=axes[0, 1], edgecolor='black', color='orange')\n",
                "axes[0, 1].set_title('Returns Distribution', fontsize=14, fontweight='bold')\n",
                "axes[0, 1].set_xlabel('Returns (%)')\n",
                "axes[0, 1].set_ylabel('Frequency')\n",
                "\n",
                "# QQ plot for returns\n",
                "from scipy import stats\n",
                "stats.probplot(df['returns'].dropna(), dist=\"norm\", plot=axes[1, 0])\n",
                "axes[1, 0].set_title('Q-Q Plot for Returns', fontsize=14, fontweight='bold')\n",
                "\n",
                "# Box plot for returns\n",
                "df['returns'].dropna().boxplot(ax=axes[1, 1])\n",
                "axes[1, 1].set_title('Returns Box Plot', fontsize=14, fontweight='bold')\n",
                "axes[1, 1].set_ylabel('Returns (%)')\n",
                "\n",
                "plt.tight_layout()\n",
                "plt.show()"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Statistical metrics\n",
                "print(\"=\" * 60)\n",
                "print(\"📊 PRICE STATISTICS\")\n",
                "print(\"=\" * 60)\n",
                "price_stats = df[['open', 'high', 'low', 'close', 'volume']].describe()\n",
                "print(price_stats)\n",
                "\n",
                "print(\"\\n\" + \"=\" * 60)\n",
                "print(\"📊 RETURNS STATISTICS\")\n",
                "print(\"=\" * 60)\n",
                "returns_stats = df[['returns', 'log_returns']].describe()\n",
                "print(returns_stats)\n",
                "\n",
                "print(\"\\n\" + \"=\" * 60)\n",
                "print(\"📊 SKEWNESS & KURTOSIS\")\n",
                "print(\"=\" * 60)\n",
                "for col in ['close', 'returns', 'log_returns']:\n",
                "    if col in df.columns:\n",
                "        data = df[col].dropna()\n",
                "        skew = data.skew()\n",
                "        kurt = data.kurtosis()\n",
                "        print(f\"{col:15s} | Skewness: {skew:8.4f} | Kurtosis: {kurt:8.4f}\")"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Outlier detection\n",
                "print(\"=\" * 60)\n",
                "print(\"🔍 OUTLIER DETECTION\")\n",
                "print(\"=\" * 60)\n",
                "\n",
                "# IQR method\n",
                "def detect_outliers_iqr(data, multiplier=1.5):\n",
                "    Q1 = data.quantile(0.25)\n",
                "    Q3 = data.quantile(0.75)\n",
                "    IQR = Q3 - Q1\n",
                "    lower_bound = Q1 - multiplier * IQR\n",
                "    upper_bound = Q3 + multiplier * IQR\n",
                "    outliers = (data < lower_bound) | (data > upper_bound)\n",
                "    return outliers, lower_bound, upper_bound\n",
                "\n",
                "# Detect outliers in returns\n",
                "for multiplier in [1.5, 2.0, 3.0]:\n",
                "    outliers, lb, ub = detect_outliers_iqr(df['returns'].dropna(), multiplier)\n",
                "    count = outliers.sum()\n",
                "    pct = count / len(df['returns'].dropna()) * 100\n",
                "    print(f\"IQR (multiplier={multiplier}): {count} outliers ({pct:.2f}%)\")\n",
                "    print(f\"  Bounds: [{lb:.2f}, {ub:.2f}]\\n\")\n",
                "\n",
                "# Z-score method\n",
                "from scipy import stats\n",
                "returns = df['returns'].dropna()\n",
                "z_scores = np.abs(stats.zscore(returns))\n",
                "\n",
                "for threshold in [2, 2.5, 3]:\n",
                "    outliers = z_scores > threshold\n",
                "    count = outliers.sum()\n",
                "    pct = count / len(returns) * 100\n",
                "    print(f\"Z-Score (threshold={threshold}): {count} outliers ({pct:.2f}%)\")"
            ]
        }
    ]

def get_correlation_analysis_cells():
    """Cells for 03_correlation_analysis.ipynb"""
    return [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# Correlation Analysis\n",
                "## Price Relationships and Dependencies\n",
                "\n",
                "### Objectives:\n",
                "- Analyze correlations between OHLCV variables\n",
                "- Identify leading indicators\n",
                "- Understand price-volume relationships\n",
                "- Lag analysis and autocorrelation\n",
                "- Feature correlation for model development"
            ]
        },
        get_base_imports(),
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Load data\n",
                "loader = DataLoader()\n",
                "df = loader.load_from_csv()\n",
                "\n",
                "if df.empty:\n",
                "    df = loader.load_from_db()\n",
                "\n",
                "print(f\"✅ Data loaded: {len(df)} rows\")\n",
                "\n",
                "# Calculate additional metrics\n",
                "df['returns'] = df['close'].pct_change() * 100\n",
                "df['range'] = df['high'] - df['low']\n",
                "df['range_pct'] = (df['high'] - df['low']) / df['close'] * 100\n",
                "df['mid'] = (df['high'] + df['low']) / 2\n",
                "df['vwap'] = (df['high'] + df['low'] + df['close']) / 3\n",
                "\n",
                "df.head()"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Correlation matrix\n",
                "corr_cols = ['open', 'high', 'low', 'close', 'volume', 'returns', 'range', 'range_pct', 'mid', 'vwap']\n",
                "corr_matrix = df[corr_cols].corr()\n",
                "\n",
                "fig, ax = plt.subplots(figsize=(12, 10))\n",
                "\n",
                "# Heatmap with annotations\n",
                "mask = np.triu(np.ones_like(corr_matrix, dtype=bool))\n",
                "sns.heatmap(corr_matrix, \n",
                "            mask=mask,\n",
                "            annot=True, \n",
                "            fmt='.2f',\n",
                "            cmap='coolwarm',\n",
                "            center=0,\n",
                "            square=True,\n",
                "            linewidths=0.5,\n",
                "            cbar_kws={\"shrink\": 0.8},\n",
                "            ax=ax)\n",
                "ax.set_title('Correlation Matrix - OHLCV Variables', fontsize=16, fontweight='bold')\n",
                "plt.tight_layout()\n",
                "plt.show()"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Volume vs Price relationships\n",
                "fig, axes = plt.subplots(1, 3, figsize=(18, 5))\n",
                "\n",
                "# Volume vs Price\n",
                "axes[0].scatter(df['volume'], df['close'], alpha=0.5, s=1)\n",
                "axes[0].set_xlabel('Volume', fontweight='bold')\n",
                "axes[0].set_ylabel('Price ($)', fontweight='bold')\n",
                "axes[0].set_title('Volume vs Price', fontsize=12, fontweight='bold')\n",
                "\n",
                "# Volume vs Returns\n",
                "axes[1].scatter(df['volume'], df['returns'], alpha=0.5, s=1, color='orange')\n",
                "axes[1].set_xlabel('Volume', fontweight='bold')\n",
                "axes[1].set_ylabel('Returns (%)', fontweight='bold')\n",
                "axes[1].set_title('Volume vs Returns', fontsize=12, fontweight='bold')\n",
                "\n",
                "# Range vs Volume\n",
                "axes[2].scatter(df['volume'], df['range_pct'], alpha=0.5, s=1, color='green')\n",
                "axes[2].set_xlabel('Volume', fontweight='bold')\n",
                "axes[2].set_ylabel('Range (%)', fontweight='bold')\n",
                "axes[2].set_title('Volume vs Range (%)', fontsize=12, fontweight='bold')\n",
                "\n",
                "plt.tight_layout()\n",
                "plt.show()"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Autocorrelation analysis\n",
                "from statsmodels.graphics.tsaplots import plot_acf, plot_pacf\n",
                "\n",
                "fig, axes = plt.subplots(2, 2, figsize=(16, 10))\n",
                "\n",
                "# ACF for returns\n",
                "plot_acf(df['returns'].dropna(), lags=40, ax=axes[0, 0])\n",
                "axes[0, 0].set_title('Autocorrelation - Returns', fontsize=12, fontweight='bold')\n",
                "\n",
                "# PACF for returns\n",
                "plot_pacf(df['returns'].dropna(), lags=40, ax=axes[0, 1])\n",
                "axes[0, 1].set_title('Partial Autocorrelation - Returns', fontsize=12, fontweight='bold')\n",
                "\n",
                "# ACF for log returns\n",
                "plot_acf(df['log_returns'].dropna(), lags=40, ax=axes[1, 0])\n",
                "axes[1, 0].set_title('Autocorrelation - Log Returns', fontsize=12, fontweight='bold')\n",
                "\n",
                "# PACF for log returns\n",
                "plot_pacf(df['log_returns'].dropna(), lags=40, ax=axes[1, 1])\n",
                "axes[1, 1].set_title('Partial Autocorrelation - Log Returns', fontsize=12, fontweight='bold')\n",
                "\n",
                "plt.tight_layout()\n",
                "plt.show()"
            ]
        }
    ]

def get_notebook_configs():
    """Return all notebook configurations"""
    return {
        "01_eda_exploratory_data_analysis": [
            ("01_data_overview.ipynb", get_data_overview_cells()),
            ("02_statistical_analysis.ipynb", get_statistical_analysis_cells()),
            ("03_correlation_analysis.ipynb", get_correlation_analysis_cells())
        ],
        # Add more categories here as you create them
        # "02_data_visualization": [...],
        # "03_feature_engineering": [...],
        # etc.
    }

def main():
    """Main function to create all notebooks"""
    
    base_path = Path(__file__).parent / "notebooks"
    notebook_configs = get_notebook_configs()
    
    print("=" * 60)
    print("📓 CREATING OHLCV NOTEBOOKS")
    print("=" * 60)
    print(f"📁 Base path: {base_path}\n")
    
    for category, notebooks in notebook_configs.items():
        category_path = base_path / category
        category_path.mkdir(parents=True, exist_ok=True)
        print(f"\n📁 Creating category: {category}")
        
        for filename, cells in notebooks:
            filepath = category_path / filename
            create_notebook(cells, str(filepath))
    
    print("\n" + "=" * 60)
    print("✅ All notebooks created successfully!")
    print(f"📁 Location: {base_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()