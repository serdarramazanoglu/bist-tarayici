import streamlit as st
import requests
import pandas as pd
import ta
import time
import warnings
warnings.filterwarnings('ignore')

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
  .plan-badge { display:inline-block; background:#1a6e3b; color:white;
    padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600; margin-left:8px; }
  div[data-testid="stExpander"] {
    border:1px solid #e0e0e0 !important;
    border-radius:10px !important; margin-bottom:6px; }
</style>
""", unsafe_allow_html=True)

# ── API Key ───────────────────────────────────────────────────────────────────
try:
    API_KEY = st.secrets["TWELVEDATA_API_KEY"]
except Exception:
    API_KEY = None

# ── Grow plan sabitleri ───────────────────────────────────────────────────────
# Grow: 55 istek/dk → her istek arası ~1.1sn
# Güvenli taraf için 1.2sn kullanıyoruz
GROW_SLEEP    = 1.2
GROW_RATE_MIN = 55

# ── Periyot haritası — Grow'da tümü açık ─────────────────────────────────────
PERIYOTLAR = {
    "1 Dakikalık":  {"interval": "1min",  "outputsize": 100, "key": "1m",  "aciklama": "Son ~100 mum (~1.5 saat)"},
    "5 Dakikalık":  {"interval": "5min",  "outputsize": 100, "key": "5m",  "aciklama": "Son ~100 mum (~8 saat)"},
    "15 Dakikalık": {"interval": "15min", "outputsize": 100, "key": "15m", "aciklama": "Son ~100 mum (~25 saat)"},
    "1 Saatlik":    {"interval": "1h",    "outputsize": 150, "key": "1h",  "aciklama": "Son 150 saat"},
    "4 Saatlik":    {"interval": "4h",    "outputsize": 120, "key": "4h",  "aciklama": "Son 480 saat (~20 gün)"},
    "Günlük":       {"interval": "1day",  "outputsize": 200, "key": "1d",  "aciklama": "Son 200 gün"},
}

# ── Hisse listeleri ───────────────────────────────────────────────────────────
ENDEKSLER = {
    "BIST 30": [
        "AKBNK","ARCLK","ASELS","BIMAS","DOHOL","EKGYO","EREGL","FROTO","GARAN",
        "GUBRF","HEKTS","ISCTR","KCHOL","KOZAL","MGROS","OYAKC","PETKM","PGSUS",
        "SAHOL","SISE","TAVHL","TCELL","THYAO","TKFEN","TOASO","TTKOM","TUPRS",
        "ULKER","VAKBN","YKBNK"
    ],
    "BIST 50": [
        "AKBNK","AKSEN","ARCLK","ASELS","BIMAS","CCOLA","DOHOL","EKGYO","ENKAI",
        "EREGL","FROTO","GARAN","GUBRF","HEKTS","ISCTR","ISGYO","KCHOL","KRDMD",
        "KOZAL","LOGO","MAVI","MGROS","OYAKC","PETKM","PGSUS","SAHOL","SISE",
        "SODA","TAVHL","TCELL","THYAO","TKFEN","TOASO","TTKOM","TUPRS","ULKER",
        "VAKBN","VESTL","YKBNK","ALARK","AEFES","CIMSA","DOAS","ENJSA","INDES",
        "KLNMA","SELEC","BRSAN","ODAS","SKBNK"
    ],
    "BIST 100": [
        "THYAO","GARAN","AKBNK","EREGL","SISE","KCHOL","BIMAS","SAHOL","PGSUS","TUPRS",
        "FROTO","TOASO","ASELS","TCELL","KOZAL","EKGYO","ISCTR","HEKTS","MGROS","DOHOL",
        "TAVHL","ARCLK","ULKER","PETKM","CCOLA","ENKAI","KRDMD","VAKBN","SODA","TTKOM",
        "AEFES","OYAKC","ALARK","AKSEN","YKBNK","LOGO","MAVI","BERA","ENJSA","VESTL",
        "CIMSA","EGEEN","NETAS","KARSN","KONTR","IPEKE","ISGYO","GOLTS","GLYHO","KLNMA",
        "AGHOL","ANACM","BRSAN","BRYAT","BTCIM","DOAS","EUPWR","GESAN","GUBRF","HATEK",
        "IMASM","INDES","ISDMR","ISFIN","KAREL","KARTN","KERVT","KRSUS",
        "MPARK","NTTUR","ODAS","REEDR","RNPOL","RYSAS","SELEC","SKBNK",
        "SOKM","TATGD","TKFEN","TKNSA","TMSN"
    ],
    "BIST TÜM (Geniş)": [
        "THYAO","GARAN","AKBNK","EREGL","SISE","KCHOL","BIMAS","SAHOL","PGSUS","TUPRS",
        "FROTO","TOASO","ASELS","TCELL","KOZAL","EKGYO","ISCTR","HEKTS","MGROS","DOHOL",
        "TAVHL","ARCLK","ULKER","PETKM","CCOLA","ENKAI","KRDMD","VAKBN","SODA","TTKOM",
        "AEFES","OYAKC","ALARK","AKSEN","YKBNK","LOGO","MAVI","BERA","ENJSA","VESTL",
        "CIMSA","EGEEN","NETAS","KARSN","KONTR","IPEKE","ISGYO","GOLTS","GLYHO","KLNMA",
        "AGHOL","ANACM","BRSAN","BRYAT","BTCIM","DOAS","EUPWR","GESAN","GUBRF","HATEK",
        "IMASM","INDES","ISDMR","ISFIN","KAREL","KARTN","KERVT","KRSUS",
        "MPARK","NTTUR","ODAS","REEDR","RNPOL","RYSAS","SELEC","SKBNK",
        "SOKM","TATGD","TKFEN","TKNSA","TMSN",
        "ACSEL","ADEL","ADESE","AGESA","AGROT","AHGAZ","AKCNS","AKFGY","AKGRT",
        "AKIS","AKSA","AKSGY","ALBRK","ALCAR","ALFAS","ALKIM","ALTIN","ALYAG",
        "ANELE","ANGYO","ANHYT","ANSGR","ARDYZ","ARENA","ARSAN","ARZUM","ASCEL",
        "ASGYO","ASTOR","ATAKP","ATGYO","AVGYO","AVHOL","AVOD","AVPGY","AYCES",
        "AYEN","AYES","AYDEM","AYGAZ","BAGFS","BALSU","BANVT","BASGZ","BAYRK",
        "BEYAZ","BFREN","BIENY","BINHO","BIOEN","BIZIM","BJKAS","BLCYT","BMEKS",
        "BNTAS","BOSSA","BORSK","BSOKE","BUCIM","BURCE","BURVA","CANTE","CARFA",
        "CASA","CEMAS","CEMTS","CLEBI","COPCL","CRDFA","DARDL","DENGE","DERHL",
        "DERIM","DESA","DEVA","DGATE","DGGYO","DIRIT","DITAS","DMRGD","DNISI",
        "DOBUR","DOCO","DOGUB","DOJOB","DOKTA","DORTS","DPAZR","DRGYO","DURAN",
        "DYOBY","DZGYO","ECILC","ECZYT","EDIP","EGGUB","EGPRO","EGSER","EKIZ",
        "EKSUN","ELITE","EMKEL","EMNIS","ENERY","ENSRI","ENTRA","EPLAS","ERBOS",
        "ERSU","ESCAR","ESCOM","ESEN","ETILR","EUREN","EYGYO","FADE","FENER",
        "FITAS","FONET","FORTE","FRIGO","GARFA","GEDIK","GEDZA","GENTS","GEREL",
        "GLBMD","GLRYH","GMTAS","GOKNR","GOODY","GOZDE","GRSEL","GSDDE","GSDHO",
        "GSRAY","GULFA","HAEKO","HALKB","HDFGS","HEDEF","HKTM","HLGYO","HOROZ",
        "HTTBT","HUNER","ICBCT","IDGYO","IEYHO","IHLGM","IHEVA","IHLAS","IHYAY",
        "IKTLL","IMEN","INTEM","ITTFK","IZFAS","IZINV","IZMDC","JANTS","KATMR",
        "KBORU","KFEIN","KIMMR","KLGYO","KLSER","KMPUR","KNFRT","KONYA","KOPOL",
        "KORDS","KRDMA","KRDMB","KRPLS","KSTUR","KTLEV","KURTL","KUYAS","LIDER",
        "LILAK","LINK","LKMNH","LUKSK","MAALT","MACKO","MAGEN","MAKIM","MAKTK",
        "MANAS","MARBL","MARKA","MARTI","MEDTR","MEGAP","MEGMT","MEKAG","MERKO",
        "METRO","METUR","MIPAZ","MNDRS","MOBTL","MOGAN","MRGYO","MRSHL","MSGYO",
        "MTRKS","MZHLD","NATEN","NIBAS","NTHOL","NUGYO","NUHCM","NWIN","OBAMS",
        "OFSYM","ONCSM","ONRYT","ORCAY","ORGE","OSTIM","OTKAR","OYYAT","OZKGY",
        "PAGYO","PAMEL","PAPIL","PARSN","PASEU","PATEK","PCILT","PEGYO","PEKGY",
        "PETUN","PINSU","PKART","PKENT","PLTUR","PNLSN","POLHO","POLTK","PRZMA",
        "PSDTC","PSGYO","QNBFB","QUAGR","RALYH","RAYSG","RGYAS","RHEAG","RODRG",
        "RTALB","RUBNS","RYGYO","SAFKR","SAMAT","SANEL","SANFM","SANKO","SARKY",
        "SASA","SAYAS","SDTTR","SEGYO","SEYKM","SILVR","SKTAS","SMART","SNICA",
        "SNKRN","SNPAM","SRVGY","SUMAS","SUNTK","SURGY","SUWEN","TBORG","TDGYO",
        "TEKTU","TERA","TIRE","TRCAS","TRETN","TRGYO","TRILC","TSGYO","TTRAK",
        "TUCLK","TULGA","TURGZ","TURGG","TURGY","TURSG","UFUK","ULUFA","ULUSE",
        "ULUUN","USAK","USDMR","VAKFN","VAKGY","VANGD","VBTYZ","VERTU","VERUS",
        "VKFYO","YAPRK","YATAS","YAYLA","YBTAS","YEOTK","YESIL","YGGYO","YKSLN",
        "YONGA","YUNSA","YYAPI","ZEDUR","ZOREN","ZRGYO"
    ]
}
for k in ENDEKSLER:
    ENDEKSLER[k] = list(dict.fromkeys(ENDEKSLER[k]))

if "ozel_listeler" not in st.session_state:
    st.session_state.ozel_listeler = {}

# ══════════════════════════════════════════════════════════════════════════════
# VERİ ÇEKME  —  Grow plan, tüm periyotlar açık, exchange=BIST ✅
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=60, show_spinner=False)
def veri_cek_cached(ticker: str, interval: str, outputsize: int, api_key: str):
    """60 saniyelik cache — aynı hisseyi tekrar tararken API israfı olmaz."""
    try:
        r = requests.get(
            "https://api.twelvedata.com/time_series",
            params={
                "symbol":     ticker,
                "exchange":   "BIST",
                "interval":   interval,
                "outputsize": outputsize,
                "apikey":     api_key,
                "format":     "JSON",
                "order":      "ASC",
            },
            timeout=15
        )
        data = r.json()

        if data.get("status") == "error":
            msg = data.get("message", "")
            if "credits" in msg.lower() or "limit" in msg.lower():
                return None, "RATE_LIMIT"
            return None, msg[:100]

        values = data.get("values", [])
        if len(values) < 30:
            return None, f"Yetersiz veri ({len(values)} mum)"

        df = pd.DataFrame(values)
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.set_index("datetime", inplace=True)
        df.rename(columns={
            "open":"Open","high":"High","low":"Low",
            "close":"Close","volume":"Volume"
        }, inplace=True)
        for col in ["Open","High","Low","Close","Volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df.dropna(inplace=True)
        return df, None

    except requests.exceptions.Timeout:
        return None, "Zaman aşımı (15sn)"
    except Exception as e:
        return None, str(e)[:80]


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
    s = 50
    ind = {}

    rsi = row.get("RSI")
    if pd.notna(rsi):
        ind["RSI"] = round(float(rsi), 1)
        if rsi < 25:   s += 22
        elif rsi < 35: s += 14
        elif rsi < 45: s += 6
        elif rsi > 75: s -= 22
        elif rsi > 65: s -= 14
        elif rsi > 55: s -= 6

    mh = row.get("MACD_hist")
    mv = row.get("MACD")
    if pd.notna(mh):
        ind["MACD_hist"] = round(float(mh), 4)
        ind["MACD_yon"]  = "↑" if mh > 0 else "↓"
        if mh > 0 and pd.notna(mv) and mv < 0:    s += 18
        elif mh > 0:                                s += 10
        elif mh < 0 and pd.notna(mv) and mv > 0:  s -= 18
        else:                                        s -= 10

    bu = row.get("BB_upper"); bl = row.get("BB_lower"); bm = row.get("BB_middle")
    if pd.notna(bu) and pd.notna(bl) and close:
        bw = float(bu) - float(bl)
        bp = (close - float(bl)) / bw if bw > 0 else 0.5
        ind["BB_alt"]  = round(float(bl), 2)
        ind["BB_orta"] = round(float(bm), 2) if pd.notna(bm) else None
        ind["BB_ust"]  = round(float(bu), 2)
        ind["BB_pct"]  = round(bp * 100, 1)
        if bp < 0.10:   s += 20
        elif bp < 0.25: s += 12
        elif bp < 0.35: s += 5
        elif bp > 0.90: s -= 20
        elif bp > 0.75: s -= 12
        elif bp > 0.65: s -= 5

    sk = row.get("STOCH_K"); sd = row.get("STOCH_D")
    if pd.notna(sk):
        ind["Stoch_K"] = round(float(sk), 1)
        ind["Stoch_D"] = round(float(sd), 1) if pd.notna(sd) else None
        if sk < 20:   s += 14
        elif sk < 30: s += 7
        elif sk > 80: s -= 14
        elif sk > 70: s -= 7

    e20 = row.get("EMA20"); e50 = row.get("EMA50")
    if pd.notna(e20) and pd.notna(e50) and close:
        e20f, e50f = float(e20), float(e50)
        ind["EMA20"] = round(e20f, 2)
        ind["EMA50"] = round(e50f, 2)
        if close > e20f > e50f:
            ind["EMA_trend"] = "↑ Yükseliş"; s += 10
        elif close < e20f < e50f:
            ind["EMA_trend"] = "↓ Düşüş";   s -= 10
        else:
            ind["EMA_trend"] = "→ Nötr"

    mfi = row.get("MFI")
    if pd.notna(mfi):
        ind["MFI"] = round(float(mfi), 1)
        if mfi < 20:   s += 10
        elif mfi < 30: s += 5
        elif mfi > 80: s -= 10
        elif mfi > 70: s -= 5

    return max(0, min(100, round(s))), ind


def skor_stil(s):
    if s >= 70: return "GÜÇLÜ AL",  "#0d6e3b", "#d4f4e5", "🟢"
    if s >= 55: return "AL",         "#1a9653", "#e2f7ed", "🟩"
    if s >= 40: return "NÖTR",       "#7a6300", "#fdf4c7", "🟡"
    if s >= 25: return "SAT",        "#b83232", "#fde8e8", "🔴"
    return              "GÜÇLÜ SAT","#8b1a1a", "#f9d0d0", "⛔"


def analiz_et(ticker, interval, outputsize):
    df, hata = veri_cek_cached(ticker, interval, outputsize, API_KEY)
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
        return None, str(e)[:60]


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ Ayarlar")

    if not API_KEY:
        st.error("⚠️ API key bulunamadı!\n\nStreamlit → Settings → Secrets:\n```\nTWELVEDATA_API_KEY = \"key\"\n```")
        st.stop()

    st.markdown("""
    <div style="background:#d4f4e5;border-radius:8px;padding:8px 12px;margin-bottom:4px;">
      <span style="color:#0d6e3b;font-weight:600;">✅ Grow Plan Aktif</span><br>
      <span style="color:#1a9653;font-size:12px;">55 istek/dk · Tüm periyotlar · BIST tam erişim</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Hisse grubu ───────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**📂 Hisse Grubu**")
    kayitli = list(st.session_state.ozel_listeler.keys())
    ayrac   = ["─── Kayıtlı Listelerim ───"] if kayitli else []
    tum_sec = list(ENDEKSLER.keys()) + ayrac + kayitli + ["➕ Özel Hisseler Gir"]
    grup_sec = st.selectbox("Grup", tum_sec, label_visibility="collapsed")

    hisseler_secilen = []

    if grup_sec in ENDEKSLER:
        hisseler_secilen = ENDEKSLER[grup_sec]
        # Grow plan: 55 istek/dk → BIST 30 ~35sn, BIST 100 ~2dk, TÜM ~5-8dk
        toplam = len(hisseler_secilen)
        est_sn = round(toplam * GROW_SLEEP)
        est_dk = max(1, round(est_sn / 60))
        if est_sn < 60:
            st.caption(f"📊 {toplam} hisse · ~{est_sn} saniye")
        else:
            st.caption(f"📊 {toplam} hisse · ~{est_dk} dakika")

    elif grup_sec in st.session_state.ozel_listeler:
        hisseler_secilen = st.session_state.ozel_listeler[grup_sec]
        st.caption(f"📋 {len(hisseler_secilen)} hisse · Kayıtlı liste")
        if st.button("🗑️ Bu listeyi sil", use_container_width=True):
            del st.session_state.ozel_listeler[grup_sec]
            st.rerun()

    elif grup_sec == "➕ Özel Hisseler Gir":
        girdi = st.text_area(
            "Hisse kodları (her satıra bir tane veya virgülle ayır)",
            placeholder="OYAKC\nTHYAO\nGARAN\nAKBNK",
            height=130,
            label_visibility="collapsed"
        )
        if girdi.strip():
            hisseler_secilen = list(dict.fromkeys([
                h.strip().upper().replace(".IS","").replace(":XIST","")
                for h in girdi.replace(",","\n").split("\n") if h.strip()
            ]))
            est_sn = round(len(hisseler_secilen) * GROW_SLEEP)
            st.caption(f"✅ {len(hisseler_secilen)} hisse · ~{est_sn} saniye")

        with st.expander("💾 Bu listeyi kaydet"):
            ad = st.text_input("Liste adı", placeholder="Portföyüm")
            if st.button("Kaydet", use_container_width=True):
                if ad and hisseler_secilen:
                    st.session_state.ozel_listeler[ad] = hisseler_secilen
                    st.success(f"✅ '{ad}' kaydedildi!")
                    st.rerun()
                else:
                    st.error("Ad ve hisse kodları gerekli.")

    # ── Periyot ───────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**⏱️ Periyot**")
    periyot_adi = st.selectbox(
        "Periyot",
        list(PERIYOTLAR.keys()),
        index=3,  # Varsayılan: 1 Saatlik
        label_visibility="collapsed"
    )
    pconf = PERIYOTLAR[periyot_adi]
    st.caption(pconf["aciklama"])

    # ── Filtreler ─────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**🔽 Filtreler**")
    sadece_al = st.checkbox("Sadece AL sinyalleri (%55+)")
    min_skor  = st.slider("Minimum skor", 0, 100, 0, 5)

    st.markdown("---")
    tara_btn = st.button("🔍 TARA", use_container_width=True, type="primary")

    # Kayıtlı listeler özeti
    if st.session_state.ozel_listeler:
        st.markdown("---")
        st.markdown("**📋 Kayıtlı Listelerim**")
        for ad, h in st.session_state.ozel_listeler.items():
            st.caption(f"• {ad} ({len(h)} hisse)")

    st.markdown("---")
    st.caption(
        "📡 Twelve Data · Grow Plan\n"
        "✅ Tüm periyotlar aktif\n"
        "🔄 60sn önbellek\n"
        "⚡ 55 istek/dakika"
    )


