# gui/sprint_validation_page.py
import logging
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from gui.ui_sprint_validation_page import Ui_SprintValidationPage

class SprintValidationPage(QWidget):
    """
    The logic handler for the new Sprint Validation Report page.
    """
    proceed_to_planning = Signal()
    return_to_backlog = Signal()
    rerun_stale_analysis = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_SprintValidationPage()
        self.ui.setupUi(self)
        self.stale_item_ids = []
        self.connect_signals()

    def connect_signals(self):
        """Connects UI element signals to this widget's public signals."""
        self.ui.proceedButton.clicked.connect(self.on_proceed_clicked)
        self.ui.returnToBacklogButton.clicked.connect(self.return_to_backlog.emit)

    def on_proceed_clicked(self):
        """Determines which signal to emit based on the validation results."""
        if self.stale_item_ids:
            self.rerun_stale_analysis.emit(self.stale_item_ids)
        else:
            self.proceed_to_planning.emit()

    def show_processing(self):
        """Switches the view to show the processing message."""
        self.ui.reportStackedWidget.setCurrentWidget(self.ui.processingPage)

    def populate_report(self, report_data: dict):
        """Populates the UI with the results of the validation checks."""
        self.ui.reportStackedWidget.setCurrentWidget(self.ui.reportPage)
        self.stale_item_ids = [] # Reset

        def set_header_style(label, base_text, status):
            """Sets the label text and colors using rich text HTML."""
            status_html = ""
            if status == 'PASS':
                status_html = f"<font color='#52A350'>{status}</font>" # Brighter Green
            elif status == 'FAIL':
                status_html = f"<font color='#FFC66D'>{status}</font>" # Bright Amber
            else: # NOT_RUN or other
                status_html = f"<font color='#A9B7C6'>{status}</font>" # Secondary/Muted Grey

            label.setText(f"<b>{base_text}: {status_html}</b>")

        # Populate Scope Guardrail
        scope_report = report_data.get("scope_guardrail", {})
        set_header_style(self.ui.scopeHeaderLabel, "Scope Guardrail Check", scope_report.get("status"))
        self.ui.scopeDetailsTextEdit.setText(scope_report.get("details", ""))
        self.ui.scopeDetailsTextEdit.setVisible(bool(scope_report.get("details")))

        # Populate Stale Analysis
        stale_report = report_data.get("stale_analysis", {})
        set_header_style(self.ui.staleHeaderLabel, "Stale Analysis Check", stale_report.get("status"))
        self.ui.staleDetailsTextEdit.setText(stale_report.get("details", ""))
        self.ui.staleDetailsTextEdit.setVisible(bool(stale_report.get("details")))

        # Populate Technical Risk
        risk_report = report_data.get("technical_risk", {})
        set_header_style(self.ui.riskHeaderLabel, "Technical Risk Check", risk_report.get("status"))
        self.ui.riskDetailsTextEdit.setText(risk_report.get("details", ""))
        self.ui.riskDetailsTextEdit.setVisible(bool(risk_report.get("details")))

        # Configure the "Proceed" button's text and behavior
        if stale_report.get("status") == 'FAIL':
            self.ui.proceedButton.setText("Re-run Impact Analysis for Stale Items")
            self.stale_item_ids = stale_report.get("stale_item_ids", [])
        else:
            self.ui.proceedButton.setText("Proceed to Plan Generation")

        is_critical_failure = (scope_report.get("status") == 'FAIL' or risk_report.get("status") == 'FAIL')
        self.ui.proceedButton.setEnabled(not is_critical_failure)