import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Stahování dat
print("⏳ Stahuji data...")
data = yf.download("BTC-USD", start="2010-01-01")

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.droplevel(1)

# --- PŘÍPRAVA DAT ---
weekly_df = pd.DataFrame()
weekly_df["Close"] = data["Close"].resample('W').last()
weekly_df["Low"] = data["Low"].resample('W').min()
weekly_df["High"] = data["High"].resample('W').max()

# Indikátor
weekly_df["SMA_38"] = weekly_df["Close"].rolling(window=50).mean()

weekly_df.dropna(inplace=True)

# --- PROMĚNNÉ ---
pozice = 0 
setup_long = False
setup_short = False

moje_entry_cena = 0
moje_sl_cena = 0
moje_tp_cena = 0

start_kapital = 10000
kapital = start_kapital
equity_historie = [kapital]
equity_datumy = [weekly_df.index[0]]
trades_log = [] # Zde budeme ukládat výsledek každého obchodu v USD

# Grafické seznamy
signal_entry_long = []
signal_entry_short = []
signal_tp = []
signal_sl = []

print(f"🏁 Startovní kapitál: {kapital} USD")
print("-" * 40)

for i in range(2, len(weekly_df)):
    low = weekly_df["Low"].iloc[i]
    high = weekly_df["High"].iloc[i]
    datum = weekly_df.index[i]
    
    sma_limit = weekly_df["SMA_38"].iloc[i-1]
    
    cena_minule = weekly_df["Close"].iloc[i-1]
    sma_minule = weekly_df["SMA_38"].iloc[i-1]
    cena_predminule = weekly_df["Close"].iloc[i-2]
    sma_predminule = weekly_df["SMA_38"].iloc[i-2]

    trade_closed_this_week = False
    pnl = 0 # Profit/Loss z aktuálního obchodu
    kapital_pred_obchodem = kapital

    # --- A) ŘÍZENÍ POZICE ---
    if pozice == 1: # LONG
        if low <= moje_sl_cena: 
            pozice = 0
            trade_closed_this_week = True
            kapital = kapital * 0.97 # SL 5%
            signal_sl.append(datum)
        elif high >= moje_tp_cena:
            pozice = 0
            trade_closed_this_week = True
            kapital = kapital * 1.10 # TP 15%
            signal_tp.append(datum)

    elif pozice == -1: # SHORT
        if high >= moje_sl_cena:
            pozice = 0
            trade_closed_this_week = True
            kapital = kapital * 0.97 # SL 5%
            signal_sl.append(datum)
        elif low <= moje_tp_cena:
            pozice = 0
            trade_closed_this_week = True
            kapital = kapital * 1.10 # TP 15%
            signal_tp.append(datum)
    
    # Zápis výsledku obchodu, pokud byl uzavřen
    if trade_closed_this_week:
        pnl = kapital - kapital_pred_obchodem
        trades_log.append(pnl)
        equity_historie.append(kapital)
        equity_datumy.append(datum)

    # --- B) VSTUPY ---
    if pozice == 0 and not trade_closed_this_week:
        
        if cena_minule > sma_minule and cena_predminule > sma_predminule:
            setup_long = True
            setup_short = False 
        elif cena_minule < sma_minule and cena_predminule < sma_predminule:
            setup_short = True
            setup_long = False
        else:
            setup_long = False
            setup_short = False

        # VSTUPY NA RETESTU
        if setup_long and low <= sma_limit:
            pozice = 1
            moje_entry_cena = sma_limit
            moje_sl_cena = moje_entry_cena * 0.97
            moje_tp_cena = moje_entry_cena * 1.10
            signal_entry_long.append(datum)
            
            # Intra-bar check
            kapital_pred_obchodem = kapital
            trade_done = False
            if low <= moje_sl_cena:
                pozice = 0
                kapital = kapital * 0.97
                signal_sl.append(datum)
                trade_done = True
                print(f"⚠️ Okamžitý SL")
            elif high >= moje_tp_cena:
                pozice = 0
                kapital = kapital * 1.10
                signal_tp.append(datum)
                trade_done = True
                print(f"⚡ Okamžitý TP")
            
            if trade_done:
                pnl = kapital - kapital_pred_obchodem
                trades_log.append(pnl)
                equity_historie.append(kapital)
                equity_datumy.append(datum)

        elif setup_short and high >= sma_limit:
            pozice = -1
            moje_entry_cena = sma_limit
            moje_sl_cena = moje_entry_cena * 1.02
            moje_tp_cena = moje_entry_cena * 0.90
            signal_entry_short.append(datum)

            # Intra-bar check
            kapital_pred_obchodem = kapital
            trade_done = False
            if high >= moje_sl_cena:
                pozice = 0
                kapital = kapital * 0.97
                signal_sl.append(datum)
                trade_done = True
                print(f"⚠️ Okamžitý SL")
            elif low <= moje_tp_cena:
                pozice = 0
                kapital = kapital * 1.10
                signal_tp.append(datum)
                trade_done = True
                print(f"⚡ Okamžitý TP")
            
            if trade_done:
                pnl = kapital - kapital_pred_obchodem
                trades_log.append(pnl)
                equity_historie.append(kapital)
                equity_datumy.append(datum)