# ══════════════════════════════════════════════════════════════════════════════
# ANA SAYFA
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="baslik">
  <div style="font-size:22px;font-weight:700;">
    📈 BIST Teknik Tarayıcı
    <span class="plan-badge">Grow Plan</span>
  </div>
  <div style="opacity:0.85;margin-top:4px;font-size:13px;">
    Canlı Veri · Twelve Data · RSI · MACD · Bollinger · Stoch · EMA · MFI
    &nbsp;|&nbsp; 1dk · 5dk · 15dk · 1S · 4S · Günlük
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
        **Grow Plan — Aktif Özellikler**
        - ✅ Tüm 6 periyot açık
        - ✅ BIST 30 → ~35 saniye
        - ✅ BIST 100 → ~2 dakika
        - ✅ BIST TÜM → ~5-8 dakika
        - ✅ 60sn önbellek
        """)
    with col3:
        st.markdown("""
        **İndikatörler**
        - RSI(14)
        - MACD(12,26,9)
        - Bollinger Bantları(20,2)
        - Stochastic(14,3)
        - EMA 20 & 50
        - MFI(14)
        """)
    with col4:
        st.markdown("""
        **Hisse Grupları**
        - BIST 30 / 50 / 100
        - BIST TÜM (300+ hisse)
        - Kayıtlı özel listeler
        - Manuel hisse girişi
        """)
    st.info("👈 Sol menüden hisse grubu ve periyot seçip **TARA** butonuna bas.")
    if st.session_state.ozel_listeler:
        st.markdown("---")
        st.markdown("### 📋 Kayıtlı Listelerim")
        for ad, h in st.session_state.ozel_listeler.items():
            st.markdown(f"**{ad}** ({len(h)} hisse): `{'`, `'.join(h[:10])}{'...' if len(h)>10 else ''}`")
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# TARAMA — Grow plan hızında
# ══════════════════════════════════════════════════════════════════════════════
if not hisseler_secilen:
    st.error("Lütfen sol menüden bir hisse grubu seçin veya hisse kodlarını girin.")
    st.stop()

toplam   = len(hisseler_secilen)
est_sn   = round(toplam * GROW_SLEEP)
est_dk   = max(1, round(est_sn / 60))

if toplam > 50:
    st.info(f"⏳ **{toplam} hisse** taranacak · Tahmini süre: ~**{est_dk} dakika**")

sonuclar  = []
hatalar   = []
rate_hits = 0

pb    = st.progress(0)
durum = st.empty()

for i, ticker in enumerate(hisseler_secilen):
    durum.caption(f"⏳ **{ticker}** analiz ediliyor... ({i+1}/{toplam})")

    r, hata = analiz_et(ticker, pconf["interval"], pconf["outputsize"])

    if r:
        sonuclar.append(r)
    elif hata == "RATE_LIMIT":
        rate_hits += 1
        # Grow plan'da rate limit nadiren olur — 65sn bekle ve tekrar dene
        durum.warning(f"⚠️ Rate limit ({rate_hits}x) · 65sn bekleniyor · **{ticker}** tekrar denenecek...")
        time.sleep(65)
        r2, hata2 = analiz_et(ticker, pconf["interval"], pconf["outputsize"])
        if r2:
            sonuclar.append(r2)
        else:
            hatalar.append(f"{ticker}: {hata2 or 'Rate limit'}")
    else:
        hatalar.append(f"{ticker}: {hata}")

    pb.progress((i + 1) / toplam)
    time.sleep(GROW_SLEEP)  # 55 istek/dk limiti için 1.2sn

pb.empty()
durum.empty()

# Filtrele & sırala
filtreli = [r for r in sonuclar if r["skor"] >= min_skor]
if sadece_al:
    filtreli = [r for r in filtreli if r["skor"] >= 55]
filtreli.sort(key=lambda x: x["skor"], reverse=True)

# ── Özet metrikler ────────────────────────────────────────────────────────────
st.markdown(f"### Sonuçlar — {grup_sec} · {periyot_adi} · {len(filtreli)} hisse")
c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("Başarılı",    len(sonuclar))
c2.metric("🟢 Güçlü AL", sum(1 for r in filtreli if r["skor"]>=70))
c3.metric("🟩 AL",        sum(1 for r in filtreli if 55<=r["skor"]<70))
c4.metric("🟡 Nötr",      sum(1 for r in filtreli if 40<=r["skor"]<55))
c5.metric("🔴 SAT",       sum(1 for r in filtreli if 25<=r["skor"]<40))
c6.metric("⛔ G.SAT",     sum(1 for r in filtreli if r["skor"]<25))

if hatalar:
    with st.expander(f"⚠️ {len(hatalar)} hissede sorun"):
        for h in hatalar[:30]:
            st.caption(h)

st.markdown("---")

# Sıralama & filtre
sc1, sc2 = st.columns([2, 4])
with sc1:
    siralama = st.selectbox("Sırala", [
        "Puan (Yüksek→Düşük)", "Puan (Düşük→Yüksek)", "Değişim %", "İsim A-Z"
    ])
with sc2:
    filtre2 = st.selectbox("Göster", [
        "Tümü", "Sadece AL & Güçlü AL", "Sadece Nötr", "Sadece SAT & Güçlü SAT"
    ])

if siralama == "Puan (Düşük→Yüksek)":   filtreli.sort(key=lambda x: x["skor"])
elif siralama == "Değişim %":             filtreli.sort(key=lambda x: x["degisim"], reverse=True)
elif siralama == "İsim A-Z":              filtreli.sort(key=lambda x: x["ticker"])

if filtre2 == "Sadece AL & Güçlü AL":       filtreli = [r for r in filtreli if r["skor"]>=55]
elif filtre2 == "Sadece Nötr":               filtreli = [r for r in filtreli if 40<=r["skor"]<55]
elif filtre2 == "Sadece SAT & Güçlü SAT":   filtreli = [r for r in filtreli if r["skor"]<40]

if not filtreli:
    st.info("Bu kriterlere uyan hisse bulunamadı.")
    st.stop()

# ── Hisse kartları ────────────────────────────────────────────────────────────
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
        f"{em} **{r['ticker']}** — {r['fiyat']:.2f} TL  :{drc}[{drs}]"
        f"  |  Skor: **{r['skor']}** ({et})  ·  {r['zaman']}",
        expanded=False
    ):
        cs, cd = st.columns([3, 1])

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
            detay["Son Mum"]       = r["zaman"]

            df_det = pd.DataFrame(list(detay.items()), columns=["İndikatör", "Değer"])
            st.dataframe(df_det, use_container_width=True, hide_index=True,
                         height=min(len(detay)*36+40, 520))

        with cd:
            br = "#22c55e" if r["skor"]>=70 else "#4ade80" if r["skor"]>=55 else "#fbbf24" if r["skor"]>=40 else "#f87171"
            st.markdown(f"""
            <div style="text-align:center;padding:14px;">
              <div style="width:80px;height:80px;border-radius:50%;background:{bg};color:{fg};
                display:flex;align-items:center;justify-content:center;
                font-size:26px;font-weight:700;margin:0 auto;">{r['skor']}</div>
              <div style="font-size:13px;font-weight:700;color:{fg};margin-top:8px;">{et}</div>
              <div style="margin-top:14px;">
                <div style="font-size:10px;color:#999;margin-bottom:5px;">Sinyal Gücü</div>
                <div style="background:#eee;border-radius:4px;height:10px;">
                  <div style="width:{r['skor']}%;background:{br};height:10px;border-radius:4px;"></div>
                </div>
                <div style="display:flex;justify-content:space-between;
                  font-size:9px;color:#bbb;margin-top:2px;">
                  <span>0</span><span>50</span><span>100</span>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

