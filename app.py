import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import time
import json
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
  div[data-testid="stExpander"] { border: 1px solid #e0e0e0 !important; border-radius: 10px !important; margin-bottom: 6px; }
</style>
""", unsafe_allow_html=True)

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
        'AKBNK','AKSEN','ARCLK','ASELS','BIMAS','BRSAN','CCOLA','DOHOL','EKGYO',
        'ENKAI','EREGL','FROTO','GARAN','GUBRF','HEKTS','ISCTR','ISGYO','KCHOL',
        'KRDMD','KOZAL','LOGO','MAVI','MGROS','ODAS','OYAKC','PETKM','PGSUS',
        'SAHOL','SISE','SODA','TAVHL','TCELL','THYAO','TKFEN','TOASO','TTKOM',
        'TUPRS','ULKER','VAKBN','VESTL','YKBNK','ALARK','AEFES','CCOLA','CIMSA',
        'DOAS','ENJSA','INDES','KLNMA','SELEC'
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
        'SOKM','TATGD','TKFEN','TKNSA','TMSN','TKFEN','ODAS','QUAGR',
        'ALKIM','ALTIN','AYCES','BASGZ','BORSK','BUCIM','BURVA','CANTE',
        'DERIM','DEVA','ECILC','EDIP','EGE','EMKEL','ESCOM','FENER',
        'FLAP','GSDHO','GSDDE','HLGYO','HTTBT','HUNER','IDGYO','IHLGM',
        'IHEVA','IHYAY','IKTLL','IMEN','INTEM','IPEKE','IPEKE','IZFAS'
    ],
    "BIST TÜM (Geniş Liste)": [
        # BIST 100
        'THYAO','GARAN','AKBNK','EREGL','SISE','KCHOL','BIMAS','SAHOL','PGSUS','TUPRS',
        'FROTO','TOASO','ASELS','TCELL','KOZAL','EKGYO','ISCTR','HEKTS','MGROS','DOHOL',
        'TAVHL','ARCLK','ULKER','PETKM','CCOLA','ENKAI','KRDMD','VAKBN','SODA','TTKOM',
        'AEFES','OYAKC','ALARK','AKSEN','YKBNK','LOGO','MAVI','BERA','ENJSA','VESTL',
        'CIMSA','EGEEN','NETAS','KARSN','KONTR','IPEKE','ISGYO','GOLTS','GLYHO','KLNMA',
        'AGHOL','ANACM','BRSAN','BRYAT','BTCIM','DOAS','EUPWR','GESAN','GUBRF','HATEK',
        'IMASM','INDES','ISDMR','ISFIN','KAREL','KARTN','KERVT','KRSUS',
        'MPARK','NTTUR','ODAS','REEDR','RNPOL','RYSAS','SELEC','SKBNK',
        'SOKM','TATGD','TKFEN','TKNSA','TMSN',
        # Ek hisseler (BIST TÜM)
        'ACSEL','ADEL','ADESE','ADGYO','AEFES','AFYON','AGESA','AGROT','AGYO',
        'AHGAZ','AHSGY','AKBNK','AKCNS','AKFGY','AKGRT','AKIS','AKSA','AKSEN',
        'AKSGY','AKSUE','AKTIF','ALBRK','ALCAR','ALCTL','ALFAS','ALKA','ALKIM',
        'ALKLC','ALTIN','ALTINS','ALYAG','ANELE','ANGYO','ANHYT','ANSGR',
        'ARCLK','ARDYZ','ARENA','ARSAN','ARZUM','ASCEL','ASGYO','ASTOR',
        'ATAKP','ATATP','ATGYO','AVGYO','AVHOL','AVOD','AVPGY','AYCES',
        'AYEN','AYES','AYDEM','AYGAZ','AZTEK',
        'BAGFS','BALSU','BANVT','BASGZ','BAYRK','BEYAZ','BFREN','BIENY',
        'BIGCH','BINHO','BIOEN','BIZIM','BJKAS','BLCYT','BMEKS','BMSCH',
        'BNTAS','BOSSA','BORSK','BORVE','BRKVY','BSOKE','BTCIM','BUCIM',
        'BURCE','BURVA','BVSAN',
        'CANTE','CARFA','CASA','CEMAS','CEMTS','CEOEM','CIMSA','CLEBI',
        'CMBTN','CMENT','COPCL','COSMO','CRDFA','CRFSA',
        'DAGHL','DARDL','DENGE','DERHL','DERIM','DESA','DEVA','DGATE',
        'DGGYO','DIRIT','DITAS','DMRGD','DNISI','DOBUR','DOCO','DOGUB',
        'DOHOL','DOJOB','DOKTA','DORTS','DPAZR','DRGYO','DTRND','DURAN',
        'DYOBY','DZGYO',
        'ECILC','ECZYT','EDIP','EGEEN','EGGUB','EGPRO','EGSER','EKGYO',
        'EKIZ','EKSUN','ELITE','EMKEL','EMNIS','ENERY','ENJSA','ENKAI',
        'ENSRI','ENTRA','EPLAS','ERBOS','ERCB','ERSU','ESCAR','ESCOM',
        'ESEN','ETILR','EUPWR','EUREN','EYGYO',
        'FADE','FENER','FITAS','FLAP','FONET','FORMT','FORTE','FRIGO',
        'FZLGY',
        'GARFA','GDKGS','GEDIK','GEDZA','GENTS','GEREL','GESAN','GLBMD',
        'GLRYH','GLYHO','GMTAS','GOKNR','GOLTS','GOODY','GOZDE','GRSEL',
        'GSDDE','GSDHO','GSRAY','GUBRF','GULFA','GUNDG','GZNMI',
        'HAEKO','HALKB','HATEK','HDFGS','HEDEF','HEKTS','HKTM','HLGYO',
        'HOROZ','HTTBT','HUNER','HURGZ',
        'ICBCT','IDGYO','IEYHO','IHLGM','IHEVA','IHLAS','IHYAY','IKTLL',
        'IMASM','IMEN','INDES','INTEM','IPEKE','ISGYO','ISKPL','ISYAT',
        'ITTFK','IZFAS','IZINV','IZMDC',
        'JANTS',
        'KAREL','KARTN','KATMR','KBORU','KERVT','KFEIN','KGYO','KIMMR',
        'KLGYO','KLNMA','KLSER','KMPUR','KNFRT','KONYA','KOPOL','KORDS',
        'KRDMA','KRDMB','KRDMD','KRPLS','KRSUS','KSTUR','KTLEV','KURTL',
        'KUYAS','KZBGY',
        'LIDER','LILAK','LINK','LKMNH','LOGO','LUKSK',
        'MAALT','MACKO','MAGEN','MAKIM','MAKTK','MANAS','MARBL','MARKA',
        'MARTI','MAVI','MEDTR','MEGAP','MEGMT','MEKAG','MERKO','METRO',
        'METUR','MGROS','MIPAZ','MNDRS','MNVAU','MOBTL','MOGAN','MPARK',
        'MRGYO','MRSHL','MSGYO','MTRKS','MZHLD',
        'NATEN','NETAS','NIBAS','NTHOL','NTTUR','NUGYO','NUHCM','NWIN',
        'OBAMS','ODAS','OFSYM','ONCSM','ONRYT','ORCAY','ORGE','OSTIM',
        'OTKAR','OYAKC','OYYAT','OZKGY',
        'PAGYO','PAMEL','PAPIL','PARSN','PASEU','PATEK','PCILT','PEGYO',
        'PEKGY','PETKM','PETUN','PGSUS','PINSU','PKART','PKENT','PLTUR',
        'PNLSN','POLHO','POLTK','PRZMA','PSDTC','PSGYO',
        'QNBFB','QUAGR',
        'RALYH','RAYSG','REEDR','RGYAS','RHEAG','RNPOL','RODRG','RTALB',
        'RUBNS','RYGYO','RYSAS',
        'SAFKR','SAHOL','SAMAT','SANEL','SANFM','SANKO','SARKY','SASA',
        'SAYAS','SDTTR','SEGYO','SELEC','SEYKM','SILVR','SISE','SKBNK',
        'SKTAS','SMART','SNICA','SNKRN','SNPAM','SODA','SOKM','SRVGY',
        'SUMAS','SUNTK','SURGY','SUWEN',
        'TATGD','TAVHL','TBORG','TCELL','TDGYO','TEKTU','TERA','THYAO',
        'TICARET','TIRE','TKFEN','TKNSA','TMSN','TOASO','TRCAS','TRETN',
        'TRGYO','TRILC','TSGYO','TTKOM','TTRAK','TUCLK','TULGA','TUPRS',
        'TURGZ','TURGG','TURGY','TURSG',
        'UFUK','ULUFA','ULUSE','ULKER','ULUUN','USAK','USDMR',
        'VAKBN','VAKFN','VAKGY','VANGD','VBTYZ','VERTU','VERUS','VESTL','VKFYO',
        'YAPRK','YATAS','YAYLA','YBTAS','YEOTK','YESIL','YGGYO','YKBNK',
        'YKSLN','YONGA','YUNSA','YYAPI',
        'ZEDUR','ZOREN','ZRGYO'
    ]
}

# Tekrar kaldır
for k in ENDEKSLER:
    ENDEKSLER[k] = list(dict.fromkeys(ENDEKSLER[k]))

# ── Periyot tanımları ─────────────────────────────────────────────────────────
PERIYOT_MAP = {
    '15 Dakikalık': {'interval': '15m', 'period': '5d',   'key': '15m'},
    '1 Saatlik':    {'interval': '1h',  'period': '7d',   'key': '1h'},
    '4 Saatlik':    {'interval': '1h',  'period': '30d',  'key': '4h'},
    'Günlük':       {'interval': '1d',  'period': '180d', 'key': '1d'},
}

# ══════════════════════════════════════════════════════════════════════════════
# ÖZEL LİSTE YÖNETİMİ (session state)
# ══════════════════════════════════════════════════════════════════════════════
if 'ozel_listeler' not in st.session_state:
    st.session_state.ozel_listeler = {}   # {'Liste Adı': ['THYAO', 'GARAN', ...]}

# ══════════════════════════════════════════════════════════════════════════════
# YARDIMCI FONKSİYONLAR
# ══════════════════════════════════════════════════════════════════════════════
def resample_4h(df):
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    return df.resample('4h').agg({
        'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'
    }).dropna()

def hesapla_indiktorler(df):
    if len(df) < 30:
        return None
    df = df.copy()
    c, h, l, v = df['Close'], df['High'], df['Low'], df['Volume']
    df['RSI']       = ta.momentum.RSIIndicator(c, window=14).rsi()
    macd            = ta.trend.MACD(c, window_slow=26, window_fast=12, window_sign=9)
    df['MACD']      = macd.macd()
    df['MACD_sig']  = macd.macd_signal()
    df['MACD_hist'] = macd.macd_diff()
    bb              = ta.volatility.BollingerBands(c, window=20, window_dev=2)
    df['BB_upper']  = bb.bollinger_hband()
    df['BB_lower']  = bb.bollinger_lband()
    df['BB_middle'] = bb.bollinger_mavg()
    stoch           = ta.momentum.StochasticOscillator(h, l, c, window=14, smooth_window=3)
    df['STOCH_K']   = stoch.stoch()
    df['STOCH_D']   = stoch.stoch_signal()
    df['EMA20']     = ta.trend.EMAIndicator(c, window=20).ema_indicator()
    df['EMA50']     = ta.trend.EMAIndicator(c, window=50).ema_indicator()
    df['MFI']       = ta.volume.MFIIndicator(h, l, c, v, window=14).money_flow_index()
    return df

def skor_hesapla(row, close):
    skor = 50
    ind  = {}

    rsi = row.get('RSI')
    if pd.notna(rsi):
        ind['RSI'] = round(float(rsi), 1)
        if rsi < 25:   skor += 22
        elif rsi < 35: skor += 14
        elif rsi < 45: skor += 6
        elif rsi > 75: skor -= 22
        elif rsi > 65: skor -= 14
        elif rsi > 55: skor -= 6

    macd_h = row.get('MACD_hist')
    macd_v = row.get('MACD')
    if pd.notna(macd_h):
        ind['MACD_hist'] = round(float(macd_h), 4)
        ind['MACD_yon']  = '↑' if macd_h > 0 else '↓'
        if macd_h > 0 and pd.notna(macd_v) and macd_v < 0:    skor += 18
        elif macd_h > 0:                                        skor += 10
        elif macd_h < 0 and pd.notna(macd_v) and macd_v > 0:  skor -= 18
        else:                                                    skor -= 10

    bb_up  = row.get('BB_upper')
    bb_low = row.get('BB_lower')
    bb_mid = row.get('BB_middle')
    if pd.notna(bb_up) and pd.notna(bb_low) and close:
        bw = float(bb_up) - float(bb_low)
        bp = (close - float(bb_low)) / bw if bw > 0 else 0.5
        ind['BB_alt']  = round(float(bb_low), 2)
        ind['BB_orta'] = round(float(bb_mid), 2) if pd.notna(bb_mid) else None
        ind['BB_ust']  = round(float(bb_up), 2)
        ind['BB_pct']  = round(bp * 100, 1)
        if bp < 0.10:   skor += 20
        elif bp < 0.25: skor += 12
        elif bp < 0.35: skor += 5
        elif bp > 0.90: skor -= 20
        elif bp > 0.75: skor -= 12
        elif bp > 0.65: skor -= 5

    stk = row.get('STOCH_K')
    std = row.get('STOCH_D')
    if pd.notna(stk):
        ind['Stoch_K'] = round(float(stk), 1)
        ind['Stoch_D'] = round(float(std), 1) if pd.notna(std) else None
        if stk < 20:   skor += 14
        elif stk < 30: skor += 7
        elif stk > 80: skor -= 14
        elif stk > 70: skor -= 7

    ema20 = row.get('EMA20')
    ema50 = row.get('EMA50')
    if pd.notna(ema20) and pd.notna(ema50) and close:
        e20, e50 = float(ema20), float(ema50)
        ind['EMA20'] = round(e20, 2)
        ind['EMA50'] = round(e50, 2)
        if close > e20 > e50:
            ind['EMA_trend'] = '↑ Yükseliş'; skor += 10
        elif close < e20 < e50:
            ind['EMA_trend'] = '↓ Düşüş';   skor -= 10
        else:
            ind['EMA_trend'] = '→ Nötr'

    mfi = row.get('MFI')
    if pd.notna(mfi):
        ind['MFI'] = round(float(mfi), 1)
        if mfi < 20:   skor += 10
        elif mfi < 30: skor += 5
        elif mfi > 80: skor -= 10
        elif mfi > 70: skor -= 5

    return max(0, min(100, round(skor))), ind

def skor_stil(skor):
    if skor >= 70: return 'GÜÇLÜ AL',  '#0d6e3b', '#d4f4e5', '🟢'
    if skor >= 55: return 'AL',         '#1a9653', '#e2f7ed', '🟩'
    if skor >= 40: return 'NÖTR',       '#7a6300', '#fdf4c7', '🟡'
    if skor >= 25: return 'SAT',        '#b83232', '#fde8e8', '🔴'
    return              'GÜÇLÜ SAT', '#8b1a1a', '#f9d0d0', '⛔'

@st.cache_data(ttl=900)
def veri_cek(ticker, interval, period, periyot_key):
    try:
        df = yf.download(ticker + '.IS', interval=interval, period=period,
                         progress=False, auto_adjust=True)
        if df.empty or len(df) < 30:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if periyot_key == '4h':
            df = resample_4h(df)
        return hesapla_indiktorler(df)
    except Exception:
        return None

def analiz_et(ticker, interval, period, periyot_key):
    df = veri_cek(ticker, interval, period, periyot_key)
    if df is None or len(df) < 2:
        return None
    try:
        son   = df.iloc[-1]
        prev  = df.iloc[-2]
        close = float(son['Close'])
        skor, ind = skor_hesapla(son, close)
        return {
            'ticker':  ticker,
            'fiyat':   close,
            'degisim': ((close - float(prev['Close'])) / float(prev['Close'])) * 100,
            'high':    float(son['High']),
            'low':     float(son['Low']),
            'volume':  float(son['Volume']),
            'skor':    skor,
            'ind':     ind,
        }
    except Exception:
        return None

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ Tarama Ayarları")
    st.markdown("---")

    # ── Kaynak seçimi ─────────────────────────────────────────────────────────
    st.markdown("**📂 Hisse Grubu**")

    endeks_secenekleri = list(ENDEKSLER.keys())
    kayitli_secenekler = list(st.session_state.ozel_listeler.keys())
    ozel_secenek       = ["➕ Özel Hisseler Gir"]

    tum_secenekler = endeks_secenekleri + (
        ["─── Kayıtlı Listelerim ───"] + kayitli_secenekler if kayitli_secenekler else []
    ) + ozel_secenek

    grup_sec = st.selectbox("Grup seç", tum_secenekler, label_visibility="collapsed")

    # ── Özel hisse girişi ─────────────────────────────────────────────────────
    hisseler_secilen = []
    yeni_liste_kaydet = False

    if grup_sec in ENDEKSLER:
        hisseler_secilen = ENDEKSLER[grup_sec]
        st.caption(f"📊 {len(hisseler_secilen)} hisse")

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
            height=140
        )
        if girdi.strip():
            hisseler_secilen = [
                h.strip().upper().replace('.IS', '')
                for h in girdi.replace(',', '\n').split('\n') if h.strip()
            ]
            hisseler_secilen = list(dict.fromkeys(hisseler_secilen))
            st.caption(f"✅ {len(hisseler_secilen)} hisse girildi")

        # Listeyi kaydet
        with st.expander("💾 Bu listeyi kaydet"):
            liste_adi = st.text_input("Liste adı", placeholder="Portföyüm")
            if st.button("Kaydet", use_container_width=True):
                if liste_adi and hisseler_secilen:
                    st.session_state.ozel_listeler[liste_adi] = hisseler_secilen
                    st.success(f"'{liste_adi}' kaydedildi!")
                    st.rerun()
                elif not liste_adi:
                    st.error("Liste adı boş olamaz.")
                else:
                    st.error("Önce hisse kodlarını girin.")

    elif grup_sec == "─── Kayıtlı Listelerim ───":
        st.info("Listelerinizden birini seçin.")

    # ── Periyot ───────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**⏱️ Periyot**")
    periyot_sec = st.selectbox("Periyot seç", list(PERIYOT_MAP.keys()), label_visibility="collapsed")
    pconf = PERIYOT_MAP[periyot_sec]

    if periyot_sec == '15 Dakikalık':
        st.caption("⚠️ 15dk periyot son 5 günü kapsar. Çok sayıda hisse için yavaş olabilir.")

    # ── Filtreler ─────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**🔽 Filtreler**")
    sadece_al = st.checkbox("Sadece AL sinyalleri (%55+)")
    min_skor  = st.slider("Minimum skor", 0, 100, 0, 5)

    st.markdown("---")
    tara_btn = st.button("🔍 TARA", use_container_width=True, type="primary")

    # ── Kayıtlı listeler özeti ────────────────────────────────────────────────
    if st.session_state.ozel_listeler:
        st.markdown("---")
        st.markdown("**📋 Kayıtlı Listelerim**")
        for ad, hisseler in st.session_state.ozel_listeler.items():
            st.caption(f"• {ad} ({len(hisseler)} hisse)")

    st.markdown("---")
    st.caption("📡 Veri: Yahoo Finance · 15dk gecikmeli\n\nÖnbellek: 15 dakika")

# ══════════════════════════════════════════════════════════════════════════════
# ANA SAYFA
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="baslik">
  <div style="font-size:22px;font-weight:700;">📈 BIST Teknik Tarayıcı</div>
  <div style="opacity:0.85;margin-top:4px;font-size:13px;">
    RSI · MACD · Bollinger Bantları · Stochastic · EMA20/50 · MFI &nbsp;|&nbsp;
    15dk · 1S · 4S · Günlük Periyot
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
        - BIST 30 (30 hisse)
        - BIST 50 (50 hisse)
        - BIST 100 (100 hisse)
        - BIST TÜM (300+ hisse)
        - Kayıtlı özel listeler
        """)
    with col4:
        st.markdown("""
        **Periyotlar**
        - 15 Dakikalık (son 5g)
        - 1 Saatlik (son 7g)
        - 4 Saatlik (son 30g)
        - Günlük (son 180g)
        """)
    st.info("👈 Sol menüden grup ve periyot seçip **TARA** butonuna bas.")

    # Kayıtlı liste varsa göster
    if st.session_state.ozel_listeler:
        st.markdown("---")
        st.markdown("### 📋 Kayıtlı Listelerim")
        for ad, hisseler in st.session_state.ozel_listeler.items():
            st.markdown(f"**{ad}** ({len(hisseler)} hisse): `{'`, `'.join(hisseler[:10])}{'...' if len(hisseler)>10 else ''}`")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# TARAMA
