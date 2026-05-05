import streamlit as st

def show_maintenance():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800;900&family=Mulish:wght@300;400;500&display=swap');

        .stApp {
            background: radial-gradient(ellipse 80% 50% at 20% -10%, rgba(120,80,255,0.15) 0%, transparent 60%),
                        radial-gradient(ellipse 60% 40% at 80% 110%, rgba(255,100,150,0.1) 0%, transparent 55%),
                        radial-gradient(ellipse 100% 80% at 50% 50%, #090d1a 0%, #060910 100%);
            overflow: hidden;
        }

        /* === CANVAS FEUX D'ARTIFICE === */
        #fireworks-canvas {
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            pointer-events: none;
            z-index: 0;
            filter: blur(2px);
            opacity: 0.5;
        }

        .maint-wrap {
            position: relative;
            z-index: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 75vh;
            font-family: 'Mulish', sans-serif;
        }

        .maint-card {
            background: rgba(255,255,255,0.04);
            backdrop-filter: blur(28px) saturate(180%);
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 40px 80px rgba(0,0,0,0.6), 0 1px 0 rgba(255,255,255,0.06) inset;
            padding: 3rem 3.5rem;
            border-radius: 28px;
            max-width: 480px;
            width: 100%;
            text-align: center;
        }

        .maint-emoji {
            font-size: 72px;
            line-height: 1;
            margin-bottom: 24px;
            filter: drop-shadow(0 0 30px rgba(196,181,253,0.5));
            animation: float 4s ease-in-out infinite;
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50%       { transform: translateY(-10px); }
        }

        .maint-title {
            font-family: 'Outfit', sans-serif;
            font-size: 28px;
            font-weight: 800;
            background: linear-gradient(135deg, #ffd6e7 0%, #c4b5fd 40%, #7dd3fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 12px;
            letter-spacing: -0.5px;
        }

        .maint-sub {
            color: #334155;
            font-size: 14px;
            font-weight: 400;
            line-height: 1.7;
            margin-bottom: 32px;
        }

        .maint-divider {
            height: 1px;
            background: rgba(255,255,255,0.05);
            margin: 24px 0;
        }

        .maint-hint {
            color: #1e293b;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 10px;
            font-family: 'Outfit', sans-serif;
        }

        div[data-baseweb="input"] {
            background: rgba(255,255,255,0.03) !important;
            border: 1px solid rgba(255,255,255,0.06) !important;
            border-radius: 14px !important;
        }

        div[data-baseweb="input"]:focus-within {
            border-color: rgba(196,181,253,0.3) !important;
            box-shadow: 0 0 0 3px rgba(196,181,253,0.08) !important;
        }

        input {
            text-align: center !important;
            color: rgba(255,255,255,0.25) !important;
            font-family: 'Outfit', sans-serif !important;
            letter-spacing: 4px !important;
        }

        input::placeholder { color: rgba(255,255,255,0.1) !important; }
    </style>

    <canvas id="fireworks-canvas"></canvas>

    <script>
        (function() {
            const canvas = document.getElementById('fireworks-canvas');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');

            function resize() {
                canvas.width  = window.innerWidth;
                canvas.height = window.innerHeight;
            }
            resize();
            window.addEventListener('resize', resize);

            const COLORS = [
                '#ffb3d1', '#c4b5fd', '#7dd3fc', '#6ee7b7',
                '#fbbf24', '#f87171', '#a78bfa', '#38bdf8',
                '#fcd34d', '#86efac', '#fb923c'
            ];

            class Particle {
                constructor(x, y, color) {
                    this.x = x;
                    this.y = y;
                    this.color = color;
                    const angle = Math.random() * Math.PI * 2;
                    const speed = Math.random() * 3 + 0.5;
                    this.vx = Math.cos(angle) * speed;
                    this.vy = Math.sin(angle) * speed;
                    this.life = 1;
                    this.decay = Math.random() * 0.015 + 0.008;
                    this.size = Math.random() * 2.5 + 1;
                    this.gravity = 0.04;
                }

                update() {
                    this.x  += this.vx;
                    this.y  += this.vy;
                    this.vy += this.gravity;
                    this.vx *= 0.99;
                    this.life -= this.decay;
                }

                draw() {
                    ctx.save();
                    ctx.globalAlpha = this.life;
                    ctx.fillStyle   = this.color;
                    ctx.shadowColor = this.color;
                    ctx.shadowBlur  = 6;
                    ctx.beginPath();
                    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                    ctx.fill();
                    ctx.restore();
                }
            }

            class Firework {
                constructor() {
                    this.reset();
                }

                reset() {
                    // Position aléatoire dans la moitié haute/basse de l'écran, loin du centre
                    const side = Math.random() < 0.5 ? 'left' : 'right';
                    this.x = side === 'left'
                        ? Math.random() * canvas.width * 0.35
                        : canvas.width * 0.65 + Math.random() * canvas.width * 0.35;
                    this.y = Math.random() * canvas.height * 0.6 + canvas.height * 0.05;
                    this.color     = COLORS[Math.floor(Math.random() * COLORS.length)];
                    this.particles = [];
                    this.exploded  = false;
                    this.delay     = Math.random() * 180 + 60;
                    this.timer     = 0;
                }

                explode() {
                    const count = Math.floor(Math.random() * 60) + 40;
                    for (let i = 0; i < count; i++) {
                        this.particles.push(new Particle(this.x, this.y, this.color));
                    }
                    this.exploded = true;
                }

                update() {
                    this.timer++;
                    if (!this.exploded && this.timer >= this.delay) {
                        this.explode();
                    }
                    this.particles = this.particles.filter(p => p.life > 0);
                    this.particles.forEach(p => p.update());
                }

                draw() {
                    this.particles.forEach(p => p.draw());
                }

                isDone() {
                    return this.exploded && this.particles.length === 0;
                }
            }

            let fireworks = [];

            // Lance 3 feux au départ
            for (let i = 0; i < 3; i++) {
                const fw = new Firework();
                fw.delay = i * 80 + 30;
                fireworks.push(fw);
            }

            function loop() {
                ctx.clearRect(0, 0, canvas.width, canvas.height);

                fireworks.forEach(fw => { fw.update(); fw.draw(); });
                fireworks = fireworks.filter(fw => !fw.isDone());

                // Maintenir 2-4 feux actifs en permanence
                while (fireworks.length < 3) {
                    fireworks.push(new Firework());
                }

                requestAnimationFrame(loop);
            }

            loop();
        })();
    </script>

    <div class="maint-wrap">
        <div class="maint-card">
            <div class="maint-emoji">🏰</div>
            <div class="maint-title">Mise à jour en cours</div>
            <div class="maint-sub">
                Le Disney Tracker se refait une beauté.<br>
                Revenez dans quelques instants.
            </div>
            <div class="maint-divider"></div>
            <div class="maint-hint">Accès restreint</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        code = st.text_input(
            "Accès",
            type="password",
            label_visibility="collapsed",
            placeholder="· · · · · · ·",
            key="maint_password"
        )

    if code == "123456789":
        st.session_state.bypass_maintenance = True
        st.rerun()

    st.stop()