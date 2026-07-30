import json
from pathlib import Path

# Create notebooks directory
notebooks_dir = Path('notebooks')
notebooks_dir.mkdir(exist_ok=True)

print("=" * 60)
print("🚀 Creating ETH Analysis Notebooks")
print("=" * 60)

# ============================================
# NOTEBOOK 1: Data Exploration
# ============================================
print("\n📊 Creating 01_data_exploration.ipynb...")

notebook1 = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# 📊 ETH OHLCV Data Exploration",
                "## Using SQLite Database",
                "",
                "This notebook explores Ethereum OHLCV (Open, High, Low, Close, Volume) data stored in SQLite database."
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 1. Import Libraries"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import pandas as pd",
                "import numpy as np",
                "import sqlite3",
                "import matplotlib.pyplot as plt",
                "import seaborn as sns",
                "from pathlib import Path",
                "import warnings",
                "warnings.filterwarnings('ignore')",
                "",
                "# Set style for better visualizations",
                "plt.style.use('seaborn-v0_8-darkgrid')",
                "sns.set_palette(\"husl\")",
                "%matplotlib inline"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 2. Connect to SQLite Database"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Define database path",
                "DATA_DIR = Path('..') / 'data'",
                "db_path = DATA_DIR / 'ETH.db'",
                "",
                "# Connect to SQLite database",
                "conn = sqlite3.connect(db_path)",
                "",
                "# Check if table exists",
                "tables = pd.read_sql(\"SELECT name FROM sqlite_master WHERE type='table';\", conn)",
                "print(\"📋 Tables in database:\")",
                "print(tables)"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Load data from SQLite",
                "query = \"SELECT * FROM eth_ohlcv ORDER BY date\"",
                "df = pd.read_sql(query, conn, parse_dates=['date'])",
                "",
                "# Close connection",
                "conn.close()",
                "",
                "print(f\"✅ Loaded {len(df)} days of OHLCV data from SQLite\")",
                "print(f\"📅 Period: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}\")",
                "df.head(10)"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 3. Basic Statistics"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "print(\"📊 Basic Statistics:\")",
                "print(\"=\"*50)",
                "df[['open', 'high', 'low', 'close', 'volume']].describe()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 4. Check for Missing Values"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "print(\"🔍 Missing Values:\")",
                "df.isnull().sum()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 5. Correlation Matrix"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Correlation matrix",
                "correlation = df[['open', 'high', 'low', 'close', 'volume']].corr()",
                "",
                "plt.figure(figsize=(10, 8))",
                "sns.heatmap(correlation, annot=True, cmap='coolwarm', center=0, fmt='.2f', square=True)",
                "plt.title('📈 Correlation Matrix - ETH Price Metrics', fontsize=14)",
                "plt.tight_layout()",
                "plt.show()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 6. Price Distribution Analysis"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "fig, axes = plt.subplots(2, 2, figsize=(14, 10))",
                "",
                "# Close price distribution",
                "axes[0, 0].hist(df['close'], bins=50, edgecolor='black', alpha=0.7, color='blue')",
                "axes[0, 0].set_title('Close Price Distribution')",
                "axes[0, 0].set_xlabel('Price (USD)')",
                "axes[0, 0].set_ylabel('Frequency')",
                "axes[0, 0].axvline(df['close'].mean(), color='red', linestyle='--', ",
                "                   label=f'Mean: ${df[\"close\"].mean():.2f}')",
                "axes[0, 0].legend()",
                "",
                "# Volume distribution",
                "axes[0, 1].hist(df['volume'], bins=50, edgecolor='black', alpha=0.7, color='green')",
                "axes[0, 1].set_title('Volume Distribution')",
                "axes[0, 1].set_xlabel('Volume')",
                "axes[0, 1].set_ylabel('Frequency')",
                "",
                "# Box plot for price",
                "axes[1, 0].boxplot(df['close'])",
                "axes[1, 0].set_title('Close Price Box Plot')",
                "axes[1, 0].set_ylabel('Price (USD)')",
                "",
                "# Box plot for volume",
                "axes[1, 1].boxplot(df['volume'])",
                "axes[1, 1].set_title('Volume Box Plot')",
                "axes[1, 1].set_ylabel('Volume')",
                "",
                "plt.tight_layout()",
                "plt.show()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 7. Daily Returns Analysis"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Calculate returns",
                "df['returns'] = df['close'].pct_change() * 100",
                "df['log_returns'] = np.log(df['close'] / df['close'].shift(1)) * 100",
                "",
                "fig, axes = plt.subplots(1, 2, figsize=(14, 5))",
                "",
                "# Returns over time",
                "axes[0].plot(df['date'], df['returns'], color='blue', alpha=0.7, linewidth=0.8)",
                "axes[0].axhline(y=0, color='red', linestyle='--', alpha=0.5)",
                "axes[0].set_title('Daily Returns (%) Over Time')",
                "axes[0].set_xlabel('Date')",
                "axes[0].set_ylabel('Return (%)')",
                "axes[0].grid(True, alpha=0.3)",
                "",
                "# Returns distribution",
                "axes[1].hist(df['returns'].dropna(), bins=50, edgecolor='black', alpha=0.7, color='purple')",
                "axes[1].axvline(df['returns'].mean(), color='red', linestyle='--', ",
                "                label=f'Mean: {df[\"returns\"].mean():.2f}%')",
                "axes[1].axvline(df['returns'].median(), color='green', linestyle='--', ",
                "                label=f'Median: {df[\"returns\"].median():.2f}%')",
                "axes[1].set_title('Returns Distribution')",
                "axes[1].set_xlabel('Return (%)')",
                "axes[1].set_ylabel('Frequency')",
                "axes[1].legend()",
                "",
                "plt.tight_layout()",
                "plt.show()",
                "",
                "print(\"📊 Returns Statistics:\")",
                "print(f\"   Mean: {df['returns'].mean():.2f}%\")",
                "print(f\"   Std Dev: {df['returns'].std():.2f}%\")",
                "print(f\"   Skewness: {df['returns'].skew():.2f}\")",
                "print(f\"   Kurtosis: {df['returns'].kurtosis():.2f}\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 8. SQL Queries Examples"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Reconnect for SQL queries",
                "conn = sqlite3.connect(db_path)",
                "",
                "# Query: Top 10 highest price days",
                "top_days_query = \"\"\"",
                "SELECT date, open, high, low, close, volume",
                "FROM eth_ohlcv",
                "ORDER BY close DESC",
                "LIMIT 10",
                "\"\"\"",
                "top_days = pd.read_sql(top_days_query, conn)",
                "print(\"📈 Top 10 Highest Price Days:\")",
                "top_days"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Query: Monthly averages",
                "monthly_query = \"\"\"",
                "SELECT ",
                "    strftime('%Y-%m', date) as month,",
                "    COUNT(*) as days,",
                "    ROUND(AVG(close), 2) as avg_price,",
                "    ROUND(MIN(close), 2) as min_price,",
                "    ROUND(MAX(close), 2) as max_price,",
                "    ROUND(AVG(volume), 0) as avg_volume",
                "FROM eth_ohlcv",
                "GROUP BY month",
                "ORDER BY month DESC",
                "LIMIT 12",
                "\"\"\"",
                "monthly = pd.read_sql(monthly_query, conn)",
                "print(\"\\n📅 Last 12 Months Averages:\")",
                "monthly",
                "",
                "conn.close()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 9. Summary",
                "",
                "✅ Data loaded successfully from SQLite",
                "✅ Basic statistics calculated",
                "✅ Missing values checked",
                "✅ Correlation matrix created",
                "✅ Price distribution analyzed",
                "✅ Returns calculated and visualized",
                "✅ SQL queries executed"
            ]
        }
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
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
            "version": "3.8.0"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

