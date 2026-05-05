import streamlit as st

def show_maintenance():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800;900&family=Mulish:wght@300;400;500&display=swap');

        .stApp {
            background: radial-gradient(ellipse 80% 50% at 20% -10%, rgba(120,80,255,0.15) 0%, transparent 60%),
                        radial-gradient(ellipse 60% 40% at 80% 110%, rgba(255,100,150,0.1) 0%, transparent 55%),
                        radial-gradient(ellipse 100% 80% at 50% 50%, #090d1a 0%, #060910 100%);
        }

        .maint-wrap {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 60vh;
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
            line-height: 1.7;
            margin-bottom: 32px;
        }

        .maint-divider { height: 1px; background: rgba(255,255,255,0.05); margin: 24px 0; }

        .maint-hint {
            color: #1e293b; font-size: 10px; font-weight: 600;
            text-transform: uppercase; letter-spacing: 1.5px;
            margin-bottom: 10px; font-family: 'Outfit', sans-serif;
        }

        div[data-baseweb="input"] {
            background: rgba(255,255,255,0.03) !important;
            border: 1px solid rgba(255,255,255,0.06) !important;
            border-radius: 14px !important;
        }
        input {
            text-align: center !important;
            color: rgba(255,255,255,0.25) !important;
            font-family: 'Outfit', sans-serif !important;
            letter-spacing: 4px !important;
        }
        input::placeholder { color: rgba(255,255,255,0.1) !important; }
    </style>

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

    # --- FEUX D'ARTIFICE via st.iframe ---
    fireworks_html = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        * { margin: 0; padding: 0; }
        body { background: transparent; overflow: hidden; }
        canvas { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; }
    </style>
    </head>
    <body>
    <canvas id="fw"></canvas>
    <script>
        const canvas = document.getElementById('fw');
        const ctx    = canvas.getContext('2d');

        function resize() {
            canvas.width  = window.innerWidth;
            canvas.height = window.innerHeight;
        }
        resize();
        window.addEventListener('resize', resize);

        const COLORS = [
            '#ffb3d1','#c4b5fd','#7dd3fc','#6ee7b7',
            '#fbbf24','#f87171','#a78bfa','#fb923c',
            '#fcd34d','#86efac','#38bdf8'
        ];

        class Particle {
            constructor(x, y, color) {
                this.x = x; this.y = y; this.color = color;
                const angle = Math.random() * Math.PI * 2;
                const speed = Math.random() * 3.5 + 0.5;
                this.vx = Math.cos(angle) * speed;
                this.vy = Math.sin(angle) * speed;
                this.life    = 1;
                this.decay   = Math.random() * 0.012 + 0.007;
                this.size    = Math.random() * 2.5 + 1;
                this.gravity = 0.045;
            }
            update() {
                this.x  += this.vx;
                this.y  += this.vy;
                this.vy += this.gravity;
                this.vx *= 0.985;
                this.life -= this.decay;
            }
            draw() {
                ctx.save();
                ctx.globalAlpha = Math.max(0, this.life);
                ctx.fillStyle   = this.color;
                ctx.shadowColor = this.color;
                ctx.shadowBlur  = 8;
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                ctx.fill();
                ctx.restore();
            }
        }

        class Firework {
            constructor(delay) {
                this.reset(delay || 0);
            }
            reset(delay) {
                const W = canvas.width;
                const H = canvas.height;
                const side = Math.random() < 0.5;
                this.x = side
                    ? Math.random() * W * 0.3
                    : W * 0.7 + Math.random() * W * 0.3;
                this.y     = Math.random() * H * 0.55 + H * 0.05;
                this.color = COLORS[Math.floor(Math.random() * COLORS.length)];
                this.particles = [];
                this.exploded  = false;
                this.timer     = 0;
                this.delay     = delay !== undefined ? delay : Math.random() * 200 + 60;
            }
            explode() {
                const n = Math.floor(Math.random() * 70) + 50;
                for (let i = 0; i < n; i++)
                    this.particles.push(new Particle(this.x, this.y, this.color));
                this.exploded = true;
            }
            update() {
                this.timer++;
                if (!this.exploded && this.timer >= this.delay) this.explode();
                this.particles = this.particles.filter(p => p.life > 0);
                this.particles.forEach(p => p.update());
            }
            draw() { this.particles.forEach(p => p.draw()); }
            isDone() { return this.exploded && this.particles.length === 0; }
        }

        let fireworks = [
            new Firework(30),
            new Firework(110),
            new Firework(200),
        ];

        function loop() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            fireworks.forEach(fw => { fw.update(); fw.draw(); });
            fireworks = fireworks.filter(fw => !fw.isDone());
            while (fireworks.length < 3) fireworks.push(new Firework());
            requestAnimationFrame(loop);
        }
        loop();
    </script>
    </body>
    </html>
    """

    st.iframe(fireworks_html, height=0)

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