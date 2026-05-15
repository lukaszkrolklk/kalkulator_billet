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
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)

    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=220)

    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.title("Kalkulator Dostaw Aluminium")
    st.caption("Aliplast Aluminium Extrusion")

st.divider()

# ==================================================
# GOOGLE SHEETS
# ==================================================
SHEET_ID = "1iXlPar8-AnWVJiZHjkU2muf6dwJnGvLvCZqxaJG2OAE"

GID_PIVOT = "1361838733"
GID_SOURCE = "0"

url_pivot = (
    f"https://docs.google.com/spreadsheets/d/"
    f"{SHEET_ID}/export?format=csv&gid={GID_PIVOT}"
)

url_source = (
    f"https://docs.google.com/spreadsheets/d/"
    f"{SHEET_ID}/export?format=csv&gid={GID_SOURCE}"
)

# ==================================================
# WCZYTYWANIE TABELI PRZESTAWNEJ
# ==================================================
@st.cache_data(ttl=60)
def load_data():

    df = pd.read_csv(
        url_pivot,
        header=None
    )

    df = df.iloc[:, :4]

    df.columns = [
        "FIRMA",
        "STOP",
        "BILLET",
        "MASA_1MB"
    ]

    df = df.replace(
        r"^\s*$",
        pd.NA,
        regex=True
    )

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

    df["FIRMA"] = df["FIRMA"].ffill()
    df["STOP"] = df["STOP"].ffill()

    df["BILLET"] = (
        df["BILLET"]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .str.replace('"', "", regex=False)
        .str.strip()
        .str.extract(r"(\d+\.?\d*)")[0]
    )

    df["BILLET"] = pd.to_numeric(
        df["BILLET"],
        errors="coerce"
    )

    df["MASA_1MB"] = (
        df["MASA_1MB"]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .str.strip()
        .str.extract(r"(\d+\.?\d*)")[0]
    )

    df["MASA_1MB"] = pd.to_numeric(
        df["MASA_1MB"],
        errors="coerce"
    )

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

    df["FIRMA"] = df["FIRMA"].astype(str).str.strip()
    df["STOP"] = df["STOP"].astype(str).str.strip()

    return df


# ==================================================
# WCZYTYWANIE DANYCH ŹRÓDŁOWYCH DO WIDEŁEK
# ==================================================
@st.cache_data(ttl=60)
def load_source_data():

    df = pd.read_csv(
        url_source,
        header=None
    )

    df = df.iloc[:, :9]

    df.columns = [
        "INDEKS",
        "BILLET",
        "DLUGOSC",
        "FIRMA",
        "SZTUK",
        "KG",
        "MASA_1MB",
        "INDEX",
        "DATA"
    ]

    df = df.replace(
        r"^\s*$",
        pd.NA,
        regex=True
    )

    mask_usun = (
        df["INDEKS"]
        .astype(str)
        .str.contains(
            "indeks|suma|billet|wytop|firma",
            case=False,
            na=False
        )
    )

    df = df[~mask_usun]

    df["FIRMA"] = df["FIRMA"].ffill()
    df["INDEX"] = df["INDEX"].ffill()

    df["BILLET"] = (
        df["BILLET"]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .str.replace('"', "", regex=False)
        .str.strip()
        .str.extract(r"(\d+\.?\d*)")[0]
    )

    df["BILLET"] = pd.to_numeric(
        df["BILLET"],
        errors="coerce"
    )

    df["MASA_1MB"] = (
        df["MASA_1MB"]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .str.strip()
        .str.extract(r"(\d+\.?\d*)")[0]
    )

    df["MASA_1MB"] = pd.to_numeric(
        df["MASA_1MB"],
        errors="coerce"
    )

    df = df.dropna(
        subset=[
            "FIRMA",
            "INDEX",
            "BILLET",
            "MASA_1MB"
        ]
    )

    df = df[
        (df["BILLET"] > 0)
        &
        (df["MASA_1MB"] > 0)
    ]

    df["FIRMA"] = df["FIRMA"].astype(str).str.strip()
    df["INDEX"] = df["INDEX"].astype(str).str.strip()

    return df


# ==================================================
# FORMAT KG
# ==================================================
def format_kg(value):
    return f"{value:,.0f} kg".replace(",", " ")