# ── CSV İndir ─────────────────────────────────────────────────────────────────
st.markdown("---")
rows = []
for r in filtreli:
    et, _, _, _ = skor_stil(r["skor"])
    s = r["ind"]
    rows.append({
        "Hisse":        r["ticker"],
        "Fiyat (TL)":   round(r["fiyat"], 2),
        "Değişim (%)":  round(r["degisim"], 2),
        "Yüksek":       round(r["high"], 2),
        "Düşük":        round(r["low"], 2),
        "Skor":         r["skor"],
        "Sinyal":       et,
        "RSI(14)":      s.get("RSI", "-"),
        "MACD Yön":     s.get("MACD_yon", "-"),
        "BB Konum %":   s.get("BB_pct", "-"),
        "BB Alt":       s.get("BB_alt", "-"),
        "BB Üst":       s.get("BB_ust", "-"),
        "Stoch K":      s.get("Stoch_K", "-"),
        "EMA 20":       s.get("EMA20", "-"),
        "EMA 50":       s.get("EMA50", "-"),
        "EMA Trend":    s.get("EMA_trend", "-"),
        "MFI(14)":      s.get("MFI", "-"),
        "Son Mum":      r["zaman"],
    })

df_exp = pd.DataFrame(rows)
c1, _ = st.columns([1, 3])
with c1:
    st.download_button(
        "📥 CSV İndir",
        data=df_exp.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"BIST_{grup_sec.replace(' ','_')}_{pconf['key']}.csv",
        mime="text/csv",
        use_container_width=True
    )