# Save Notebook 1
file_path1 = notebooks_dir / '01_data_exploration.ipynb'
with open(file_path1, 'w', encoding='utf-8') as f:
    json.dump(notebook1, f, indent=1, ensure_ascii=False)
print(f"✅ Created: {file_path1}")

# ============================================
# NOTEBOOK 2: Technical Analysis
# ============================================
print("\n📈 Creating 02_technical_analysis.ipynb...")

notebook2 = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# 📈 ETH Technical Analysis",
                "## Indicators and Trading Signals",
                "",
                "This notebook calculates and visualizes technical indicators using data from SQLite."
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 1. Import Libraries"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import pandas as pd",
                "import numpy as np",
                "import sqlite3",
                "import matplotlib.pyplot as plt",
                "import seaborn as sns",
                "from pathlib import Path",
                "import warnings",
                "warnings.filterwarnings('ignore')",
                "",
                "plt.style.use('seaborn-v0_8-darkgrid')",
                "sns.set_palette(\"husl\")",
                "%matplotlib inline"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 2. Connect to SQLite and Load Data"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Load data from SQLite",
                "DATA_DIR = Path('..') / 'data'",
                "db_path = DATA_DIR / 'ETH.db'",
                "",
                "conn = sqlite3.connect(db_path)",
                "df = pd.read_sql(\"SELECT * FROM eth_ohlcv ORDER BY date\", conn, parse_dates=['date'])",
                "conn.close()",
                "",
                "print(f\"✅ Loaded {len(df)} days of data from SQLite\")",
                "df.head()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 3. Calculate Technical Indicators"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "def calculate_indicators(df):",
                "    \"\"\"Calculate all technical indicators\"\"\"",
                "    df = df.copy()",
                "    ",
                "    # Simple Moving Averages",
                "    df['SMA_7'] = df['close'].rolling(7).mean()",
                "    df['SMA_20'] = df['close'].rolling(20).mean()",
                "    df['SMA_50'] = df['close'].rolling(50).mean()",
                "    df['SMA_200'] = df['close'].rolling(200).mean()",
                "    ",
                "    # Exponential Moving Averages",
                "    df['EMA_12'] = df['close'].ewm(span=12, adjust=False).mean()",
                "    df['EMA_26'] = df['close'].ewm(span=26, adjust=False).mean()",
                "    ",
                "    # MACD",
                "    df['MACD'] = df['EMA_12'] - df['EMA_26']",
                "    df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()",
                "    df['MACD_hist'] = df['MACD'] - df['MACD_signal']",
                "    ",
                "    # RSI",
                "    delta = df['close'].diff()",
                "    gain = (delta.where(delta > 0, 0)).rolling(14).mean()",
                "    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()",
                "    rs = gain / loss",
                "    df['RSI_14'] = 100 - (100 / (1 + rs))",
                "    ",
                "    # Bollinger Bands",
                "    df['BB_middle'] = df['close'].rolling(20).mean()",
                "    bb_std = df['close'].rolling(20).std()",
                "    df['BB_upper'] = df['BB_middle'] + (bb_std * 2)",
                "    df['BB_lower'] = df['BB_middle'] - (bb_std * 2)",
                "    ",
                "    # ATR",
                "    high_low = df['high'] - df['low']",
                "    high_close = abs(df['high'] - df['close'].shift())",
                "    low_close = abs(df['low'] - df['close'].shift())",
                "    ranges = pd.concat([high_low, high_close, low_close], axis=1)",
                "    true_range = ranges.max(axis=1)",
                "    df['ATR_14'] = true_range.rolling(14).mean()",
                "    ",
                "    return df",
                "",
                "df = calculate_indicators(df)",
                "print(\"✅ Technical indicators calculated\")",
                "df.tail(10)"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 4. Price with Moving Averages"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "fig, ax = plt.subplots(figsize=(16, 8))",
                "",
                "ax.plot(df['date'], df['close'], label='Close Price', color='black', linewidth=2)",
                "ax.plot(df['date'], df['SMA_20'], label='SMA 20', color='blue', linewidth=1.5)",
                "ax.plot(df['date'], df['SMA_50'], label='SMA 50', color='orange', linewidth=1.5)",
                "ax.plot(df['date'], df['SMA_200'], label='SMA 200', color='red', linewidth=1.5)",
                "",
                "ax.fill_between(df['date'], df['BB_lower'], df['BB_upper'], ",
                "                 alpha=0.2, color='gray', label='Bollinger Bands')",
                "",
                "ax.set_title('ETH Price with Moving Averages and Bollinger Bands', fontsize=16)",
                "ax.set_xlabel('Date')",
                "ax.set_ylabel('Price (USD)')",
                "ax.legend(loc='upper left')",
                "ax.grid(True, alpha=0.3)",
                "plt.tight_layout()",
                "plt.show()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 5. MACD Indicator"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "fig, axes = plt.subplots(2, 1, figsize=(16, 10), gridspec_kw={'height_ratios': [2, 1]})",
                "",
                "# Price",
                "axes[0].plot(df['date'], df['close'], label='Close Price', color='black', linewidth=1.5)",
                "axes[0].set_title('ETH Price')",
                "axes[0].set_ylabel('Price (USD)')",
                "axes[0].grid(True, alpha=0.3)",
                "",
                "# MACD",
                "axes[1].plot(df['date'], df['MACD'], label='MACD', color='blue', linewidth=1.5)",
                "axes[1].plot(df['date'], df['MACD_signal'], label='Signal Line', color='red', linewidth=1.5)",
                "axes[1].bar(df['date'], df['MACD_hist'], label='Histogram', color='gray', alpha=0.5)",
                "axes[1].axhline(y=0, color='black', linestyle='--', alpha=0.5)",
                "axes[1].set_title('MACD Indicator')",
                "axes[1].set_xlabel('Date')",
                "axes[1].set_ylabel('MACD')",
                "axes[1].legend(loc='upper left')",
                "axes[1].grid(True, alpha=0.3)",
                "",
                "plt.tight_layout()",
                "plt.show()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 6. RSI and Volume"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "fig, axes = plt.subplots(3, 1, figsize=(16, 12), gridspec_kw={'height_ratios': [2, 1, 1]})",
                "",
                "# Price",
                "axes[0].plot(df['date'], df['close'], color='black', linewidth=1.5)",
                "axes[0].set_title('ETH Price')",
                "axes[0].set_ylabel('Price (USD)')",
                "axes[0].grid(True, alpha=0.3)",
                "",
                "# RSI",
                "axes[1].plot(df['date'], df['RSI_14'], color='purple', linewidth=1.5)",
                "axes[1].axhline(y=70, color='red', linestyle='--', alpha=0.5, label='Overbought (70)')",
                "axes[1].axhline(y=30, color='green', linestyle='--', alpha=0.5, label='Oversold (30)')",
                "axes[1].fill_between(df['date'], 70, 100, alpha=0.2, color='red')",
                "axes[1].fill_between(df['date'], 0, 30, alpha=0.2, color='green')",
                "axes[1].set_title('Relative Strength Index (RSI)')",
                "axes[1].set_ylabel('RSI')",
                "axes[1].set_ylim(0, 100)",
                "axes[1].legend(loc='upper left')",
                "axes[1].grid(True, alpha=0.3)",
                "",
                "# Volume",
                "axes[2].bar(df['date'], df['volume'], color='blue', alpha=0.7)",
                "axes[2].set_title('Trading Volume')",
                "axes[2].set_xlabel('Date')",
                "axes[2].set_ylabel('Volume')",
                "axes[2].grid(True, alpha=0.3)",
                "",
                "plt.tight_layout()",
                "plt.show()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 7. Generate Trading Signals"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "def generate_signals(df):",
                "    \"\"\"Generate trading signals\"\"\"",
                "    df = df.copy()",
                "    df['signal'] = 0",
                "    ",
                "    # MACD crossover",
                "    df.loc[df['MACD'] > df['MACD_signal'], 'signal'] += 1",
                "    df.loc[df['MACD'] < df['MACD_signal'], 'signal'] -= 1",
                "    ",
                "    # RSI signals",
                "    df.loc[df['RSI_14'] < 30, 'signal'] += 1",
                "    df.loc[df['RSI_14'] > 70, 'signal'] -= 1",
                "    ",
                "    # Bollinger Bands",
                "    df.loc[df['close'] < df['BB_lower'], 'signal'] += 1",
                "    df.loc[df['close'] > df['BB_upper'], 'signal'] -= 1",
                "    ",
                "    return df",
                "",
                "df_signals = generate_signals(df)",
                "",
                "fig, ax = plt.subplots(figsize=(16, 8))",
                "ax.plot(df_signals['date'], df_signals['close'], label='Close Price', color='black', linewidth=1.5)",
                "",
                "buy_signals = df_signals[df_signals['signal'] > 0]",
                "ax.scatter(buy_signals['date'], buy_signals['close'], ",
                "           color='green', s=100, marker='^', label='Buy Signal', alpha=0.8)",
                "",
                "sell_signals = df_signals[df_signals['signal'] < 0]",
                "ax.scatter(sell_signals['date'], sell_signals['close'], ",
                "           color='red', s=100, marker='v', label='Sell Signal', alpha=0.8)",
                "",
                "ax.set_title('ETH Trading Signals', fontsize=16)",
                "ax.set_xlabel('Date')",
                "ax.set_ylabel('Price (USD)')",
                "ax.legend()",
                "ax.grid(True, alpha=0.3)",
                "plt.tight_layout()",
                "plt.show()",
                "",
                "print(\"📊 Signal Summary:\")",
                "print(f\"   Buy Signals: {(df_signals['signal'] > 0).sum()}\")",
                "print(f\"   Sell Signals: {(df_signals['signal'] < 0).sum()}\")",
                "print(f\"   Neutral: {(df_signals['signal'] == 0).sum()}\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 8. Save Trading Signals to SQLite"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Save signals to SQLite",
                "conn = sqlite3.connect(db_path)",
                "",
                "conn.execute('''",
                "    CREATE TABLE IF NOT EXISTS eth_signals (",
                "        date TEXT PRIMARY KEY,",
                "        signal INTEGER,",
                "        signal_type TEXT",
                "    )",
                "''')",
                "",
                "df_signals_db = df_signals[['date', 'signal']].copy()",
                "df_signals_db['date'] = df_signals_db['date'].dt.strftime('%Y-%m-%d')",
                "df_signals_db['signal_type'] = df_signals_db['signal'].apply(",
                "    lambda x: 'BUY' if x > 0 else ('SELL' if x < 0 else 'NEUTRAL')",
                ")",
                "",
                "df_signals_db.to_sql('eth_signals', conn, if_exists='replace', index=False)",
                "conn.close()",
                "",
                "print(\"✅ Trading signals saved to SQLite\")",
                "df_signals_db.tail()"
            ]
        }
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
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
            "version": "3.8.0"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

