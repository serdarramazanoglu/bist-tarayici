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
  .rozet { display:inline-block; padding:3px 10px; border-radius:5px;
    font-size:12px; font-weight:600; margin:2px; }
  .baslik { background:linear-gradient(135deg,#cc0000,#8b0000);
    color:white; padding:18px 24px; border-radius:14px; margin-bottom:18px; }
  div[data-testid="stExpander"] {
    border:1px solid #e0e0e0 !important; border-radius:10px !important; margin-bottom:6px; }
  .plan-kutu { border-radius:10px; padding:12px 16px; margin-bottom:8px; font-size:13px; }
</style>
""", unsafe_allow_html=True)

# ── API Key ───────────────────────────────────────────────────────────────────
try:
    API_KEY = st.secrets["TWELVEDATA_API_KEY"]
except Exception:
    API_KEY = None

# ══════════════════════════════════════════════════════════════════════════════
# PLAN TANIMLARI
# ══════════════════════════════════════════════════════════════════════════════
PLANLAR = {
    "Ücretsiz (8 istek/dk)": {
        "rate_per_min": 8,
        "sleep":        8.0,   # 60/8 = 7.5sn, biraz marj
        "batch_size":   6,     # güvenli batch
        "aciklama":     "Ücretsiz · Yavaş ama gerçek veri · Test için ideal"
    },
    "Grow ($29/ay — 55 istek/dk)": {
        "rate_per_min": 55,
        "sleep":        1.2,
        "batch_size":   50,
        "aciklama":     "Ücretli · Hızlı · Tüm BIST hisseleri"
    },
    "Pro ($99/ay — 610 istek/dk)": {
        "rate_per_min": 610,
        "sleep":        0.2,
        "batch_size":   100,
        "aciklama":     "Ücretli · Çok hızlı · WebSocket destekli"
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# HİSSE LİSTELERİ
# ══════════════════════════════════════════════════════════════════════════════
ENDEKSLER = {
    "BIST 30 (Test için önerilir)": [
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
        'BMEKS','BNTAS','BOSSA','BORSK','BSOKE','BUCIM','BURCE','BURVA',
        'CANTE','CARFA','CASA','CEMAS','CEMTS','CLEBI','COPCL','CRDFA',
        'DARDL','DENGE','DERHL','DERIM','DESA','DEVA','DGATE','DGGYO','DIRIT',
        'DITAS','DMRGD','DNISI','DOBUR','DOCO','DOGUB','DOJOB','DOKTA','DORTS',
        'DPAZR','DRGYO','DURAN','DYOBY','DZGYO','ECILC','ECZYT','EDIP',
        'EGGUB','EGPRO','EGSER','EKIZ','EKSUN','ELITE','EMKEL','EMNIS','ENERY',
        'ENSRI','ENTRA','EPLAS','ERBOS','ERSU','ESCAR','ESCOM','ESEN','ETILR',
        'EUREN','EYGYO','FADE','FENER','FITAS','FONET','FORTE','FRIGO',
        'GARFA','GEDIK','GEDZA','GENTS','GEREL','GLBMD','GLRYH','GMTAS',
        'GOKNR','GOODY','GOZDE','GRSEL','GSDDE','GSDHO','GSRAY','GULFA',
        'HAEKO','HALKB','HDFGS','HEDEF','HKTM','HLGYO','HOROZ','HTTBT','HUNER',
        'ICBCT','IDGYO','IEYHO','IHLGM','IHEVA','IHLAS','IHYAY','IKTLL',
        'IMEN','INTEM','ITTFK','IZFAS','IZINV','IZMDC','JANTS','KATMR','KBORU',
        'KFEIN','KIMMR','KLGYO','KLSER','KMPUR','KNFRT','KONYA','KOPOL','KORDS',
        'KRDMA','KRDMB','KRPLS','KSTUR','KTLEV','KURTL','KUYAS',
        'LIDER','LILAK','LINK','LKMNH','LUKSK','MAALT','MACKO','MAGEN','MAKIM',
        'MAKTK','MANAS','MARBL','MARKA','MARTI','MEDTR','MEGAP','MEGMT','MEKAG',
        'MERKO','METRO','METUR','MIPAZ','MNDRS','MOBTL','MOGAN','MRGYO','MRSHL',
        'MSGYO','MTRKS','MZHLD','NATEN','NIBAS','NTHOL','NUGYO','NUHCM','NWIN',
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
        'VANGD','VBTYZ','VERTU','VERUS','VKFYO','YAPRK','YATAS','YAYLA',
        'YBTAS','YEOTK','YESIL','YGGYO','YKSLN','YONGA','YUNSA','YYAPI',
        'ZEDUR','ZOREN','ZRGYO'
    ]
}
for k in ENDEKSLER:
    ENDEKSLER[k] = list(dict.fromkeys(ENDEKSLER[k]))

PERIYOT_MAP = {
    '1 Dakikalık':  {'interval': '1min',  'outputsize': 100, 'key': '1m'},
    '5 Dakikalık':  {'interval': '5min',  'outputsize': 100, 'key': '5m'},
    '15 Dakikalık': {'interval': '15min', 'outputsize': 100, 'key': '15m'},
    '1 Saatlik':    {'interval': '1h',    'outputsize': 120, 'key': '1h'},
    '4 Saatlik':    {'interval': '4h',    'outputsize': 120, 'key': '4h'},
    'Günlük':       {'interval': '1day',  'outputsize': 200, 'key': '1d'},
}

if 'ozel_listeler' not in st.session_state:
    st.session_state.ozel_listeler = {}

# ══════════════════════════════════════════════════════════════════════════════
# VERİ ÇEKME
# ══════════════════════════════════════════════════════════════════════════════
def veri_cek_td(ticker, interval, outputsize, api_key):
    """Twelve Data REST API — cache YOK, her seferinde taze veri"""
    try:
        url = "https://api.twelvedata.com/time_series"
        params = {
            "symbol":     ticker,
            "exchange":   "XIST",
            "interval":   interval,
            "outputsize": outputsize,
            "apikey":     api_key,
            "format":     "JSON",
            "order":      "ASC",
        }
        r = requests.get(url, params=params, timeout=15)
        data = r.json()

        # Rate limit hatası
        if data.get("status") == "error":
            msg = data.get("message","Bilinmeyen hata")
            if "credits" in msg.lower() or "limit" in msg.lower():
                return None, "RATE_LIMIT"
            return None, msg

        if "values" not in data:
            return None, "Veri yok"

        values = data["values"]
        if len(values) < 30:
            return None, f"Yetersiz veri ({len(values)} mum)"

        df = pd.DataFrame(values)
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.set_index("datetime", inplace=True)
        df = df.rename(columns={"open":"Open","high":"High","low":"Low","close":"Close","volume":"Volume"})
        for col in ["Open","High","Low","Close","Volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df.dropna(inplace=True)
        return df, None

    except requests.exceptions.Timeout:
        return None, "Timeout (15sn)"
    except Exception as e:
        return None, str(e)[:80]


def fiyat_cek_tek(ticker, api_key):
    """Tek hisse anlık fiyat — 1 kredi"""
    try:
        r = requests.get(
            "https://api.twelvedata.com/price",
            params={"symbol": ticker, "exchange": "XIST", "apikey": api_key},
            timeout=10
        )
        data = r.json()
        if "price" in data:
            return float(data["price"])
        return None
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
# İNDİKATÖRLER
# ══════════════════════════════════════════════════════════════════════════════
def hesapla_indiktorler(df):
    if len(df) < 30:
        return None
    df = df.copy()
    c, h, l, v = df["Close"], df["High"], df["Low"], df["Volume"]
    df["RSI"]       = ta.momentum.RSIIndicator(c, window=14).rsi()
    mi              = ta.trend.MACD(c, window_slow=26, window_fast=12, window_sign=9)
    df["MACD"]      = mi.macd()
    df["MACD_sig"]  = mi.macd_signal()
    df["MACD_hist"] = mi.macd_diff()
    bi              = ta.volatility.BollingerBands(c, window=20, window_dev=2)
    df["BB_upper"]  = bi.bollinger_hband()
    df["BB_lower"]  = bi.bollinger_lband()
    df["BB_middle"] = bi.bollinger_mavg()
    si              = ta.momentum.StochasticOscillator(h, l, c, window=14, smooth_window=3)
    df["STOCH_K"]   = si.stoch()
    df["STOCH_D"]   = si.stoch_signal()
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

    mh = row.get("MACD_hist")
    mv = row.get("MACD")
    if pd.notna(mh):
        ind["MACD_hist"] = round(float(mh), 4)
        ind["MACD_yon"]  = "↑" if mh > 0 else "↓"
        if mh > 0 and pd.notna(mv) and mv < 0:    skor += 18
        elif mh > 0:                                skor += 10
        elif mh < 0 and pd.notna(mv) and mv > 0:  skor -= 18
        else:                                        skor -= 10

    bu = row.get("BB_upper"); bl = row.get("BB_lower"); bm = row.get("BB_middle")
    if pd.notna(bu) and pd.notna(bl) and close:
        bw = float(bu) - float(bl)
        bp = (close - float(bl)) / bw if bw > 0 else 0.5
        ind["BB_alt"]  = round(float(bl), 2)
        ind["BB_orta"] = round(float(bm), 2) if pd.notna(bm) else None
        ind["BB_ust"]  = round(float(bu), 2)
        ind["BB_pct"]  = round(bp * 100, 1)
        if bp < 0.10:   skor += 20
        elif bp < 0.25: skor += 12
        elif bp < 0.35: skor += 5
        elif bp > 0.90: skor -= 20
        elif bp > 0.75: skor -= 12
        elif bp > 0.65: skor -= 5

    sk = row.get("STOCH_K"); sd = row.get("STOCH_D")
    if pd.notna(sk):
        ind["Stoch_K"] = round(float(sk), 1)
        ind["Stoch_D"] = round(float(sd), 1) if pd.notna(sd) else None
        if sk < 20:   skor += 14
        elif sk < 30: skor += 7
        elif sk > 80: skor -= 14
        elif sk > 70: skor -= 7

    e20 = row.get("EMA20"); e50 = row.get("EMA50")
    if pd.notna(e20) and pd.notna(e50) and close:
        e20f, e50f = float(e20), float(e50)
        ind["EMA20"] = round(e20f, 2)
        ind["EMA50"] = round(e50f, 2)
        if close > e20f > e50f:
            ind["EMA_trend"] = "↑ Yükseliş"; skor += 10
        elif close < e20f < e50f:
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


def skor_stil(s):
    if s >= 70: return "GÜÇLÜ AL",  "#0d6e3b", "#d4f4e5", "🟢"
    if s >= 55: return "AL",         "#1a9653", "#e2f7ed", "🟩"
    if s >= 40: return "NÖTR",       "#7a6300", "#fdf4c7", "🟡"
    if s >= 25: return "SAT",        "#b83232", "#fde8e8", "🔴"
    return              "GÜÇLÜ SAT","#8b1a1a", "#f9d0d0", "⛔"


def analiz_et(ticker, interval, outputsize):
    df, hata = veri_cek_td(ticker, interval, outputsize, API_KEY)
    if df is None:
        return None, hata
    df = hesapla_indiktorler(df)
    if df is None or len(df) < 2:
        return None, "İndikatör hesaplanamadı"
    try:
        son  = df.iloc[-1]
        prev = df.iloc[-2]
        close = float(son["Close"])
        skor, ind = skor_hesapla(son, close)
        return {
            "ticker":  ticker,
            "fiyat":   close,
            "degisim": ((close - float(prev["Close"])) / float(prev["Close"])) * 100,
            "high":    float(son["High"]),
            "low":     float(son["Low"]),
            "volume":  float(son["Volume"]),
            "skor":    skor,
            "ind":     ind,
            "zaman":   str(son.name)[:16],
        }, None
    except Exception as e:
        return None, str(e)[:80]


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ Ayarlar")

    if not API_KEY:
        st.error("⚠️ API key bulunamadı!\n\nStreamlit Cloud → Settings → Secrets:\n```\nTWELVEDATA_API_KEY = \"key\"\n```")
        st.stop()
    else:
        st.success("✅ API bağlantısı hazır")

    # ── Plan seçimi ───────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**💳 API Planı**")
    plan_sec = st.selectbox("Plan", list(PLANLAR.keys()), label_visibility="collapsed")
    plan = PLANLAR[plan_sec]
    st.caption(plan["aciklama"])

    if "Ücretsiz" in plan_sec:
        n_hisse = len(ENDEKSLER.get("BIST 30 (Test için önerilir)", []))
        est_dk = max(1, round(n_hisse / plan["rate_per_min"] * 1.2))
        st.info(f"⏳ BIST 30 için tahmini süre: **~{est_dk} dakika**\n\nÜcretsiz plan: dakikada 8 istek. Her hisse 1 istek tüketir, her 6 hisseden sonra ~60sn bekler.")

    # ── Hisse grubu ───────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**📂 Hisse Grubu**")

    endeks_sec  = list(ENDEKSLER.keys())
    kayitli_sec = list(st.session_state.ozel_listeler.keys())
    ayrac       = ["─── Kayıtlı Listelerim ───"] if kayitli_sec else []
    tum_sec     = endeks_sec + ayrac + kayitli_sec + ["➕ Özel Hisseler Gir"]
    grup_sec    = st.selectbox("Grup", tum_sec, label_visibility="collapsed")

    hisseler_secilen = []

    if grup_sec in ENDEKSLER:
        hisseler_secilen = ENDEKSLER[grup_sec]
        # Ücretsiz planda çok hisse uyarısı
        if "Ücretsiz" in plan_sec and len(hisseler_secilen) > 20:
            est = round(len(hisseler_secilen) / plan["rate_per_min"] * 1.2)
            st.warning(f"⚠️ {len(hisseler_secilen)} hisse × ~8sn/istek = **~{est} dakika**\nTest için az hisse önerilir.")
        else:
            st.caption(f"📊 {len(hisseler_secilen)} hisse")

    elif grup_sec in st.session_state.ozel_listeler:
        hisseler_secilen = st.session_state.ozel_listeler[grup_sec]
        st.caption(f"📋 {len(hisseler_secilen)} hisse · Kayıtlı")
        if st.button("🗑️ Sil", use_container_width=True):
            del st.session_state.ozel_listeler[grup_sec]
            st.rerun()

    elif grup_sec == "➕ Özel Hisseler Gir":
        girdi = st.text_area("Hisse kodları",
            placeholder="OYAKC\nTHYAO\nGARAN", height=120, label_visibility="collapsed")
        if girdi.strip():
            hisseler_secilen = list(dict.fromkeys([
                h.strip().upper().replace(".IS","").replace(":XIST","")
                for h in girdi.replace(",","\n").split("\n") if h.strip()
            ]))
            if "Ücretsiz" in plan_sec:
                est = round(len(hisseler_secilen) / plan["rate_per_min"] * 1.2)
                st.caption(f"✅ {len(hisseler_secilen)} hisse · ~{est} dk")
            else:
                st.caption(f"✅ {len(hisseler_secilen)} hisse")

        with st.expander("💾 Kaydet"):
            ad = st.text_input("Liste adı", placeholder="Portföyüm")
            if st.button("Kaydet", use_container_width=True):
                if ad and hisseler_secilen:
                    st.session_state.ozel_listeler[ad] = hisseler_secilen
                    st.success(f"✅ '{ad}' kaydedildi!")
                    st.rerun()
                else:
                    st.error("Ad ve hisse gerekli.")

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
            st.caption(f"• {ad} ({len(h)})")

    st.markdown("---")
    st.caption("📡 Twelve Data · XIST\nÜcretsiz: 8 istek/dk\nGrow: 55 istek/dk")

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
    # Plan karşılaştırma tablosu
    st.markdown("### 💳 Plan Karşılaştırması")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="plan-kutu" style="background:#f0fdf4;border:1px solid #86efac;">
        <b>🆓 Ücretsiz</b><br>
        8 istek/dakika<br>
        BIST 30 → ~5 dk<br>
        BIST 100 → ~15 dk<br>
        <b>Test için ideal</b>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="plan-kutu" style="background:#eff6ff;border:1px solid #93c5fd;">
        <b>💰 Grow ($29/ay)</b><br>
        55 istek/dakika<br>
        BIST 30 → ~40 sn<br>
        BIST 100 → ~2 dk<br>
        <b>Günlük kullanım için</b>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="plan-kutu" style="background:#fdf4ff;border:1px solid #d8b4fe;">
        <b>🚀 Pro ($99/ay)</b><br>
        610 istek/dakika<br>
        BIST TÜM → ~30 sn<br>
        WebSocket destekli<br>
        <b>Profesyonel kullanım</b>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    col1, col2 = st.columns(2)
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
        - RSI(14) · MACD(12,26,9)
        - Bollinger Bantları(20,2)
        - Stochastic(14,3)
        - EMA 20 & 50 · MFI(14)
        """)

    st.info("👈 Sol menüden plan, grup ve periyot seçip **TARA** butonuna bas.")
    if st.session_state.ozel_listeler:
        st.markdown("---")
        for ad, h in st.session_state.ozel_listeler.items():
            st.markdown(f"**{ad}**: `{'`, `'.join(h[:8])}{'...' if len(h)>8 else ''}`")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# TARAMA
# ══════════════════════════════════════════════════════════════════════════════
if not hisseler_secilen:
    st.error("Lütfen bir hisse grubu seçin veya hisse kodları girin.")
    st.stop()

toplam       = len(hisseler_secilen)
sleep_sure   = plan["sleep"]
batch_size   = plan["batch_size"]
est_sure_sn  = toplam * sleep_sure
est_sure_dk  = max(1, round(est_sure_sn / 60))

if "Ücretsiz" in plan_sec and toplam > 8:
    st.warning(
        f"⏳ **{toplam} hisse × {sleep_sure:.0f}sn/hisse ≈ ~{est_sure_dk} dakika** sürecek.\n\n"
        f"Ücretsiz planda her {batch_size} hisseden sonra sistem otomatik bekler. "
        f"Sayfayı kapatmayın."
    )

sonuclar   = []
hatalar    = []
rate_limit_bekle = False

pb     = st.progress(0)
durum  = st.empty()
kredi_uyari = st.empty()

istek_sayisi = 0
baslangic    = time.time()

for i, ticker in enumerate(hisseler_secilen):
    durum.caption(f"⏳ **{ticker}** analiz ediliyor... ({i+1}/{toplam})")

    # Rate limit kontrolü: ücretsiz planda dakikada 8
    # Her 7 istekten sonra kalan süreyi hesapla ve bekle
    if istek_sayisi > 0 and istek_sayisi % batch_size == 0:
        gecen = time.time() - baslangic
        if gecen < 62:
            bekle = 62 - gecen
            for kalan in range(int(bekle), 0, -1):
                kredi_uyari.info(f"⏸️ Rate limit koruması: **{kalan} saniye** bekleniyor... ({istek_sayisi}/{toplam} hisse tamamlandı)")
                time.sleep(1)
            kredi_uyari.empty()
            baslangic = time.time()
            istek_sayisi = 0

    r, hata = analiz_et(ticker, pconf["interval"], pconf["outputsize"])

    if r:
        sonuclar.append(r)
        istek_sayisi += 1
    elif hata == "RATE_LIMIT":
        # Beklenmedik rate limit — 65sn bekle ve tekrar dene
        kredi_uyari.warning(f"⚠️ Rate limit! 65sn bekleniyor, sonra **{ticker}** tekrar denenecek...")
        time.sleep(65)
        kredi_uyari.empty()
        baslangic = time.time()
        istek_sayisi = 0
        r2, hata2 = analiz_et(ticker, pconf["interval"], pconf["outputsize"])
        if r2:
            sonuclar.append(r2)
            istek_sayisi += 1
        else:
            hatalar.append(f"{ticker}: {hata2 or 'Rate limit'}")
    else:
        hatalar.append(f"{ticker}: {hata}")
        istek_sayisi += 1

    pb.progress((i + 1) / toplam)

    # Normal bekleme (sadece ücretsiz plan için anlamlı)
    if "Ücretsiz" in plan_sec:
        time.sleep(sleep_sure)

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
    with st.expander(f"⚠️ {len(hatalar)} hissede sorun var"):
        for h in hatalar[:30]:
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
    st.info("Bu kriterlere uyan hisse bulunamadı.")
    st.stop()

# ── Kartlar ───────────────────────────────────────────────────────────────────
def rozet(label, val, bull):
    rc = "#0d6e3b" if bull is True else "#b83232" if bull is False else "#7a6300"
    rb = "#d4f4e5" if bull is True else "#fde8e8" if bull is False else "#fdf4c7"
    return f'<span class="rozet" style="background:{rb};color:{rc};">{label} {val}</span>'

for r in filtreli:
    et, fg, bg, em = skor_stil(r["skor"])
    ind = r["ind"]
    drc = "green" if r["degisim"] >= 0 else "red"
    drs = f"+{r['degisim']:.2f}%" if r["degisim"] >= 0 else f"{r['degisim']:.2f}%"

    with st.expander(
        f"{em} **{r['ticker']}** — {r['fiyat']:.2f} TL  :{drc}[{drs}]  |  Skor: **{r['skor']}** ({et})  ·  {r['zaman']}",
        expanded=False
    ):
        cs, cd = st.columns([3,1])
        with cs:
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
                et2 = ind["EMA_trend"]
                html += rozet("EMA", et2, True if "↑" in et2 else (False if "↓" in et2 else None))
            if "MFI" in ind:
                mv = ind["MFI"]
                html += rozet("MFI", mv, True if mv<30 else (False if mv>70 else None))
            st.markdown(html, unsafe_allow_html=True)
            st.markdown("")

            detay = {}
            if "RSI"       in ind: detay["RSI(14)"]       = ind["RSI"]
            if "MACD_yon"  in ind: detay["MACD Yön"]      = ind["MACD_yon"]
            if "MACD_hist" in ind: detay["MACD Hist"]     = ind["MACD_hist"]
            if "BB_alt"    in ind:
                detay["BB Alt"]     = ind["BB_alt"]
                detay["BB Orta"]    = ind["BB_orta"]
                detay["BB Üst"]     = ind["BB_ust"]
                detay["BB Konum %"] = ind["BB_pct"]
            if "Stoch_K"   in ind: detay["Stoch K"]       = ind["Stoch_K"]
            if "Stoch_D"   in ind: detay["Stoch D"]       = ind["Stoch_D"]
            if "EMA20"     in ind:
                detay["EMA 20"] = ind["EMA20"]
                detay["EMA 50"] = ind["EMA50"]
            if "EMA_trend" in ind: detay["EMA Trend"]     = ind["EMA_trend"]
            if "MFI"       in ind: detay["MFI(14)"]       = ind["MFI"]
            detay["Fiyat"]         = f"{r['fiyat']:.2f} TL"
            detay["Gün Yüksek"]    = f"{r['high']:.2f} TL"
            detay["Gün Düşük"]     = f"{r['low']:.2f} TL"
            detay["Hacim"]         = f"{r['volume']/1e6:.2f}M"
            detay["Son Veri"]      = r["zaman"]

            df_det = pd.DataFrame(list(detay.items()), columns=["İndikatör","Değer"])
            st.dataframe(df_det, use_container_width=True, hide_index=True,
                         height=min(len(detay)*36+40, 500))

        with cd:
            br = "#22c55e" if r["skor"]>=70 else "#4ade80" if r["skor"]>=55 else "#fbbf24" if r["skor"]>=40 else "#f87171"
            st.markdown(f"""
            <div style="text-align:center;padding:14px;">
              <div style="width:80px;height:80px;border-radius:50%;background:{bg};color:{fg};
                display:flex;align-items:center;justify-content:center;font-size:26px;
                font-weight:700;margin:0 auto;">{r['skor']}</div>
              <div style="font-size:13px;font-weight:700;color:{fg};margin-top:8px;">{et}</div>
              <div style="margin-top:14px;">
                <div style="font-size:10px;color:#999;margin-bottom:5px;">Sinyal Gücü</div>
                <div style="background:#eee;border-radius:4px;height:10px;">
                  <div style="width:{r['skor']}%;background:{br};height:10px;border-radius:4px;"></div>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:9px;color:#bbb;margin-top:2px;">
                  <span>0</span><span>50</span><span>100</span>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

# ── CSV ───────────────────────────────────────────────────────────────────────
st.markdown("---")
rows = []
for r in filtreli:
    et,_,_,_ = skor_stil(r["skor"])
    s = r["ind"]
    rows.append({"Hisse":r["ticker"],"Fiyat(TL)":round(r["fiyat"],2),
        "Değişim(%)":round(r["degisim"],2),"Yüksek":round(r["high"],2),
        "Düşük":round(r["low"],2),"Skor":r["skor"],"Sinyal":et,
        "RSI":s.get("RSI","-"),"MACD":s.get("MACD_yon","-"),
        "BB%":s.get("BB_pct","-"),"Stoch K":s.get("Stoch_K","-"),
        "EMA20":s.get("EMA20","-"),"EMA50":s.get("EMA50","-"),
        "EMA Trend":s.get("EMA_trend","-"),"MFI":s.get("MFI","-"),
        "Veri Zamanı":r["zaman"]})

df_exp = pd.DataFrame(rows)
c1, _ = st.columns([1,3])
with c1:
    st.download_button("📥 CSV İndir",
        data=df_exp.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"BIST_{pconf['key']}.csv", mime="text/csv",
        use_container_width=True)
