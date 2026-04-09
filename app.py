import streamlit as st
import yfinance as yf
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
  .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
  .rozet {
    display: inline-block; padding: 3px 10px; border-radius: 5px;
    font-size: 12px; font-weight: 600; margin: 2px;
  }
  .baslik {
    background: linear-gradient(135deg, #cc0000, #990000);
    color: white; padding: 20px 24px; border-radius: 14px;
    margin-bottom: 20px;
  }
</style>
""", unsafe_allow_html=True)

# ── Sabitler ──────────────────────────────────────────────────────────────────
BIST100 = [
    'THYAO','GARAN','AKBNK','EREGL','SISE','KCHOL','BIMAS','SAHOL','PGSUS','TUPRS',
    'FROTO','TOASO','ASELS','TCELL','KOZAL','EKGYO','ISCTR','HEKTS','MGROS','DOHOL',
    'TAVHL','ARCLK','ULKER','PETKM','CCOLA','ENKAI','KRDMD','VAKBN','SODA','TTKOM',
    'AEFES','OYAKC','ALARK','AKSEN','YKBNK','LOGO','MAVI','BERA','ENJSA','VESTL',
    'CIMSA','EGEEN','NETAS','KARSN','KONTR','IPEKE','ISGYO','GOLTS','GLYHO','KLNMA',
    'AGHOL','ANACM','BRSAN','BRYAT','BTCIM','DOAS','EUPWR','GESAN','GUBRF','HATEK',
    'IMASM','INDES','ISDMR','ISFIN','KAREL','KARTN','KERVT','KRSUS',
    'MPARK','NTTUR','ODAS','REEDR','RNPOL','RYSAS','SELEC','SKBNK',
    'SOKM','TATGD','TKFEN','TKNSA','TMSN'
]
BIST100 = list(dict.fromkeys(BIST100))

PERIYOT_MAP = {
    '1 Saatlik': {'interval': '1h',  'period': '7d',   'key': '1h'},
    '4 Saatlik': {'interval': '1h',  'period': '30d',  'key': '4h'},
    'Günlük':    {'interval': '1d',  'period': '180d', 'key': '1d'},
}

# ── Yardımcı fonksiyonlar ─────────────────────────────────────────────────────
def resample_4h(df):
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    return df.resample('4h').agg({
        'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'
    }).dropna()

def hesapla_indiktorler(df):
    """ta kütüphanesi ile indikatör hesapla"""
    if len(df) < 30:
        return None
    df = df.copy()
    close  = df['Close']
    high   = df['High']
    low    = df['Low']
    volume = df['Volume']

    # RSI
    df['RSI'] = ta.momentum.RSIIndicator(close, window=14).rsi()

    # MACD
    macd_ind = ta.trend.MACD(close, window_slow=26, window_fast=12, window_sign=9)
    df['MACD']      = macd_ind.macd()
    df['MACD_sig']  = macd_ind.macd_signal()
    df['MACD_hist'] = macd_ind.macd_diff()

    # Bollinger Bands
    bb_ind = ta.volatility.BollingerBands(close, window=20, window_dev=2)
    df['BB_upper']  = bb_ind.bollinger_hband()
    df['BB_lower']  = bb_ind.bollinger_lband()
    df['BB_middle'] = bb_ind.bollinger_mavg()

    # Stochastic
    stoch_ind = ta.momentum.StochasticOscillator(high, low, close, window=14, smooth_window=3)
    df['STOCH_K'] = stoch_ind.stoch()
    df['STOCH_D'] = stoch_ind.stoch_signal()

    # EMA 20 & 50
    df['EMA20'] = ta.trend.EMAIndicator(close, window=20).ema_indicator()
    df['EMA50'] = ta.trend.EMAIndicator(close, window=50).ema_indicator()

    # MFI
    df['MFI'] = ta.volume.MFIIndicator(high, low, close, volume, window=14).money_flow_index()

    return df

def skor_hesapla(row, close):
    skor = 50
    ind  = {}

    # RSI
    rsi = row.get('RSI')
    if pd.notna(rsi):
        ind['RSI'] = round(float(rsi), 1)
        if rsi < 25:   skor += 22
        elif rsi < 35: skor += 14
        elif rsi < 45: skor += 6
        elif rsi > 75: skor -= 22
        elif rsi > 65: skor -= 14
        elif rsi > 55: skor -= 6

    # MACD
    macd_h = row.get('MACD_hist')
    macd_v = row.get('MACD')
    if pd.notna(macd_h):
        ind['MACD_hist'] = round(float(macd_h), 4)
        ind['MACD_yon']  = '↑' if macd_h > 0 else '↓'
        if macd_h > 0 and pd.notna(macd_v) and macd_v < 0:    skor += 18
        elif macd_h > 0:                                        skor += 10
        elif macd_h < 0 and pd.notna(macd_v) and macd_v > 0:  skor -= 18
        else:                                                    skor -= 10

    # Bollinger Bands
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

    # Stochastic
    stk = row.get('STOCH_K')
    std = row.get('STOCH_D')
    if pd.notna(stk):
        ind['Stoch_K'] = round(float(stk), 1)
        ind['Stoch_D'] = round(float(std), 1) if pd.notna(std) else None
        if stk < 20:   skor += 14
        elif stk < 30: skor += 7
        elif stk > 80: skor -= 14
        elif stk > 70: skor -= 7

    # EMA trend
    ema20 = row.get('EMA20')
    ema50 = row.get('EMA50')
    if pd.notna(ema20) and pd.notna(ema50) and close:
        ema20, ema50 = float(ema20), float(ema50)
        ind['EMA20'] = round(ema20, 2)
        ind['EMA50'] = round(ema50, 2)
        if close > ema20 > ema50:
            ind['EMA_trend'] = '↑ Yükseliş'; skor += 10
        elif close < ema20 < ema50:
            ind['EMA_trend'] = '↓ Düşüş';   skor -= 10
        else:
            ind['EMA_trend'] = '→ Nötr'

    # MFI
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
        df = yf.download(
            ticker + '.IS',
            interval=interval,
            period=period,
            progress=False,
            auto_adjust=True
        )
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
        son  = df.iloc[-1]
        prev = df.iloc[-2]
        close     = float(son['Close'])
        prev_close = float(prev['Close'])
        skor, ind = skor_hesapla(son, close)
        return {
            'ticker':  ticker,
            'fiyat':   close,
            'degisim': ((close - prev_close) / prev_close) * 100,
            'high':    float(son['High']),
            'low':     float(son['Low']),
            'volume':  float(son['Volume']),
            'skor':    skor,
            'ind':     ind,
        }
    except Exception:
        return None

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Ayarlar")
    st.markdown("---")

    mod = st.radio("Tarama Modu", ["BIST 100 (Tümü)", "Özel Hisseler"])

    ozel = []
    if mod == "Özel Hisseler":
        girdi = st.text_area(
            "Hisse kodları (her satıra bir tane veya virgülle ayır)",
            placeholder="OYAKC\nTHYAO\nGARAN",
            height=130
        )
        if girdi.strip():
            ozel = [h.strip().upper().replace('.IS', '')
                    for h in girdi.replace(',', '\n').split('\n') if h.strip()]
            if ozel:
                st.success(f"{len(ozel)} hisse seçildi")

    st.markdown("---")
    periyot_sec = st.selectbox("Periyot", list(PERIYOT_MAP.keys()))
    pconf = PERIYOT_MAP[periyot_sec]

    st.markdown("---")
    st.markdown("**Filtreler**")
    sadece_al = st.checkbox("Sadece AL sinyalleri (%55+)")
    min_skor  = st.slider("Minimum skor", 0, 100, 0, 5)

    st.markdown("---")
    tara_btn = st.button("🔍 TARA", use_container_width=True, type="primary")

    st.markdown("---")
    st.caption("📡 Veri: Yahoo Finance · 15dk gecikmeli\n\nÖnbellek: 15 dakika")

# ── Ana sayfa ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="baslik">
  <div style="font-size:24px;font-weight:700;">📈 BIST Teknik Tarayıcı</div>
  <div style="opacity:0.85;margin-top:4px;font-size:14px;">
    RSI · MACD · Bollinger Bantları · Stochastic · EMA · MFI
  </div>
</div>
""", unsafe_allow_html=True)

