├── collect_ohlcv.py
    ├── collect_trades.py
    ├── collect_orderbook.py
    ├── collect_funding_rate.py
    ├── collect_open_interest.py
    └── collect_option_chain.py


    scripts/
├── ohlcv/
├── orderbook/
├── open_interest/
├── funding_rate/
├── trades/
├── liquidations/
├── option_chain/
├── greeks/
├── implied_volatility/
├── fear_greed/
├── news/
├── onchain/
└── whale_transactions/



scripts/
├── ohlcv/
├── orderbook/
├── trades/
├── funding_rate/
├── open_interest/
├── option_chain/
├── greeks/
├── implied_volatility/
├── liquidations/
├── fear_greed/
├── news/
└── onchain/

scripts/
└── indicators/
    ├── sma.py
    ├── ema.py
    ├── rsi.py
    ├── macd.py
    ├── bollinger.py
    ├── atr.py
    ├── stochastic.py
    ├── adx.py
    ├── obv.py
    └── volume_profile.py



    trading/
├── strategies/
│   ├── sma_cross.py
│   ├── ema_cross.py
│   ├── rsi.py
│   ├── macd.py
│   ├── breakout.py
│   ├── trend_following.py
│   ├── scalping.py
│   ├── mean_reversion.py
│   └── options_strategy.py



backtesting/
├── engine.py
├── metrics.py
├── portfolio.py
├── broker.py
└── reports.py


ml/
├── datasets/
├── features/
├── models/
│   ├── xgboost/
│   ├── lstm/
│   ├── transformer/
│   └── reinforcement/
├── training/
└── prediction/


bot/
├── signal_generator.py
├── risk_manager.py
├── position_manager.py
├── order_executor.py
├── paper_trading.py
└── live_trading.py