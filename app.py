import streamlit as st
import pandas as pd

st.set_page_config(page_title="Kalkulator Masy Aluminium", layout="centered")
st.title("⚖️ Kalkulator Dostaw Aluminium")

SHEET_ID = "1iXlPar8-AnWVJiZHjkU2muf6dwJnGvLvCZqxaJG2OAE"
GID = "1361838733"
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

@st.cache_data(ttl=60)
def load_data():
    # 1. Wczytujemy surowe dane bez nagłówków
    raw_df = pd.read_csv(url, header=None)
    
    # 2. Szukamy wiersza, w którym jest słowo "WYTOP" lub Twoja pierwsza firma
    # Jeśli nie znajdziemy, bierzemy dane od drugiego wiersza (indeks 1)
    start_row = 0
    for i, row in raw_df.iterrows():
        if 'WYTOP' in str(row[0]).upper() or 'ALCOA' in str(row[0]).upper():
            start_row = i + 1
            break
            
    # 3. Wycinamy dane od znalezionego miejsca i bierzemy 4 kolumny
    df = raw_df.iloc[start_row:, :4].copy()
    df.columns = ['FIRMA', 'STOP', 'SREDNICA', 'MASA_1MB']
    
    # 4. Wypełnianie pustych pól (Forward Fill) - kluczowe dla tabel przestawnych
    df['FIRMA'] = df['FIRMA'].ffill()
    df['STOP'] = df['STOP'].ffill()
    
    # 5. Czyszczenie liczb (zamiana przecinków i usuwanie znaków tekstowych)
    for col in ['SREDNICA', 'MASA_1MB']:
        df[col] = df[col].astype(str).str.replace(',', '.')
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 6. Usuwamy tylko wiersze, gdzie nie ma liczb w kolumnie MASA (np. puste końcówki arkusza)
    df = df.dropna(subset=['MASA_1MB']).reset_index(drop=True)
    
    return df

try:
    df = load_data()

    if df.empty:
        st.error("Baza danych jest pusta!")
        st.write("Program nie znalazł danych. Sprawdź, czy Twoja tabela przestawna na pewno jest w arkuszu o GID: 1361838733.")
    else:
        # --- SIDEBAR ---
        st.sidebar.header("Ustawienia")
        
        firmy = sorted(df['FIRMA'].unique().tolist())
        firma = st.sidebar.selectbox("1. Wybierz firmę", ["Wybierz..."] + firmy)
        
        if firma != "Wybierz...":
            df_firma = df[df['FIRMA'] == firma]
            stopy = sorted(df_firma['STOP'].unique().tolist())
            stop = st.sidebar.selectbox("2. Wybierz stop (INDEX)", ["Wybierz..."] + stopy)
            
            if stop != "Wybierz...":
                df_stop = df_firma[df_firma['STOP'] == stop]
                srednice = sorted(df_stop['SREDNICA'].unique().tolist())
                srednica = st.sidebar.selectbox("3. Wybierz średnicę (BILLET)", srednice)
                
                # Pobranie wyniku
                row = df_stop[df_stop['SREDNICA'] == srednica]
                if not row.empty:
                    masa_1mb = row['MASA_1MB'].values[0]
                    
                    # --- GŁÓWNY PANEL ---
                    st.success(f"Parametry: **{firma} | {stop} | ø{srednica}**")
                    st.metric("Masa jednostkowa", f"{masa_1mb:.3f} kg/mb")
                    
                    st.subheader("Kalkulacja")
                    szt_7 = st.number_input("Ilość sztuk (7mb)", min_value=0, step=1)
                    
                    # Dodatkowe wałki
                    dodatkowe = st.expander("Dodaj inne długości (opcjonalnie)")
                    with dodatkowe:
                        c1, c2 = st.columns(2)
                        dl_x = c1.number_input("Długość (mb)", min_value=0.0, step=0.1)
                        il_x = c2.number_input("Ilość (szt)", min_value=0, step=1)
                    
                    suma_kg = (szt_7 * 7 * masa_1mb) + (dl_x * il_x * masa_1mb)
                    st.divider()
                    st.metric("TEORETYCZNA MASA NETTO", f"{suma_kg:.2f} kg")

    # Podgląd dla Ciebie, żebyś widział co się dzieje "pod maską"
    with st.expander("Diagnostyka danych"):
        st.write("Wczytane wiersze:")
        st.dataframe(df.head(20))

except Exception as e:
    st.error(f"Błąd krytyczny: {e}")