# ==================================================
# GŁÓWNA APLIKACJA
# ==================================================
try:

    df = load_data()
    df_source = load_source_data()

    if df.empty:
        st.error("Brak danych w arkuszu.")
        st.stop()

    # ==================================================
    # WYBÓR PARAMETRÓW
    # ==================================================
    st.subheader("Wybierz parametry")

    col1, col2, col3 = st.columns(3)

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

            row = df_stop[
                df_stop["BILLET"] == billet
            ]

            if not row.empty:

                masa_1mb = row["MASA_1MB"].values[0]

                st.divider()

                # ==================================================
                # PARAMETRY
                # ==================================================
                with st.container(border=True):

                    st.subheader("Wybrane parametry")

                    p1, p2, p3, p4 = st.columns(4)

                    p1.metric("Firma", firma)
                    p2.metric("Stop", stop)
                    p3.metric("Billet", f'{billet:g}"')
                    p4.metric("Masa 1 mb", f"{masa_1mb:.3f} kg")

                # ==================================================
                # ILOŚCI
                # ==================================================
                st.subheader("Wprowadź ilości")

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
                mb_standard = szt_7 * 7
                mb_dodatkowe = dl_x * il_x
                suma_mb = mb_standard + mb_dodatkowe

                masa_standard = mb_standard * masa_1mb
                masa_dodatkowa = mb_dodatkowe * masa_1mb
                suma_kg = masa_standard + masa_dodatkowa

                st.divider()

                # ==================================================
                # WYNIK
                # ==================================================
                with st.container(border=True):

                    st.subheader("Wynik")

                    st.metric(
                        label="TEORETYCZNA SUMA MASY NETTO",
                        value=format_kg(suma_kg)
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
                                round(masa_standard, 0),
                                round(masa_dodatkowa, 0),
                                round(suma_kg, 0)
                            ]
                        }
                    )

                    st.dataframe(
                        tabela,
                        use_container_width=True,
                        hide_index=True
                    )

                # ==================================================
                # WIDEŁKI HISTORYCZNE
                # ==================================================
                hist = df_source[
                    (df_source["FIRMA"] == firma)
                    &
                    (df_source["INDEX"] == stop)
                    &
                    (df_source["BILLET"] == billet)
                ]

                if suma_mb > 0:

                    with st.container(border=True):

                        st.subheader("Widełki historyczne")

                        if not hist.empty:

                            min_1mb = hist["MASA_1MB"].min()
                            avg_1mb = hist["MASA_1MB"].mean()
                            max_1mb = hist["MASA_1MB"].max()

                            masa_min = suma_mb * min_1mb
                            masa_avg = suma_mb * avg_1mb
                            masa_max = suma_mb * max_1mb

                            odchylenie_minus = suma_kg - masa_min
                            odchylenie_plus = masa_max - suma_kg

                            w1, w2, w3 = st.columns(3)

                            w1.metric(
                                "Minimum",
                                format_kg(masa_min)
                            )

                            w2.metric(
                                "Średnia historyczna",
                                format_kg(masa_avg)
                            )

                            w3.metric(
                                "Maksimum",
                                format_kg(masa_max)
                            )

                            st.info(
                                f"Zakres historyczny dla wybranego materiału: "
                                f"**{format_kg(masa_min)} – {format_kg(masa_max)}**"
                            )

                            st.write(
                                f"Odchylenie względem wyniku teoretycznego: "
                                f"**-{odchylenie_minus:.0f} kg / +{odchylenie_plus:.0f} kg**"
                            )

                            st.write(
                                f"Liczba pozycji historycznych: **{len(hist)}**"
                            )

                            with st.expander("Szczegóły masy 1 mb"):
                                st.write(f"Minimum 1 mb: **{min_1mb:.3f} kg/mb**")
                                st.write(f"Średnia historyczna 1 mb: **{avg_1mb:.3f} kg/mb**")
                                st.write(f"Maksimum 1 mb: **{max_1mb:.3f} kg/mb**")
                                st.write(f"Masa z tabeli przestawnej: **{masa_1mb:.3f} kg/mb**")

                        else:

                            st.warning(
                                "Brak danych historycznych dla wybranej firmy, stopu i billetu."
                            )

    else:

        st.info("Wybierz firmę, aby rozpocząć kalkulację.")

    # ==================================================
    # PODGLĄD DANYCH
    # ==================================================
    with st.expander("Podgląd danych z tabeli przestawnej"):

        st.dataframe(
            df,
            use_container_width=True
        )

    with st.expander("Podgląd danych źródłowych do widełek"):

        st.dataframe(
            df_source,
            use_container_width=True
        )

except Exception as e:

    st.error("Wystąpił błąd aplikacji.")
    st.exception(e)
