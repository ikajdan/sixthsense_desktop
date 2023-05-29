import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

import requests
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas


import matplotlib.style as mpl_style


class SixthSense(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="SixthSense")
        self.set_default_size(800, 600)
        self.connect("destroy", Gtk.main_quit)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(500)

        self.view1 = Gtk.Label(label="Sensors")
        self.view2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.view3 = Gtk.Label(label="Control")
        self.view4 = Gtk.Label(label="Settings")

        self.stack.add_named(self.view1, "Sensors")
        self.stack.add_named(self.view2, "Plots")
        self.stack.add_named(self.view3, "Control")
        self.stack.add_named(self.view4, "Settings")

        self.view2.set_margin_top(20)
        self.view2.set_margin_end(10)
        self.view2.set_margin_bottom(20)
        self.view2.set_margin_start(10)

        self.button1 = Gtk.Button(label="Sensors")
        self.button1.connect("clicked", self.switch_view, "Sensors")
        self.button2 = Gtk.Button(label="Plots")
        self.button2.connect("clicked", self.switch_view, "Plots")
        self.button3 = Gtk.Button(label="Control")
        self.button3.connect("clicked", self.switch_view, "Control")
        self.button4 = Gtk.Button(label="Settings")
        self.button4.connect("clicked", self.switch_view, "Settings")

        # Create a plot
        native_theme = {
            "text.color": "#454242",
            "xtick.color": "#242424",
            "ytick.color": "#454242",
            "grid.color": "#454242",
            "axes.facecolor": "#242424",
            "axes.edgecolor": "#242424",
            "axes.labelcolor": "#454242",
            "figure.facecolor": "#242424",
            "figure.edgecolor": "#242424",
            "grid.linestyle": "--",
        }

        mpl_style.use(native_theme)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.view2.pack_start(self.canvas, True, True, 0)

        self.x_data = []
        self.temperature_data = []
        self.pressure_data = []
        self.humidity_data = []

        self.axis = self.figure.add_subplot(1, 1, 1)
        self.line1 = self.axis.plot([], [], marker="o", color="#F66151")[0]
        self.axis.grid(axis="y")
        self.figure.subplots_adjust(top=1, right=0.91, bottom=0.05, left=0.09)

        self.sample_counter = 0
        self.updateSensorsPlot()

        # Vertical box layout
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(self.box)

        # Horizontal box for buttons
        buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        self.box.pack_start(buttons_box, False, False, 0)
        buttons_box.set_margin_bottom(5)
        buttons_box.set_margin_top(10)
        buttons_box.set_margin_left(10)
        buttons_box.set_margin_right(10)

        buttons_box.pack_start(self.button1, True, True, 0)
        buttons_box.pack_start(self.button2, True, True, 0)
        buttons_box.pack_start(self.button3, True, True, 0)
        buttons_box.pack_start(self.button4, True, True, 0)

        self.box.pack_start(self.stack, True, True, 0)

    def switch_view(self, widget, view_name):
        self.stack.set_visible_child_name(view_name)

    def updateSensorsPlot(self):
        # Fetch data from the REST API
        response = requests.get("http://localhost:8000/sensors/all?t=c&p=hpa&h=perc")

        # Parse the data and add it to the plot
        self.temperature = response.json()["temperature"]["value"]
        self.pressure = response.json()["pressure"]["value"]
        self.humidity = response.json()["humidity"]["value"]

        self.sample_counter += 1
        self.x_data.append(self.sample_counter)
        self.temperature_data.append(self.temperature)
        self.pressure_data.append(self.pressure)
        self.humidity_data.append(self.humidity)

        self.x_data = self.x_data[-10:]
        self.temperature_data = self.temperature_data[-10:]
        self.pressure_data = self.pressure_data[-10:]
        self.humidity_data = self.humidity_data[-10:]

        # Update the plots
        self.line1.set_data(self.x_data, self.temperature_data)

        # Autoscale the plots
        self.axis.relim()
        self.axis.autoscale_view(True, True, True)

        self.canvas.draw()

        # Schedule the next data fetch
        GLib.timeout_add_seconds(1, self.updateSensorsPlot)


window = SixthSense()
window.show_all()

Gtk.main()
