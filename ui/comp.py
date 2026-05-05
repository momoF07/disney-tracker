import streamlit as st
from modules.emojis import get_emoji

def render_weather_card(weather):
    if not weather: return

    from modules.weather import info_weather_code, info_msc, info_dsp
    ressenti = weather.get('feels_like')

    alert = info_weather_code(ressenti, code=weather.get('code'))
    msc   = info_msc(ressenti)
    dsp   = info_dsp(ressenti)

    alert_html = ""
    if alert:
        alert_html = (
            '<div style="margin-top:14px; padding:11px 16px;'
            'background:linear-gradient(135deg,' + alert['color'] + 'cc,' + alert['color'] + '99);'
            'border-radius:14px; border:1px solid ' + alert['color'] + '44;'
            'display:flex; align-items:center; gap:10px;">'
            '<span style="font-size:18px;">⚠️</span>'
            '<div>'
            '<div style="color:white; font-size:12px; font-weight:700; font-family:Outfit,sans-serif; letter-spacing:0.5px;">'
            + alert['code'] + '</div>'
            '<div style="color:rgba(255,255,255,0.75); font-size:11px; margin-top:1px;">' + alert['sub'] + '</div>'
            '</div>'
            '</div>'
        )

    shows_html = ""
    if msc or dsp:
        def get_box(title, data):
            if not data: return ""
            return (
                '<div style="flex:1; min-width:200px; padding:12px 14px;'
                'background:rgba(255,255,255,0.03); border-radius:14px;'
                'border:1px solid rgba(255,255,255,0.07);">'
                '<div style="display:flex; align-items:center; gap:6px; margin-bottom:5px;">'
                '<span style="font-size:11px; font-weight:800; font-family:Outfit,sans-serif;'
                'color:rgba(255,255,255,0.4); text-transform:uppercase; letter-spacing:1px;">' + title + '</span>'
                '<span style="font-size:10px; font-weight:700; padding:1px 7px; border-radius:8px;'
                'background:' + data['color'] + '22; color:' + data['color'] + '; border:1px solid ' + data['color'] + '44;">'
                + data['t'] + '</span>'
                '</div>'
                '<div style="color:rgba(255,255,255,0.7); font-size:11px; line-height:1.5;">' + data['msg'] + '</div>'
                '</div>'
            )
        shows_html = (
            '<div style="display:flex; gap:10px; margin-top:14px; flex-wrap:wrap;">'
            + get_box("🎨 MSC", msc) + get_box("🎭 DSP", dsp) +
            '</div>'
        )

    html = (
        '<div style="background:rgba(255,255,255,0.03); padding:20px 24px; border-radius:24px;'
        'border:1px solid rgba(255,255,255,0.07); margin-bottom:20px;'
        'backdrop-filter:blur(20px); box-shadow:0 20px 60px rgba(0,0,0,0.4), 0 1px 0 rgba(255,255,255,0.05) inset;">'

        # Ligne principale
        '<div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:16px;">'

        # Gauche : emoji + description
        '<div style="display:flex; align-items:center; gap:18px;">'
        '<span style="font-size:52px; line-height:1; filter:drop-shadow(0 0 20px rgba(255,255,255,0.15));">'
        + weather['emoji'] +
        '</span>'
        '<div>'
        '<div style="font-family:Outfit,sans-serif; color:white; font-size:18px; font-weight:700; line-height:1.1;">'
        + weather['desc'] +
        '</div>'
        '<div style="color:#334155; font-size:11px; font-weight:500; margin-top:3px; letter-spacing:0.3px;">'
        '📍 Marne-la-Vallée, France'
        '</div>'
        '</div>'
        '</div>'

        # Droite : température
        '<div style="text-align:right;">'
        '<div style="display:flex; align-items:baseline; gap:6px; justify-content:flex-end;">'
        '<span style="font-family:Outfit,sans-serif; color:white; font-size:24px; font-weight:800; line-height:1;">'
        + str(weather['temp']) +
        '</span>'
        '<span style="font-family:Outfit,sans-serif; color:rgba(255,255,255,0.4); font-size:18px; font-weight:700;">°C</span>'
        '</div>'
        '<div style="color:rgba(255,255,255,0.35); font-size:12px; font-weight:500; margin-top:2px;">'
        'Ressenti ' + str(ressenti) + '°C'
        '</div>'
        '<div style="color:rgba(255,255,255,0.45); font-size:11px; font-weight:500; margin-top:4px; letter-spacing:0.3px;">'
        '💨 ' + weather['wind'] + ' &nbsp;·&nbsp; 🚩 ' + weather['gusts'] +
        '</div>'
        '</div>'
        '</div>'

        + alert_html + shows_html +
        '</div>'
    )

    st.markdown(html, unsafe_allow_html=True)


