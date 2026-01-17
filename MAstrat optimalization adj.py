import yfinance as yf
import pandas as pd
import numpy as np

# 1. Stáhneme data jen jednou
print("⏳ Stahuji data...")
raw_data = yf.download("BTC-USD", start="2010-01-01", progress=False)
if isinstance(raw_data.columns, pd.MultiIndex):
    raw_data.columns = raw_data.columns.droplevel(1)

# Převedeme na týdenní
weekly_base = pd.DataFrame()
weekly_base["Close"] = raw_data["Close"].resample('W').last()
weekly_base["Low"] = raw_data["Low"].resample('W').min()
weekly_base["High"] = raw_data["High"].resample('W').max()

# Seznam pro ukládání výsledků
vysledky = []

print("🚀 Spouštím realistickou optimalizaci (SMA 20 až 210)...")
print("-" * 60)

# 2. CYKLUS PRO RŮZNÉ SMA
for delka_sma in range(20, 210, 1): # Skáčeme po 2, ať je to rychlejší
    
    # Vytvoříme sloupec SMA v kopii dat
    df = weekly_base.copy()
    df["SMA"] = df["Close"].rolling(window=delka_sma).mean()
    df.dropna(inplace=True)
    
    # Reset proměnných pro simulaci
    kapital = 10000
    pozice = 0 
    setup_long = False
    setup_short = False
    
    moje_sl_cena = 0
    moje_tp_cena = 0
    
    wins = 0
    losses = 0
    
    # Rychlá simulace strategie
    for i in range(2, len(df)):
        low = df["Low"].iloc[i]
        high = df["High"].iloc[i]
        
        # KLÍČOVÁ ZMĚNA: Limitní cena je SMA z PŘEDCHOZÍHO týdne
        sma_limit = df["SMA"].iloc[i-1]
        
        # Kontext z minulosti
        cena_minule = df["Close"].iloc[i-1]
        sma_minule = df["SMA"].iloc[i-1]
        cena_predminule = df["Close"].iloc[i-2]
        sma_predminule = df["SMA"].iloc[i-2]
        
        trade_closed_this_week = False
        
        # A) ŘÍZENÍ POZICE (Kontrola SL/TP z minula)
        if pozice == 1: # Long
            if low <= moje_sl_cena:
                kapital *= 0.97 # SL 5%
                pozice = 0
                trade_closed_this_week = True
                losses += 1
            elif high >= moje_tp_cena:
                kapital *= 1.10 # TP 15%
                pozice = 0
                trade_closed_this_week = True
                wins += 1
                
        elif pozice == -1: # Short
            if high >= moje_sl_cena:
                kapital *= 0.97
                pozice = 0
                trade_closed_this_week = True
                losses += 1
            elif low <= moje_tp_cena:
                kapital *= 1.10
                pozice = 0
                trade_closed_this_week = True
                wins += 1

        # B) VSTUPY (Pokud nemáme pozici a nic jsme tento týden nezavřeli)
        if pozice == 0 and not trade_closed_this_week:
            # Setupy
            if cena_minule > sma_minule and cena_predminule > sma_predminule:
                setup_long = True; setup_short = False
            elif cena_minule < sma_minule and cena_predminule < sma_predminule:
                setup_short = True; setup_long = False
            else:
                setup_long = False; setup_short = False
            
            # Vstup Long
            if setup_long and low <= sma_limit:
                pozice = 1
                moje_entry_cena = sma_limit
                moje_sl_cena = moje_entry_cena * 0.97
                moje_tp_cena = moje_entry_cena * 1.10
                
                # Intra-bar check (okamžitá smrt nebo výhra)
                if low <= moje_sl_cena:
                    pozice = 0
                    kapital *= 0.97
                    losses += 1
                elif high >= moje_tp_cena:
                    pozice = 0
                    kapital *= 1.10
                    wins += 1

            # Vstup Short
            elif setup_short and high >= sma_limit:
                pozice = -1
                moje_entry_cena = sma_limit
                moje_sl_cena = moje_entry_cena * 1.05
                moje_tp_cena = moje_entry_cena * 0.85
                
                # Intra-bar check
                if high >= moje_sl_cena:
                    pozice = 0
                    kapital *= 0.97
                    losses += 1
                elif low <= moje_tp_cena:
                    pozice = 0
                    kapital *= 1.10
                    wins += 1

    # Výpočet statistik pro toto SMA
    celkem_obchodu = wins + losses
    winrate = (wins / celkem_obchodu * 100) if celkem_obchodu > 0 else 0
    zisk = kapital - 10000
    
    # Uložíme jen pokud proběhl aspoň jeden obchod
    if celkem_obchodu > 0:
        vysledky.append({
            "SMA": delka_sma, 
            "Konečný kapitál": int(kapital), 
            "Zisk %": round((zisk/10000)*100, 2),
            "Obchodů": celkem_obchodu,
            "WinRate %": round(winrate, 1)
        })

# 3. Seřadíme a vypíšeme
vysledky_df = pd.DataFrame(vysledky)
vysledky_df = vysledky_df.sort_values(by="Konečný kapitál", ascending=False)

print("\n" + "="*60)
print("🏆 REALISTICKÝ ŽEBŘÍČEK (Limit = SMA min. týdne) 🏆")
print("="*60)
print(vysledky_df.head(10).to_string(index=False))

# Zobrazíme i nejhorší, abychom viděli riziko
print("\n" + "="*60)
print("💀 NEJHORŠÍ NASTAVENÍ")
print("="*60)
print(vysledky_df.tail(5).to_string(index=False))