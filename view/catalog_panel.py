"""Component catalog panel for selecting circuit items."""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QToolButton,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QLabel,
    QSizePolicy,
)

class ComponentCatalogWidget(QWidget):
    """Sidebar catalog for component groups and items."""

    tool_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._group_headers = {}
        self._item_buttons = []
        self._item_meta = []
        self._is_collapsed = False

        self._build_ui()
        self.set_groups(self._default_groups())

    def _build_ui(self):
        self.setMinimumWidth(220)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(6, 6, 6, 6)
        root_layout.setSpacing(6)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search components...")
        self.search_input.textChanged.connect(self._apply_filter)

        self.collapse_button = QToolButton()
        self.collapse_button.setText("<--")
        self.collapse_button.setToolTip("Collapse catalog")
        self.collapse_button.clicked.connect(self._toggle_collapsed)

        header_layout.addWidget(self.search_input)
        header_layout.addWidget(self.collapse_button)

        self.content_widget = QWidget()
        content_layout = QHBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(6)

        self.group_list = QListWidget()
        self.group_list.setFixedWidth(110)
        self.group_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.group_list.itemClicked.connect(self._on_group_clicked)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(6, 6, 6, 6)
        self.scroll_layout.setSpacing(6)
        self.scroll_layout.addStretch(1)

        self.scroll_area.setWidget(self.scroll_content)

        content_layout.addWidget(self.group_list)
        content_layout.addWidget(self.scroll_area)

        root_layout.addLayout(header_layout)
        root_layout.addWidget(self.content_widget)

    def _default_groups(self):
        return [
            (
                "Sources",
                [
                    ("DC Source", "source_dc"),
                    ("AC Source", "source_ac"),
                ],
            ),
            (
                "Passives",
                [
                    ("Resistor", "resistor"),
                    ("Capacitor", "capacitor"),
                    ("Inductor", "inductor"),
                ],
            ),
        ]

    def set_groups(self, groups):
        """Set the groups and component items shown in the catalog."""
        self._group_headers.clear()
        self._item_buttons.clear()
        self._item_meta.clear()

        self.group_list.clear()
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for group_name, items in groups:
            list_item = QListWidgetItem(group_name)
            self.group_list.addItem(list_item)

            header = QLabel(group_name)
            header.setProperty("catalogHeader", True)
            self.scroll_layout.addWidget(header)
            self._group_headers[group_name] = header

            for label, tool_name in items:
                button = QToolButton()
                button.setText(label)
                button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                button.setToolButtonStyle(Qt.ToolButtonTextOnly)
                button.clicked.connect(lambda _, t=tool_name: self.tool_selected.emit(t))
                self.scroll_layout.addWidget(button)
                self._item_buttons.append(button)
                self._item_meta.append((group_name, label.lower(), button))

        self.scroll_layout.addStretch(1)
        self._apply_filter(self.search_input.text())

    def _on_group_clicked(self, item):
        group_name = item.text()
        header = self._group_headers.get(group_name)
        if header is not None:
            self.scroll_area.ensureWidgetVisible(header, 0, 10)

    def _apply_filter(self, text):
        query = text.strip().lower()
        visible_groups = set()

        for group_name, label, button in self._item_meta:
            is_visible = not query or query in label
            button.setVisible(is_visible)
            if is_visible:
                visible_groups.add(group_name)

        for group_name, header in self._group_headers.items():
            header.setVisible(group_name in visible_groups)

    def _toggle_collapsed(self):
        self._is_collapsed = not self._is_collapsed
        self.content_widget.setVisible(not self._is_collapsed)
        if self._is_collapsed:
            self.collapse_button.setText("-->")
            self.collapse_button.setToolTip("Expand catalog")
        else:
            self.collapse_button.setText("<--")
            self.collapse_button.setToolTip("Collapse catalog")