# Save Notebook 2
file_path2 = notebooks_dir / '02_technical_analysis.ipynb'
with open(file_path2, 'w', encoding='utf-8') as f:
    json.dump(notebook2, f, indent=1, ensure_ascii=False)
print(f"✅ Created: {file_path2}")

# ============================================
# NOTEBOOK 3: Visualization Dashboard
# ============================================
print("\n📊 Creating 03_visualization_dashboard.ipynb...")

notebook3 = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# 📊 ETH Visualization Dashboard",
                "## Interactive Charts and Analysis",
                "",
                "This notebook creates interactive visualizations for Ethereum OHLCV data."
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 1. Import Libraries"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import pandas as pd",
                "import numpy as np",
                "import sqlite3",
                "import matplotlib.pyplot as plt",
                "import seaborn as sns",
                "from pathlib import Path",
                "import plotly.graph_objects as go",
                "from plotly.subplots import make_subplots",
                "import warnings",
                "warnings.filterwarnings('ignore')",
                "",
                "plt.style.use('seaborn-v0_8-darkgrid')",
                "%matplotlib inline"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 2. Load Data from SQLite"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Load data from SQLite",
                "DATA_DIR = Path('..') / 'data'",
                "db_path = DATA_DIR / 'ETH.db'",
                "",
                "conn = sqlite3.connect(db_path)",
                "df = pd.read_sql(\"SELECT * FROM eth_ohlcv ORDER BY date\", conn, parse_dates=['date'])",
                "conn.close()",
                "",
                "print(f\"✅ Loaded {len(df)} days of data from SQLite\")\n",
                "df.tail()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 3. Interactive Candlestick Chart"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Create interactive candlestick chart\n",
                "fig = make_subplots(rows=3, cols=1, \n",
                "                    shared_xaxes=True,\n",
                "                    vertical_spacing=0.05,\n",
                "                    row_heights=[0.5, 0.25, 0.25],\n",
                "                    subplot_titles=('ETH Price - Candlestick', 'Volume', 'Returns'))\n",
                "\n",
                "# Candlestick chart\n",
                "fig.add_trace(go.Candlestick(x=df['date'],\n",
                "                              open=df['open'],\n",
                "                              high=df['high'],\n",
                "                              low=df['low'],\n",
                "                              close=df['close'],\n",
                "                              name='OHLC'),\n",
                "              row=1, col=1)\n",
                "\n",
                "# Volume\n",
                "colors = ['green' if close >= open else 'red' for close, open in zip(df['close'], df['open'])]\n",
                "fig.add_trace(go.Bar(x=df['date'], y=df['volume'], name='Volume', marker_color=colors),\n",
                "              row=2, col=1)\n",
                "\n",
                "# Returns\n",
                "df['returns'] = df['close'].pct_change() * 100\n",
                "fig.add_trace(go.Scatter(x=df['date'], y=df['returns'], \n",
                "                         name='Daily Returns', line=dict(color='purple', width=1)),\n",
                "              row=3, col=1)\n",
                "\n",
                "# Update layout\n",
                "fig.update_layout(\n",
                "    title='📈 ETH Price Dashboard',\n",
                "    height=800,\n",
                "    showlegend=True,\n",
                "    template='plotly_dark'\n",
                ")\n",
                "\n",
                "fig.show()"
            ]
        }
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
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
            "version": "3.8.0"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