if not tara_btn:
    col1, col2, col3 = st.columns(3)
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
        - Bollinger Bantları(20,2)
        - Stochastic(14,3)
        - EMA 20 & 50
        - MFI(14)
        """)
    with col3:
        st.markdown("""
        **Periyotlar**
        - 1 Saatlik (son 7 gün verisi)
        - 4 Saatlik (son 30 gün verisi)
        - Günlük (son 180 gün verisi)
        """)
    st.info("👈 Sol menüden ayarları yap ve **TARA** butonuna bas.")
    st.stop()

# ── Tarama ────────────────────────────────────────────────────────────────────
hisseler = BIST100 if mod == "BIST 100 (Tümü)" else ozel
if not hisseler:
    st.error("Lütfen en az bir hisse kodu girin.")
    st.stop()

sonuclar = []
hatalar  = []
pb       = st.progress(0)
durum    = st.empty()

for i, ticker in enumerate(hisseler):
    durum.caption(f"⏳ **{ticker}** analiz ediliyor... ({i+1}/{len(hisseler)})")
    r = analiz_et(ticker, pconf['interval'], pconf['period'], pconf['key'])
    if r:
        sonuclar.append(r)
    else:
        hatalar.append(ticker)
    pb.progress((i + 1) / len(hisseler))
    if (i + 1) % 5 == 0:
        time.sleep(0.8)

pb.empty()
durum.empty()

# Filtrele & sırala
filtreli = [r for r in sonuclar if r['skor'] >= min_skor]
if sadece_al:
    filtreli = [r for r in filtreli if r['skor'] >= 55]
filtreli.sort(key=lambda x: x['skor'], reverse=True)

# ── Özet ─────────────────────────────────────────────────────────────────────
st.markdown(f"### Sonuçlar — {periyot_sec} · {len(filtreli)} hisse")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Toplam",      len(filtreli))
c2.metric("🟢 Güçlü AL", sum(1 for r in filtreli if r['skor'] >= 70))
c3.metric("🟩 AL",        sum(1 for r in filtreli if 55 <= r['skor'] < 70))
c4.metric("🟡 Nötr",      sum(1 for r in filtreli if 40 <= r['skor'] < 55))
c5.metric("🔴 SAT",       sum(1 for r in filtreli if r['skor'] < 40))

if hatalar:
    st.warning(f"Veri alınamayan hisseler ({len(hatalar)}): {', '.join(hatalar)}")

st.markdown("---")

# Sıralama
siralama = st.selectbox("Sırala", [
    "Puan (Yüksek→Düşük)", "Puan (Düşük→Yüksek)", "Değişim %", "İsim A-Z"
])
if siralama == "Puan (Düşük→Yüksek)":
    filtreli.sort(key=lambda x: x['skor'])
elif siralama == "Değişim %":
    filtreli.sort(key=lambda x: x['degisim'], reverse=True)
elif siralama == "İsim A-Z":
    filtreli.sort(key=lambda x: x['ticker'])

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
            # Rozetler
            html = ""
            if 'RSI' in ind:
                rv = ind['RSI']
                rc = '#0d6e3b' if rv<45 else '#b83232' if rv>60 else '#7a6300'
                rb = '#d4f4e5' if rv<45 else '#fde8e8' if rv>60 else '#fdf4c7'
                html += f'<span class="rozet" style="background:{rb};color:{rc};">RSI {rv}</span>'

            if 'MACD_yon' in ind:
                mc = '#0d6e3b' if ind['MACD_yon']=='↑' else '#b83232'
                mb = '#d4f4e5' if ind['MACD_yon']=='↑' else '#fde8e8'
                html += f'<span class="rozet" style="background:{mb};color:{mc};">MACD {ind["MACD_yon"]}</span>'

            if 'BB_pct' in ind:
                bv = ind['BB_pct']
                bc = '#0d6e3b' if bv<35 else '#b83232' if bv>65 else '#7a6300'
                bb2 = '#d4f4e5' if bv<35 else '#fde8e8' if bv>65 else '#fdf4c7'
                bl  = 'Alt Bant' if bv<35 else 'Üst Bant' if bv>65 else 'Orta Bant'
                html += f'<span class="rozet" style="background:{bb2};color:{bc};">BB {bl} %{bv}</span>'

            if 'Stoch_K' in ind:
                sv = ind['Stoch_K']
                sc = '#0d6e3b' if sv<30 else '#b83232' if sv>70 else '#7a6300'
                sb = '#d4f4e5' if sv<30 else '#fde8e8' if sv>70 else '#fdf4c7'
                html += f'<span class="rozet" style="background:{sb};color:{sc};">STOCH {sv}</span>'

            if 'EMA_trend' in ind:
                ec = '#0d6e3b' if '↑' in ind['EMA_trend'] else '#b83232' if '↓' in ind['EMA_trend'] else '#7a6300'
                eb = '#d4f4e5' if '↑' in ind['EMA_trend'] else '#fde8e8' if '↓' in ind['EMA_trend'] else '#fdf4c7'
                html += f'<span class="rozet" style="background:{eb};color:{ec};">EMA {ind["EMA_trend"]}</span>'

            if 'MFI' in ind:
                mfv = ind['MFI']
                mfc = '#0d6e3b' if mfv<30 else '#b83232' if mfv>70 else '#7a6300'
                mfb = '#d4f4e5' if mfv<30 else '#fde8e8' if mfv>70 else '#fdf4c7'
                html += f'<span class="rozet" style="background:{mfb};color:{mfc};">MFI {mfv}</span>'

            st.markdown(html, unsafe_allow_html=True)
            st.markdown("")

            # Detay tablosu
            detay = {}
            if 'RSI'       in ind: detay['RSI(14)']     = ind['RSI']
            if 'MACD_yon'  in ind: detay['MACD Yön']    = ind['MACD_yon']
            if 'MACD_hist' in ind: detay['MACD Hist']   = ind['MACD_hist']
            if 'BB_alt'    in ind:
                detay['BB Alt']  = ind['BB_alt']
                detay['BB Orta'] = ind['BB_orta']
                detay['BB Üst']  = ind['BB_ust']
            if 'Stoch_K'   in ind: detay['Stoch K']     = ind['Stoch_K']
            if 'Stoch_D'   in ind: detay['Stoch D']     = ind['Stoch_D']
            if 'EMA20'     in ind:
                detay['EMA 20']  = ind['EMA20']
                detay['EMA 50']  = ind['EMA50']
            if 'EMA_trend' in ind: detay['EMA Trend']   = ind['EMA_trend']
            if 'MFI'       in ind: detay['MFI(14)']     = ind['MFI']
            detay['Günlük Yüksek'] = f"{r['high']:.2f} TL"
            detay['Günlük Düşük']  = f"{r['low']:.2f} TL"
            detay['Hacim']          = f"{r['volume']/1e6:.1f}M lot"

            df_det = pd.DataFrame(list(detay.items()), columns=['İndikatör', 'Değer'])
            st.dataframe(df_det, use_container_width=True, hide_index=True,
                         height=min(len(detay)*35+40, 420))

        with col_sag:
            st.markdown(f"""
            <div style="text-align:center;padding:16px;">
              <div style="width:80px;height:80px;border-radius:50%;
                          background:{bg};color:{fg};
                          display:flex;align-items:center;justify-content:center;
                          font-size:26px;font-weight:700;margin:0 auto;">
                {r['skor']}
              </div>
              <div style="font-size:13px;font-weight:700;color:{fg};margin-top:8px;">{etiket}</div>
              <div style="margin-top:12px;">
                <div style="font-size:11px;color:#888;margin-bottom:4px;">Sinyal Gücü</div>
                <div style="background:#eee;border-radius:4px;height:8px;">
                  <div style="width:{r['skor']}%;
                               background:{'#22c55e' if r['skor']>=70 else '#4ade80' if r['skor']>=55 else '#fbbf24' if r['skor']>=40 else '#f87171'};
                               height:8px;border-radius:4px;"></div>
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
        'Hisse':       r['ticker'],
        'Fiyat (TL)':  round(r['fiyat'], 2),
        'Değişim (%)': round(r['degisim'], 2),
        'Yüksek':      round(r['high'], 2),
        'Düşük':       round(r['low'], 2),
        'Skor':        r['skor'],
        'Sinyal':      etiket,
        'RSI(14)':     s.get('RSI', '-'),
        'MACD Yön':    s.get('MACD_yon', '-'),
        'BB Konum%':   s.get('BB_pct', '-'),
        'BB Alt':      s.get('BB_alt', '-'),
        'BB Üst':      s.get('BB_ust', '-'),
        'Stoch K':     s.get('Stoch_K', '-'),
        'EMA20':       s.get('EMA20', '-'),
        'EMA50':       s.get('EMA50', '-'),
        'EMA Trend':   s.get('EMA_trend', '-'),
        'MFI(14)':     s.get('MFI', '-'),
    })

df_exp = pd.DataFrame(rows)
col1, col2 = st.columns([1, 3])
with col1:
    st.download_button(
        label="📥 CSV İndir",
        data=df_exp.to_csv(index=False).encode('utf-8-sig'),
        file_name=f"BIST_Tarama_{pconf['key']}.csv",
        mime="text/csv",
        use_container_width=True
    )
