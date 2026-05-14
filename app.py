import streamlit as st
import pandas as pd

# Konfiguracja strony
st.set_page_config(page_title="Kalkulator Masy Aluminium", layout="centered")

st.title("⚖️ Kalkulator Dostaw Aluminium")

# 1. Ładowanie danych z Twojego arkusza (eksport do CSV)
# Wykorzystujemy link do Twojej tabeli przestawnej (gid=1361838733)
SHEET_ID = "1iXlPar8-AnWVJiZHjkU2muf6dwJnGvLvCZqxaJG2OAE"
GID = "1361838733"
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

@st.cache_data
def load_data():
    # Wczytujemy dane i czyścimy nazwy kolumn
    df = pd.read_csv(url)
    return df

try:
    df = load_data()

    # --- SEKCJA WYBORU ---
    st.sidebar.header("Parametry dostawy")
    
    # Wybór firmy
    firma = st.sidebar.selectbox("Wybierz firmę", sorted(df['WYTOP/FIRMA'].unique()))
    
    # Filtrowanie stopów dla wybranej firmy
    df_firma = df[df['WYTOP/FIRMA'] == firma]
    stop = st.sidebar.selectbox("Wybierz stop (INDEKS)", sorted(df_firma['INDEKS'].unique()))
    
    # Filtrowanie średnic dla wybranego stopu
    df_stop = df_firma[df_firma['INDEKS'] == stop]
    srednica = st.sidebar.selectbox("Wybierz średnicę (BILLET)", sorted(df_stop['BILLET'].unique()))
    
    # Pobranie masy na 1mb z tabeli
    masa_1mb = df_stop[df_stop['BILLET'] == srednica].iloc[0,-1] # Ostatnia kolumna to masa/1mb
    
    st.info(f"Wybrany materiał: **{firma} | {stop} | ø{srednica}** \nŚrednia masa: **{masa_1mb:.3f} kg/mb**")

    # --- SEKCJA OBLICZEŃ ---
    st.subheader("Ilości w dostawie")
    
    # Standardowe wałki (7mb)
    col1, col2 = st.columns(2)
    with col1:
        sztuki_7 = st.number_input("Ilość sztuk (7mb)", min_value=0, step=1, value=0)
    with col2:
        st.write("") # Odstęp
        st.write(f"Masa: {sztuki_7 * 7 * masa_1mb:.2f} kg")

    # Obsługa dodatkowych (krótszych) wałków
    if 'extra_rows' not in st.session_state:
        st.session_state.extra_rows = []

    if st.button("➕ Dodaj krótszy wałek"):
        st.session_state.extra_rows.append({"len": 0.0, "qty": 0})

    total_extra_mass = 0.0
    
    for i, row in enumerate(st.session_state.extra_rows):
        st.markdown(f"**Wałek niestandardowy nr {i+1}**")
        c1, c2, c3 = st.columns([3, 3, 1])
        with c1:
            row['len'] = st.number_input(f"Długość (mb)", key=f"len_{i}", min_value=0.0, step=0.1)
        with c2:
            row['qty'] = st.number_input(f"Ilość (szt)", key=f"qty_{i}", min_value=0, step=1)
        with c3:
            st.write("") # Miejsce na przycisk usuwania w przyszłości
        
        total_extra_mass += row['len'] * row['qty'] * masa_1mb

    # --- WYNIK KOŃCOWY ---
    st.divider()
    masa_calkowita = (sztuki_7 * 7 * masa_1mb) + total_extra_mass
    
    st.metric(label="TEORETYCZNA MASA NETTO", value=f"{masa_calkowita:.2f} kg")

except Exception as e:
    st.error(f"Błąd połączenia z danymi: {e}")
    st.write("Upewnij się, że arkusz jest udostępniony 'każdemu z linkiem'.")