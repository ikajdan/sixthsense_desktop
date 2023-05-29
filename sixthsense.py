import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

import requests
from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas


import matplotlib.style as mpl_style

host_name_pref = "localhost"
port_number_pref = 8000
refresh_time_pref = 1000


class SettingsView(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL, spacing=20)

        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_spacing(6)
        self.pack_start(self.grid, False, False, 0)

        self.host_name_label = Gtk.Label(label="Hostname:")
        self.port_number_label = Gtk.Label(label="Port:")
        self.refresh_time_label = Gtk.Label(label="Sampling Time:")

        self.host_entry = Gtk.Entry()
        self.port_entry = Gtk.Entry()
        self.refresh_time_entry = Gtk.Entry()

        save_button = Gtk.Button(label="Save")
        save_button.connect("clicked", self.save_settings)

        self.grid.attach(self.create_aligned_label(self.host_name_label), 0, 0, 2, 1)
        self.grid.attach(self.host_entry, 0, 1, 2, 1)
        self.grid.attach(self.create_aligned_label(self.port_number_label), 0, 2, 2, 1)
        self.grid.attach(self.port_entry, 0, 3, 2, 1)
        self.grid.attach(self.create_aligned_label(self.refresh_time_label), 0, 4, 2, 1)
        self.grid.attach(self.refresh_time_entry, 0, 5, 2, 1)
        self.pack_end(save_button, False, False, 0)

        self.restore_settings()

    def create_aligned_label(self, label):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hbox.pack_start(label, False, False, 0)
        return hbox

    def save_settings(self, widget):
        global host_name_pref, port_number_pref, refresh_time_pref
        host_name_pref = self.host_entry.get_text()
        port_number_pref = self.port_entry.get_text()
        refresh_time_pref = self.refresh_time_entry.get_text()

    def restore_settings(self):
        self.host_entry.set_text(host_name_pref)
        self.port_entry.set_text(str(port_number_pref))
        self.refresh_time_entry.set_text(str(refresh_time_pref))


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
        self.settings_view = Gtk.Label(label="Settings")
        self.settings_view = SettingsView()

        self.stack.add_named(self.view1, "Sensors")
        self.stack.add_named(self.view2, "Plots")
        self.stack.add_named(self.view3, "Control")
        self.stack.add_named(self.settings_view, "Settings")

        # TODO: Move this to a separate function
        self.view2.set_margin_top(20)
        self.view2.set_margin_end(10)
        self.view2.set_margin_bottom(20)
        self.view2.set_margin_start(10)
        self.settings_view.set_margin_top(20)
        self.settings_view.set_margin_end(10)
        self.settings_view.set_margin_bottom(20)
        self.settings_view.set_margin_start(10)

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
        buttons_box.set_margin_top(10)
        buttons_box.set_margin_end(10)
        buttons_box.set_margin_bottom(5)
        buttons_box.set_margin_start(10)

        buttons_box.pack_start(self.button1, True, True, 0)
        buttons_box.pack_start(self.button2, True, True, 0)
        buttons_box.pack_start(self.button3, True, True, 0)
        buttons_box.pack_start(self.button4, True, True, 0)

        self.box.pack_start(self.stack, True, True, 0)

    def switch_view(self, widget, view_name):
        self.stack.set_visible_child_name(view_name)

    def updateSensorsPlot(self):
        # Fetch data from the REST API

        api_endpoint = (
            "http://" + host_name_pref + ":" + str(port_number_pref) + "/sensors/all"
        )
        response = requests.get(api_endpoint)

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

        self.line1.set_data(self.x_data, self.temperature_data)

        self.axis.relim()
        self.axis.autoscale_view(True, True, True)

        self.canvas.draw()

        GLib.timeout_add(refresh_time_pref, self.updateSensorsPlot)


window = SixthSense()
window.show_all()

Gtk.main()
