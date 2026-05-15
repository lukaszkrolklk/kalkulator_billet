import streamlit as st
import pandas as pd

# Konfiguracja strony
st.set_page_config(page_title="Kalkulator Masy Aluminium", layout="centered")

st.title("⚖️ Kalkulator Dostaw Aluminium")

# Google Sheet
SHEET_ID = "1iXlPar8-AnWVJiZHjkU2muf6dwJnGvLvCZqxaJG2OAE"

# Tabela przestawna
GID_PIVOT = "1361838733"
url_pivot = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_PIVOT}"

# Dane źródłowe
GID_SOURCE = "0"
url_source = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_SOURCE}"


@st.cache_data(ttl=300)
def load_pivot_data():
    df = pd.read_csv(url_pivot)

    df = df.iloc[:, :4]
    df.columns = ['FIRMA', 'STOP', 'SREDNICA', 'MASA_1MB']

    for col in ['SREDNICA', 'MASA_1MB']:
        df[col] = df[col].astype(str).str.replace(',', '.', regex=False).str.strip()
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.dropna(subset=['FIRMA', 'STOP', 'SREDNICA', 'MASA_1MB'])

    df['FIRMA'] = df['FIRMA'].astype(str).str.strip()
    df['STOP'] = df['STOP'].astype(str).str.strip()

    return df


@st.cache_data(ttl=300)
def load_source_data():
    df = pd.read_csv(url_source)

    df = df.iloc[:, :9]
    df.columns = [
        'INDEKS',
        'BILLET',
        'DLUGOSC',
        'FIRMA',
        'SZTUK',
        'KG',
        'MASA_1MB',
        'INDEX',
        'DATA'
    ]

    for col in ['BILLET', 'DLUGOSC', 'SZTUK', 'KG', 'MASA_1MB']:
        df[col] = df[col].astype(str).str.replace(',', '.', regex=False).str.strip()
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df['FIRMA'] = df['FIRMA'].astype(str).str.strip()
    df['INDEX'] = df['INDEX'].astype(str).str.strip()

    df = df.dropna(subset=['FIRMA', 'INDEX', 'BILLET', 'MASA_1MB'])

    return df


try:
    df = load_pivot_data()
    df_source = load_source_data()

    # --- SIDEBAR ---
    st.sidebar.header("Parametry dostawy")

    firmy = sorted(df['FIRMA'].unique())
    firma = st.sidebar.selectbox("Wybierz firmę", firmy)

    df_firma = df[df['FIRMA'] == firma]
    stopy = sorted(df_firma['STOP'].unique())
    stop = st.sidebar.selectbox("Wybierz stop (INDEKS)", stopy)

    df_stop = df_firma[df_firma['STOP'] == stop]
    srednice = sorted(df_stop['SREDNICA'].unique())
    srednica = st.sidebar.selectbox("Wybierz średnicę (BILLET)", srednice)

    masa_1mb = df_stop[df_stop['SREDNICA'] == srednica]['MASA_1MB'].values[0]

    st.info(
        f"Wybrany materiał: **{firma} | {stop} | ø{srednica}**  \n\n"
        f"Średnia masa z tabeli przestawnej: **{masa_1mb:.3f} kg/mb**"
    )

    # --- OBLICZENIA ---
    st.subheader("Ilości w dostawie")

    col1, col2 = st.columns(2)

    with col1:
        sztuki_7 = st.number_input("Ilość sztuk (7mb)", min_value=0, step=1, value=0)

    with col2:
        masa_standard = sztuki_7 * 7 * masa_1mb
        st.write("")
        st.write("")
        st.write(f"Masa: **{masa_standard:.0f} kg**")

    st.divider()

    if 'extra_rows' not in st.session_state:
        st.session_state.extra_rows = []

    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        if st.button("➕ Dodaj inne długości"):
            st.session_state.extra_rows.append({"len": 0.0, "qty": 0})
            st.rerun()

    with col_btn2:
        if st.button("🗑️ Wyczyść wszystko"):
            st.session_state.extra_rows = []
            st.rerun()

    total_extra_mass = 0.0
    total_extra_mb = 0.0

    for i, row in enumerate(st.session_state.extra_rows):
        c1, c2, c3 = st.columns([2, 2, 2])

        with c1:
            row['len'] = st.number_input(
                f"Długość (mb) #{i + 1}",
                key=f"len_{i}",
                min_value=0.0,
                step=0.01
            )

        with c2:
            row['qty'] = st.number_input(
                f"Ilość (szt) #{i + 1}",
                key=f"qty_{i}",
                min_value=0,
                step=1
            )

        with c3:
            m_wiersz = row['len'] * row['qty'] * masa_1mb
            st.write(f"Masa #{i + 1}:")
            st.write(f"**{m_wiersz:.0f} kg**")

        total_extra_mass += m_wiersz
        total_extra_mb += row['len'] * row['qty']

    st.markdown("---")

    laczne_mb = (sztuki_7 * 7) + total_extra_mb
    masa_calkowita = masa_standard + total_extra_mass

    # --- WIDEŁKI HISTORYCZNE ---
    hist = df_source[
        (df_source['FIRMA'] == firma) &
        (df_source['INDEX'] == stop) &
        (df_source['BILLET'] == srednica)
    ]

    st.metric(
        label="TEORETYCZNA MASA NETTO CAŁEJ DOSTAWY",
        value=f"{masa_calkowita:.0f} kg"
    )

    if laczne_mb > 0 and not hist.empty:
        min_1mb = hist['MASA_1MB'].min()
        avg_1mb = hist['MASA_1MB'].mean()
        max_1mb = hist['MASA_1MB'].max()

        masa_min = laczne_mb * min_1mb
        masa_avg_hist = laczne_mb * avg_1mb
        masa_max = laczne_mb * max_1mb

        odchylenie_minus = masa_calkowita - masa_min
        odchylenie_plus = masa_max - masa_calkowita

        st.subheader("📊 Widełki historyczne")

        st.info(
            f"Zakres na podstawie danych źródłowych:  \n\n"
            f"**{masa_min:.0f} kg – {masa_max:.0f} kg**  \n\n"
            f"Średnia historyczna: **{masa_avg_hist:.0f} kg**  \n\n"
            f"Odchylenie od wyniku teoretycznego: **-{odchylenie_minus:.0f} kg / +{odchylenie_plus:.0f} kg**  \n\n"
            f"Liczba pozycji historycznych: **{len(hist)}**"
        )

        with st.expander("Szczegóły masy 1 mb"):
            st.write(f"Minimalna masa 1 mb: **{min_1mb:.3f} kg/mb**")
            st.write(f"Średnia historyczna 1 mb: **{avg_1mb:.3f} kg/mb**")
            st.write(f"Maksymalna masa 1 mb: **{max_1mb:.3f} kg/mb**")
            st.write(f"Masa z tabeli przestawnej: **{masa_1mb:.3f} kg/mb**")

    elif laczne_mb == 0:
        st.warning("Wpisz ilość sztuk, aby policzyć widełki.")

    else:
        st.warning("Brak danych historycznych dla wybranej firmy, stopu i średnicy.")

except Exception as e:
    st.error("Problem z wczytaniem danych z Arkusza.")
    st.write("Sprawdź, czy arkusze mają właściwe kolumny i czy są dostępne jako CSV.")

    with st.expander("Szczegóły błędu"):
        st.write(e)
