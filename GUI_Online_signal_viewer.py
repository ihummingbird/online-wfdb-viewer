import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QSizePolicy, QLabel, QLineEdit, \
    QPushButton, QHBoxLayout, QSplitter, QTextEdit
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QHBoxLayout, QAction
from PyQt5.QtGui import QIcon
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from PyQt5.QtGui import QGuiApplication
import csv
import pandas as pd
import sys
from pathlib import Path
import wfdb
import os
from matplotlib import pyplot as plt
from scipy.signal import resample
import sys
from PyQt5.QtWidgets import QApplication, QSplashScreen, QMainWindow
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel, QHBoxLayout, QComboBox
import time
import h5py


# Define the style
stylesheet = """
    QMainWindow {
        background-color: #ffffff;
    }
    QWidget {
        background-color: #ffffff;
    }
    QPushButton {
        background-color: #5CACEE;
        border-style: outset;
        border-width: 2px;
        border-radius: 10px;
        border-color: #1E90FF;
        font: bold 14px;
        padding: 6px;
        color: white;
    }
    QPushButton:pressed {
        background-color: #1E90FF;
        border-style: inset;
    }
    QLabel {
        color: #333333;
        font-size: 14px;
    }
    QLineEdit {
        border: 2px solid #1E90FF;
        border-radius: 4px;
        background: #FFFFFF;
        selection-background-color: #5CACEE;
    }
    QComboBox {
        border: 1px solid #1E90FF;
        border-radius: 3px;
        padding: 1px 18px 1px 3px;
        min-width: 6em;
    }
    QComboBox:editable {
        background: white;
    }
    QComboBox:!editable, QComboBox::drop-down:editable {
         background: #1E90FF;
         color: white;
    }
    QComboBox:!editable:on, QComboBox::drop-down:editable:on {
        background: #5CACEE;
    }
    QComboBox:on {
        padding-top: 3px;
        padding-left: 4px;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 15px;

        border-left-width: 1px;
        border-left-color: darkgray;
        border-left-style: solid;
        border-top-right-radius: 3px;
        border-bottom-right-radius: 3px;
    }
"""



class MyMplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=10, height=8, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)

        super(MyMplCanvas, self).__init__(fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)


    def plot(self, data):
        self.axes.plot(data)
        self.draw()