def render_api_info(api_time, refresh_time):
    st.markdown(
        '<div style="display:flex; justify-content:space-between; align-items:center;'
        'background:rgba(255,255,255,0.02); padding:10px 16px; border-radius:14px;'
        'border:1px solid rgba(255,255,255,0.05); margin-bottom:14px;">'
        '<div style="display:flex; align-items:center; gap:6px;">'
        '<span style="width:6px; height:6px; background:#34d399; border-radius:50%;'
        'box-shadow:0 0 8px #34d399; display:inline-block; animation:pulse 2s infinite;"></span>'
        '<span style="color:#334155; font-size:11px;">API :</span>'
        '<span style="color:rgba(255,255,255,0.6); font-size:11px; font-weight:600;">' + api_time + '</span>'
        '</div>'
        '<div style="color:#1e293b; font-size:10px;">· · ·</div>'
        '<div>'
        '<span style="color:#334155; font-size:11px;">Refresh :</span>'
        '<span style="color:rgba(255,255,255,0.6); font-size:11px; font-weight:600; margin-left:5px;">' + refresh_time + '</span>'
        '</div>'
        '</div>'
        '<style>@keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:0.4;} }</style>',
        unsafe_allow_html=True
    )


def render_ride_card(ride, sub, wait, bg, card_style, pill, show_wait=True):
    wait_section = ""
    flex_style = ""

    if show_wait:
        wait_html = '<span class="wait-val">' + str(wait) + '</span>'
        if str(wait).isdigit():
            wait_html += '<span class="wait-unit">min</span>'
        wait_section = (
            '<div class="ride-right-wait ' + bg + '">'
            '<span style="font-size:8px; opacity:0.5; font-weight:600; letter-spacing:0.5px; text-transform:uppercase; margin-bottom:1px;">Attente</span>'
            + wait_html +
            '</div>'
        )
    else:
        flex_style = "flex-grow:1;"

    st.markdown(
        '<div class="ride-row">'
        '<div class="ride-left-card ' + card_style + '" style="' + flex_style + '">'
        '<div class="ride-info-meta">'
        '<span style="font-size:22px; line-height:1;">' + get_emoji(ride) + '</span>'
        '<div class="ride-titles">'
        '<p class="ride-main-name">' + ride + '</p>'
        '<p class="ride-sub-status">' + sub + '</p>'
        '</div>'
        '</div>'
        '<div class="state-pill">' + pill + '</div>'
        '</div>'
        + wait_section +
        '</div>',
        unsafe_allow_html=True
    )


