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


class SensorsView(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)

        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.list_store = Gtk.ListStore(str, float, str)
        self.pack_start(self.scrolled_window, True, True, 0)

        self.updateSensorsData()

    def updateSensorsData(self):
        api_endpoint = (
            "http://" + host_name_pref + ":" + str(port_number_pref) + "/sensors/all"
        )
        response = requests.get(api_endpoint)
        if response.status_code == 200:
            data = response.json()
            for key, value in data.items():
                name = value["name"]
                if name == "":
                    name = key
                unit = value.get("unit", "")
                if unit == "":
                    unit = "-"
                self.list_store.append([name, value["value"], unit])

        self.tree_view = Gtk.TreeView(model=self.list_store)

        self.name_column = Gtk.TreeViewColumn("Name")
        self.value_column = Gtk.TreeViewColumn("Value")
        self.unit_column = Gtk.TreeViewColumn("Unit")

        self.name_renderer = Gtk.CellRendererText()
        self.value_renderer = Gtk.CellRendererText()
        self.unit_renderer = Gtk.CellRendererText()

        self.name_column.pack_start(self.name_renderer, True)
        self.value_column.pack_start(self.value_renderer, True)
        self.unit_column.pack_start(self.unit_renderer, True)

        self.name_column.add_attribute(self.name_renderer, "text", 0)
        self.value_column.add_attribute(self.value_renderer, "text", 1)
        self.unit_column.add_attribute(self.unit_renderer, "text", 2)

        self.tree_view.append_column(self.name_column)
        self.tree_view.append_column(self.value_column)
        self.tree_view.append_column(self.unit_column)

        self.scrolled_window.add(self.tree_view)

        GLib.timeout_add(refresh_time_pref, self.updateSensorsData)


class PlotsView(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)

        self.set_margin_top(20)
        self.set_margin_end(10)
        self.set_margin_bottom(10)
        self.set_margin_start(10)

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
        self.pack_start(self.canvas, True, True, 0)

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

    def updateSensorsPlot(self):
        api_endpoint = (
            "http://" + host_name_pref + ":" + str(port_number_pref) + "/sensors/all"
        )

        response = requests.get(api_endpoint)

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


class ControlView(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)

        self.set_margin_top(20)
        self.set_margin_end(10)
        self.set_margin_bottom(10)
        self.set_margin_start(10)

        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_spacing(6)
        self.pack_start(self.grid, False, False, 0)

        self.led_label = Gtk.Label(label="LED:")
        self.color_label = Gtk.Label(label="Color:")

        self.led_entry = Gtk.Entry()
        self.color_entry = Gtk.Entry()

        self.led_entry.set_text("0")

        apply_button = Gtk.Button(label="Apply")
        apply_button.connect("clicked", self.set_led_grid)

        self.grid.attach(self.create_aligned_label(self.led_label), 0, 0, 2, 1)
        self.grid.attach(self.led_entry, 0, 1, 2, 1)
        self.grid.attach(self.create_aligned_label(self.color_label), 0, 2, 2, 1)
        self.grid.attach(self.color_entry, 0, 3, 2, 1)
        self.pack_end(apply_button, False, False, 0)

    def create_aligned_label(self, label):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hbox.pack_start(label, False, False, 0)
        return hbox

    def set_led_grid(self, label):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hbox.pack_start(label, False, False, 0)
        return hbox


class SettingsView(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)

        self.set_margin_top(20)
        self.set_margin_end(10)
        self.set_margin_bottom(10)
        self.set_margin_start(10)

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

        # View stack
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(100)

        self.sensors_view = SensorsView()
        self.plots_view = PlotsView()
        self.control_view = ControlView()
        self.settings_view = SettingsView()

        self.stack.add_named(self.sensors_view, "Sensors")
        self.stack.add_named(self.plots_view, "Plots")
        self.stack.add_named(self.control_view, "Control")
        self.stack.add_named(self.settings_view, "Settings")

        # Navigation bar
        self.sensors_view_button = Gtk.Button(label="Sensors")
        self.sensors_view_button.connect("clicked", self.switch_view, "Sensors")
        self.plots_view_button = Gtk.Button(label="Plots")
        self.plots_view_button.connect("clicked", self.switch_view, "Plots")
        self.control_view_button = Gtk.Button(label="Control")
        self.control_view_button.connect("clicked", self.switch_view, "Control")
        self.settings_view_button = Gtk.Button(label="Settings")
        self.settings_view_button.connect("clicked", self.switch_view, "Settings")

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.box)

        navigation_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.box.pack_start(navigation_bar, False, False, 0)
        navigation_bar.set_margin_top(10)
        navigation_bar.set_margin_end(10)
        navigation_bar.set_margin_bottom(10)
        navigation_bar.set_margin_start(10)

        navigation_bar.pack_start(self.sensors_view_button, True, True, 0)
        navigation_bar.pack_start(self.plots_view_button, True, True, 0)
        navigation_bar.pack_start(self.control_view_button, True, True, 0)
        navigation_bar.pack_start(self.settings_view_button, True, True, 0)

        self.box.pack_start(self.stack, True, True, 0)

    def switch_view(self, widget, view_name):
        self.stack.set_visible_child_name(view_name)


window = SixthSense()
window.show_all()

Gtk.main()
