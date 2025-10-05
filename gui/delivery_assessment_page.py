# gui/delivery_assessment_page.py
import logging
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import Signal

# This import will be generated in the next step
from .ui_delivery_assessment_page import Ui_DeliveryAssessmentPage

class DeliveryAssessmentPage(QWidget):
    """
    The logic handler for the graphical Delivery Assessment report page.
    """
    assessment_approved = Signal()
    project_cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_DeliveryAssessmentPage()
        self.ui.setupUi(self)
        self.connect_signals()

    def connect_signals(self):
        """Connects UI element signals to this widget's public signals."""
        self.ui.approveButton.clicked.connect(self.assessment_approved.emit)
        self.ui.cancelButton.clicked.connect(self.on_cancel_clicked)

    def on_cancel_clicked(self):
        reply = QMessageBox.warning(self, "Cancel Project",
                                    "Are you sure you want to cancel this project?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.project_cancelled.emit()

    def populate_data(self, assessment_data: dict):
        """
        Parses the assessment data from the agent and populates the UI widgets,
        including setting the values and styles for the gauges with improved labels.
        """
        # Inverts risk level to confidence level (Low Risk = High Confidence)
        CONFIDENCE_MAP = {
            "Low": ("High", "#6A8759"),      # Green
            "Medium": ("Medium", "#FFC66D"),    # Yellow
            "High": ("Low", "#CC7832"),      # Orange/Red
            "Very Large": ("Low", "#CC7832") # Orange/Red
        }

        # Maps agent ratings to specific gauge values and descriptive labels
        GAUGE_CONFIG = {
            "feature_scope": {
                "Low": (33, "Small"), "Medium": (66, "Medium"), "High": (100, "Large"), "Very Large": (100, "Very Large")
            },
            "data_schema": {
                "Low": (33, "Simple"), "Medium": (66, "Moderate"), "High": (100, "Complex"), "Very Large": (100, "Very Complex")
            },
            "ui_ux": {
                "Low": (33, "Simple"), "Medium": (66, "Moderate"), "High": (100, "Complex"), "Very Large": (100, "Very Complex")
            },
            "integrations": {
                "Low": (33, "Low"), "Medium": (66, "Medium"), "High": (100, "High"), "Very Large": (100, "Very High")
            }
        }

        def set_gauge(gauge_widget, parameter_name, rating_str):
            config = GAUGE_CONFIG.get(parameter_name, {})
            value, display_text = config.get(rating_str, (0, "N/A"))

            gauge_widget.setValue(value)
            # This dynamic property is used by the QSS for coloring
            gauge_widget.setProperty("level", rating_str)
            gauge_widget.style().unpolish(gauge_widget)
            gauge_widget.style().polish(gauge_widget)
            gauge_widget.setFormat(display_text)

        try:
            # Overall Confidence Level
            risk_data = assessment_data.get("risk_assessment") or {} # FIX
            confidence_level = risk_data.get("overall_risk_level", "N/A")

            confidence_text, confidence_color = CONFIDENCE_MAP.get(confidence_level, ("N/A", "#F0F0F0"))
            self.ui.automationConfidenceLabel.setText(
                f'<b>Automation Confidence Level: <font color="{confidence_color}">{confidence_text}</font></b>'
            )

            # Individual Gauges
            complexity = assessment_data.get("complexity_analysis") or {} # FIX
            set_gauge(self.ui.featureScopeGauge, "feature_scope", complexity.get("feature_scope", {}).get("rating", "N/A"))
            set_gauge(self.ui.dataSchemaGauge, "data_schema", complexity.get("data_schema", {}).get("rating", "N/A"))
            set_gauge(self.ui.uiuxGauge, "ui_ux", complexity.get("ui_ux", {}).get("rating", "N/A"))
            set_gauge(self.ui.integrationsGauge, "integrations", complexity.get("integrations", {}).get("rating", "N/A"))

            # Summary Text (No recommendations)
            summary = risk_data.get("summary", "No summary provided.")
            details_html = f"<b>Summary:</b><p>{summary}</p>"
            self.ui.detailsTextEdit.setHtml(details_html)

        except Exception as e:
            logging.error(f"Failed to populate Delivery Assessment page: {e}", exc_info=True)
            self.ui.detailsTextEdit.setText(f"An error occurred while parsing the assessment data:\n{e}")