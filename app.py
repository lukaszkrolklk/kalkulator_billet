import streamlit as st
import pandas as pd

# Konfiguracja strony
st.set_page_config(page_title="Kalkulator Masy Aluminium", layout="centered")

st.title("⚖️ Kalkulator Dostaw Aluminium")

# 1. Dane z Twojego arkusza
SHEET_ID = "1iXlPar8-AnWVJiZHjkU2muf6dwJnGvLvCZqxaJG2OAE"
GID = "1361838733"
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

@st.cache_data(ttl=300)
def load_data():
    # Wczytujemy standardowo przecinkami
    df = pd.read_csv(url)
    
    # 2. Naprawa nazw kolumn - bierzemy pierwsze 4, nieważne jak się nazywają
    # To chroni przed błędami typu 'KeyError'
    df.columns = ['FIRMA', 'STOP', 'SREDNICA', 'MASA_1MB']
    
    # 3. Czyszczenie liczb - zamiana przecinków na kropki (częsty problem w PL Excelu)
    for col in ['SREDNICA', 'MASA_1MB']:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.replace(',', '.').str.strip()
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 4. Usuwamy puste wiersze i wiersz "Suma końcowa"
    df = df.dropna(subset=['FIRMA', 'STOP', 'SREDNICA', 'MASA_1MB'])
    
    # 5. Czyścimy tekst
    df['FIRMA'] = df['FIRMA'].astype(str).str.strip()
    df['STOP'] = df['STOP'].astype(str).str.strip()
    
    return df

try:
    df = load_data()

    # --- SEKCJA WYBORU (SIDEBAR) ---
    st.sidebar.header("Parametry dostawy")
    
    firmy = sorted(df['FIRMA'].unique())
    firma = st.sidebar.selectbox("Wybierz firmę", firmy)
    
    df_firma = df[df['FIRMA'] == firma]
    stopy = sorted(df_firma['STOP'].unique())
    stop = st.sidebar.selectbox("Wybierz stop (INDEKS)", stopy)
    
    df_stop = df_firma[df_firma['STOP'] == stop]
    srednice = sorted(df_stop['SREDNICA'].unique())
    srednica = st.sidebar.selectbox("Wybierz średnicę (BILLET)", srednice)
    
    # Wyciągamy wartość masy 1mb
    masa_1mb = df_stop[df_stop['SREDNICA'] == srednica]['MASA_1MB'].values[0]
    
    st.info(f"Wybrany materiał: **{firma} | {stop} | ø{srednica}** \n\nŚrednia masa: **{masa_1mb:.3f} kg/mb**")

    # --- SEKCJA OBLICZEŃ ---
    st.subheader("Ilości w dostawie")
    
    col1, col2 = st.columns(2)
    with col1:
        sztuki_7 = st.number_input("Ilość sztuk (7mb)", min_value=0, step=1, value=0)
    with col2:
        masa_standard = sztuki_7 * 7 * masa_1mb
        st.write("") 
        st.write("") 
        st.write(f"Masa: **{masa_standard:.2f} kg**")

    st.divider()

    # Obsługa dodatkowych wierszy
    if 'extra_rows' not in st.session_state:
        st.session_state.extra_rows = []

    if st.button("➕ Dodaj inne długości"):
        st.session_state.extra_rows.append({"len": 0.0, "qty": 0})

    if st.button("🗑️ Wyczyść wszystko"):
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

    st.markdown("---")
    masa_calkowita = masa_standard + total_extra_mass
    st.metric(label="TEORETYCZNA MASA NETTO CAŁEJ DOSTAWY", value=f"{masa_calkowita:.2f} kg")

except Exception as e:
    st.error("Problem z wczytaniem danych z Arkusza.")
    st.write("Sprawdź czy Twoja tabela przestawna ma dokładnie te 4 kolumny w tej kolejności.")
    with st.expander("Szczegóły błędu"):
        st.write(e)