def render_park_hours(schedules):
    if not schedules: return

    parks = [s for s in schedules if s.get('type') == 'PARK']
    emts  = {s['ride_name'].replace('EMT ', ''): s['opening_time'] for s in schedules if s.get('type') == 'EMT'}

    if not parks: return

    boxes = ""
    for p in parks:
        is_dlp   = "Disneyland" in p['ride_name']
        name     = "Disneyland Park" if is_dlp else "Disney Adventure World"
        color    = "#ffb3d1" if is_dlp else "#fb923c"
        emt_time = emts.get(p['ride_name'])
        opening  = p['opening_time'][:5]
        closing  = p['closing_time'][:5]

        emt_html = ""
        if emt_time:
            emt_html = (
                '<div style="margin-top:8px; display:inline-flex; align-items:center; gap:5px;'
                'background:rgba(167,139,250,0.1); border:1px solid rgba(167,139,250,0.2);'
                'padding:3px 10px; border-radius:20px;">'
                '<span style="font-size:10px;">✨</span>'
                '<span style="color:#a78bfa; font-size:10px; font-weight:700;">EMT ' + emt_time[:5] + ' → ' + opening + '</span>'
                '</div>'
            )

        boxes += (
            '<div style="flex:1; min-width:150px; padding:16px 18px;'
            'background:rgba(255,255,255,0.02); border-radius:18px;'
            'border:1px solid rgba(255,255,255,0.06);'
            'border-top:2px solid ' + color + '66;">'
            '<div style="font-family:Outfit,sans-serif; font-size:9px; color:' + color + '; font-weight:700;'
            'text-transform:uppercase; letter-spacing:1.5px; margin-bottom:6px; opacity:0.8;">' + name + '</div>'
            '<div style="font-family:Outfit,sans-serif; font-size:22px; color:white; font-weight:700; line-height:1;">'
            + opening + ' <span style="color:rgba(255,255,255,0.25); font-size:16px;">→</span> ' + closing +
            '</div>'
            + emt_html +
            '</div>'
        )

    st.markdown(
        '<div style="background:rgba(255,255,255,0.03); padding:18px 20px; border-radius:22px;'
        'border:1px solid rgba(255,255,255,0.07); margin-bottom:16px; backdrop-filter:blur(20px);'
        'box-shadow:0 20px 40px rgba(0,0,0,0.3);">'
        '<div style="font-family:Outfit,sans-serif; color:rgba(255,255,255,0.4); font-size:9.5px;'
        'font-weight:700; text-transform:uppercase; letter-spacing:2px; margin-bottom:14px;">🕒 Horaires des parcs</div>'
        '<div style="display:flex; gap:12px; flex-wrap:wrap;">' + boxes + '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    # --- RADIO DISNEY VILLAGE ---
    radio_html = """<!DOCTYPE html>
<html>
<head>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@500;600;700&display=swap');
  * { margin:0; padding:0; box-sizing:border-box; }

  body {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 22px;
    font-family: Outfit, sans-serif;
    padding: 14px 20px;
    overflow: hidden;
  }

  .label {
    font-size: 8.5px; color: rgba(255,255,255,0.25);
    font-weight: 700; text-transform: uppercase;
    letter-spacing: 2px; margin-bottom: 10px;
    display: block;
  }

  .player {
    display: flex;
    align-items: center;
    gap: 14px;
  }

  @keyframes rpulse { 0%,100%{opacity:1; transform:scale(1);} 50%{opacity:0.4; transform:scale(0.8);} }
  @keyframes eq1 { 0%,100%{height:4px;} 50%{height:14px;} }
  @keyframes eq2 { 0%,100%{height:11px;} 50%{height:3px;} }
  @keyframes eq3 { 0%,100%{height:6px;} 50%{height:16px;} }
  @keyframes eq4 { 0%,100%{height:13px;} 50%{height:4px;} }

  .eq { display:flex; align-items:flex-end; gap:3px; height:18px; flex-shrink:0; }
  .eq span { width:3px; border-radius:3px; background:linear-gradient(to top,#a78bfa,#7dd3fc); }
  .eq span:nth-child(1) { animation:eq1 0.85s ease-in-out infinite; }
  .eq span:nth-child(2) { animation:eq2 0.65s ease-in-out infinite; }
  .eq span:nth-child(3) { animation:eq3 1.05s ease-in-out infinite; }
  .eq span:nth-child(4) { animation:eq4 0.75s ease-in-out infinite; }
  .eq.stopped span { animation:none !important; height:3px !important; opacity:0.2; }

  .info { flex:1; min-width:0; }
  .info .name { font-size:12px; font-weight:700; color:rgba(255,255,255,0.8); }
  .info .sub  { font-size:9px; color:rgba(255,255,255,0.22); font-weight:500; margin-top:2px; }

  #btn-mute {
    width:34px; height:34px; border-radius:50%; border:none;
    background:linear-gradient(135deg,#a78bfa,#7dd3fc);
    box-shadow:0 0 16px rgba(167,139,250,0.4);
    font-size:15px; cursor:pointer; flex-shrink:0;
    display:flex; align-items:center; justify-content:center;
    transition:transform 0.15s ease, box-shadow 0.15s ease;
  }
  #btn-mute:hover { transform:scale(1.12); box-shadow:0 0 24px rgba(167,139,250,0.6); }
  #btn-mute:active { transform:scale(0.93); }

  .vol-wrap { display:flex; align-items:center; gap:6px; flex-shrink:0; }
  input[type=range] { width:72px; height:3px; border-radius:3px; accent-color:#a78bfa; cursor:pointer; }
  .vol-pct { font-size:9px; color:#475569; min-width:26px; text-align:right; font-weight:600; }

  .live { display:flex; align-items:center; gap:4px; flex-shrink:0; }
  .live-dot {
    width:5px; height:5px; border-radius:50%;
    background:#34d399; box-shadow:0 0 8px #34d399;
    animation:rpulse 2s ease-in-out infinite;
  }
  .live-txt { font-size:8px; color:#34d399; font-weight:700; text-transform:uppercase; letter-spacing:1.2px; }
</style>
</head>
<body>
  <span class="label">🎵 Radio Disney Village</span>

  <div class="player">
    <div class="eq" id="eq">
      <span></span><span></span><span></span><span></span>
    </div>

    <div class="info">
      <div class="name">Radio Disney Village</div>
      <div class="sub">Diffusion continue — Disney Village, Marne-la-Vallée</div>
    </div>

    <button id="btn-mute" onclick="toggleMute()">🔇</button>

    <div class="vol-wrap">
      <input id="vol" type="range" min="0" max="100" value="0">
      <span class="vol-pct" id="pct">0%</span>
    </div>

    <div class="live">
      <div class="live-dot"></div>
      <span class="live-txt">En direct</span>
    </div>
  </div>

  <audio id="audio" src="https://webradio.ice.infomaniak.ch/webradio-128.mp3" preload="none"></audio>

  <script>
    var audio  = document.getElementById('audio');
    var slider = document.getElementById('vol');
    var btn    = document.getElementById('btn-mute');
    var pct    = document.getElementById('pct');
    var eq     = document.getElementById('eq');
    var going  = false;

    audio.volume = 0;

    function boot() {
      if (going) return;
      audio.load();
      audio.play().catch(function(){});
      going = true;
    }

    function applyVol(v) {
      audio.volume = v / 100;
      pct.textContent = v + '%';
      btn.textContent = v == 0 ? '🔇' : v < 50 ? '🔉' : '🔊';
      eq.classList.toggle('stopped', v == 0);
    }

    function toggleMute() {
      boot();
      if (audio.volume > 0) { slider.value = 0; applyVol(0); }
      else                  { slider.value = 70; applyVol(70); }
    }

    slider.addEventListener('input', function() {
      boot();
      applyVol(parseInt(this.value));
    });
  </script>
</body>
</html>"""

    st.iframe(radio_html, height=100)


def render_upcoming_shows(schedules):
    import datetime as dt
    import re
    from zoneinfo import ZoneInfo

    if not schedules: return

    HIDDEN_SHOWS = ["philharmagic", "reserved viewing", "animation academy"]
    PARKS = [
        {"label": "Disneyland Park", "prefix": "Disneyland Park", "color": "#ffb3d1"},
        {"label": "Adventure World",  "prefix": "Adventure World",  "color": "#fb923c"},
    ]

    now_paris = dt.datetime.now(ZoneInfo("Europe/Paris"))
    now_str   = now_paris.strftime("%H:%M")

    all_shows = []
    for park_index, park in enumerate(PARKS):
        for s in schedules:
            if s.get('type') != 'SHOW': continue
            if f"[{park['prefix']}]" not in s['ride_name']: continue
            hhmm = s['opening_time'][:5]
            if hhmm < now_str: continue
            clean_name = re.sub(r'^\[.*?\]\s*', '', s['ride_name'])
            clean_name = re.sub(r'\s*\(\d{2}:\d{2}\)$', '', clean_name)
            if any(h in clean_name.lower() for h in HIDDEN_SHOWS): continue
            all_shows.append({**s, '_park_index': park_index, '_paris_time': hhmm,
                               '_clean_name': clean_name, '_color': park['color'], '_park_label': park['label']})

    all_shows = sorted(all_shows, key=lambda x: (x['_park_index'], x['_paris_time']))

    grouped = {}
    for show in all_shows:
        key = show['_park_label']
        if key not in grouped: grouped[key] = []
        if len(grouped[key]) < 3: grouped[key].append(show)

    def make_rows(shows, color):
        if not shows:
            return '<div style="color:#1e293b; font-size:11px; padding:8px 4px;">Plus de spectacles aujourd\'hui.</div>'
        rows = ""
        for s in shows:
            rows += (
                '<div style="display:flex; justify-content:space-between; align-items:center;'
                'padding:9px 12px; background:rgba(255,255,255,0.02); border-radius:12px;'
                'margin-bottom:6px; border:1px solid rgba(255,255,255,0.04);">'
                '<span style="color:rgba(255,255,255,0.75); font-size:12.5px; font-weight:500;">'
                '🎭 ' + s['_clean_name'] + '</span>'
                '<span style="font-family:Outfit,sans-serif; color:' + color + '; font-size:12px; font-weight:800;'
                'background:' + color + '15; border:1px solid ' + color + '30;'
                'padding:2px 10px; border-radius:8px; letter-spacing:0.5px;">'
                + s['_paris_time'] + '</span>'
                '</div>'
            )
        return rows

    sections = ""
    for i, park in enumerate(PARKS):
        shows = grouped.get(park['label'], [])
        divider = '<div style="height:1px; background:rgba(255,255,255,0.05); margin:12px 0;"></div>' if i > 0 else ""
        sections += (
            divider +
            '<div style="font-family:Outfit,sans-serif; font-size:9px; font-weight:700;'
            'text-transform:uppercase; letter-spacing:1.5px; color:' + park['color'] + '; opacity:0.8;'
            'margin-bottom:9px;">' + park['label'] + '</div>'
            + make_rows(shows, park['color'])
        )

    st.markdown(
        '<div style="background:rgba(255,255,255,0.03); padding:18px 20px; border-radius:22px;'
        'border:1px solid rgba(255,255,255,0.07); margin-bottom:16px; backdrop-filter:blur(20px);'
        'box-shadow:0 20px 40px rgba(0,0,0,0.3);">'
        '<div style="font-family:Outfit,sans-serif; color:rgba(255,255,255,0.4); font-size:9.5px;'
        'font-weight:700; text-transform:uppercase; letter-spacing:2px; margin-bottom:14px;">✨ Prochaines représentations</div>'
        + sections +
        '</div>',
        unsafe_allow_html=True
    )