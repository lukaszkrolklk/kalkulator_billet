import streamlit as st
import pandas as pd
from pathlib import Path

# ==================================================
# KONFIGURACJA STRONY
# ==================================================
st.set_page_config(
    page_title="Kalkulator Dostaw Aluminium",
    page_icon="⚖️",
    layout="centered"
)

# ==================================================
# CSS
# ==================================================
st.markdown("""
<style>

.logo-container {
    margin-top: 35px;
}

</style>
""", unsafe_allow_html=True)

# ==================================================
# LOGO
# ==================================================
LOGO_PATH = Path(__file__).parent / "logo.PNG"

# ==================================================
# NAGŁÓWEK
# ==================================================
c1, c2 = st.columns([1, 2])

with c1:

    st.markdown(
        '<div class="logo-container">',
        unsafe_allow_html=True
    )

    if LOGO_PATH.exists():

        st.image(
            str(LOGO_PATH),
            width=220
        )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

with c2:

    st.title(
        "Kalkulator Dostaw Aluminium"
    )

    st.caption(
        "Aliplast Aluminium Extrusion"
    )

st.divider()

# ==================================================
# GOOGLE SHEETS
# ==================================================
SHEET_ID = "1iXlPar8-AnWVJiZHjkU2muf6dwJnGvLvCZqxaJG2OAE"
GID = "1361838733"

url = (
    f"https://docs.google.com/spreadsheets/d/"
    f"{SHEET_ID}/export?format=csv&gid={GID}"
)

# ==================================================
# WCZYTYWANIE DANYCH
# ==================================================
@st.cache_data(ttl=60)
def load_data():

    df = pd.read_csv(
        url,
        header=None
    )

    # Pobieramy pierwsze 4 kolumny
    df = df.iloc[:, :4]

    df.columns = [
        "FIRMA",
        "STOP",
        "BILLET",
        "MASA_1MB"
    ]

    # Zamiana pustych tekstów
    df = df.replace(
        r"^\s*$",
        pd.NA,
        regex=True
    )

    # Usuwamy tylko nagłówki / sumy
    mask_usun = (
        df["FIRMA"]
        .astype(str)
        .str.contains(
            "suma|firma|wytop",
            case=False,
            na=False
        )
    )

    df = df[~mask_usun]

    # Forward fill
    df["FIRMA"] = df["FIRMA"].ffill()
    df["STOP"] = df["STOP"].ffill()

    # ==================================================
    # CZYSZCZENIE BILLET
    # ==================================================
    df["BILLET"] = (
        df["BILLET"]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .str.replace('"', "", regex=False)
        .str.strip()
    )

    df["BILLET"] = (
        df["BILLET"]
        .str.extract(r"(\d+\.?\d*)")[0]
    )

    df["BILLET"] = pd.to_numeric(
        df["BILLET"],
        errors="coerce"
    )

    # ==================================================
    # CZYSZCZENIE MASY
    # ==================================================
    df["MASA_1MB"] = (
        df["MASA_1MB"]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )

    df["MASA_1MB"] = (
        df["MASA_1MB"]
        .str.extract(r"(\d+\.?\d*)")[0]
    )

    df["MASA_1MB"] = pd.to_numeric(
        df["MASA_1MB"],
        errors="coerce"
    )

    # ==================================================
    # USUWANIE BŁĘDÓW
    # ==================================================
    df = df.dropna(
        subset=[
            "FIRMA",
            "STOP",
            "BILLET",
            "MASA_1MB"
        ]
    )

    df = df[
        (df["BILLET"] > 0)
        &
        (df["MASA_1MB"] > 0)
    ]

    return df

