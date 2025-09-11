"""Label Editor Dialog for managing labels and labeling modes."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLineEdit,
    QColorDialog,
    QLabel,
    QComboBox,
    QTextEdit,
    QMessageBox,
    QDialogButtonBox,
    QFrame,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon

from ..core.label_manager import LabelManager
from ..core.config import AppConfig


class LabelEditor(QDialog):
    """Dialog for editing labels and configuring labeling modes."""

    # Signal emitted when labels are modified
    labels_changed = Signal()

    def __init__(self, label_manager: LabelManager, parent=None):
        super().__init__(parent)
        self.label_manager = label_manager
        self.setWindowTitle("MuSeg - Label Editor")
        self.setModal(True)
        self.resize(500, 600)

        # Set application icon
        icon_path = AppConfig.get_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(str(icon_path)))

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Labeling Mode Section
        mode_group = QGroupBox("Labeling Mode")
        mode_layout = QVBoxLayout(mode_group)

        # Mode selection
        mode_form = QFormLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Segmentation", "segmentation")
        self.mode_combo.addItem("Annotation", "annotation")
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        mode_form.addRow("Mode:", self.mode_combo)
        mode_layout.addLayout(mode_form)

        # Mode descriptions
        self.mode_description = QTextEdit()
        self.mode_description.setMaximumHeight(100)
        self.mode_description.setReadOnly(True)
        mode_layout.addWidget(self.mode_description)

        layout.addWidget(mode_group)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # Labels Section
        labels_group = QGroupBox("Labels")
        labels_layout = QVBoxLayout(labels_group)

        # Label list
        self.label_list = QListWidget()
        self.label_list.itemSelectionChanged.connect(self._on_label_selection_changed)
        labels_layout.addWidget(self.label_list)

        # Label editing controls
        edit_layout = QHBoxLayout()

        # Left side - ID, name and color
        left_layout = QVBoxLayout()

        form_layout = QFormLayout()
        
        self.id_edit = QLineEdit()
        self.id_edit.textChanged.connect(self._on_id_changed)
        self.id_edit.setPlaceholderText("Unique identifier (e.g. intro, verse, chorus)")
        form_layout.addRow("ID:", self.id_edit)
        
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self._on_name_changed)
        self.name_edit.setPlaceholderText("Display name (e.g. Intro, Verse, Chorus)")
        form_layout.addRow("Name:", self.name_edit)

        color_layout = QHBoxLayout()
        self.color_button = QPushButton()
        self.color_button.setFixedSize(30, 30)
        self.color_button.clicked.connect(self._choose_color)
        self.color_label = QLabel("Click to change color")
        color_layout.addWidget(self.color_button)
        color_layout.addWidget(self.color_label)
        color_layout.addStretch()
        form_layout.addRow("Color:", color_layout)

        left_layout.addLayout(form_layout)
        edit_layout.addLayout(left_layout)

        # Right side - buttons
        button_layout = QVBoxLayout()
        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self._add_label)
        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self._remove_label)
        self.remove_button.setEnabled(False)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addStretch()

        edit_layout.addLayout(button_layout)
        labels_layout.addLayout(edit_layout)

        layout.addWidget(labels_group)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self._update_mode_description()

    def _load_data(self):
        """Load current labels and mode into the UI."""
        # Load labeling mode
        current_mode = self.label_manager.get_labeling_mode()
        mode_index = self.mode_combo.findData(current_mode)
        if mode_index >= 0:
            self.mode_combo.setCurrentIndex(mode_index)

        # Load labels
        self._refresh_label_list()

    def _refresh_label_list(self):
        """Refresh the label list widget."""
        self.label_list.clear()

        for label_data in self.label_manager.get_labels():
            # Display both name and ID
            display_text = f"{label_data['name']} ({label_data.get('id', '')})" if label_data.get('id') else label_data['name']
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, label_data)

            # Set color indicator
            color = QColor(label_data["color"])
            item.setBackground(color)

            # Set text color based on background brightness
            brightness = (
                color.red() * 0.299 + color.green() * 0.587 + color.blue() * 0.114
            )
            text_color = QColor("white") if brightness < 128 else QColor("black")
            item.setForeground(text_color)

            self.label_list.addItem(item)

    def _on_mode_changed(self):
        """Handle labeling mode change."""
        self._update_mode_description()

        # Update the label manager
        selected_mode = self.mode_combo.currentData()
        if selected_mode:
            self.label_manager.set_labeling_mode(selected_mode)

    def _update_mode_description(self):
        """Update the mode description text."""
        current_mode = self.mode_combo.currentData()

        if current_mode == "segmentation":
            description = (
                "Segmentation Mode:\n"
                "• Labels form connected segments with no gaps\n"
                "• New labels start where the previous label ends\n"
                "• Moving boundaries affects adjacent labels\n"
                "• Best for dividing audio into continuous sections"
            )
        elif current_mode == "annotation":
            description = (
                "Annotation Mode:\n"
                "• Labels can be placed freely with gaps and overlaps\n"
                "• New labels are independent of existing ones\n"
                "• Moving boundaries only affects the selected label\n"
                "• Best for marking specific events or features"
            )
        else:
            description = "Select a labeling mode above."

        self.mode_description.setPlainText(description)

    def _on_label_selection_changed(self):
        """Handle label selection change."""
        current_item = self.label_list.currentItem()

        if current_item:
            label_data = current_item.data(Qt.ItemDataRole.UserRole)
            self.id_edit.setText(label_data.get("id", ""))
            self.name_edit.setText(label_data["name"])
            self._update_color_button(QColor(label_data["color"]))
            self.remove_button.setEnabled(True)
        else:
            self.id_edit.clear()
            self.name_edit.clear()
            self._update_color_button(QColor(100, 150, 200))
            self.remove_button.setEnabled(False)

    def _on_id_changed(self):
        """Handle ID edit change."""
        current_item = self.label_list.currentItem()
        if current_item and self.id_edit.text().strip():
            label_data = current_item.data(Qt.ItemDataRole.UserRole)
            new_id = self.id_edit.text().strip()
            
            # Validate ID (alphanumeric and underscores only)
            if not all(c.isalnum() or c == '_' for c in new_id):
                # Reset to previous value
                self.id_edit.setText(label_data.get("id", ""))
                return
                
            label_data["id"] = new_id
            
            # Update the display text to show both name and ID
            current_item.setText(f"{label_data['name']} ({new_id})")
            current_item.setData(Qt.ItemDataRole.UserRole, label_data)

    def _on_name_changed(self):
        """Handle name edit change."""
        current_item = self.label_list.currentItem()
        if current_item and self.name_edit.text().strip():
            label_data = current_item.data(Qt.ItemDataRole.UserRole)
            label_data["name"] = self.name_edit.text().strip()
            
            # Update the display text to show both name and ID
            label_id = label_data.get("id", "")
            current_item.setText(f"{label_data['name']} ({label_id})" if label_id else label_data['name'])
            current_item.setData(Qt.ItemDataRole.UserRole, label_data)

    def _choose_color(self):
        """Open color picker dialog."""
        current_item = self.label_list.currentItem()
        current_color = QColor(100, 150, 200)

        if current_item:
            label_data = current_item.data(Qt.ItemDataRole.UserRole)
            current_color = QColor(label_data["color"])

        color = QColorDialog.getColor(current_color, self, "Choose Label Color")

        if color.isValid():
            self._update_color_button(color)

            if current_item:
                label_data = current_item.data(Qt.ItemDataRole.UserRole)
                label_data["color"] = color.name()
                current_item.setData(Qt.ItemDataRole.UserRole, label_data)

                # Update item appearance
                current_item.setBackground(color)
                brightness = (
                    color.red() * 0.299 + color.green() * 0.587 + color.blue() * 0.114
                )
                text_color = QColor("white") if brightness < 128 else QColor("black")
                current_item.setForeground(text_color)

    def _update_color_button(self, color: QColor):
        """Update the color button appearance."""
        self.color_button.setStyleSheet(f"background-color: {color.name()};")

    def _add_label(self):
        """Add a new label."""
        name = self.name_edit.text().strip()
        label_id = self.id_edit.text().strip()
        
        if not name:
            name = f"Label {self.label_list.count() + 1}"
            
        if not label_id:
            # Generate ID from name
            label_id = name.lower().replace(" ", "_").replace("-", "_")
            # Remove any non-alphanumeric characters except underscores
            label_id = ''.join(c if c.isalnum() or c == '_' else '' for c in label_id)

        # Check for duplicate names and IDs
        existing_names = [
            self.label_list.item(i).data(Qt.ItemDataRole.UserRole)["name"] 
            for i in range(self.label_list.count())
        ]
        existing_ids = [
            self.label_list.item(i).data(Qt.ItemDataRole.UserRole).get("id", "") 
            for i in range(self.label_list.count())
        ]
        
        if name in existing_names:
            base_name = name
            counter = 1
            while f"{base_name} {counter}" in existing_names:
                counter += 1
            name = f"{base_name} {counter}"
            
        if label_id in existing_ids:
            base_id = label_id
            counter = 1
            while f"{base_id}_{counter}" in existing_ids:
                counter += 1
            label_id = f"{base_id}_{counter}"

        # Get color from button or use default
        color = QColor(100, 150, 200)
        button_style = self.color_button.styleSheet()
        if "background-color:" in button_style:
            color_str = button_style.split("background-color:")[1].split(";")[0].strip()
            color = QColor(color_str)

        # Create new label data
        label_data = {
            "id": label_id,
            "name": name,
            "color": color.name(),
            "key": None,  # Will be assigned when used
            "description": "",
        }

        # Add to list
        item = QListWidgetItem(f"{name} ({label_id})")
        item.setData(Qt.ItemDataRole.UserRole, label_data)
        item.setBackground(color)

        brightness = color.red() * 0.299 + color.green() * 0.587 + color.blue() * 0.114
        text_color = QColor("white") if brightness < 128 else QColor("black")
        item.setForeground(text_color)

        self.label_list.addItem(item)
        self.label_list.setCurrentItem(item)

        # Clear fields for next label
        self.id_edit.clear()
        self.name_edit.clear()

    def _remove_label(self):
        """Remove the selected label."""
        current_item = self.label_list.currentItem()
        if not current_item:
            return

        label_data = current_item.data(Qt.ItemDataRole.UserRole)
        label_identifier = label_data.get("id", label_data["name"])

        # Check if label is in use
        if self.label_manager.is_label_in_use(label_identifier):
            reply = QMessageBox.question(
                self,
                "Label In Use",
                f"The label '{label_data['name']}' is currently being used. "
                "Removing it will delete all associated segments. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

        # Remove from list
        row = self.label_list.row(current_item)
        self.label_list.takeItem(row)

    def accept(self):
        """Save changes and close dialog."""
        try:
            # Collect all labels from the list
            labels = []
            ids_used = set()
            
            for i in range(self.label_list.count()):
                item = self.label_list.item(i)
                label_data = item.data(Qt.ItemDataRole.UserRole)
                
                # Validate required fields
                if not label_data.get("name", "").strip():
                    QMessageBox.warning(self, "Validation Error", f"Label at position {i+1} is missing a name.")
                    return
                    
                if not label_data.get("id", "").strip():
                    QMessageBox.warning(self, "Validation Error", f"Label '{label_data['name']}' is missing an ID.")
                    return
                    
                # Check for duplicate IDs
                label_id = label_data["id"]
                if label_id in ids_used:
                    QMessageBox.warning(self, "Validation Error", f"Duplicate ID '{label_id}' found. Each label must have a unique ID.")
                    return
                ids_used.add(label_id)
                
                labels.append(label_data)

            # Update label manager
            self.label_manager.set_labels(labels)

            # Save to config
            self.label_manager.save_config()

            # Emit signal
            self.labels_changed.emit()

            super().accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save labels: {str(e)}")
