import streamlit as st
import pandas as pd

# Konfiguracja strony
st.set_page_config(page_title="Kalkulator Masy Aluminium", layout="centered")

st.title("⚖️ Kalkulator Dostaw Aluminium")

# 1. Dane z Twojego arkusza
SHEET_ID = "1iXlPar8-AnWVJiZHjkU2muf6dwJnGvLvCZqxaJG2OAE"
GID = "1361838733"
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

@st.cache_data(ttl=600)  # Odświeżaj dane co 10 minut
def load_data():
    # Wczytujemy dane
    df = pd.read_csv(url)
    
    # CZYSZCZENIE DANYCH:
    # 1. Konwertujemy BILLET na liczby, błędy (np. tekst) zamieniamy na puste pola (NaN)
    df['BILLET'] = pd.to_numeric(df['BILLET'], errors='coerce')
    
    # 2. Zakładamy, że ostatnia kolumna to Masa/1mb - czyścimy ją tak samo
    masa_col = df.columns[-1]
    df[masa_col] = pd.to_numeric(df[masa_col], errors='coerce')
    
    # 3. Usuwamy wiersze, które mają puste wartości (np. puste linie w Excelu lub wiersz "Suma")
    df = df.dropna(subset=['WYTOP/FIRMA', 'INDEKS', 'BILLET', masa_col])
    
    # 4. Upewniamy się, że nazwy firm i indeksów są traktowane jako tekst do sortowania
    df['WYTOP/FIRMA'] = df['WYTOP/FIRMA'].astype(str)
    df['INDEKS'] = df['INDEKS'].astype(str)
    
    return df

try:
    df = load_data()

    # --- SEKCJA WYBORU (SIDEBAR) ---
    st.sidebar.header("Parametry dostawy")
    
    # Wybór firmy
    firmy = sorted(df['WYTOP/FIRMA'].unique())
    firma = st.sidebar.selectbox("Wybierz firmę", firmy)
    
    # Filtrowanie i wybór stopu
    df_firma = df[df['WYTOP/FIRMA'] == firma]
    stopy = sorted(df_firma['INDEKS'].unique())
    stop = st.sidebar.selectbox("Wybierz stop (INDEKS)", stopy)
    
    # Filtrowanie i wybór średnicy
    df_stop = df_firma[df_firma['INDEKS'] == stop]
    srednice = sorted(df_stop['BILLET'].unique())
    srednica = st.sidebar.selectbox("Wybierz średnicę (BILLET)", srednice)
    
    # Pobranie masy na 1mb
    masa_col = df.columns[-1]
    masa_1mb = df_stop[df_stop['BILLET'] == srednica][masa_col].values[0]
    
    st.info(f"Wybrany materiał: **{firma} | {stop} | ø{srednica}** \n\nŚrednia masa z Twoich dostaw: **{masa_1mb:.3f} kg/mb**")

    # --- SEKCJA OBLICZEŃ ---
    st.subheader("Ilości w dostawie")
    
    # Standardowe wałki (7mb)
    col1, col2 = st.columns(2)
    with col1:
        sztuki_7 = st.number_input("Ilość sztuk (7mb)", min_value=0, step=1, value=0)
    with col2:
        masa_standard = sztuki_7 * 7 * masa_1mb
        st.write("") 
        st.write("") 
        st.write(f"Masa: **{masa_standard:.2f} kg**")

    st.divider()

    # Obsługa dodatkowych (krótszych) wałków
    if 'extra_rows' not in st.session_state:
        st.session_state.extra_rows = []

    if st.button("➕ Dodaj inne długości"):
        st.session_state.extra_rows.append({"len": 0.0, "qty": 0})

    if st.button("🗑️ Wyczyść dodatkowe"):
        st.session_state.extra_rows = []
        st.rerun()

    total_extra_mass = 0.0
    
    for i, row in enumerate(st.session_state.extra_rows):
        c1, c2, c3 = st.columns([2, 2, 2])
        with c1:
            row['len'] = st.number_input(f"Długość (mb) #{i+1}", key=f"len_{i}", min_value=0.0, step=0.01)
        with c2:
            row['qty'] = st.number_input(f"Ilość (szt) #{i+1}", key=f"qty_{i}", min_value=0, step=1)
        with c3:
            m_wiersz = row['len'] * row['qty'] * masa_1mb
            st.write(f"Masa #{i+1}:")
            st.write(f"**{m_wiersz:.2f} kg**")
        
        total_extra_mass += m_wiersz

    # --- WYNIK KOŃCOWY ---
    st.write("")
    st.markdown("---")
    masa_calkowita = masa_standard + total_extra_mass
    
    st.metric(label="TEORETYCZNA MASA NETTO CAŁEJ DOSTAWY", value=f"{masa_calkowita:.2f} kg")
    
    if st.button("🔄 Oblicz od nowa"):
        st.session_state.extra_rows = []
        st.rerun()

except Exception as e:
    st.error(f"Wystąpił błąd podczas przetwarzania danych.")
    st.info("Najczęstsza przyczyna: Tabela przestawna w Arkuszu Google zawiera puste wiersze lub sumy końcowe.")
    with st.expander("Szczegóły błędu dla programisty"):
        st.write(e)