class ApplicationWindow(QMainWindow):
    def __init__(self, frequency):
        self.points = []
        QMainWindow.__init__(self)
        self.setWindowTitle("Online Waveform Database Signal Viewer")
        self.resize(1024, 768)  # Set window size
        self.setWindowIcon(QIcon('WFDB_V.png'))


        # Set the signal frequency
        self.frequency = frequency

        # Generate some sin data for this example
        # Set the sample rate, frequency, and the number of points
        sample_rate = 100  # Sample rate in Hz
        frequency = 1  # Frequency of the sine wave in Hz
        num_points = 100  # Number of data points

        # Generate an array of time points
        time_points = np.linspace(0, 2 * np.pi, num_points)

        # Generate the sine wave
        self.data = np.sin(frequency * time_points)

        self.main_widget = QWidget(self)
        self.signal_type_dropdown = QComboBox()
        self.main_widget.setStyleSheet(stylesheet)
        layout = QVBoxLayout(self.main_widget)

        # Create input fields
        self.db_name_input = QLineEdit()
        self.db_name_input.setText("mimic4wdb/0.1.0/")

        self.segment_address_input = QLineEdit()
        self.segment_address_input.setText("waves/p137/p13791821/82803505/")

        self.signal_name_input = QLineEdit()
        self.signal_name_input.setText("82803505")

        # Create time input fields
        self.start_hour_input = QLineEdit()
        self.start_hour_input.setFixedSize(25, 25)  # Set width and height of the input field
        self.start_hour_input.setText("1")

        self.start_minute_input = QLineEdit()
        self.start_minute_input.setFixedSize(25, 25)  # Set width and height of the input field
        self.start_minute_input.setText("5")

        self.start_second_input = QLineEdit()
        self.start_second_input.setFixedSize(25, 25)  # Set width and height of the input field
        self.start_second_input.setText("0")

        # Create duration input fields
        self.Fs = QLineEdit()
        self.Fs.setFixedSize(25, 25)  # Set width and height of the input field
        self.Fs.setReadOnly(True)
        self.Fs.setStyleSheet("QLineEdit { background-color: lightgray; }")

        self.duration_second_input = QLineEdit()
        self.duration_second_input.setFixedSize(25, 25)  # Set width and height of the input field
        self.duration_second_input.setText("2")

        # Create fields for displaying clicked points
        self.point1_label = QTextEdit("Point 1: time=N/A, amplitude=N/A")
        self.point1_label.setReadOnly(True)
        self.point1_label.setFixedSize(500, 25)  # Set width and height of the input field
        self.point2_label = QTextEdit("Point 2: time=N/A, amplitude=N/A")
        self.point2_label.setReadOnly(True)
        self.point2_label.setFixedSize(500, 25)  # Set width and height of the input field
        self.time_diff_label = QTextEdit("Time difference: N/A")
        self.time_diff_label.setFixedSize(500, 25)  # Set width and height of the input field
        self.time_diff_label.setReadOnly(True)

        # Create update button
        update_button = QPushButton("Update")
        update_button.clicked.connect(self.update_plot)

        # Add widgets to layout
        layout.addWidget(QLabel("Database name:"))
        layout.addWidget(self.db_name_input)
        layout.addWidget(QLabel("Segment address:"))
        layout.addWidget(self.segment_address_input)
        layout.addWidget(QLabel("Signal name:"))
        layout.addWidget(self.signal_name_input)

        # Creating horizontal layout for time input
        time_input_layout = QHBoxLayout()  # Create a horizontal layout
        time_input_layout.addWidget(QLabel("Start time (h:m:s):"))
        time_input_layout.addWidget(self.start_hour_input)
        time_input_layout.addWidget(self.start_minute_input)
        time_input_layout.addWidget(self.start_second_input)
        time_input_layout.addStretch(1)  # Add a stretch to push everything to the left
        layout.addLayout(time_input_layout)  # Add the horizontal layout to the main layout

        # Creating horizontal layout for Fs and duration input
        fsdu_input_layout = QHBoxLayout()  # Create a horizontal layout
        fsdu_input_layout.addWidget(QLabel("Fs, Duration(s) and Signal Type:"))
        fsdu_input_layout.addWidget(self.Fs)
        fsdu_input_layout.addWidget(self.duration_second_input)
        fsdu_input_layout.addWidget(self.signal_type_dropdown)  # Add the dropdown to the layout
        self.signal_type_dropdown.addItem("II")  # This is an example item, you can add more as needed
        fsdu_input_layout.addStretch(1)  # Add a stretch to push everything to the left
        layout.addLayout(fsdu_input_layout)  # Add the horizontal layout to the main layout


        layout.addWidget(update_button)

        splitter = QSplitter(self)  # Create a splitter to divide the window

        self.sc = MyMplCanvas(self.main_widget, width=5, height=4, dpi=100)
        self.sc.plot(self.data)
        layout.addWidget(self.sc)

        # Add labels to layout
        layout.addWidget(self.point1_label)
        layout.addWidget(self.point2_label)
        layout.addWidget(self.time_diff_label)

        self.setCentralWidget(self.main_widget)

        # Connect the button_press_event to our custom function
        self.sc.mpl_connect('button_press_event', self.on_click)
        # Connect the motion_notify_event to our custom function

        self.sc.mpl_connect('motion_notify_event', self.on_move)

        # Initialize variables to store clicked points
        self.point1 = None
        self.point2 = None

    def on_move(self, event):
        if event.inaxes:
            x = event.xdata  # time index
            y = event.ydata  # amplitude
            time = x / self.frequency  # calculate time
            self.statusBar().showMessage(f"time={time:.3f}s, amplitude={y:.3f}")

    def on_click(self, event):
        if event.inaxes:
            x = event.xdata  # time index
            y = event.ydata  # amplitude
            time = x / self.frequency  # calculate time

            # Highlight the clicked point
            point = self.sc.axes.plot(x, y, 'ro')
            self.points.append(point[0])

            # If there are more than 2 points, remove the oldest one
            if len(self.points) > 2:
                old_point = self.points.pop(0)  # Remove the oldest point from the list
                old_point.remove()  # Remove the oldest point from the plot

            # Store clicked points and update labels
            if self.point1 is None:
                self.point1 = (x, y, time)
                self.point1_label.setText(f"Point 1: time={self.point1[2]:.3f}s, amplitude={self.point1[1]:.3f}")
            else:
                self.point2 = (x, y, time)
                self.point2_label.setText(f"Point 2: time={self.point2[2]:.3f}s, amplitude={self.point2[1]:.3f}")

                # Remove the old line if it exists
                if hasattr(self, 'line') and self.line is not None:
                    self.line.remove()

                # Draw a line between the two points
                self.line, = self.sc.axes.plot([self.point1[0], self.point2[0]], [self.point1[1], self.point2[1]], 'r-')

                # Calculate and display time difference
                time_diff = abs(self.point2[2] - self.point1[2])
                self.time_diff_label.setText(f"Time difference: {time_diff:.3f}s")

                # Reset points
                self.point1 = None
                self.point2 = None

            # Redraw the canvas
            self.sc.draw()

    def update_plot(self):
        try:
            # Here you can implement getting the signal from the database
            # based on the user input and plotting it. For this example,

            # Defining Database info.
            database_name = self.db_name_input.text()
            # Get user input
            db_name = self.db_name_input.text().strip()
            segment_address = self.segment_address_input.text().strip()
            signal_name = self.signal_name_input.text().strip()

            # Defining Start time and Du.
            start_hour = int(self.start_hour_input.text())
            start_minute = int(self.start_minute_input.text())
            start_second = int(self.start_second_input.text())
            start_seconds = (start_hour * 3600) + (start_minute * 60) + start_second
            n_seconds_to_load = int(self.duration_second_input.text())

            # Setting Patient Directory and name
            segment_dir = str(db_name) + str(segment_address)
            segment_name = signal_name

            segment_metadata = wfdb.rdheader(record_name=segment_name,
                                             pn_dir=segment_dir)
            Fs = round(segment_metadata.fs)


            #Defining Fs
            self.Fs.setText(str(Fs))


            duration_second = int(self.duration_second_input.text())
            sampfrom = Fs * start_seconds
            sampto = Fs * (start_seconds + n_seconds_to_load)

            if sampto > segment_metadata.sig_len:  # check if signal is long enough
                self.statusBar().showMessage(str(segment_name) + ': signal is too short')

            #Getting Signal from Database
            segment_data = wfdb.rdrecord(record_name=segment_name,
                                         sampfrom=sampfrom,
                                         sampto=sampto,
                                         pn_dir=segment_dir)

            #Getting Signal Type
            # Getting the selected signal type from the dropdown
            selected_signal = self.signal_type_dropdown.currentText()
            for sig_no in range(0, len(segment_data.sig_name)):
                if selected_signal in segment_data.sig_name[sig_no]:
                    break

            #Getting Signal
            II = segment_data.p_signal[:, sig_no]
            Fs = round(segment_data.fs)
            #if Fs == 62:
            #    Fs = 62
            #    Basically NVM It's working fine.
            self.data = II
            self.frequency = Fs
            self.Fs.setText(str(Fs))
            frequency = Fs

            # Generate some random data for this example
            time_stamps = np.arange(0, (len(II) / Fs), 1.0 / Fs)

            # Clear the axes and plot the new data
            self.sc.axes.clear()
            self.sc.plot(self.data)

            # Updating the signal type dropdown menu
            # Clear the current items in the dropdown
            current_selection = self.signal_type_dropdown.currentText()
            self.signal_type_dropdown.clear()
            # Loop through the signal names and add them to the dropdown
            for sig_no in range(0, len(segment_data.sig_name)):
                self.signal_type_dropdown.addItem(segment_data.sig_name[sig_no])
            # Restore the previous selection if it still exists in the list
            index = self.signal_type_dropdown.findText(current_selection)
            if index != -1:  # Check if the current selection was found in the list
                self.signal_type_dropdown.setCurrentIndex(index)
            else:
                self.signal_type_dropdown.setCurrentIndex(0)  # Optional: set to default value if not found


        except Exception as e:
            # If anything went wrong, show an error message
            self.statusBar().showMessage(str(e))

if __name__ == "__main__":
    qApp = QApplication(sys.argv)

    # Create and display the splash screen
    splash_pix = QPixmap('WFDB_V.png')  # Replace with the path to your image
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())
    splash.show()

    # This will show the splash screen for 5 seconds
    time.sleep(1)

    # Provide the frequency of your signal here
    frequency = 100  # for start
    aw = ApplicationWindow(frequency)

    # Set the window icon (logo)
    aw.setWindowIcon(QIcon('WFDB_V.png'))

    aw.show()

    # Close the splash screen
    splash.finish(aw)

    sys.exit(qApp.exec_())