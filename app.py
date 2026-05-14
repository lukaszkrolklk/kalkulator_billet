import streamlit as st
import pandas as pd

st.set_page_config(page_title="Kalkulator Masy Aluminium", layout="centered")
st.title("⚖️ Kalkulator Dostaw Aluminium")

SHEET_ID = "1iXlPar8-AnWVJiZHjkU2muf6dwJnGvLvCZqxaJG2OAE"
GID = "1361838733"
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

@st.cache_data(ttl=60)
def load_data():
    # 1. Wczytujemy dane (pomijamy nagłówki, bo sami je nadamy)
    df = pd.read_csv(url, header=None)
    
    # 2. Szukamy wiersza, gdzie zaczynają się dane (omijamy napisy "Suma" itp.)
    # Bierzemy 4 kolumny
    df = df.iloc[:, :4]
    df.columns = ['FIRMA', 'STOP', 'SREDNICA', 'MASA_1MB']
    
    # 3. Wypełniamy puste nazwy Firm i Stopów (Forward Fill)
    df['FIRMA'] = df['FIRMA'].ffill()
    df['STOP'] = df['STOP'].ffill()
    
    # 4. NAPRAWA "NaN": Czyścimy kolumny liczbowe
    for col in ['SREDNICA', 'MASA_1MB']:
        # Zamieniamy wszystko na tekst, usuwamy spacje, zamieniamy przecinek na kropkę
        df[col] = df[col].astype(str).str.replace(',', '.').str.strip()
        # Wyciągamy tylko cyfry i kropkę (usuwamy np. "mm", cale, litery)
        df[col] = df[col].str.extract(r'(\d+\.?\d*)')[0]
        # Konwertujemy na prawdziwe liczby
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 5. Kluczowe: usuwamy wszystkie wiersze, które po czyszczeniu mają NaN (puste)
    df = df.dropna(subset=['FIRMA', 'STOP', 'SREDNICA', 'MASA_1MB'])
    
    # Usuwamy wiersze, gdzie Masa lub Średnica wynosi 0
    df = df[(df['SREDNICA'] > 0) & (df['MASA_1MB'] > 0)]
    
    return df

try:
    df = load_data()

    if df.empty:
        st.error("Baza danych jest pusta lub zawiera same błędy (NaN).")
        st.info("Sprawdź czy w arkuszu kolumny Średnica i Masa zawierają same liczby.")
    else:
        # --- SIDEBAR ---
        st.sidebar.header("Wybierz parametry")
        
        firmy = sorted(df['FIRMA'].unique().tolist())
        firma = st.sidebar.selectbox("1. Firma", ["Wybierz..."] + firmy)
        
        if firma != "Wybierz...":
            df_firma = df[df['FIRMA'] == firma]
            stopy = sorted(df_firma['STOP'].unique().tolist())
            stop = st.sidebar.selectbox("2. Stop (INDEX)", ["Wybierz..."] + stopy)
            
            if stop != "Wybierz...":
                df_stop = df_firma[df_firma['STOP'] == stop]
                # Sortujemy średnice od najmniejszej do największej
                srednice = sorted(df_stop['SREDNICA'].unique().tolist())
                srednica = st.sidebar.selectbox("3. Średnica (BILLET)", srednice)
                
                # Pobieranie wyniku
                row = df_stop[df_stop['SREDNICA'] == srednica]
                if not row.empty:
                    masa_1mb = row['MASA_1MB'].values[0]
                    
                    # --- PANEL GŁÓWNY ---
                    st.success(f"Wybrano: **{firma} | {stop} | ø{srednica}**")
                    st.write(f"Masa jednostkowa dla tego wyboru: **{masa_1mb:.3f} kg/mb**")
                    
                    st.subheader("Wprowadź ilość")
                    szt_7 = st.number_input("Ilość sztuk (standard 7mb)", min_value=0, step=1)
                    
                    if st.checkbox("Dodaj wałki o innej długości"):
                        c1, c2 = st.columns(2)
                        dl_x = c1.number_input("Długość (mb)", min_value=0.0, step=0.01, format="%.2f")
                        il_x = c2.number_input("Ilość (szt)", min_value=0, step=1)
                    else:
                        dl_x, il_x = 0.0, 0
                    
                    suma_kg = (szt_7 * 7 * masa_1mb) + (dl_x * il_x * masa_1mb)
                    st.divider()
                    st.metric("TEORETYCZNE SUMA MASY NETTO", f"{suma_kg:.2f} kg")

    # Podgląd diagnostyczny
    with st.expander("Podgląd przefiltrowanych danych"):
        st.dataframe(df)

except Exception as e:
    st.error(f"Wystąpił błąd: {e}")