# Save Notebook 3
file_path3 = notebooks_dir / '03_visualization_dashboard.ipynb'
with open(file_path3, 'w', encoding='utf-8') as f:
    json.dump(notebook3, f, indent=1, ensure_ascii=False)
print(f"✅ Created: {file_path3}")

# ============================================
# NOTEBOOK 4: Price Prediction
# ============================================
print("\n🔮 Creating 04_price_prediction.ipynb...")

notebook4 = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# 🔮 ETH Price Prediction",
                "## Simple Forecasting Models",
                "",
                "This notebook uses various forecasting methods to predict ETH prices."
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 1. Import Libraries"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import pandas as pd",
                "import numpy as np",
                "import sqlite3",
                "import matplotlib.pyplot as plt",
                "from pathlib import Path",
                "from sklearn.linear_model import LinearRegression",
                "from sklearn.metrics import mean_squared_error, r2_score",
                "import warnings",
                "warnings.filterwarnings('ignore')",
                "",
                "plt.style.use('seaborn-v0_8-darkgrid')",
                "%matplotlib inline"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 2. Load Data"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Load data from SQLite\n",
                "DATA_DIR = Path('..') / 'data'\n",
                "db_path = DATA_DIR / 'ETH.db'\n",
                "\n",
                "conn = sqlite3.connect(db_path)\n",
                "df = pd.read_sql(\"SELECT * FROM eth_ohlcv ORDER BY date\", conn, parse_dates=['date'])\n",
                "conn.close()\n",
                "\n",
                "print(f\"✅ Loaded {len(df)} days of data\")\n",
                "df.tail()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 3. Simple Moving Average Forecast"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Calculate moving averages\n",
                "df['SMA_7'] = df['close'].rolling(7).mean()\n",
                "df['SMA_30'] = df['close'].rolling(30).mean()\n",
                "df['SMA_90'] = df['close'].rolling(90).mean()\n",
                "\n",
                "# Plot\n",
                "fig, ax = plt.subplots(figsize=(16, 8))\n",
                "ax.plot(df['date'], df['close'], label='Actual Price', color='black', linewidth=2)\n",
                "ax.plot(df['date'], df['SMA_7'], label='7-Day SMA', color='blue', linewidth=1.5)\n",
                "ax.plot(df['date'], df['SMA_30'], label='30-Day SMA', color='orange', linewidth=1.5)\n",
                "ax.plot(df['date'], df['SMA_90'], label='90-Day SMA', color='red', linewidth=1.5)\n",
                "\n",
                "ax.set_title('ETH Price with Moving Averages', fontsize=16)\n",
                "ax.set_xlabel('Date')\n",
                "ax.set_ylabel('Price (USD)')\n",
                "ax.legend()\n",
                "ax.grid(True, alpha=0.3)\n",
                "plt.tight_layout()\n",
                "plt.show()"
            ]
        }
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
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
            "version": "3.8.0"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

# Save Notebook 4
file_path4 = notebooks_dir / '04_price_prediction.ipynb'
with open(file_path4, 'w', encoding='utf-8') as f:
    json.dump(notebook4, f, indent=1, ensure_ascii=False)
print(f"✅ Created: {file_path4}")

# ============================================
# Summary
# ============================================
print("\n" + "=" * 60)
print("🎉 ALL NOTEBOOKS CREATED SUCCESSFULLY!")
print("=" * 60)
print("\n📁 Location:", notebooks_dir.absolute())
print("\n📊 Notebooks created:")
print("   ✅ 01_data_exploration.ipynb")
print("   ✅ 02_technical_analysis.ipynb")
print("   ✅ 03_visualization_dashboard.ipynb")
print("   ✅ 04_price_prediction.ipynb")
print("\n🚀 To open:")
print("   cd", Path.cwd())
print("   jupyter notebook")
print("=" * 60)