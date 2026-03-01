import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button, Slider

# ------------------------------------------------------------
# Interactive GH (dGH) simulator with sliders (matplotlib)
# Assumptions:
#  - Evaporation -> top-off -> water change (at full volume) each interval
#  - Top-off water GH == water-change water GH == gh_a
#  - Evaporation concentrates (solutes remain), top-off adds solutes
#  - Tank-source leaching gh_s is modeled as + (gh_s * w_0) dGH·L per week
# ------------------------------------------------------------

LEFT = 0.30
WIDTH = 0.65

def simulate(w_0, gh_0, w_a, gh_a, t_a, w_f, gh_s, weeks_total=30):
    # Derived per-interval evaporation/top-off volume
    w_e = w_f * (t_a / 7.0)

    # Sanity: keep simulation stable
    if w_0 <= 0:
        w_0 = 1e-6
    if t_a <= 0:
        t_a = 1e-6
    if w_a < 0:
        w_a = 0.0
    if w_a > w_0:
        w_a = w_0
    if w_f < 0:
        w_f = 0.0

    steps = int(np.ceil((weeks_total * 7) / t_a))
    gh = np.zeros(steps + 1)
    time_days = np.zeros(steps + 1)
    gh[0] = gh_0

    for n in range(steps):
        gh_n = gh[n]
        M = gh_n * w_0  # dGH·L

        # top-off contribution
        M += gh_a * w_e

        # leaching contribution (per week scaled to interval length)
        M += gh_s * w_0 * (t_a / 7.0)

        gh_pre = M / w_0

        # water change at full volume
        M -= gh_pre * w_a
        M += gh_a * w_a

        gh[n + 1] = M / w_0
        time_days[n + 1] = time_days[n] + t_a

    return time_days / 7.0, gh, w_e

# ===== Default parameters (user-provided) =====
defaults = dict(
    w_0=65.0,
    gh_0=7.0,
    w_a=7.0,
    gh_a=3.0,
    t_a=7.0,
    w_f=2.0,
    gh_s=0.0,
)

weeks_total = 30

# ----- Initial simulation -----
x, y, w_e = simulate(**defaults, weeks_total=weeks_total)

# ----- Figure setup -----
plt.close("all")
fig, ax = plt.subplots()
plt.subplots_adjust(left=0.12, bottom=0.50, right=0.98, top=0.90)

(line,) = ax.plot(x, y, marker="o")
ax.set_xlabel("Time (weeks)")
ax.set_ylabel("GH (dGH)")
ax.set_title("Aquarium GH Simulator (top-off → water change)")
ax.grid(True)

info = ax.text(
    0.02,
    0.98,
    "",
    transform=ax.transAxes,
    va="top",
    ha="left",
)

def update_info(params):
    x_, y_, w_e_ = simulate(**params, weeks_total=weeks_total)
    info.set_text(
        f"w_e per interval = {w_e_:.2f} L   |   final GH @ {x_[-1]:.1f} w = {y_[-1]:.2f} dGH"
    )
    return x_, y_

# ----- Sliders -----
axcolor = "lightgoldenrodyellow"

# Slider axes positions: [left, bottom, width, height]
ax_w0  = plt.axes([LEFT, 0.34, WIDTH, 0.03], facecolor=axcolor)
ax_gh0 = plt.axes([LEFT, 0.30, WIDTH, 0.03], facecolor=axcolor)
ax_wa  = plt.axes([LEFT, 0.26, WIDTH, 0.03], facecolor=axcolor)
ax_gha = plt.axes([LEFT, 0.22, WIDTH, 0.03], facecolor=axcolor)
ax_ta  = plt.axes([LEFT, 0.18, WIDTH, 0.03], facecolor=axcolor)
ax_wf  = plt.axes([LEFT, 0.14, WIDTH, 0.03], facecolor=axcolor)
ax_ghs = plt.axes([LEFT, 0.10, WIDTH, 0.03], facecolor=axcolor)

# Ranges chosen to be practical for aquarium use; edit as desired.
s_w0  = Slider(ax_w0,  "Base Water Volume (L)",    10.0, 200.0, valinit=defaults["w_0"],  valstep=1.0)
s_gh0 = Slider(ax_gh0, "Base Water GH (dGH)", 0.0,  30.0,  valinit=defaults["gh_0"], valstep=0.1)
s_wa  = Slider(ax_wa,  "Refill Water Volume (L)",    0.0,  80.0,  valinit=defaults["w_a"],  valstep=0.5)
s_gha = Slider(ax_gha, "Refill Water GH (dGH)", 0.0,  30.0,  valinit=defaults["gh_a"], valstep=0.1)
s_ta  = Slider(ax_ta,  "Refill Interval (days)", 1.0,  28.0,  valinit=defaults["t_a"],  valstep=1.0)
s_wf  = Slider(ax_wf,  "Top-off and Refill Water Volume (L/week)", 0.0,  20.0,  valinit=defaults["w_f"],  valstep=0.1)
s_ghs = Slider(ax_ghs, "Other Adding GH (dGH/wk)", 0.0, 10.0, valinit=defaults["gh_s"], valstep=0.05)

def current_params():
    # Clamp w_a to w_0 to avoid impossible changes
    w0 = float(s_w0.val)
    wa = float(min(s_wa.val, w0))
    return dict(
        w_0=w0,
        gh_0=float(s_gh0.val),
        w_a=wa,
        gh_a=float(s_gha.val),
        t_a=float(s_ta.val),
        w_f=float(s_wf.val),
        gh_s=float(s_ghs.val),
    )

def on_change(val):
    params = current_params()
    x_, y_ = update_info(params)
    line.set_xdata(x_)
    line.set_ydata(y_)
    ax.relim()
    ax.autoscale_view()
    fig.canvas.draw_idle()

for s in (s_w0, s_gh0, s_wa, s_gha, s_ta, s_wf, s_ghs):
    s.on_changed(on_change)

# ----- Buttons: reset + toggle markers -----
ax_reset = plt.axes([0.12, 0.02, 0.12, 0.05])
btn_reset = Button(ax_reset, "Reset")

ax_toggle = plt.axes([0.26, 0.02, 0.22, 0.05])
btn_toggle = Button(ax_toggle, "Toggle markers")

markers_on = True

def do_reset(event):
    s_w0.reset()
    s_gh0.reset()
    s_wa.reset()
    s_gha.reset()
    s_ta.reset()
    s_wf.reset()
    s_ghs.reset()

def do_toggle(event):
    global markers_on
    markers_on = not markers_on
    line.set_marker("o" if markers_on else "")
    fig.canvas.draw_idle()

btn_reset.on_clicked(do_reset)
btn_toggle.on_clicked(do_toggle)

# Initial info
update_info(defaults)

plt.show()
