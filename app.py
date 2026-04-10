import streamlit as st
import requests
import pandas as pd
import ta
import time
import warnings
warnings.filterwarnings('ignore')

# ── Sayfa ayarı ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BIST Teknik Tarayıcı",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
  .block-container { padding-top: 1.2rem; padding-bottom: 1rem; }
  .rozet {
    display: inline-block; padding: 3px 10px; border-radius: 5px;
    font-size: 12px; font-weight: 600; margin: 2px;
  }
  .baslik {
    background: linear-gradient(135deg, #cc0000, #8b0000);
    color: white; padding: 18px 24px; border-radius: 14px; margin-bottom: 18px;
  }
  div[data-testid="stExpander"] {
    border: 1px solid #e0e0e0 !important;
    border-radius: 10px !important;
    margin-bottom: 6px;
  }
</style>
""", unsafe_allow_html=True)

# ── API Key ───────────────────────────────────────────────────────────────────
try:
    API_KEY = st.secrets["TWELVEDATA_API_KEY"]
except Exception:
    API_KEY = None

# ══════════════════════════════════════════════════════════════════════════════
# HİSSE LİSTELERİ
# ══════════════════════════════════════════════════════════════════════════════
ENDEKSLER = {
    "BIST 30": [
        'AKBNK','ARCLK','ASELS','BIMAS','DOHOL','EKGYO','EREGL','FROTO','GARAN',
        'GUBRF','HEKTS','ISCTR','KCHOL','KOZAL','MGROS','OYAKC','PETKM','PGSUS',
        'SAHOL','SISE','TAVHL','TCELL','THYAO','TKFEN','TOASO','TTKOM','TUPRS',
        'ULKER','VAKBN','YKBNK'
    ],
    "BIST 50": [
        'AKBNK','AKSEN','ARCLK','ASELS','BIMAS','CCOLA','DOHOL','EKGYO','ENKAI',
        'EREGL','FROTO','GARAN','GUBRF','HEKTS','ISCTR','ISGYO','KCHOL','KRDMD',
        'KOZAL','LOGO','MAVI','MGROS','OYAKC','PETKM','PGSUS','SAHOL','SISE',
        'SODA','TAVHL','TCELL','THYAO','TKFEN','TOASO','TTKOM','TUPRS','ULKER',
        'VAKBN','VESTL','YKBNK','ALARK','AEFES','CIMSA','DOAS','ENJSA','INDES',
        'KLNMA','SELEC','BRSAN','ODAS','SKBNK'
    ],
    "BIST 100": [
        'THYAO','GARAN','AKBNK','EREGL','SISE','KCHOL','BIMAS','SAHOL','PGSUS','TUPRS',
        'FROTO','TOASO','ASELS','TCELL','KOZAL','EKGYO','ISCTR','HEKTS','MGROS','DOHOL',
        'TAVHL','ARCLK','ULKER','PETKM','CCOLA','ENKAI','KRDMD','VAKBN','SODA','TTKOM',
        'AEFES','OYAKC','ALARK','AKSEN','YKBNK','LOGO','MAVI','BERA','ENJSA','VESTL',
        'CIMSA','EGEEN','NETAS','KARSN','KONTR','IPEKE','ISGYO','GOLTS','GLYHO','KLNMA',
        'AGHOL','ANACM','BRSAN','BRYAT','BTCIM','DOAS','EUPWR','GESAN','GUBRF','HATEK',
        'IMASM','INDES','ISDMR','ISFIN','KAREL','KARTN','KERVT','KRSUS',
        'MPARK','NTTUR','ODAS','REEDR','RNPOL','RYSAS','SELEC','SKBNK',
        'SOKM','TATGD','TKFEN','TKNSA','TMSN'
    ],
    "BIST TÜM (Geniş)": [
        'THYAO','GARAN','AKBNK','EREGL','SISE','KCHOL','BIMAS','SAHOL','PGSUS','TUPRS',
        'FROTO','TOASO','ASELS','TCELL','KOZAL','EKGYO','ISCTR','HEKTS','MGROS','DOHOL',
        'TAVHL','ARCLK','ULKER','PETKM','CCOLA','ENKAI','KRDMD','VAKBN','SODA','TTKOM',
        'AEFES','OYAKC','ALARK','AKSEN','YKBNK','LOGO','MAVI','BERA','ENJSA','VESTL',
        'CIMSA','EGEEN','NETAS','KARSN','KONTR','IPEKE','ISGYO','GOLTS','GLYHO','KLNMA',
        'AGHOL','ANACM','BRSAN','BRYAT','BTCIM','DOAS','EUPWR','GESAN','GUBRF','HATEK',
        'IMASM','INDES','ISDMR','ISFIN','KAREL','KARTN','KERVT','KRSUS',
        'MPARK','NTTUR','ODAS','REEDR','RNPOL','RYSAS','SELEC','SKBNK',
        'SOKM','TATGD','TKFEN','TKNSA','TMSN',
        'ACSEL','ADEL','ADESE','AGESA','AGROT','AHGAZ','AKCNS','AKFGY','AKGRT',
        'AKIS','AKSA','AKSGY','ALBRK','ALCAR','ALCTL','ALFAS','ALKIM','ALTIN',
        'ALYAG','ANELE','ANGYO','ANHYT','ANSGR','ARDYZ','ARENA','ARSAN','ARZUM',
        'ASCEL','ASGYO','ASTOR','ATAKP','ATGYO','AVGYO','AVHOL','AVOD','AVPGY',
        'AYCES','AYEN','AYES','AYDEM','AYGAZ','BAGFS','BALSU','BANVT','BASGZ',
        'BAYRK','BEYAZ','BFREN','BIENY','BINHO','BIOEN','BIZIM','BJKAS','BLCYT',
        'BMEKS','BNTAS','BOSSA','BORSK','BRSAN','BSOKE','BUCIM','BURCE','BURVA',
        'CANTE','CARFA','CASA','CEMAS','CEMTS','CLEBI','COPCL','CRDFA',
        'DARDL','DENGE','DERHL','DERIM','DESA','DEVA','DGATE','DGGYO','DIRIT',
        'DITAS','DMRGD','DNISI','DOBUR','DOCO','DOGUB','DOJOB','DOKTA','DORTS',
        'DPAZR','DRGYO','DURAN','DYOBY','DZGYO','ECILC','ECZYT','EDIP',
        'EGGUB','EGPRO','EGSER','EKIZ','EKSUN','ELITE','EMKEL','EMNIS','ENERY',
        'ENSRI','ENTRA','EPLAS','ERBOS','ERSU','ESCAR','ESCOM','ESEN','ETILR',
        'EUREN','EYGYO','FADE','FENER','FITAS','FONET','FORTE','FRIGO',
        'GARFA','GEDIK','GEDZA','GENTS','GEREL','GLBMD','GLRYH','GMTAS',
        'GOKNR','GOODY','GOZDE','GRSEL','GSDDE','GSDHO','GSRAY','GULFA',
        'GUNDG','HAEKO','HALKB','HDFGS','HEDEF','HKTM','HLGYO','HOROZ',
        'HTTBT','HUNER','HURGZ','ICBCT','IDGYO','IEYHO','IHLGM','IHEVA',
        'IHLAS','IHYAY','IKTLL','IMEN','INTEM','ITTFK','IZFAS','IZINV','IZMDC',
        'JANTS','KATMR','KBORU','KFEIN','KGGYO','KIMMR','KLGYO','KLSER',
        'KMPUR','KNFRT','KONYA','KOPOL','KORDS','KRDMA','KRDMB','KRPLS',
        'KSTUR','KTLEV','KURTL','KUYAS','LIDER','LILAK','LINK','LKMNH','LUKSK',
        'MAALT','MACKO','MAGEN','MAKIM','MAKTK','MANAS','MARBL','MARKA','MARTI',
        'MEDTR','MEGAP','MEGMT','MEKAG','MERKO','METRO','METUR','MIPAZ',
        'MNDRS','MOBTL','MOGAN','MRGYO','MRSHL','MSGYO','MTRKS','MZHLD',
        'NATEN','NIBAS','NTHOL','NTTUR','NUGYO','NUHCM','NWIN',
        'OBAMS','OFSYM','ONCSM','ONRYT','ORCAY','ORGE','OSTIM','OTKAR',
        'OYYAT','OZKGY','PAGYO','PAMEL','PAPIL','PARSN','PASEU','PATEK',
        'PCILT','PEGYO','PEKGY','PETUN','PINSU','PKART','PKENT','PLTUR',
        'PNLSN','POLHO','POLTK','PRZMA','PSDTC','PSGYO','QNBFB','QUAGR',
        'RALYH','RAYSG','RGYAS','RHEAG','RODRG','RTALB','RUBNS','RYGYO',
        'SAFKR','SAMAT','SANEL','SANFM','SANKO','SARKY','SASA','SAYAS',
        'SDTTR','SEGYO','SEYKM','SILVR','SKTAS','SMART','SNICA','SNKRN',
        'SNPAM','SOKM','SRVGY','SUMAS','SUNTK','SURGY','SUWEN',
        'TBORG','TDGYO','TEKTU','TERA','TIRE','TRCAS','TRETN','TRGYO',
        'TRILC','TSGYO','TTRAK','TUCLK','TULGA','TURGZ','TURGG','TURGY','TURSG',
        'UFUK','ULUFA','ULUSE','ULUUN','USAK','USDMR','VAKFN','VAKGY',
        'VANGD','VBTYZ','VERTU','VERUS','VKFYO',
        'YAPRK','YATAS','YAYLA','YBTAS','YEOTK','YESIL','YGGYO','YKSLN',
        'YONGA','YUNSA','YYAPI','ZEDUR','ZOREN','ZRGYO'
    ]
}
for k in ENDEKSLER:
    ENDEKSLER[k] = list(dict.fromkeys(ENDEKSLER[k]))

# ── Periyot tanımları ─────────────────────────────────────────────────────────
PERIYOT_MAP = {
    '1 Dakikalık':  {'interval': '1min',  'outputsize': 100, 'key': '1m'},
    '5 Dakikalık':  {'interval': '5min',  'outputsize': 100, 'key': '5m'},
    '15 Dakikalık': {'interval': '15min', 'outputsize': 100, 'key': '15m'},
    '1 Saatlik':    {'interval': '1h',    'outputsize': 120, 'key': '1h'},
    '4 Saatlik':    {'interval': '4h',    'outputsize': 120, 'key': '4h'},
    'Günlük':       {'interval': '1day',  'outputsize': 200, 'key': '1d'},
}

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
if 'ozel_listeler' not in st.session_state:
    st.session_state.ozel_listeler = {}

# ══════════════════════════════════════════════════════════════════════════════
# VERİ ÇEKME — TWELVE DATA
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=60)   # 1 dakika cache — gerçek zamanlı hissi
def veri_cek_td(ticker, interval, outputsize, api_key):
    """Twelve Data REST API ile OHLCV verisi çek"""
    try:
        symbol = f"{ticker}:XIST"
        url = "https://api.twelvedata.com/time_series"
        params = {
            "symbol":     symbol,
            "interval":   interval,
            "outputsize": outputsize,
            "apikey":     api_key,
            "format":     "JSON",
            "order":      "ASC",
        }
        r = requests.get(url, params=params, timeout=15)
        data = r.json()

        if data.get("status") == "error" or "values" not in data:
            return None, data.get("message", "Bilinmeyen hata")

        values = data["values"]
        if len(values) < 30:
            return None, "Yetersiz veri"

        df = pd.DataFrame(values)
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.set_index("datetime", inplace=True)
        df = df.rename(columns={
            "open": "Open", "high": "High",
            "low": "Low", "close": "Close", "volume": "Volume"
        })
        for col in ["Open","High","Low","Close","Volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df.dropna(inplace=True)
        return df, None

    except requests.exceptions.Timeout:
        return None, "Timeout"
    except Exception as e:
        return None, str(e)


@st.cache_data(ttl=60)
def toplu_fiyat_cek(tickers, api_key):
    """Twelve Data batch endpoint — tek istekle çok hisse fiyatı"""
    try:
        symbols = ",".join([f"{t}:XIST" for t in tickers])
        url = "https://api.twelvedata.com/price"
        params = {"symbol": symbols, "apikey": api_key}
        r = requests.get(url, params=params, timeout=20)
        data = r.json()
        sonuc = {}
        for ticker in tickers:
            key = f"{ticker}:XIST"
            if key in data and "price" in data[key]:
                sonuc[ticker] = float(data[key]["price"])
        return sonuc
    except Exception:
        return {}


# ══════════════════════════════════════════════════════════════════════════════
# İNDİKATÖR HESAPLAMA
# ══════════════════════════════════════════════════════════════════════════════
def hesapla_indiktorler(df):
    if len(df) < 30:
        return None
    df = df.copy()
    c, h, l, v = df["Close"], df["High"], df["Low"], df["Volume"]
    df["RSI"]       = ta.momentum.RSIIndicator(c, window=14).rsi()
    macd_i          = ta.trend.MACD(c, window_slow=26, window_fast=12, window_sign=9)
    df["MACD"]      = macd_i.macd()
    df["MACD_sig"]  = macd_i.macd_signal()
    df["MACD_hist"] = macd_i.macd_diff()
    bb_i            = ta.volatility.BollingerBands(c, window=20, window_dev=2)
    df["BB_upper"]  = bb_i.bollinger_hband()
    df["BB_lower"]  = bb_i.bollinger_lband()
    df["BB_middle"] = bb_i.bollinger_mavg()
    stoch_i         = ta.momentum.StochasticOscillator(h, l, c, window=14, smooth_window=3)
    df["STOCH_K"]   = stoch_i.stoch()
    df["STOCH_D"]   = stoch_i.stoch_signal()
    df["EMA20"]     = ta.trend.EMAIndicator(c, window=20).ema_indicator()
    df["EMA50"]     = ta.trend.EMAIndicator(c, window=50).ema_indicator()
    df["MFI"]       = ta.volume.MFIIndicator(h, l, c, v, window=14).money_flow_index()
    return df

def skor_hesapla(row, close):
    skor = 50
    ind  = {}

    rsi = row.get("RSI")
    if pd.notna(rsi):
        ind["RSI"] = round(float(rsi), 1)
        if rsi < 25:   skor += 22
        elif rsi < 35: skor += 14
        elif rsi < 45: skor += 6
        elif rsi > 75: skor -= 22
        elif rsi > 65: skor -= 14
        elif rsi > 55: skor -= 6

    macd_h = row.get("MACD_hist")
    macd_v = row.get("MACD")
    if pd.notna(macd_h):
        ind["MACD_hist"] = round(float(macd_h), 4)
        ind["MACD_yon"]  = "↑" if macd_h > 0 else "↓"
        if macd_h > 0 and pd.notna(macd_v) and macd_v < 0:    skor += 18
        elif macd_h > 0:                                        skor += 10
        elif macd_h < 0 and pd.notna(macd_v) and macd_v > 0:  skor -= 18
        else:                                                    skor -= 10

    bb_up  = row.get("BB_upper")
    bb_low = row.get("BB_lower")
    bb_mid = row.get("BB_middle")
    if pd.notna(bb_up) and pd.notna(bb_low) and close:
        bw = float(bb_up) - float(bb_low)
        bp = (close - float(bb_low)) / bw if bw > 0 else 0.5
        ind["BB_alt"]  = round(float(bb_low), 2)
        ind["BB_orta"] = round(float(bb_mid), 2) if pd.notna(bb_mid) else None
        ind["BB_ust"]  = round(float(bb_up), 2)
        ind["BB_pct"]  = round(bp * 100, 1)
        if bp < 0.10:   skor += 20
        elif bp < 0.25: skor += 12
        elif bp < 0.35: skor += 5
        elif bp > 0.90: skor -= 20
        elif bp > 0.75: skor -= 12
        elif bp > 0.65: skor -= 5

    stk = row.get("STOCH_K")
    std = row.get("STOCH_D")
    if pd.notna(stk):
        ind["Stoch_K"] = round(float(stk), 1)
        ind["Stoch_D"] = round(float(std), 1) if pd.notna(std) else None
        if stk < 20:   skor += 14
        elif stk < 30: skor += 7
        elif stk > 80: skor -= 14
        elif stk > 70: skor -= 7

    ema20 = row.get("EMA20")
    ema50 = row.get("EMA50")
    if pd.notna(ema20) and pd.notna(ema50) and close:
        e20, e50 = float(ema20), float(ema50)
        ind["EMA20"] = round(e20, 2)
        ind["EMA50"] = round(e50, 2)
        if close > e20 > e50:
            ind["EMA_trend"] = "↑ Yükseliş"; skor += 10
        elif close < e20 < e50:
            ind["EMA_trend"] = "↓ Düşüş";   skor -= 10
        else:
            ind["EMA_trend"] = "→ Nötr"

    mfi = row.get("MFI")
    if pd.notna(mfi):
        ind["MFI"] = round(float(mfi), 1)
        if mfi < 20:   skor += 10
        elif mfi < 30: skor += 5
        elif mfi > 80: skor -= 10
        elif mfi > 70: skor -= 5

    return max(0, min(100, round(skor))), ind

def skor_stil(skor):
    if skor >= 70: return "GÜÇLÜ AL",  "#0d6e3b", "#d4f4e5", "🟢"
    if skor >= 55: return "AL",         "#1a9653", "#e2f7ed", "🟩"
    if skor >= 40: return "NÖTR",       "#7a6300", "#fdf4c7", "🟡"
    if skor >= 25: return "SAT",        "#b83232", "#fde8e8", "🔴"
    return              "GÜÇLÜ SAT", "#8b1a1a", "#f9d0d0", "⛔"

def analiz_et(ticker, interval, outputsize, canli_fiyat=None):
    df, hata = veri_cek_td(ticker, interval, outputsize, API_KEY)
    if df is None:
        return None, hata
    df = hesapla_indiktorler(df)
    if df is None or len(df) < 2:
        return None, "İndikatör hesaplanamadı"
    try:
        son   = df.iloc[-1]
        prev  = df.iloc[-2]
        # Canlı fiyat varsa onu kullan, yoksa son mumu kullan
        close = canli_fiyat if canli_fiyat else float(son["Close"])
        skor, ind = skor_hesapla(son, close)
        return {
            "ticker":  ticker,
            "fiyat":   close,
            "son_mum": float(son["Close"]),
            "degisim": ((close - float(prev["Close"])) / float(prev["Close"])) * 100,
            "high":    float(son["High"]),
            "low":     float(son["Low"]),
            "volume":  float(son["Volume"]),
            "skor":    skor,
            "ind":     ind,
            "zaman":   son.name.strftime("%H:%M") if hasattr(son.name, "strftime") else "-",
        }, None
    except Exception as e:
        return None, str(e)

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ Ayarlar")

    # API key kontrolü
    if not API_KEY:
        st.error("⚠️ API key bulunamadı!\n\nStreamlit Cloud → Settings → Secrets bölümüne ekleyin:\n```\nTWELVEDATA_API_KEY = \"key\"\n```")
        st.stop()
    else:
        st.success("✅ API bağlantısı hazır")

    st.markdown("---")
    st.markdown("**📂 Hisse Grubu**")

    endeks_sec  = list(ENDEKSLER.keys())
    kayitli_sec = list(st.session_state.ozel_listeler.keys())
    ozel_sec    = ["➕ Özel Hisseler Gir"]
    ayrac       = ["─── Kayıtlı Listelerim ───"] if kayitli_sec else []

    tum_sec = endeks_sec + ayrac + kayitli_sec + ozel_sec
    grup_sec = st.selectbox("Grup", tum_sec, label_visibility="collapsed")

    hisseler_secilen = []

    if grup_sec in ENDEKSLER:
        hisseler_secilen = ENDEKSLER[grup_sec]
        st.caption(f"📊 {len(hisseler_secilen)} hisse")

    elif grup_sec in st.session_state.ozel_listeler:
        hisseler_secilen = st.session_state.ozel_listeler[grup_sec]
        st.caption(f"📋 {len(hisseler_secilen)} hisse · Kayıtlı")
        if st.button("🗑️ Bu listeyi sil", use_container_width=True):
            del st.session_state.ozel_listeler[grup_sec]
            st.rerun()

    elif grup_sec == "➕ Özel Hisseler Gir":
        girdi = st.text_area(
            "Hisse kodları",
            placeholder="OYAKC\nTHYAO\nGARAN",
            height=130,
            label_visibility="collapsed"
        )
        if girdi.strip():
            hisseler_secilen = list(dict.fromkeys([
                h.strip().upper().replace(".IS","").replace(":XIST","")
                for h in girdi.replace(",","\n").split("\n") if h.strip()
            ]))
            st.caption(f"✅ {len(hisseler_secilen)} hisse")

        with st.expander("💾 Listeyi kaydet"):
            liste_adi = st.text_input("Liste adı", placeholder="Portföyüm")
            if st.button("Kaydet", use_container_width=True):
                if liste_adi and hisseler_secilen:
                    st.session_state.ozel_listeler[liste_adi] = hisseler_secilen
                    st.success(f"✅ '{liste_adi}' kaydedildi!")
                    st.rerun()
                else:
                    st.error("Liste adı ve hisse girişi gerekli.")

    # ── Periyot ───────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**⏱️ Periyot**")
    periyot_sec = st.selectbox("Periyot", list(PERIYOT_MAP.keys()), label_visibility="collapsed")
    pconf = PERIYOT_MAP[periyot_sec]

    # ── Filtreler ─────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**🔽 Filtreler**")
    sadece_al = st.checkbox("Sadece AL sinyalleri (%55+)")
    min_skor  = st.slider("Minimum skor", 0, 100, 0, 5)

    st.markdown("---")
    tara_btn = st.button("🔍 TARA", use_container_width=True, type="primary")

    if st.session_state.ozel_listeler:
        st.markdown("---")
        st.markdown("**📋 Kayıtlı Listelerim**")
        for ad, h in st.session_state.ozel_listeler.items():
            st.caption(f"• {ad} ({len(h)} hisse)")

    st.markdown("---")
    st.caption("📡 Twelve Data · Gerçek Zamanlı · XIST\n\nCache: 1 dakika")

# ══════════════════════════════════════════════════════════════════════════════
# ANA SAYFA
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="baslik">
  <div style="font-size:22px;font-weight:700;">📈 BIST Teknik Tarayıcı</div>
  <div style="opacity:0.85;margin-top:4px;font-size:13px;">
    Gerçek Zamanlı · Twelve Data · RSI · MACD · Bollinger · Stoch · EMA · MFI
  </div>
</div>
""", unsafe_allow_html=True)

