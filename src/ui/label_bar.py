"""Label visualization bar that shows labeled segments."""

from typing import List, Optional, Tuple
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont
from PySide6.QtCore import QPoint

from ..core.label_manager import LabelSegment, LabelDefinition


class LabelBar(QWidget):
    """Visual bar showing labeled segments with draggable boundaries."""

    # Signals
    boundary_moved = Signal(
        int, str, float
    )  # segment_index, boundary_type ('start'/'end'), new_time
    segment_selected = Signal(int)  # segment_index
    segment_deleted = Signal(int)  # segment_index
    segment_moved = Signal(
        int, float, float
    )  # segment_index, new_start_time, new_end_time
    boundary_drag_started = Signal(float)  # position where drag started
    boundary_drag_position = Signal(float)  # current drag position
    boundary_drag_ended = Signal()  # drag ended

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setMinimumWidth(200)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Enable keyboard focus

        # Data
        self._segments: List[LabelSegment] = []
        self._label_definitions: dict = {}  # label_id -> LabelDefinition
        self._duration: float = 0.0

        # Interaction state
        self._dragging_boundary: Optional[Tuple[int, str]] = (
            None  # (segment_index, boundary_type)
        )
        self._dragging_segment: Optional[int] = (
            None  # segment_index when dragging entire segment
        )
        self._drag_start_pos: Optional[QPoint] = None
        self._drag_start_time: Optional[float] = (
            None  # Time when drag started (for segment dragging)
        )
        self._segment_start_offset: Optional[float] = (
            None  # Offset from segment start when dragging
        )
        self._hover_boundary: Optional[Tuple[int, str]] = None
        self._selected_segment: Optional[int] = None

        # Visual settings - margins calculated to match matplotlib's actual plot area
        # Matplotlib with tight_layout typically uses these margins for standard figure size
        self._left_margin = 20
        self._right_margin = 18
        self._boundary_width = 3
        self._min_segment_width = 1

        # Mode setting - will be set by parent
        self._annotation_mode = False

        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)

    def set_duration(self, duration_seconds: float) -> None:
        """Set the total duration for scaling."""
        self._duration = duration_seconds
        self.update()

    def set_segments(self, segments: List[LabelSegment]) -> None:
        """Set the label segments to display."""
        self._segments = segments.copy()
        self.update()

    def set_label_definitions(self, label_definitions: List[LabelDefinition]) -> None:
        """Set the label definitions for colors and names."""
        self._label_definitions = {ld.id: ld for ld in label_definitions}
        self.update()

    def set_selected_segment(self, segment_index: Optional[int]) -> None:
        """Set the selected segment index."""
        if segment_index != self._selected_segment:
            self._selected_segment = segment_index
            self.update()

    def get_selected_segment(self) -> Optional[int]:
        """Get the currently selected segment index."""
        return self._selected_segment

    def clear_selection(self) -> None:
        """Clear the current selection."""
        self.set_selected_segment(None)

    def set_annotation_mode(self, enabled: bool) -> None:
        """Set whether annotation mode (segment dragging) is enabled."""
        self._annotation_mode = enabled

    def _time_to_x(self, time_seconds: float) -> int:
        """Convert time to x coordinate, matching waveform alignment."""
        if self._duration <= 0:
            return self._left_margin

        # Calculate usable width (account for left and right margins that match matplotlib)
        total_width = self.width()
        usable_width = total_width - self._left_margin - self._right_margin

        # Ensure we don't go outside bounds
        ratio = min(1.0, max(0.0, time_seconds / self._duration))
        return self._left_margin + int(ratio * usable_width)

    def _x_to_time(self, x: int) -> float:
        """Convert x coordinate to time, matching waveform alignment."""
        if self._duration <= 0:
            return 0.0

        total_width = self.width()
        usable_width = total_width - self._left_margin - self._right_margin

        # Clamp x to valid range
        relative_x = max(0, min(usable_width, x - self._left_margin))
        return (relative_x / usable_width) * self._duration

    def _get_boundary_at_pos(self, pos: QPoint) -> Optional[Tuple[int, str]]:
        """Get boundary (segment_index, boundary_type) at position."""
        tolerance = 5

        for i, segment in enumerate(self._segments):
            start_x = self._time_to_x(segment.start_seconds)
            end_x = self._time_to_x(segment.end_seconds)

            # Check start boundary
            if abs(pos.x() - start_x) <= tolerance:
                return (i, "start")

            # Check end boundary
            if abs(pos.x() - end_x) <= tolerance:
                return (i, "end")

        return None

    def _get_segment_at_pos(self, pos: QPoint) -> Optional[int]:
        """Get segment index at position."""
        for i, segment in enumerate(self._segments):
            start_x = self._time_to_x(segment.start_seconds)
            end_x = self._time_to_x(segment.end_seconds)

            if start_x <= pos.x() <= end_x:
                return i

        return None

    def paintEvent(self, event):
        """Paint the label bar."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor("#2b2b2b"))

        if self._duration <= 0 or not self._segments:
            # Draw empty state
            painter.setPen(QPen(QColor("#666666"), 1))
            painter.drawText(
                self.rect(), Qt.AlignmentFlag.AlignCenter, "No labels defined"
            )
            return

        # Draw segments
        for i, segment in enumerate(self._segments):
            start_x = self._time_to_x(segment.start_seconds)
            end_x = self._time_to_x(segment.end_seconds)
            width = max(self._min_segment_width, end_x - start_x)

            # Get label definition for color
            label_def = self._label_definitions.get(segment.label_id)
            if label_def:
                color = QColor(label_def.color)
            else:
                color = QColor("#888888")  # Default color

            # Draw segment rectangle with proper vertical margins
            top_margin = 5
            rect = QRect(start_x, top_margin, width, self.height() - 2 * top_margin)

            # Highlight selected segment
            if i == self._selected_segment:
                # Draw selection border
                painter.setPen(QPen(QColor("#FFD700"), 3))  # Gold border for selection
                painter.drawRect(rect)
                # Make color slightly brighter for selected segments
                color = color.lighter(120)

            painter.fillRect(rect, QBrush(color))

            # Draw label text
            if width > 40:  # Only draw text if there's enough space
                painter.setPen(QPen(QColor("white"), 1))
                font = QFont()
                font.setPointSize(8)
                font.setBold(True)
                painter.setFont(font)

                text = label_def.name if label_def else str(segment.label_id)
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

            # Highlight boundaries if hovering or dragging
            active_boundary = (
                self._dragging_boundary
                if self._dragging_boundary
                else self._hover_boundary
            )
            if active_boundary:
                hover_index, hover_type = active_boundary
                if hover_index == i:
                    # Use different colors for hover vs drag
                    color = (
                        QColor("#FF0000")
                        if self._dragging_boundary
                        else QColor("#FFFF00")
                    )  # Red for drag, Yellow for hover
                    painter.setPen(QPen(color, 3))
                    if hover_type == "start":
                        painter.drawLine(start_x, 5, start_x, self.height() - 5)
                    elif hover_type == "end":
                        painter.drawLine(end_x, 5, end_x, self.height() - 5)

        # Draw time scale (optional - can be added later)
        painter.setPen(QPen(QColor("#666666"), 1))
        y = self.height() - 2
        painter.drawLine(self._left_margin, y, self.width() - self._right_margin, y)

    def mousePressEvent(self, event):
        """Handle mouse press for dragging boundaries and selecting segments."""
        if event.button() == Qt.MouseButton.LeftButton:
            boundary = self._get_boundary_at_pos(event.pos())
            if boundary:
                self._dragging_boundary = boundary
                self._drag_start_pos = event.pos()
                self.setCursor(Qt.CursorShape.SizeHorCursor)

                # Emit boundary drag started signal with current position
                drag_position = self._x_to_time(event.pos().x())
                self.boundary_drag_started.emit(drag_position)
            else:
                # Check if clicking on a segment
                segment_index = self._get_segment_at_pos(event.pos())
                if segment_index is not None:
                    self.set_selected_segment(segment_index)
                    self.segment_selected.emit(segment_index)
                    self.setFocus()  # Ensure widget has focus for keyboard events

                    # In annotation mode, prepare for segment dragging
                    if self._annotation_mode:
                        self._dragging_segment = segment_index
                        self._drag_start_pos = event.pos()
                        self._drag_start_time = self._x_to_time(event.pos().x())

                        # Calculate offset from segment start
                        segment = self._segments[segment_index]
                        self._segment_start_offset = (
                            self._drag_start_time - segment.start_seconds
                        )

                        self.setCursor(Qt.CursorShape.ClosedHandCursor)
                else:
                    # Clicked on empty space, clear selection
                    self.clear_selection()

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging and hover effects."""
        if self._dragging_boundary and self._drag_start_pos:
            # Handle boundary dragging
            segment_index, boundary_type = self._dragging_boundary
            new_time = self._x_to_time(event.pos().x())

            # Emit boundary drag position for waveform indicator
            self.boundary_drag_position.emit(new_time)

            # Emit boundary moved signal with specific boundary type
            self.boundary_moved.emit(segment_index, boundary_type, new_time)

        elif (
            self._dragging_segment is not None
            and self._drag_start_pos
            and self._segment_start_offset is not None
        ):
            # Handle segment dragging in annotation mode
            current_time = self._x_to_time(event.pos().x())
            segment = self._segments[self._dragging_segment]

            # Calculate new start time based on offset
            new_start_time = current_time - self._segment_start_offset
            segment_duration = segment.end_seconds - segment.start_seconds
            new_end_time = new_start_time + segment_duration

            # Clamp to valid range
            if new_start_time < 0:
                new_start_time = 0
                new_end_time = segment_duration
            elif new_end_time > self._duration:
                new_end_time = self._duration
                new_start_time = self._duration - segment_duration

            # Emit segment moved signal
            self.segment_moved.emit(
                self._dragging_segment, new_start_time, new_end_time
            )

        else:
            # Handle hover effects for boundaries
            boundary = self._get_boundary_at_pos(event.pos())

            if boundary != self._hover_boundary:
                self._hover_boundary = boundary
                self.update()

            # Set cursor
            if boundary:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            else:
                # In annotation mode, check if hovering over a segment
                if self._annotation_mode:
                    segment_index = self._get_segment_at_pos(event.pos())
                    if segment_index is not None:
                        self.setCursor(Qt.CursorShape.OpenHandCursor)
                    else:
                        self.setCursor(Qt.CursorShape.ArrowCursor)
                else:
                    self.setCursor(Qt.CursorShape.ArrowCursor)

    def keyPressEvent(self, event):
        """Handle keyboard events for deleting segments."""
        if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            if self._selected_segment is not None:
                self.segment_deleted.emit(self._selected_segment)
                self.clear_selection()
                event.accept()
                return

        super().keyPressEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release to end dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if we were dragging a boundary
            was_dragging_boundary = self._dragging_boundary is not None

            self._dragging_boundary = None
            self._dragging_segment = None
            self._drag_start_pos = None
            self._drag_start_time = None
            self._segment_start_offset = None
            self.setCursor(Qt.CursorShape.ArrowCursor)

            # Emit boundary drag ended signal if we were dragging
            if was_dragging_boundary:
                self.boundary_drag_ended.emit()