# ==================================================
# GŁÓWNA APLIKACJA
# ==================================================
try:

    df = load_data()

    if df.empty:

        st.error(
            "Brak danych w arkuszu."
        )

        st.stop()

    # ==================================================
    # WYBÓR PARAMETRÓW
    # ==================================================
    st.subheader(
        "Wybierz parametry"
    )

    col1, col2, col3 = st.columns(3)

    # ==================================================
    # FIRMA
    # ==================================================
    with col1:

        firmy = sorted(
            df["FIRMA"]
            .dropna()
            .unique()
            .tolist()
        )

        firma = st.selectbox(
            "Firma",
            ["Wybierz..."] + firmy
        )

    if firma != "Wybierz...":

        df_firma = df[
            df["FIRMA"] == firma
        ]

        # ==================================================
        # STOP
        # ==================================================
        with col2:

            stopy = sorted(
                df_firma["STOP"]
                .dropna()
                .unique()
                .tolist()
            )

            stop = st.selectbox(
                "Stop / Index",
                ["Wybierz..."] + stopy
            )

        if stop != "Wybierz...":

            df_stop = df_firma[
                df_firma["STOP"] == stop
            ]

            # ==================================================
            # BILLET
            # ==================================================
            with col3:

                billety = sorted(
                    df_stop["BILLET"]
                    .dropna()
                    .unique()
                    .tolist()
                )

                billet = st.selectbox(
                    "Billet",
                    billety,
                    format_func=lambda x: f'{x:g}"'
                )

            # ==================================================
            # MASA
            # ==================================================
            row = df_stop[
                df_stop["BILLET"] == billet
            ]

            if not row.empty:

                masa_1mb = row[
                    "MASA_1MB"
                ].values[0]

                st.divider()

                # ==================================================
                # PARAMETRY
                # ==================================================
                with st.container(border=True):

                    st.subheader(
                        "Wybrane parametry"
                    )

                    p1, p2, p3, p4 = st.columns(4)

                    p1.metric(
                        "Firma",
                        firma
                    )

                    p2.metric(
                        "Stop",
                        stop
                    )

                    p3.metric(
                        "Billet",
                        f'{billet:g}"'
                    )

                    p4.metric(
                        "Masa 1 mb",
                        f"{masa_1mb:.3f} kg"
                    )

                # ==================================================
                # ILOŚCI
                # ==================================================
                st.subheader(
                    "Wprowadź ilości"
                )

                with st.container(border=True):

                    szt_7 = st.number_input(
                        "Ilość sztuk standardowych 7 mb",
                        min_value=0,
                        step=1
                    )

                    dodaj = st.checkbox(
                        "Dodaj dodatkową długość"
                    )

                    if dodaj:

                        d1, d2 = st.columns(2)

                        with d1:

                            dl_x = st.number_input(
                                "Długość [mb]",
                                min_value=0.0,
                                step=0.01,
                                format="%.2f"
                            )

                        with d2:

                            il_x = st.number_input(
                                "Ilość sztuk",
                                min_value=0,
                                step=1
                            )

                    else:

                        dl_x = 0.0
                        il_x = 0

                # ==================================================
                # OBLICZENIA
                # ==================================================
                masa_standard = (
                    szt_7
                    * 7
                    * masa_1mb
                )

                masa_dodatkowa = (
                    dl_x
                    * il_x
                    * masa_1mb
                )

                suma_kg = (
                    masa_standard
                    + masa_dodatkowa
                )

                st.divider()

                # ==================================================
                # WYNIK
                # ==================================================
                with st.container(border=True):

                    st.subheader(
                        "Wynik"
                    )

                    st.metric(
                        label="TEORETYCZNA SUMA MASY NETTO",
                        value=f"{suma_kg:,.2f} kg".replace(",", " ")
                    )

                    tabela = pd.DataFrame(
                        {
                            "Pozycja": [
                                "Standard 7 mb",
                                "Dodatkowa długość",
                                "RAZEM"
                            ],
                            "Długość [mb]": [
                                7,
                                dl_x,
                                ""
                            ],
                            "Ilość [szt]": [
                                szt_7,
                                il_x,
                                szt_7 + il_x
                            ],
                            "Masa [kg]": [
                                round(masa_standard, 2),
                                round(masa_dodatkowa, 2),
                                round(suma_kg, 2)
                            ]
                        }
                    )

                    st.dataframe(
                        tabela,
                        use_container_width=True,
                        hide_index=True
                    )

    else:

        st.info(
            "Wybierz firmę, aby rozpocząć kalkulację."
        )

    # ==================================================
    # PODGLĄD DANYCH
    # ==================================================
    with st.expander(
        "Podgląd danych"
    ):

        st.dataframe(
            df,
            use_container_width=True
        )

except Exception as e:

    st.error(
        "Wystąpił błąd aplikacji."
    )

    st.exception(e)
