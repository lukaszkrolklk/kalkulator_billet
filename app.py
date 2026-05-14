import streamlit as st
import pandas as pd

st.set_page_config(page_title="Kalkulator Masy Aluminium", layout="centered")
st.title("⚖️ Kalkulator Dostaw Aluminium")

SHEET_ID = "1iXlPar8-AnWVJiZHjkU2muf6dwJnGvLvCZqxaJG2OAE"
GID = "1361838733"
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

@st.cache_data(ttl=60)
def load_data():
    # Wczytujemy dane - pomijamy pierwszy wiersz, jeśli jest pusty lub błędny
    df = pd.read_csv(url, header=0)
    
    # Jeśli wczytało się za mało kolumn, spróbujmy inaczej
    if df.shape[1] < 4:
         df = pd.read_csv(url, header=1) # Spróbuj od drugiego wiersza

    # BIERZEMY TYLKO 4 PIERWSZE KOLUMNY - to najważniejsze!
    df = df.iloc[:, :4]
    df.columns = ['FIRMA', 'STOP', 'SREDNICA', 'MASA_1MB']
    
    # Czyścimy liczby (przecinki na kropki)
    for col in ['SREDNICA', 'MASA_1MB']:
        df[col] = df[col].astype(str).str.replace(',', '.').str.replace(r'[^\d.]', '', regex=True)
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Usuwamy wiersze gdzie cokolwiek jest puste
    df = df.dropna().reset_index(drop=True)
    
    # Usuwamy spacje z tekstów
    df['FIRMA'] = df['FIRMA'].astype(str).str.strip()
    df['STOP'] = df['STOP'].astype(str).str.strip()
    
    return df

try:
    df = load_data()

    if df.empty:
        st.error("Baza danych jest pusta po wczytaniu!")
        st.write("Sprawdź czy w Arkuszu Google tabela przestawna zaczyna się od komórki A1.")
    else:
        # --- SEKCJA WYBORU ---
        st.sidebar.header("Parametry dostawy")
        
        firmy = sorted(df['FIRMA'].unique())
        firma = st.sidebar.selectbox("Wybierz firmę", firmy)
        
        df_firma = df[df['FIRMA'] == firma]
        stopy = sorted(df_firma['STOP'].unique())
        stop = st.sidebar.selectbox("Wybierz stop", stopy)
        
        df_stop = df_firma[df_firma['STOP'] == stop]
        srednice = sorted(df_stop['SREDNICA'].unique())
        srednica = st.sidebar.selectbox("Wybierz średnicę", srednice)
        
        wynik = df_stop[df_stop['SREDNICA'] == srednica]

        if not wynik.empty:
            masa_1mb = wynik['MASA_1MB'].values[0]
            st.success(f"Masa: **{masa_1mb:.3f} kg/mb**")
            
            sztuki = st.number_input("Ilość sztuk (7mb)", min_value=0, value=0)
            st.metric("Masa całkowita", f"{sztuki * 7 * masa_1mb:.2f} kg")
        else:
            st.warning("Nie dopasowano masy dla tych parametrów.")

    # DIAGNOSTYKA - rozwiń to na stronie, żeby zobaczyć co widzi program
    with st.expander("Podgląd bazy (Diagnostyka)"):
        st.write("Tak wyglądają dane, które pobrał program:")
        st.dataframe(df.head(10))

except Exception as e:
    st.error(f"Błąd krytyczny: {e}")
