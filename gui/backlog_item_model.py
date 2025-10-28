# gui/backlog_item_model.py

import logging
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Signal, Qt, QMimeData, QModelIndex

class BacklogItemModel(QStandardItemModel):
    """
    A custom QStandardItemModel to handle the specific drag-and-drop logic
    and business rules for the ASDF project backlog.
    """
    itemsMoved = Signal(int, object, int) # moved_cr_id, new_parent_cr_id (can be None), new_row

    def __init__(self, parent=None):
        super().__init__(parent)

    def _find_item_by_cr_id(self, cr_id: int, parent_item=None):
        """Recursively searches the model for an item with a matching cr_id."""
        if parent_item is None:
            parent_item = self.invisibleRootItem()

        for row in range(parent_item.rowCount()):
            item = parent_item.child(row, 0)
            if item:
                item_data = item.data(Qt.UserRole)
                if item_data and item_data.get('cr_id') == cr_id:
                    return item
                # Recurse into children
                found_item = self._find_item_by_cr_id(cr_id, parent_item=item)
                if found_item:
                    return found_item
        return None

    def flags(self, index):
        """
        Overrides flags to disable dragging for locked items and to disable dropping ON
        items that cannot be parents (e.g., Backlog Items).
        """
        default_flags = super().flags(index)
        if not index.isValid():
            return default_flags | Qt.ItemIsDropEnabled

        item = self.itemFromIndex(index)
        if not item:
            return default_flags

        # CRITICAL FIX: Add a guard clause. The rest of the logic should only
        # execute if the item has data, which is only true for column 0.
        item_data = item.data(Qt.UserRole)
        if not item_data:
            return default_flags

        is_locked = False
        if item_data.get('status') in ['IMPLEMENTATION_IN_PROGRESS', 'EXISTING']:
            is_locked = True

        parent_item = item.parent()
        while parent_item:
            parent_data = parent_item.data(Qt.UserRole)
            if parent_data and parent_data.get('status') == 'IMPLEMENTATION_IN_PROGRESS':
                is_locked = True
                break
            parent_item = parent_item.parent()

        if is_locked:
            return default_flags & ~Qt.ItemIsDragEnabled & ~Qt.ItemIsDropEnabled

        # Prevent dropping ON items that cannot be parents
        item_type = item_data.get('request_type')
        if item_type in ['BACKLOG_ITEM', 'BUG_REPORT']:
            return default_flags & ~Qt.ItemIsDropEnabled

        return default_flags | Qt.ItemIsDropEnabled

    def supportedDropActions(self):
        return Qt.MoveAction

    def mimeTypes(self):
        """Specifies the custom MIME type this model uses for drag-and-drop."""
        return ["application/x-asdf-backlogitem"]

    def mimeData(self, indexes):
        """Encodes the dragged item's cr_id into the MIME data."""
        mime_data = QMimeData()
        if not indexes:
            return mime_data

        # We only care about the first selected item in a drag operation
        source_item_index = indexes[0]
        source_item = self.itemFromIndex(source_item_index)
        if source_item:
            source_data = source_item.data(Qt.UserRole)
            if source_data and 'cr_id' in source_data:
                # Encode the cr_id as bytes
                mime_data.setData("application/x-asdf-backlogitem", str(source_data['cr_id']).encode())
        return mime_data

    def dropMimeData(self, data: QMimeData, action: Qt.DropAction, row: int, column: int, parent_index: QModelIndex):
        """
        Handles dropping, validates the move, manually moves the item, and emits a signal.
        This version correctly identifies the target parent from column 0.
        """
        if action == Qt.IgnoreAction:
            return True
        if not data.hasFormat("application/x-asdf-backlogitem"):
            return False

        try:
            source_cr_id = int(data.data("application/x-asdf-backlogitem").data().decode())
            source_item = self._find_item_by_cr_id(source_cr_id)
            if not source_item:
                logging.error(f"dropMimeData: Could not find source item with cr_id {source_cr_id}")
                return False

            source_data = source_item.data(Qt.UserRole)
            source_type = source_data.get('request_type')
            source_parent = source_item.parent() or self.invisibleRootItem()
            source_row = source_item.row()

            # --- Determine target parent item and target row index ---
            target_parent_item = None
            target_row = -1

            if row != -1:
                # Dropped BETWEEN items. parent_index is the parent (col 0 or invalid root).
                target_parent_item = self.itemFromIndex(parent_index) or self.invisibleRootItem()
                target_row = row
            elif parent_index.isValid():
                # Dropped ON an item. parent_index can be ANY column.
                # We MUST get the column 0 item for the *actual* parent.
                item_at_drop_index = self.itemFromIndex(parent_index)
                if not item_at_drop_index:
                    return False # Safety check

                # Get the "real" item from column 0 of the same row
                if item_at_drop_index.parent():
                    target_parent_item = item_at_drop_index.parent().child(item_at_drop_index.row(), 0)
                else: # It's a root item
                    target_parent_item = self.item(item_at_drop_index.row(), 0)

                if not target_parent_item:
                    logging.error("Could not find column 0 item for the drop target.")
                    return False

                target_row = target_parent_item.rowCount() # Append as last child
            else:
                # Dropped ON the viewport (empty space). Becomes a root item.
                target_parent_item = self.invisibleRootItem()
                target_row = self.rowCount(QModelIndex())

            if target_parent_item is None:
                logging.error("Failed to determine target parent item.")
                return False

            target_parent_data = target_parent_item.data(Qt.UserRole) if target_parent_item != self.invisibleRootItem() else None
            target_parent_type = target_parent_data.get('request_type') if target_parent_data else None

            # --- Validation Logic (now with correct target_parent_type) ---
            if source_type == 'EPIC' and target_parent_type is not None: return False
            if source_type == 'FEATURE' and target_parent_type not in [None, 'EPIC']: return False
            if source_type in ['BACKLOG_ITEM', 'BUG_REPORT'] and target_parent_type != 'FEATURE': return False

            # Prevent dropping onto self or own children
            temp_item = target_parent_item
            while temp_item and temp_item != self.invisibleRootItem():
                if temp_item == source_item:
                    return False
                temp_item = temp_item.parent()

            # --- Perform the move ---
            if source_parent == target_parent_item and source_row < target_row:
                 target_row -= 1

            row_items = source_parent.takeRow(source_row)
            if not row_items:
                 logging.error(f"takeRow failed for source item {source_cr_id} at row {source_row}")
                 return False

            target_parent_item.insertRow(target_row, row_items)

            # --- Emit signal (now with correct new_parent_cr_id) ---
            new_parent_cr_id = target_parent_data.get('cr_id') if target_parent_data else None
            final_target_row = self.indexFromItem(row_items[0]).row()

            logging.info(f"Emitting itemsMoved: moved_cr_id={source_cr_id}, new_parent_cr_id={new_parent_cr_id}, new_row={final_target_row}")
            self.itemsMoved.emit(source_cr_id, new_parent_cr_id, final_target_row)

            return True

        except Exception as e:
            logging.error(f"An error occurred during dropMimeData: {e}", exc_info=True)
            if 'row_items' in locals() and row_items and 'source_parent' in locals() and 'source_row' in locals():
                source_parent.insertRow(source_row, row_items)
            return False