# ══════════════════════════════════════════════════════════════════════════════
if not hisseler_secilen:
    st.error("Lütfen sol menüden bir grup seçin veya hisse kodlarını girin.")
    st.stop()

# BIST TÜM için uyarı
if len(hisseler_secilen) > 150:
    st.warning(f"⚠️ {len(hisseler_secilen)} hisse taranacak — bu işlem 5-10 dakika sürebilir. Sabırlı olun!")

sonuclar, hatalar = [], []
pb    = st.progress(0)
durum = st.empty()

for i, ticker in enumerate(hisseler_secilen):
    durum.caption(f"⏳ **{ticker}** analiz ediliyor... ({i+1}/{len(hisseler_secilen)})")
    r = analiz_et(ticker, pconf['interval'], pconf['period'], pconf['key'])
    if r:
        sonuclar.append(r)
    else:
        hatalar.append(ticker)
    pb.progress((i + 1) / len(hisseler_secilen))
    # Rate limit: her 5 hissede kısa bekle
    if (i + 1) % 5 == 0:
        time.sleep(0.6)

pb.empty()
durum.empty()

# Filtrele & sırala
filtreli = [r for r in sonuclar if r['skor'] >= min_skor]
if sadece_al:
    filtreli = [r for r in filtreli if r['skor'] >= 55]
