import yfinance as yf
import pandas as pd

# 1. Stáhneme data jen jednou
print("Stahuji a připravuji data...")
raw_data = yf.download("BTC-USD", start="2010-01-01", progress=False)
if isinstance(raw_data.columns, pd.MultiIndex):
    raw_data.columns = raw_data.columns.droplevel(1)

# Převedeme na týdenní
weekly_base = pd.DataFrame()
weekly_base["Close"] = raw_data["Close"].resample('W').last()
weekly_base["Low"] = raw_data["Low"].resample('W').min()
weekly_base["High"] = raw_data["High"].resample('W').max()

# Seznam výsledků
vysledky = []

print("Testuji různé délky SMA (to může chvilku trvat)...")

# 2. CYKLUS PRO RŮZNÉ SMA (Zkoušíme od 20 do 200 po kroku 10)
for delka_sma in range(20, 210, 1):
    
    # Vytvoříme kopii dat, abychom si je nerozbili
    df = weekly_base.copy()
    
    # Vypočítáme SMA pro tuto konkrétní délku
    df[f"SMA"] = df["Close"].rolling(window=delka_sma).mean()
    df.dropna(inplace=True)
    
    # Reset proměnných pro simulaci
    kapital = 10000
    pozice = 0 # 0, 1, -1
    setup_long = False
    setup_short = False
    moje_sl = 0
    moje_tp = 0
    
    # Rychlá smyčka strategie
    for i in range(2, len(df)):
        cena = df["Close"].iloc[i]
        low = df["Low"].iloc[i]
        high = df["High"].iloc[i]
        sma = df["SMA"].iloc[i]
        
        # Minulá data
        cena_minule = df["Close"].iloc[i-1]
        sma_minule = df["SMA"].iloc[i-1]
        cena_predminule = df["Close"].iloc[i-2]
        sma_predminule = df["SMA"].iloc[i-2]
        
        # A) Hledání vstupu
        if pozice == 0:
            # Setupy
            if cena_minule > sma_minule and cena_predminule > sma_predminule:
                setup_long = True; setup_short = False
            elif cena_minule < sma_minule and cena_predminule < sma_predminule:
                setup_short = True; setup_long = False
            
            # Rušení
            if setup_long and cena < sma: setup_long = False
            if setup_short and cena > sma: setup_short = False
            
            # Vstupy
            if setup_long and low <= sma:
                pozice = 1
                setup_long = False
                moje_sl = sma * 0.98
                moje_tp = sma * 1.10
            elif setup_short and high >= sma:
                pozice = -1
                setup_short = False
                moje_sl = sma * 1.03
                moje_tp = sma * 0.90
        
        # B) Řízení pozice
        elif pozice == 1: # Long
            if low <= moje_sl:
                kapital *= 0.98
                pozice = 0
            elif high >= moje_tp:
                kapital *= 1.10
                pozice = 0
                
        elif pozice == -1: # Short
            if high >= moje_sl:
                kapital *= 0.98
                pozice = 0
            elif low <= moje_tp:
                kapital *= 1.10
                pozice = 0

    # Uložíme výsledek pro toto SMA
    zisk = kapital - 10000
    vysledky.append({"SMA": delka_sma, "Konečný kapitál": int(kapital), "Zisk USD": int(zisk)})
    print(f"SMA {delka_sma}: {int(kapital)} USD")

# 3. Seřadíme výsledky a vypíšeme TOP 5
vysledky_df = pd.DataFrame(vysledky)
vysledky_df = vysledky_df.sort_values(by="Konečný kapitál", ascending=False)

print("\n" + "="*40)
print("🏆 ŽEBŘÍČEK NEJLEPŠÍCH NASTAVENÍ 🏆")
print("="*40)
print(vysledky_df.head(5).to_string(index=False))