if not tara_btn:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        **Puan Tablosu**
        | Puan | Sinyal |
        |------|--------|
        | 70–100 | 🟢 Güçlü AL |
        | 55–70 | 🟩 AL |
        | 40–55 | 🟡 Nötr |
        | 25–40 | 🔴 SAT |
        | 0–25 | ⛔ Güçlü SAT |
        """)
    with col2:
        st.markdown("""
        **İndikatörler**
        - RSI(14)
        - MACD(12,26,9)
        - Bollinger(20,2)
        - Stochastic(14,3)
        - EMA 20 & 50
        - MFI(14)
        """)
    with col3:
        st.markdown("""
        **Endeks Grupları**
        - BIST 30 · BIST 50
        - BIST 100 · BIST TÜM
        - Kayıtlı özel listeler
        - Manuel hisse girişi
        """)
    with col4:
        st.markdown("""
        **Periyotlar**
        - 1dk · 5dk · 15dk
        - 1 Saatlik · 4 Saatlik
        - Günlük
        """)
    st.info("👈 Sol menüden grup ve periyot seçip **TARA** butonuna bas.")

    if st.session_state.ozel_listeler:
        st.markdown("---")
        st.markdown("### 📋 Kayıtlı Listelerim")
        for ad, h in st.session_state.ozel_listeler.items():
            st.markdown(f"**{ad}** ({len(h)} hisse): `{'`, `'.join(h[:8])}{'...' if len(h)>8 else ''}`")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# TARAMA
# ══════════════════════════════════════════════════════════════════════════════
if not hisseler_secilen:
    st.error("Lütfen sol menüden bir grup seçin veya hisse kodlarını girin.")
    st.stop()

if len(hisseler_secilen) > 100:
    st.warning(f"⚠️ {len(hisseler_secilen)} hisse taranacak. API rate limit nedeniyle ~{len(hisseler_secilen)//8} dakika sürebilir.")

# Önce batch ile canlı fiyatları çek (hızlı - tek istek)
st.info("📡 Canlı fiyatlar çekiliyor...")
canli_fiyatlar = {}
# Twelve Data batch max 120 sembol destekliyor
BATCH_SIZE = 100
for i in range(0, len(hisseler_secilen), BATCH_SIZE):
    batch = hisseler_secilen[i:i+BATCH_SIZE]
    canli_fiyatlar.update(toplu_fiyat_cek(batch, API_KEY))

sonuclar, hatalar = [], []
pb    = st.progress(0)
durum = st.empty()

for i, ticker in enumerate(hisseler_secilen):
    durum.caption(f"⏳ **{ticker}** analiz ediliyor... ({i+1}/{len(hisseler_secilen)})")
    canli = canli_fiyatlar.get(ticker)
    r, hata = analiz_et(ticker, pconf["interval"], pconf["outputsize"], canli)
    if r:
        sonuclar.append(r)
    else:
        hatalar.append(f"{ticker}: {hata}")
    pb.progress((i + 1) / len(hisseler_secilen))
    # Rate limit: Grow plan 55 istek/dakika → ~1.1 sn/istek güvenli
    time.sleep(1.2)

pb.empty()
durum.empty()

# Filtrele & sırala
filtreli = [r for r in sonuclar if r["skor"] >= min_skor]
if sadece_al:
    filtreli = [r for r in filtreli if r["skor"] >= 55]
filtreli.sort(key=lambda x: x["skor"], reverse=True)

# ── Özet ─────────────────────────────────────────────────────────────────────
st.markdown(f"### Sonuçlar — {grup_sec} · {periyot_sec} · {len(filtreli)} hisse")
c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("Başarılı",    len(sonuclar))
c2.metric("🟢 Güçlü AL", sum(1 for r in filtreli if r["skor"]>=70))
c3.metric("🟩 AL",        sum(1 for r in filtreli if 55<=r["skor"]<70))
c4.metric("🟡 Nötr",      sum(1 for r in filtreli if 40<=r["skor"]<55))
c5.metric("🔴 SAT",       sum(1 for r in filtreli if 25<=r["skor"]<40))
c6.metric("⛔ G.SAT",     sum(1 for r in filtreli if r["skor"]<25))

if hatalar:
    with st.expander(f"⚠️ {len(hatalar)} hissede sorun"):
        for h in hatalar[:20]:
            st.caption(h)

st.markdown("---")

sc1, sc2 = st.columns([2,4])
with sc1:
    siralama = st.selectbox("Sırala", [
        "Puan (Yüksek→Düşük)","Puan (Düşük→Yüksek)","Değişim %","İsim A-Z"
    ])
with sc2:
    filtre2 = st.selectbox("Göster", [
        "Tümü","Sadece AL & Güçlü AL","Sadece Nötr","Sadece SAT & Güçlü SAT"
    ])

if siralama == "Puan (Düşük→Yüksek)":    filtreli.sort(key=lambda x: x["skor"])
elif siralama == "Değişim %":              filtreli.sort(key=lambda x: x["degisim"], reverse=True)
elif siralama == "İsim A-Z":               filtreli.sort(key=lambda x: x["ticker"])

if filtre2 == "Sadece AL & Güçlü AL":       filtreli = [r for r in filtreli if r["skor"]>=55]
elif filtre2 == "Sadece Nötr":               filtreli = [r for r in filtreli if 40<=r["skor"]<55]
elif filtre2 == "Sadece SAT & Güçlü SAT":   filtreli = [r for r in filtreli if r["skor"]<40]

if not filtreli:
    st.info("Seçilen kriterlere uyan hisse bulunamadı.")
    st.stop()

# ── Kartlar ───────────────────────────────────────────────────────────────────
def rozet(label, val, bull):
    rc = "#0d6e3b" if bull is True else "#b83232" if bull is False else "#7a6300"
    rb = "#d4f4e5" if bull is True else "#fde8e8" if bull is False else "#fdf4c7"
    return f'<span class="rozet" style="background:{rb};color:{rc};">{label} {val}</span>'

for r in filtreli:
    etiket, fg, bg, emoji = skor_stil(r["skor"])
    ind = r["ind"]
    deg_renk = "green" if r["degisim"] >= 0 else "red"
    deg_str  = f"+{r['degisim']:.2f}%" if r["degisim"] >= 0 else f"{r['degisim']:.2f}%"
    canli_badge = "🟡 Canlı" if r["fiyat"] != r["son_mum"] else "📊 Mum"

    with st.expander(
        f"{emoji} **{r['ticker']}** — {r['fiyat']:.2f} TL  :{deg_renk}[{deg_str}]  |  Skor: **{r['skor']}** ({etiket})  ·  {r['zaman']}",
        expanded=False
    ):
        col_sol, col_sag = st.columns([3,1])

        with col_sol:
            html = ""
            if "RSI" in ind:
                rv = ind["RSI"]
                html += rozet("RSI", rv, True if rv<45 else (False if rv>60 else None))
            if "MACD_yon" in ind:
                html += rozet("MACD", ind["MACD_yon"], ind["MACD_yon"]=="↑")
            if "BB_pct" in ind:
                bv  = ind["BB_pct"]
                lbl = "Alt Bant" if bv<35 else "Üst Bant" if bv>65 else "Orta Bant"
                html += rozet(f"BB {lbl}", f"%{bv}", True if bv<35 else (False if bv>65 else None))
            if "Stoch_K" in ind:
                sv = ind["Stoch_K"]
                html += rozet("STOCH", sv, True if sv<30 else (False if sv>70 else None))
            if "EMA_trend" in ind:
                et = ind["EMA_trend"]
                html += rozet("EMA", et, True if "↑" in et else (False if "↓" in et else None))
            if "MFI" in ind:
                mv = ind["MFI"]
                html += rozet("MFI", mv, True if mv<30 else (False if mv>70 else None))
            html += f'<span class="rozet" style="background:#f0f4ff;color:#334;">{canli_badge}</span>'
            st.markdown(html, unsafe_allow_html=True)
            st.markdown("")

            detay = {}
            if "RSI"       in ind: detay["RSI(14)"]     = ind["RSI"]
            if "MACD_yon"  in ind: detay["MACD Yön"]    = ind["MACD_yon"]
            if "MACD_hist" in ind: detay["MACD Hist"]   = ind["MACD_hist"]
            if "BB_alt"    in ind:
                detay["BB Alt"]     = ind["BB_alt"]
                detay["BB Orta"]    = ind["BB_orta"]
                detay["BB Üst"]     = ind["BB_ust"]
                detay["BB Konum %"] = ind["BB_pct"]
            if "Stoch_K"   in ind: detay["Stoch K"]     = ind["Stoch_K"]
            if "Stoch_D"   in ind: detay["Stoch D"]     = ind["Stoch_D"]
            if "EMA20"     in ind:
                detay["EMA 20"] = ind["EMA20"]
                detay["EMA 50"] = ind["EMA50"]
            if "EMA_trend" in ind: detay["EMA Trend"]   = ind["EMA_trend"]
            if "MFI"       in ind: detay["MFI(14)"]     = ind["MFI"]
            detay["Canlı Fiyat"]   = f"{r['fiyat']:.2f} TL"
            detay["Son Mum Kapanış"] = f"{r['son_mum']:.2f} TL"
            detay["Gün Yüksek"]    = f"{r['high']:.2f} TL"
            detay["Gün Düşük"]     = f"{r['low']:.2f} TL"
            detay["Hacim"]         = f"{r['volume']/1e6:.2f}M lot"
            detay["Son Güncelleme"] = r["zaman"]

            df_det = pd.DataFrame(list(detay.items()), columns=["İndikatör","Değer"])
            st.dataframe(df_det, use_container_width=True, hide_index=True,
                         height=min(len(detay)*36+40, 500))

        with col_sag:
            bar_renk = "#22c55e" if r["skor"]>=70 else "#4ade80" if r["skor"]>=55 else "#fbbf24" if r["skor"]>=40 else "#f87171"
            st.markdown(f"""
            <div style="text-align:center;padding:14px;">
              <div style="width:80px;height:80px;border-radius:50%;
                background:{bg};color:{fg};display:flex;align-items:center;
                justify-content:center;font-size:26px;font-weight:700;margin:0 auto;">
                {r['skor']}
              </div>
              <div style="font-size:13px;font-weight:700;color:{fg};margin-top:8px;">{etiket}</div>
              <div style="margin-top:14px;">
                <div style="font-size:10px;color:#999;margin-bottom:5px;">Sinyal Gücü</div>
                <div style="background:#eee;border-radius:4px;height:10px;">
                  <div style="width:{r['skor']}%;background:{bar_renk};height:10px;border-radius:4px;"></div>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:9px;color:#bbb;margin-top:2px;">
                  <span>0</span><span>50</span><span>100</span>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