filtreli.sort(key=lambda x: x['skor'], reverse=True)

# ── Özet metrikler ────────────────────────────────────────────────────────────
st.markdown(f"### Sonuçlar — {grup_sec} · {periyot_sec} · {len(filtreli)} hisse")
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Başarılı",    len(sonuclar))
c2.metric("🟢 Güçlü AL", sum(1 for r in filtreli if r['skor'] >= 70))
c3.metric("🟩 AL",        sum(1 for r in filtreli if 55 <= r['skor'] < 70))
c4.metric("🟡 Nötr",      sum(1 for r in filtreli if 40 <= r['skor'] < 55))
c5.metric("🔴 SAT",       sum(1 for r in filtreli if 25 <= r['skor'] < 40))
c6.metric("⛔ G.SAT",     sum(1 for r in filtreli if r['skor'] < 25))

if hatalar:
    with st.expander(f"⚠️ {len(hatalar)} hissede veri alınamadı"):
        st.write(", ".join(hatalar))

st.markdown("---")

# Sıralama
sc1, sc2 = st.columns([2, 4])
with sc1:
    siralama = st.selectbox("Sırala", [
        "Puan (Yüksek→Düşük)", "Puan (Düşük→Yüksek)", "Değişim %", "İsim A-Z"
    ])
