import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSystemTrayIcon, QMenu, QPushButton, QComboBox, QProgressBar, QTabWidget
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QTimer

from tasks.workers import AuthWorker
from tasks.services.tasklist_service import TaskListService
from tasks.controllers.task_controller import TaskController
from tasks.controllers.tasklist_controller import TaskListController
from tasks.resources import get_icon_path


class MainWindow(QMainWindow):
    def __init__(self, credentials):
        super().__init__()
        self.credentials = credentials
        self.tasklist_service = TaskListService(credentials)
        self.fetch_worker = None
        self.selected_tasklist_id = None
        self.tasklists = []
        
        self.setup_ui()
        self.setup_controllers()
        self.setup_timer()
        
        self.task_controller.show_loading()
        self.tasklist_controller.fetch_tasklists()
    
    def setup_ui(self):
        self.setWindowTitle("Google Tasks")
        self.setWindowIcon(QIcon(str(get_icon_path())))
            
        self.setFixedSize(300, 400)
        
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.create_top_bar(layout)
        self.create_tab_widget(layout)
        self.create_loading_indicator(layout)
        
        self.setCentralWidget(main_widget)
    
    def create_top_bar(self, layout):
        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(8, 8, 8, 8)
        
        add_button = QPushButton("New task")
        top_layout.addWidget(add_button)
        
        self.tasklist_combo = QComboBox()
        top_layout.addWidget(self.tasklist_combo, 1)
        
        add_list_button = QPushButton("+")
        add_list_button.setToolTip("Add new list")
        top_layout.addWidget(add_list_button)
        
        delete_list_button = QPushButton("-")
        delete_list_button.setToolTip("Delete current list")
        top_layout.addWidget(delete_list_button)
        
        # Set heights after combo is created
        add_button.setFixedHeight(self.tasklist_combo.sizeHint().height())
        add_list_button.setFixedSize(self.tasklist_combo.sizeHint().height(), self.tasklist_combo.sizeHint().height())
        delete_list_button.setFixedSize(self.tasklist_combo.sizeHint().height(), self.tasklist_combo.sizeHint().height())
        
        # Store references for controllers
        self.add_button = add_button
        self.add_list_button = add_list_button
        self.delete_list_button = delete_list_button
        
        layout.addWidget(top_bar)
    
    def create_tab_widget(self, layout):
        self.tab_widget = QTabWidget()
        
        # Incomplete tasks tab
        self.incomplete_scroll = QScrollArea()
        self.incomplete_scroll.setWidgetResizable(True)
        self.incomplete_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.incomplete_widget = QWidget()
        self.incomplete_layout = QVBoxLayout(self.incomplete_widget)
        self.incomplete_layout.setSpacing(2)
        self.incomplete_layout.setContentsMargins(4, 4, 4, 4)
        self.incomplete_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.incomplete_scroll.setWidget(self.incomplete_widget)
        
        # Completed tasks tab
        self.completed_scroll = QScrollArea()
        self.completed_scroll.setWidgetResizable(True)
        self.completed_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.completed_widget = QWidget()
        self.completed_layout = QVBoxLayout(self.completed_widget)
        self.completed_layout.setSpacing(2)
        self.completed_layout.setContentsMargins(4, 4, 4, 4)
        self.completed_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.completed_scroll.setWidget(self.completed_widget)
        
        self.tab_widget.addTab(self.incomplete_scroll, "Tasks")
        self.tab_widget.addTab(self.completed_scroll, "Completed")
        
        layout.addWidget(self.tab_widget)
    
    def create_loading_indicator(self, layout):
        self.loading_bar = QProgressBar()
        self.loading_bar.setMaximumHeight(8)
        self.loading_bar.setRange(0, 100)
        self.loading_bar.setValue(0)
        self.loading_bar.setTextVisible(False)
        layout.addWidget(self.loading_bar)
    
    def setup_controllers(self):
        self.task_controller = TaskController(self.credentials, self)
        self.tasklist_controller = TaskListController(self.credentials, self)
        
        # Connect UI events to controllers
        self.add_button.clicked.connect(self.task_controller.show_create_dialog)
        self.add_list_button.clicked.connect(self.tasklist_controller.show_create_list_dialog)
        self.delete_list_button.clicked.connect(self.tasklist_controller.delete_current_list)
        self.tasklist_combo.currentIndexChanged.connect(self.tasklist_controller.on_tasklist_changed)
    
    def setup_timer(self):
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.task_controller.refresh_tasks)
        self.refresh_timer.start(300000)
    
    def showEvent(self, event):
        super().showEvent(event)
        self.position_bottom_right()
    
    def position_bottom_right(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.width() - self.width() - 20, screen.height() - self.height() - 20)
    
    def show_loading_indicator(self):
        self.loading_bar.setStyleSheet("")
        self.loading_bar.setRange(0, 0)
    
    def hide_loading_indicator(self):
        self.loading_bar.setStyleSheet("")
        self.loading_bar.setRange(0, 100)
        self.loading_bar.setValue(0)
    
    def show_error_indicator(self):
        self.loading_bar.setStyleSheet("QProgressBar::chunk { background-color: red; }")
        self.loading_bar.setRange(0, 100)
        self.loading_bar.setValue(100)
    
    def toggle_visibility(self):
        self.hide() if self.isVisible() else self.show()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Tasks")
    app.setApplicationDisplayName("Google Tasks")
    app.setOrganizationName("tasks")
    app.setQuitOnLastWindowClosed(False)

    # Show loading window immediately
    loading_window = QMainWindow()
    loading_window.setWindowTitle("Google Tasks")
    loading_window.setWindowIcon(QIcon(str(get_icon_path())))
    loading_window.setFixedSize(300, 400)
    
    loading_widget = QWidget()
    loading_layout = QVBoxLayout(loading_widget)
    loading_label = QLabel("Authenticating...")
    loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    loading_layout.addWidget(loading_label)
    loading_window.setCentralWidget(loading_widget)
    
    screen = QApplication.primaryScreen().availableGeometry()
    loading_window.move(screen.width() - loading_window.width() - 20, screen.height() - loading_window.height() - 20)
    loading_window.show()

    main_window = None
    tray_icon = QSystemTrayIcon(QIcon(str(get_icon_path())), app)
    
    def on_auth_success(credentials):
        nonlocal main_window
        loading_window.close()
        main_window = MainWindow(credentials)
        main_window.show()
        tray_icon.activated.connect(lambda: main_window.toggle_visibility())
        
        menu = QMenu()
        menu.addAction("Toggle", main_window.toggle_visibility)
        menu.addAction("Quit", app.quit)
        tray_icon.setContextMenu(menu)
        tray_icon.show()
        auth_worker.deleteLater()
    
    def on_auth_error(error):
        print(f"Authentication error: {error}")
        loading_window.close()
        auth_worker.deleteLater()
        sys.exit(1)
    
    auth_worker = AuthWorker()
    auth_worker.finished.connect(on_auth_success)
    auth_worker.error.connect(on_auth_error)
    auth_worker.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
