import streamlit as st
import pandas as pd

st.set_page_config(page_title="Kalkulator Masy Aluminium", layout="centered")
st.title("⚖️ Kalkulator Dostaw Aluminium")

SHEET_ID = "1iXlPar8-AnWVJiZHjkU2muf6dwJnGvLvCZqxaJG2OAE"
GID = "1361838733"
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

@st.cache_data(ttl=60)
def load_data():
    # 1. Wczytujemy dane
    df = pd.read_csv(url)
    
    # 2. Wybieramy tylko 4 pierwsze kolumny i nazywamy je
    df = df.iloc[:, :4]
    df.columns = ['FIRMA', 'STOP', 'SREDNICA', 'MASA_1MB']
    
    # 3. KLUCZOWA NAPRAWA: Wypełnianie pustych pól pod nazwą firmy i stopu (Forward Fill)
    # Jeśli Google Sheets zostawia puste pola pod nazwą firmy, ten kod je uzupełni
    df['FIRMA'] = df['FIRMA'].replace('', pd.NA).ffill()
    df['STOP'] = df['STOP'].replace('', pd.NA).ffill()
    
    # 4. Czyszczenie liczb
    for col in ['SREDNICA', 'MASA_1MB']:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.replace(',', '.').str.replace(r'[^\d.]', '', regex=True)
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 5. Usuwamy tylko te wiersze, gdzie NAPRAWDĘ nie ma danych liczbowych (średnicy lub masy)
    df = df.dropna(subset=['SREDNICA', 'MASA_1MB']).reset_index(drop=True)
    
    return df

try:
    df = load_data()

    # --- SEKCJA WYBORU (SIDEBAR) ---
    st.sidebar.header("Parametry dostawy")
    
    # Dodajemy "Wybierz..." na początku, żeby nie wypełniało automatycznie
    lista_firm = ["Wybierz firmę..."] + sorted(df['FIRMA'].unique().tolist())
    firma = st.sidebar.selectbox("1. Wybierz firmę", lista_firm)
    
    if firma != "Wybierz firmę...":
        df_firma = df[df['FIRMA'] == firma]
        
        lista_stopow = ["Wybierz stop..."] + sorted(df_firma['STOP'].unique().tolist())
        stop = st.sidebar.selectbox("2. Wybierz stop (INDEX)", lista_stopow)
        
        if stop != "Wybierz stop...":
            df_stop = df_firma[df_firma['STOP'] == stop]
            
            srednice = sorted(df_stop['SREDNICA'].unique().tolist())
            srednica = st.sidebar.selectbox("3. Wybierz średnicę (BILLET)", srednice)
            
            # Pobieranie wyniku
            wynik = df_stop[df_stop['SREDNICA'] == srednica]
            
            if not wynik.empty:
                masa_1mb = wynik['MASA_1MB'].values[0]
                
                # --- INTERFEJS GŁÓWNY ---
                st.info(f"Wybrano: **{firma} | {stop} | ø{srednica}**")
                st.metric("Średnia masa jednostkowa", f"{masa_1mb:.3f} kg/mb")
                
                st.subheader("Wpisz ilości")
                sztuki_7 = st.number_input("Ilość sztuk (7mb)", min_value=0, step=1)
                masa_std = sztuki_7 * 7 * masa_1mb
                
                if st.checkbox("Dodaj krótsze wałki"):
                    st.write("Wpisz wymiary niestandardowe:")
                    c1, c2 = st.columns(2)
                    dl_kr = c1.number_input("Długość (mb)", min_value=0.0, step=0.1, key="dl_k")
                    il_kr = c2.number_input("Ilość (szt)", min_value=0, step=1, key="il_k")
                    masa_kr = dl_kr * il_kr * masa_1mb
                else:
                    masa_kr = 0.0
                
                st.divider()
                st.metric("TEORETYCZNA MASA NETTO", f"{masa_std + masa_kr:.2f} kg")
    else:
        st.write("👈 Wybierz dostawcę z menu po lewej stronie, aby rozpocząć.")

    # Diagnostyka (zostawiamy, żebyś widział czy widzi wszystkie indeksy)
    with st.expander("Podgląd bazy danych (Diagnostyka)"):
        st.dataframe(df)

except Exception as e:
    st.error(f"Błąd: {e}")