with sc2:
    filtre2 = st.selectbox("Göster", [
        "Tümü", "Sadece AL & Güçlü AL", "Sadece Nötr", "Sadece SAT & Güçlü SAT"
    ])

if siralama == "Puan (Düşük→Yüksek)":   filtreli.sort(key=lambda x: x['skor'])
elif siralama == "Değişim %":             filtreli.sort(key=lambda x: x['degisim'], reverse=True)
elif siralama == "İsim A-Z":              filtreli.sort(key=lambda x: x['ticker'])

if filtre2 == "Sadece AL & Güçlü AL":      filtreli = [r for r in filtreli if r['skor'] >= 55]
elif filtre2 == "Sadece Nötr":              filtreli = [r for r in filtreli if 40 <= r['skor'] < 55]
elif filtre2 == "Sadece SAT & Güçlü SAT":  filtreli = [r for r in filtreli if r['skor'] < 40]

if not filtreli:
    st.info("Seçilen kriterlere uyan hisse bulunamadı.")
    st.stop()

# ── Kartlar ───────────────────────────────────────────────────────────────────
for r in filtreli:
    etiket, fg, bg, emoji = skor_stil(r['skor'])
    ind = r['ind']
    deg_renk = "green" if r['degisim'] >= 0 else "red"
    deg_str  = f"+{r['degisim']:.2f}%" if r['degisim'] >= 0 else f"{r['degisim']:.2f}%"

    with st.expander(
        f"{emoji} **{r['ticker']}** — {r['fiyat']:.2f} TL  :{deg_renk}[{deg_str}]  |  Skor: **{r['skor']}** ({etiket})",
        expanded=False
    ):
        col_sol, col_sag = st.columns([3, 1])

        with col_sol:
            html = ""
            for key, label, low_good, high_good, low_th, high_th in [
                ('RSI',       'RSI',   45, 60, None, None),
            ]:
                pass

            # Rozetler
            def rozet(label, val, bull):
                rc = '#0d6e3b' if bull is True else '#b83232' if bull is False else '#7a6300'
                rb = '#d4f4e5' if bull is True else '#fde8e8' if bull is False else '#fdf4c7'
                return f'<span class="rozet" style="background:{rb};color:{rc};">{label} {val}</span>'

            if 'RSI' in ind:
                rv = ind['RSI']
                b  = True if rv < 45 else (False if rv > 60 else None)
                html += rozet('RSI', rv, b)
            if 'MACD_yon' in ind:
                b = True if ind['MACD_yon']=='↑' else False
                html += rozet('MACD', ind['MACD_yon'], b)
            if 'BB_pct' in ind:
                bv = ind['BB_pct']
                b  = True if bv < 35 else (False if bv > 65 else None)
                lbl = 'Alt Bant' if bv<35 else 'Üst Bant' if bv>65 else 'Orta Bant'
                html += rozet(f'BB {lbl}', f'%{bv}', b)
            if 'Stoch_K' in ind:
                sv = ind['Stoch_K']
                b  = True if sv < 30 else (False if sv > 70 else None)
                html += rozet('STOCH', sv, b)
            if 'EMA_trend' in ind:
                b = True if '↑' in ind['EMA_trend'] else (False if '↓' in ind['EMA_trend'] else None)
                html += rozet('EMA', ind['EMA_trend'], b)
            if 'MFI' in ind:
                mv = ind['MFI']
                b  = True if mv < 30 else (False if mv > 70 else None)
                html += rozet('MFI', mv, b)

            st.markdown(html, unsafe_allow_html=True)
            st.markdown("")

            # Detay tablosu
            detay = {}
            if 'RSI'       in ind: detay['RSI(14)']    = ind['RSI']
            if 'MACD_yon'  in ind: detay['MACD Yön']   = ind['MACD_yon']
            if 'MACD_hist' in ind: detay['MACD Hist']  = ind['MACD_hist']
            if 'BB_alt'    in ind:
                detay['BB Alt']  = ind['BB_alt']
                detay['BB Orta'] = ind['BB_orta']
                detay['BB Üst']  = ind['BB_ust']
                detay['BB Konum %'] = ind['BB_pct']
            if 'Stoch_K'   in ind: detay['Stoch K']    = ind['Stoch_K']
            if 'Stoch_D'   in ind: detay['Stoch D']    = ind['Stoch_D']
            if 'EMA20'     in ind:
                detay['EMA 20'] = ind['EMA20']
                detay['EMA 50'] = ind['EMA50']
            if 'EMA_trend' in ind: detay['EMA Trend']  = ind['EMA_trend']
            if 'MFI'       in ind: detay['MFI(14)']    = ind['MFI']
            detay['Gün Yüksek'] = f"{r['high']:.2f} TL"
            detay['Gün Düşük']  = f"{r['low']:.2f} TL"
            detay['Hacim']      = f"{r['volume']/1e6:.2f}M lot"

            df_det = pd.DataFrame(list(detay.items()), columns=['İndikatör', 'Değer'])
            st.dataframe(df_det, use_container_width=True, hide_index=True,
                         height=min(len(detay)*36+40, 460))

        with col_sag:
            bar_renk = '#22c55e' if r['skor']>=70 else '#4ade80' if r['skor']>=55 else '#fbbf24' if r['skor']>=40 else '#f87171'
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
    etiket, _, _, _ = skor_stil(r['skor'])
    s = r['ind']
    rows.append({
        'Hisse':        r['ticker'],
        'Fiyat (TL)':   round(r['fiyat'], 2),
        'Değişim (%)':  round(r['degisim'], 2),
        'Yüksek':       round(r['high'], 2),
        'Düşük':        round(r['low'], 2),
        'Skor':         r['skor'],
        'Sinyal':       etiket,
        'RSI(14)':      s.get('RSI', '-'),
        'MACD Yön':     s.get('MACD_yon', '-'),
        'BB Konum%':    s.get('BB_pct', '-'),
        'BB Alt':       s.get('BB_alt', '-'),
        'BB Üst':       s.get('BB_ust', '-'),
        'Stoch K':      s.get('Stoch_K', '-'),
        'EMA20':        s.get('EMA20', '-'),
        'EMA50':        s.get('EMA50', '-'),
        'EMA Trend':    s.get('EMA_trend', '-'),
        'MFI(14)':      s.get('MFI', '-'),
    })

df_exp = pd.DataFrame(rows)
c1, c2 = st.columns([1, 3])
with c1:
    st.download_button(
        "📥 CSV İndir",
        data=df_exp.to_csv(index=False).encode('utf-8-sig'),
        file_name=f"BIST_{grup_sec.replace(' ','_')}_{pconf['key']}.csv",
        mime="text/csv",
        use_container_width=True
    )