# ── CSV İndir ─────────────────────────────────────────────────────────────────
st.markdown("---")
rows = []
for r in filtreli:
    etiket,_,_,_ = skor_stil(r["skor"])
    s = r["ind"]
    rows.append({
        "Hisse":          r["ticker"],
        "Canlı Fiyat":    round(r["fiyat"],2),
        "Değişim (%)":    round(r["degisim"],2),
        "Gün Yüksek":     round(r["high"],2),
        "Gün Düşük":      round(r["low"],2),
        "Skor":           r["skor"],
        "Sinyal":         etiket,
        "RSI(14)":        s.get("RSI","-"),
        "MACD Yön":       s.get("MACD_yon","-"),
        "BB Konum%":      s.get("BB_pct","-"),
        "BB Alt":         s.get("BB_alt","-"),
        "BB Üst":         s.get("BB_ust","-"),
        "Stoch K":        s.get("Stoch_K","-"),
        "EMA20":          s.get("EMA20","-"),
        "EMA50":          s.get("EMA50","-"),
        "EMA Trend":      s.get("EMA_trend","-"),
        "MFI(14)":        s.get("MFI","-"),
        "Güncelleme":     r["zaman"],
    })

df_exp = pd.DataFrame(rows)
c1, c2 = st.columns([1,3])
with c1:
    st.download_button(
        "📥 CSV İndir",
        data=df_exp.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"BIST_{grup_sec.replace(' ','_')}_{pconf['key']}.csv",
        mime="text/csv",
        use_container_width=True
    )
