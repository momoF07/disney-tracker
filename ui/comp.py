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
        '<div class="ride-left-card ' + card_style + '">'
        '<div class="ride-info-meta">'
        '<span style="font-size:20px; line-height:1; flex-shrink:0;">' + get_emoji(ride) + '</span>'
        '<div class="ride-titles">'
        '<p class="ride-main-name">' + ride + '</p>'
        '<p class="ride-sub-status">' + sub + '</p>'
        '</div>'
        '</div>'
        '<div class="state-pill" style="align-self:flex-start; margin-top:2px; flex-shrink:0;">' + pill + '</div>'
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
            '<div style="font-family:Outfit,sans-serif; font-size:12px; color:' + color + '; font-weight:700;'
            'text-transform:uppercase; letter-spacing:1.5px; margin-bottom:6px; opacity:0.8;">' + name + '</div>'
            '<div style="font-family:Outfit,sans-serif; font-size:10px; color:white; font-weight:700; line-height:1;">'
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
    background: transparent;
    font-family: Outfit, sans-serif;
    padding: 16px 20px;
    overflow: hidden;
  }

  @keyframes rpulse { 0%,100%{opacity:1;} 50%{opacity:0.3;} }

  .header {
    display: flex; align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
  }
  .title {
    font-size: 9.5px; color: rgba(255,255,255,0.4);
    font-weight: 700; text-transform: uppercase; letter-spacing: 2px;
  }
  .status { display: flex; align-items: center; gap: 6px; }
  #radio-dot {
    width: 6px; height: 6px; background: #334155;
    border-radius: 50%; display: inline-block;
    transition: background 0.3s, box-shadow 0.3s;
  }
  #radio-dot.live { background: #34d399; box-shadow: 0 0 8px #34d399; animation: rpulse 2s infinite; }
  #radio-label {
    font-size: 9px; color: #334155; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1px;
    transition: color 0.3s;
  }
  #radio-label.live { color: #34d399; }

  .controls { display: flex; align-items: center; gap: 10px; }

  #btn-mute {
    background: linear-gradient(135deg, #c4b5fd, #7dd3fc);
    border: none; border-radius: 50%;
    width: 40px; height: 40px;
    cursor: pointer; font-size: 18px; flex-shrink: 0;
    box-shadow: 0 4px 15px rgba(196,181,253,0.3);
    display: flex; align-items: center; justify-content: center;
    transition: transform 0.15s, box-shadow 0.15s;
  }
  #btn-mute:hover { transform: scale(1.1); box-shadow: 0 6px 20px rgba(196,181,253,0.5); }
  #btn-mute:active { transform: scale(0.93); }

  .vol-row { flex: 1; display: flex; align-items: center; gap: 8px; }
  input[type=range] {
    flex: 1; height: 4px; border-radius: 4px;
    accent-color: #c4b5fd; cursor: pointer;
  }
  #vol-label { font-size: 10px; color: #475569; min-width: 28px; text-align: right; }
</style>
</head>
<body>

  <div class="header">
    <span class="title">🎵 Radio Disney Village (Ne pas utiliser sur mobile pour le moment)</span>
    <div class="status">
      <span id="radio-dot"></span>
      <span id="radio-label">En veille</span>
    </div>
  </div>

  <div class="controls">
    <button id="btn-mute" onclick="toggleMute()">🔇</button>
    <div class="vol-row">
      <input id="vol-slider" type="range" min="0" max="100" value="0">
      <span id="vol-label">0%</span>
    </div>
  </div>

  <audio id="audio" src="https://webradio.ice.infomaniak.ch/webradio-128.mp3" preload="auto"></audio>

  <script>
    var audio   = document.getElementById('audio');
    var slider  = document.getElementById('vol-slider');
    var btn     = document.getElementById('btn-mute');
    var label   = document.getElementById('vol-label');
    var dot     = document.getElementById('radio-dot');
    var lbl     = document.getElementById('radio-label');
    var started = false;

    audio.volume = 0;

    function boot() {
      if (started) return;
      audio.load();
      audio.play().catch(function(){});
      started = true;
      dot.classList.add('live');
      lbl.classList.add('live');
      lbl.textContent = 'En direct';
    }

    function setVolume(v) {
      audio.volume = v / 100;
      label.textContent = v + '%';
      btn.textContent = v == 0 ? '🔇' : v < 50 ? '🔉' : '🔊';
    }

    function toggleMute() {
      boot();
      if (audio.volume > 0) {
        slider.value = 0; setVolume(0);
      } else {
        slider.value = 70; setVolume(70);
      }
    }

    slider.addEventListener('input', function() {
      boot();
      setVolume(parseInt(this.value));
    });
  </script>
</body>
</html>"""

    st.markdown(
        '<div style="border-radius:22px; overflow:hidden; margin-bottom:16px;'
        'border:1px solid rgba(255,255,255,0.07); box-shadow:0 20px 40px rgba(0,0,0,0.3);">',
        unsafe_allow_html=True
    )
    #st.iframe(radio_html, height=110)
    st.markdown('</div>', unsafe_allow_html=True)


def render_upcoming_shows(schedules):
    import datetime as dt
    import re
    from zoneinfo import ZoneInfo

    if not schedules: return

    HIDDEN_SHOWS = ["philharmagic", "reserved viewing", "animation academy"]
    #HIDDEN_SHOWS = []
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