# --- VÝPOČET STATISTIK ---
total_trades = len(trades_log)
wins = [t for t in trades_log if t > 0]
losses = [t for t in trades_log if t <= 0]

num_wins = len(wins)
num_losses = len(losses)
winrate = (num_wins / total_trades * 100) if total_trades > 0 else 0

avg_win = np.mean(wins) if wins else 0
avg_loss = np.mean(losses) if losses else 0
profit_factor = (sum(wins) / abs(sum(losses))) if sum(losses) != 0 else 0

# Max Drawdown Calculation
equity_series = pd.Series(equity_historie)
running_max = equity_series.cummax()
drawdown = (equity_series - running_max) / running_max * 100
max_drawdown = drawdown.min()

total_return = ((kapital - start_kapital) / start_kapital) * 100

# --- VÝPIS REPORTU ---
print("\n" + "="*40)
print(f"📊 VÝSLEDKY BACKTESTU (Realistický mód)")
print("="*40)
print(f"Konečný kapitál:      {kapital:,.0f} USD")
print(f"Čistý zisk:           {kapital - start_kapital:,.0f} USD")
print(f"Zhodnocení:           {total_return:.2f} %")
print("-" * 40)
print(f"Počet obchodů:        {total_trades}")
print(f"Počet výher:          {num_wins} ({winrate:.1f} %)")
print(f"Počet proher:         {num_losses} ({100-winrate:.1f} %)")
print("-" * 40)
print(f"Průměrná výhra:       {avg_win:.0f} USD")
print(f"Průměrná prohra:      {avg_loss:.0f} USD")
print(f"Profit Factor:        {profit_factor:.2f}")
print(f"Max Drawdown:         {max_drawdown:.2f} %")
print("="*40)

# --- GRAFY ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

# Graf 1: Cena
ax1.plot(weekly_df.index, weekly_df["Close"], color="#333333", alpha=0.6, label="Cena")
ax1.plot(weekly_df.index, weekly_df["SMA_38"], color="blue", linewidth=1.5, label="SMA 38")
if signal_entry_long: ax1.scatter(signal_entry_long, weekly_df.loc[signal_entry_long]["SMA_38"].shift(1), marker="^", color="green", s=80, label="Long")
if signal_entry_short: ax1.scatter(signal_entry_short, weekly_df.loc[signal_entry_short]["SMA_38"].shift(1), marker="v", color="red", s=80, label="Short")
if signal_tp: ax1.scatter(signal_tp, weekly_df.loc[signal_tp]["Close"], marker="o", color="gold", edgecolors='black', s=40, label="TP")
if signal_sl: ax1.scatter(signal_sl, weekly_df.loc[signal_sl]["Close"], marker="x", color="black", s=40, label="SL")
ax1.set_title("Obchody na grafu")
ax1.legend()
ax1.grid(True, alpha=0.2)

# Graf 2: Equity + Drawdown
color = 'tab:green'
ax2.set_ylabel('Kapitál (USD)', color=color)
ax2.plot(equity_datumy, equity_historie, color=color, linewidth=2, label="Equity")
ax2.tick_params(axis='y', labelcolor=color)
ax2.grid(True, alpha=0.2)

# Přidáme Drawdown oblast červeně pod vodou
ax2_dd = ax2.twinx()  
ax2_dd.set_ylabel('Drawdown %', color='tab:red')
# Musíme zarovnat délky pro fill_between (použijeme indexy z equity_datumy)
# Vytvoříme pomocnou sérii pro graf drawdownu v čase
dd_series = pd.Series(index=weekly_df.index, data=0.0)
# Namapujeme drawdown hodnoty na správné datumy
equity_dates_pd = pd.to_datetime(equity_datumy)
dd_values = drawdown.values
ax2_dd.fill_between(equity_dates_pd, dd_values, 0, color='red', alpha=0.15, label="Drawdown")
ax2_dd.tick_params(axis='y', labelcolor='tab:red')
ax2_dd.set_ylim(-100, 5) # Aby graf drawdownu nezabíral celou výšku

plt.title("Vývoj kapitálu a Drawdown")
plt.show()