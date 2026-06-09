"""Main window shell for the Quant Strategy Lab desktop UI."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFrame,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QToolBar,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)

from app.widgets import CandlestickChart, LogPanel, RankingTable, InstrumentEditor, EquityCurveChart, ValidationSummary, GABuildPanel, EliminationConfigWidget
from app.services import StrategyService, ReportService, InstrumentService, DataService, ProjectService
from app.services.validation_pipeline_service import (
    PipelineConfig,
    PipelineResult,
    run_validation_pipeline,
)
from app.services.ga_service import GASearchConfig, run_ga_search
from core.models.dataset import DatasetMeta
from data_engine.quality_checker import DataQualityReport




PAGE_NAMES = (
    "Dashboard",
    "Data",
    "Build",
    "Backtest",
    "Validate",
    "Results",
    "Report",
    "Settings",
)


class MainWindow(QMainWindow):
    """Minimal GUI shell with navigation, workspace, inspector, and logs."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Quant Strategy Lab")
        self.resize(1280, 800)

        self.instrument_service = InstrumentService()
        self.strategy_service = StrategyService()
        self.report_service = ReportService()
        self.data_service = DataService()
        self.project_service = ProjectService()
        self.workspace = QStackedWidget()
        self.ranked_data: list[dict] = []
        self.latest_validation_result: PipelineResult | None = None
        self._loaded_dataset: "pd.DataFrame | None" = None
        self._active_dataset_meta: DatasetMeta | None = None
        self._active_dataset_quality: DataQualityReport | None = None
        self._imported_strategies: list = []
        self.navigation = QListWidget()
        self.inspector_label = QLabel("Inspector\n\nSelect a page to view context.")
        self.log_panel = LogPanel()

        self._build_toolbar()
        self._build_workspace()
        self._build_navigation()
        self._build_inspector()
        self._build_log_panel()

        self.setCentralWidget(self.workspace)
        self.navigation.setCurrentRow(0)
        self.log_panel.add_message("INFO", "Quant Strategy Lab UI shell started.")

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        for label in ("New Project", "Open Project", "Save", "Run", "Pause", "Stop", "Export Report"):
            action = QAction(label, self)
            if label == "New Project":
                action.setEnabled(True)
                action.triggered.connect(self._handle_new_project)
                self.new_project_action = action
            elif label == "Open Project":
                action.setEnabled(True)
                action.triggered.connect(self._handle_open_project)
                self.open_project_action = action
            elif label == "Save":
                action.setEnabled(True)
                action.triggered.connect(self._handle_save)
                self.save_action = action
            elif label == "Run":
                action.setEnabled(True)
                action.triggered.connect(self._handle_run)
                self.run_action = action
                self.run_action.setObjectName("actionRun")
            elif label == "Export Report":
                action.setEnabled(False)
                action.setToolTip("Run validation first to enable report export.")
                action.triggered.connect(self._handle_export_report)
                self.export_action = action
                self.export_action.setObjectName("actionExportReport")
            else:
                action.setEnabled(False)
            toolbar.addAction(action)

    def _build_workspace(self) -> None:
        for page_name in PAGE_NAMES:
            if page_name == "Data":
                self.data_chart = CandlestickChart()
                
                # Import Control Panel (premium dark mode panel)
                control_panel = QFrame()
                control_panel.setFrameShape(QFrame.Shape.StyledPanel)
                control_panel.setStyleSheet("""
                    QFrame {
                        background-color: #1e1e24;
                        border: 1px solid #2a2a2e;
                        border-radius: 4px;
                    }
                    QLabel {
                        border: none;
                        background: transparent;
                    }
                """)
                control_layout = QHBoxLayout(control_panel)
                control_layout.setContentsMargins(8, 8, 8, 8)
                control_layout.setSpacing(12)
                
                self.data_status_label = QLabel("Historical Research Data: None loaded (Using default mock data)")
                self.data_status_label.setObjectName("dataStatusLabel")
                self.data_status_label.setStyleSheet("color: #ffb300; font-weight: bold; font-size: 12px;")
                
                self.btn_import_data = QPushButton("Import OHLCV Data File")
                self.btn_import_data.setObjectName("btnImportData")
                self.btn_import_data.setStyleSheet("""
                    QPushButton {
                        background-color: #26a69a;
                        color: white;
                        font-weight: bold;
                        border-radius: 4px;
                        padding: 6px 14px;
                        border: none;
                    }
                    QPushButton:hover {
                        background-color: #2bbbb0;
                    }
                    QPushButton:disabled {
                        background-color: #555557;
                        color: #8e8e93;
                    }
                """)
                self.btn_import_data.clicked.connect(self._handle_import_ohlcv_data)
                
                format_guide = DataService.get_expected_format_guide()
                self.data_format_guide_label = QLabel(format_guide.splitlines()[0])
                self.data_format_guide_label.setObjectName("dataFormatGuideLabel")
                self.data_format_guide_label.setToolTip(format_guide)
                self.data_format_guide_label.setStyleSheet("color: #888; font-size: 11px; padding-left: 4px;")
                self.data_format_guide_label.setWordWrap(True)

                control_layout.addWidget(self.data_status_label, 1)
                control_layout.addWidget(self.data_format_guide_label)
                control_layout.addWidget(self.btn_import_data)
                
                page = QFrame()
                page.setFrameShape(QFrame.Shape.NoFrame)
                layout = QVBoxLayout(page)
                layout.setContentsMargins(12, 12, 12, 12)
                layout.setSpacing(8)
                
                title = QLabel("Data View")
                title.setObjectName("pageTitle")
                title.setStyleSheet("font-size: 16px; font-weight: bold; color: #26a69a;")
                
                layout.addWidget(title)
                layout.addWidget(control_panel)
                layout.addWidget(self.data_chart)
                self.workspace.addWidget(page)
            elif page_name == "Results":
                from PySide6.QtWidgets import QTabWidget
                from app.widgets import TradeListWidget, ParameterHeatmapWidget, StrategyDetailWidget
                
                self.results_table = RankingTable()
                self.results_chart = EquityCurveChart()
                self.trade_list = TradeListWidget()
                self.heatmap_widget = ParameterHeatmapWidget()
                self.strategy_detail = StrategyDetailWidget()
                self.results_table.table.itemSelectionChanged.connect(self._handle_strategy_selection_changed)
                self.strategy_detail.add_custom_condition_requested.connect(self._handle_add_custom_condition)
                
                self.elimination_config_widget = EliminationConfigWidget()
                self.elimination_config_widget.set_config_dict(self.strategy_service.get_elimination_config_dict())
                self.elimination_config_widget.config_changed.connect(self._handle_elimination_config_changed)
                
                page = QFrame()
                page.setFrameShape(QFrame.Shape.NoFrame)
                layout = QVBoxLayout(page)
                layout.setContentsMargins(12, 12, 12, 12)
                layout.setSpacing(8)
                
                title = QLabel("Strategy Results Ranking")
                title.setObjectName("pageTitle")
                title.setStyleSheet("font-size: 16px; font-weight: bold; color: #26a69a;")
                
                self.btn_export_archive = QPushButton("Export Archive")
                self.btn_export_archive.setStyleSheet("""
                    QPushButton {
                        background-color: #607D8B;
                        color: white;
                        border: 1px solid #455A64;
                        border-radius: 3px;
                        padding: 6px 12px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #78909C;
                    }
                    QPushButton:disabled {
                        background-color: #CCCCCC;
                        color: #888888;
                    }
                """)
                self.btn_export_archive.setEnabled(False)
                self.btn_export_archive.clicked.connect(self._handle_export_archive)

                self.btn_export_python = QPushButton("Export Code")
                self.btn_export_python.setStyleSheet("""
                    QPushButton {
                        background-color: #3f51b5;
                        color: white;
                        font-weight: bold;
                        border-radius: 4px;
                        padding: 6px 14px;
                        border: none;
                    }
                    QPushButton:hover { background-color: #5c6bc0; }
                    QPushButton:disabled { background-color: #555557; color: #8e8e93; }
                """)
                self.btn_export_python.setEnabled(False)
                self.btn_export_python.clicked.connect(self._handle_export_code)
                
                self.btn_export_json = QPushButton("Export JSON")
                self.btn_export_json.setStyleSheet("""
                    QPushButton {
                        background-color: #fbc02d;
                        color: #1a1a1a;
                        font-weight: bold;
                        border-radius: 4px;
                        padding: 6px 14px;
                        border: none;
                    }
                    QPushButton:hover { background-color: #fdd835; }
                    QPushButton:disabled { background-color: #555557; color: #8e8e93; }
                """)
                self.btn_export_json.setEnabled(False)
                self.btn_export_json.clicked.connect(self._handle_export_json)
                
                self.btn_preview_json_import = QPushButton("Preview JSON Import")
                self.btn_preview_json_import.setStyleSheet("""
                    QPushButton {
                        background-color: #00897b;
                        color: white;
                        font-weight: bold;
                        border-radius: 4px;
                        padding: 6px 14px;
                        border: none;
                    }
                    QPushButton:hover { background-color: #26a69a; }
                """)
                self.btn_preview_json_import.clicked.connect(self._handle_import_json_preview)
                
                header_layout = QHBoxLayout()
                header_layout.addWidget(title)
                header_layout.addStretch()
                header_layout.addWidget(self.btn_preview_json_import)
                header_layout.addWidget(self.btn_export_archive)
                header_layout.addWidget(self.btn_export_json)
                header_layout.addWidget(self.btn_export_python)
                
                self.ga_results_summary_label = QLabel()
                self.ga_results_summary_label.setStyleSheet(
                    "background-color: #2e7d32; color: white; padding: 6px; border-radius: 4px;"
                )
                self.ga_results_summary_label.hide()
                
                self.gp_results_summary_label = QLabel()
                self.gp_results_summary_label.setStyleSheet(
                    "background-color: #0277bd; color: white; padding: 6px; border-radius: 4px;"
                )
                self.gp_results_summary_label.hide()
                
                self.results_tabs = QTabWidget()
                self.results_tabs.addTab(self.strategy_detail, "Strategy Detail")
                self.results_tabs.addTab(self.results_chart, "Equity Curve")
                self.results_tabs.addTab(self.trade_list, "Trade List")
                self.results_tabs.addTab(self.heatmap_widget, "Parameter Heatmap")
                
                top_split = QHBoxLayout()
                top_split.addWidget(self.results_table, stretch=7)
                top_split.addWidget(self.elimination_config_widget, stretch=3)
                
                layout.addLayout(header_layout)
                layout.addWidget(self.ga_results_summary_label)
                layout.addWidget(self.gp_results_summary_label)
                layout.addLayout(top_split, stretch=4)
                layout.addWidget(self.results_tabs, stretch=6)
                self.workspace.addWidget(page)
                
                # Fetch ranked strategies from service and load them using the active profile
                self._refresh_results_ranking()
            elif page_name == "Validate":
                self.validation_summary = ValidationSummary()
                from PySide6.QtWidgets import QCheckBox
                self.wfe_checkbox = QCheckBox("Calculate WFE")
                self.wfe_checkbox.setToolTip("Runs an extra in-sample backtest per walk-forward window. Slower; diagnostic only.")
                
                page = QFrame()
                page.setFrameShape(QFrame.Shape.NoFrame)
                layout = QVBoxLayout(page)
                layout.setContentsMargins(12, 12, 12, 12)

                title = QLabel("Validation Pipeline")
                title.setObjectName("pageTitle")
                title.setStyleSheet("font-size: 16px; font-weight: bold; color: #26a69a;")

                header_layout = QHBoxLayout()
                header_layout.addWidget(title)
                header_layout.addStretch()
                header_layout.addWidget(self.wfe_checkbox)

                layout.addLayout(header_layout)

                # Remove-best-N stress controls.
                from PySide6.QtWidgets import QSpinBox, QDoubleSpinBox
                self.remove_best_n_checkbox = QCheckBox("Remove Best N Trades Stress")
                self.remove_best_n_checkbox.setToolTip(
                    "Removes the top N best-performing trades and rechecks performance. "
                    "Requires >N trades to be meaningful. Off by default."
                )
                self.remove_best_n_checkbox.setChecked(False)

                self.remove_best_n_n_spin = QSpinBox()
                self.remove_best_n_n_spin.setMinimum(1)
                self.remove_best_n_n_spin.setMaximum(50)
                self.remove_best_n_n_spin.setValue(3)
                self.remove_best_n_n_spin.setToolTip("Number of best trades to remove.")
                self.remove_best_n_n_spin.setEnabled(False)

                self.remove_best_n_threshold_spin = QDoubleSpinBox()
                self.remove_best_n_threshold_spin.setMinimum(0.01)
                self.remove_best_n_threshold_spin.setMaximum(1.00)
                self.remove_best_n_threshold_spin.setSingleStep(0.05)
                self.remove_best_n_threshold_spin.setDecimals(2)
                self.remove_best_n_threshold_spin.setValue(0.30)
                self.remove_best_n_threshold_spin.setToolTip("Maximum allowed PnL loss ratio (0.01-1.00).")
                self.remove_best_n_threshold_spin.setEnabled(False)

                def _toggle_remove_best_n_spins(checked):
                    self.remove_best_n_n_spin.setEnabled(checked)
                    self.remove_best_n_threshold_spin.setEnabled(checked)

                self.remove_best_n_checkbox.toggled.connect(_toggle_remove_best_n_spins)

                stress_opts_layout = QHBoxLayout()
                stress_opts_layout.addWidget(self.remove_best_n_checkbox)
                stress_opts_layout.addWidget(QLabel("N:"))
                stress_opts_layout.addWidget(self.remove_best_n_n_spin)
                stress_opts_layout.addWidget(QLabel("Max PnL Loss:"))
                stress_opts_layout.addWidget(self.remove_best_n_threshold_spin)
                stress_opts_layout.addStretch()
                layout.addLayout(stress_opts_layout)

                # Bootstrap MC controls.
                self.bootstrap_checkbox = QCheckBox("Bootstrap Monte Carlo")
                self.bootstrap_checkbox.setToolTip(
                    "Resamples trades with replacement to compute 95% confidence intervals. "
                    "Heavier (200 iterations). Off by default."
                )
                self.bootstrap_checkbox.setChecked(False)

                self.bootstrap_iter_spin = QSpinBox()
                self.bootstrap_iter_spin.setMinimum(50)
                self.bootstrap_iter_spin.setMaximum(2000)
                self.bootstrap_iter_spin.setSingleStep(50)
                self.bootstrap_iter_spin.setValue(200)
                self.bootstrap_iter_spin.setToolTip("Number of bootstrap iterations (50-2000).")
                self.bootstrap_iter_spin.setEnabled(False)

                self.bootstrap_conf_spin = QDoubleSpinBox()
                self.bootstrap_conf_spin.setMinimum(0.80)
                self.bootstrap_conf_spin.setMaximum(0.99)
                self.bootstrap_conf_spin.setSingleStep(0.01)
                self.bootstrap_conf_spin.setDecimals(2)
                self.bootstrap_conf_spin.setValue(0.95)
                self.bootstrap_conf_spin.setToolTip("Confidence level for CI computation (0.80-0.99).")
                self.bootstrap_conf_spin.setEnabled(False)

                def _toggle_bootstrap_spins(checked):
                    self.bootstrap_iter_spin.setEnabled(checked)
                    self.bootstrap_conf_spin.setEnabled(checked)

                self.bootstrap_checkbox.toggled.connect(_toggle_bootstrap_spins)

                bootstrap_layout = QHBoxLayout()
                bootstrap_layout.addWidget(self.bootstrap_checkbox)
                bootstrap_layout.addWidget(QLabel("Iterations:"))
                bootstrap_layout.addWidget(self.bootstrap_iter_spin)
                bootstrap_layout.addWidget(QLabel("Confidence:"))
                bootstrap_layout.addWidget(self.bootstrap_conf_spin)
                bootstrap_layout.addStretch()
                layout.addLayout(bootstrap_layout)

                # Price-noise stress controls.
                self.price_noise_checkbox = QCheckBox("Price-Noise Stress")
                self.price_noise_checkbox.setToolTip(
                    "Adds Gaussian noise to OHLC prices. "
                    "Helps detect overfit strategies. Off by default."
                )
                self.price_noise_checkbox.setChecked(False)

                self.price_noise_pct_spin = QDoubleSpinBox()
                self.price_noise_pct_spin.setMinimum(0.001)
                self.price_noise_pct_spin.setMaximum(0.05)
                self.price_noise_pct_spin.setSingleStep(0.001)
                self.price_noise_pct_spin.setDecimals(3)
                self.price_noise_pct_spin.setValue(0.005)
                self.price_noise_pct_spin.setToolTip(
                    "Std dev of Gaussian noise as a fraction of price; 0.005 = 0.5%."
                )
                self.price_noise_pct_spin.setEnabled(False)

                self.price_noise_iter_spin = QSpinBox()
                self.price_noise_iter_spin.setMinimum(10)
                self.price_noise_iter_spin.setMaximum(500)
                self.price_noise_iter_spin.setSingleStep(10)
                self.price_noise_iter_spin.setValue(50)
                self.price_noise_iter_spin.setToolTip("Number of noise-sampled backtests (10–500).")
                self.price_noise_iter_spin.setEnabled(False)

                self.price_noise_seed_spin = QSpinBox()
                self.price_noise_seed_spin.setMinimum(1)
                self.price_noise_seed_spin.setMaximum(9999)
                self.price_noise_seed_spin.setValue(42)
                self.price_noise_seed_spin.setToolTip("Deterministic seed for reproducibility.")
                self.price_noise_seed_spin.setEnabled(False)

                def _toggle_price_noise_spins(checked):
                    self.price_noise_pct_spin.setEnabled(checked)
                    self.price_noise_iter_spin.setEnabled(checked)
                    self.price_noise_seed_spin.setEnabled(checked)

                self.price_noise_checkbox.toggled.connect(_toggle_price_noise_spins)

                pn_layout = QHBoxLayout()
                pn_layout.addWidget(self.price_noise_checkbox)
                pn_layout.addWidget(QLabel("Noise fraction:"))
                pn_layout.addWidget(self.price_noise_pct_spin)
                pn_layout.addWidget(QLabel("Iterations:"))
                pn_layout.addWidget(self.price_noise_iter_spin)
                pn_layout.addWidget(QLabel("Seed:"))
                pn_layout.addWidget(self.price_noise_seed_spin)
                pn_layout.addStretch()
                layout.addLayout(pn_layout)

                # IS Baseline Quality Precheck controls.
                self.precheck_checkbox = QCheckBox("IS Baseline Quality Precheck")
                self.precheck_checkbox.setToolTip(
                    "Skips stress/MC/WF when baseline has zero trades. Opt-in."
                )
                self.precheck_checkbox.setChecked(False)

                self.precheck_nonpositive_checkbox = QCheckBox("Fail on non-positive PnL")
                self.precheck_nonpositive_checkbox.setToolTip(
                    "Also fails strategies with total_pnl <= 0. "
                    "Works only when precheck is enabled."
                )
                self.precheck_nonpositive_checkbox.setChecked(False)
                self.precheck_nonpositive_checkbox.setEnabled(False)

                def _toggle_precheck_spins(checked):
                    self.precheck_nonpositive_checkbox.setEnabled(checked)

                self.precheck_checkbox.toggled.connect(_toggle_precheck_spins)

                precheck_layout = QHBoxLayout()
                precheck_layout.addWidget(self.precheck_checkbox)
                precheck_layout.addWidget(self.precheck_nonpositive_checkbox)
                precheck_layout.addStretch()
                layout.addLayout(precheck_layout)

                # Validation run progress / status indicator.
                self.validation_status_label = QLabel()
                self.validation_status_label.setObjectName("validationStatusLabel")
                self.validation_status_label.setStyleSheet(
                    "font-weight: bold; font-size: 12px; padding: 4px 0;"
                )
                self.validation_status_label.hide()
                layout.addWidget(self.validation_status_label)

                layout.addWidget(self.validation_summary)
                self.workspace.addWidget(page)
            elif page_name == "Settings":
                self.instrument_editor = InstrumentEditor(self.instrument_service)
                self.instrument_editor.active_profile_changed.connect(self._handle_active_profile_changed)
                page = QFrame()
                page.setFrameShape(QFrame.Shape.NoFrame)
                layout = QVBoxLayout(page)
                layout.setContentsMargins(12, 12, 12, 12)
                
                title = QLabel("Settings")
                title.setObjectName("pageTitle")
                title.setStyleSheet("font-size: 16px; font-weight: bold; color: #26a69a;")
                
                layout.addWidget(title)
                layout.addWidget(self.instrument_editor)
                self.workspace.addWidget(page)
            elif page_name == "Build":
                self.ga_build_panel = GABuildPanel()
                self.ga_build_panel.btn_run_ga.clicked.connect(self._handle_run_ga)
                self.ga_build_panel.btn_run_gp.clicked.connect(self._handle_run_gp)
                page = QFrame()
                page.setFrameShape(QFrame.Shape.NoFrame)
                layout = QVBoxLayout(page)
                layout.setContentsMargins(12, 12, 12, 12)
                layout.setSpacing(8)

                title = QLabel("Strategy Builder — Genetic Algorithm")
                title.setObjectName("pageTitle")
                title.setStyleSheet("font-size: 16px; font-weight: bold; color: #26a69a;")

                layout.addWidget(title)
                layout.addWidget(self.ga_build_panel)
                self.workspace.addWidget(page)
            else:
                self.workspace.addWidget(self._create_placeholder_page(page_name))

    def _build_navigation(self) -> None:
        for page_name in PAGE_NAMES:
            self.navigation.addItem(QListWidgetItem(page_name))
        self.navigation.currentRowChanged.connect(self._set_current_page)

        dock = QDockWidget("Navigation", self)
        dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        dock.setWidget(self.navigation)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

    def _build_inspector(self) -> None:
        self.inspector_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.inspector_label.setWordWrap(True)
        self.inspector_label.setMargin(12)

        dock = QDockWidget("Inspector", self)
        dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        dock.setWidget(self.inspector_label)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def _build_log_panel(self) -> None:
        dock = QDockWidget("Log", self)
        dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        dock.setWidget(self.log_panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)

    def _set_current_page(self, index: int) -> None:
        if index < 0:
            return
        page_name = PAGE_NAMES[index]
        self.workspace.setCurrentIndex(index)
        
        if page_name == "Data":
            desc = "Displays the normalized OHLCV candlestick chart.\n\nDouble-click or scroll to zoom/pan.\nLoaded with mock data by default."
        elif page_name == "Results":
            desc = "Displays the strategy ranking results table.\n\nStrategies are evaluated across multi-dimensional criteria (PnL, Drawdown, Profit Factor, Win Rate, and Trade Count) to emphasize robustness over simple curve-fitting."
        elif page_name == "Settings":
            desc = "Instrument Profile Editor.\n\nConfigure tick sizes, point values, per-side commission costs, default slippage, and select the active profile to override backtest assumptions."
        elif page_name == "Build":
            desc = "Genetic Algorithm Search.\n\nRun a deterministic GA search to evolve strategy candidates.\nUses multi-dimensional fitness scoring with elimination penalties."
        else:
            desc = f"Placeholder for the {page_name} page module."
            
        self.inspector_label.setText(f"{page_name} Inspector\n\n{desc}")
        self.log_panel.add_message("INFO", f"Opened {page_name} page.")

    @staticmethod
    def _create_placeholder_page(page_name: str) -> QWidget:
        page = QFrame()
        page.setFrameShape(QFrame.Shape.NoFrame)

        title = QLabel(page_name)
        title.setObjectName("pageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel(f"{page_name} page placeholder")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(page)
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch()
        return page

    def _handle_export_report(self) -> None:
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Backtest Report",
            "",
            "HTML Files (*.html);;Markdown Files (*.md);;PDF Files (*.pdf)"
        )
        
        if not file_path:
            return

        if selected_filter == "HTML Files (*.html)" and not file_path.lower().endswith(".html"):
            file_path += ".html"
        elif selected_filter == "Markdown Files (*.md)" and not file_path.lower().endswith(".md"):
            file_path += ".md"
        elif selected_filter == "PDF Files (*.pdf)" and not file_path.lower().endswith(".pdf"):
            file_path += ".pdf"

        self.log_panel.add_message("INFO", f"Exporting report to: {file_path}")
        
        try:
            # Delegate payload construction and execution to service layer.
            # Pass latest validation result if available.
            vr_dict = None
            if self.latest_validation_result is not None:
                from dataclasses import asdict
                try:
                    vr_dict = asdict(self.latest_validation_result)
                except Exception:
                    vr_dict = None
            self.report_service.export_mock_report(file_path, validation_result=vr_dict)
            
            self.log_panel.add_message("INFO", f"Report successfully exported to {file_path}")
            QMessageBox.information(
                self,
                "Export Successful",
                f"The backtest report has been successfully exported to:\n{file_path}"
            )
        except Exception as e:
            self.log_panel.add_message("ERROR", f"Failed to export report: {e}")
            QMessageBox.critical(
                self,
                "Export Failed",
                f"An error occurred while exporting the report:\n{str(e)}"
            )

    def _handle_import_json_preview(self) -> None:
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Preview JSON Import",
            "",
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return
            
        try:
            result = self.report_service.preview_strategy_json(file_path)
            if result.get("passed"):
                strat = result.get("strategy")
                name = strat.name if strat else "Unknown"
                
                blocks = 0
                conditions = 0
                if strat:
                    for b in [strat.long_entry, strat.long_exit, strat.short_entry, strat.short_exit]:
                        if b:
                            blocks += 1
                            conditions += len(b.conditions)
                            
                msg = f"Strategy Name: {name}\nBlocks: {blocks}\nConditions: {conditions}\n\nStatus: VALID (Ready for import)\n\nWould you like to import and rank this strategy now?"
                
                reply = QMessageBox.question(
                    self, 
                    "Confirm JSON Import", 
                    msg,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    if not hasattr(self, "_imported_strategies"):
                        self._imported_strategies = []
                        
                    base_name = strat.name
                    count = sum(1 for s in self._imported_strategies if s.name == f"[Imported] {base_name}" or s.name.startswith(f"[Imported] {base_name} ("))
                    
                    if count > 0:
                        strat.name = f"[Imported] {base_name} ({count + 1})"
                    else:
                        strat.name = f"[Imported] {base_name}"
                        
                    self._imported_strategies.append(strat)
                    
                    self.log_panel.add_message("INFO", f"JSON Strategy imported: {strat.name}")
                    
                    self._refresh_results_ranking()
                    
                    self.ga_results_summary_label.setText(
                        f"Imported Strategies Active: {len(self._imported_strategies)}"
                    )
                    self.ga_results_summary_label.show()
                    
                    if self.project_service.is_project_active():
                        save_reply = QMessageBox.question(
                            self,
                            "Save Imported Strategy",
                            f"Would you like to save '{strat.name}' to the active project database?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.Yes
                        )
                        if save_reply == QMessageBox.StandardButton.Yes:
                            try:
                                from app.services.strategy_persistence_service import StrategyPersistenceService
                                persistence_service = StrategyPersistenceService(self.project_service.repository.db)
                                persistence_service.save_best_strategy(
                                    strategy=strat,
                                    label=base_name,
                                    prefix="imported_"
                                )
                                self.log_panel.add_message("INFO", f"Saved imported strategy to project DB: imported_{base_name}")
                                QMessageBox.information(self, "Save Successful", f"Strategy saved to project database as: imported_{base_name}")
                            except Exception as e:
                                self.log_panel.add_message("ERROR", f"Failed to save imported strategy: {e}")
                                QMessageBox.critical(self, "Save Failed", f"Could not save strategy to database:\n{str(e)}")
                else:
                    self.log_panel.add_message("INFO", f"JSON Import declined for: {name}")
            else:
                errors = "\\n".join(result.get("errors", []))
                msg = f"Failed to preview Strategy JSON:\\n\\n{errors}"
                QMessageBox.warning(self, "JSON Preview Failed", msg)
                self.log_panel.add_message("WARN", f"Preview JSON Import failed:\\n{errors}")
        except Exception as e:
            self.log_panel.add_message("ERROR", f"Error previewing JSON: {e}")
            QMessageBox.critical(self, "Error", f"An unexpected error occurred:\\n{str(e)}")

    def _handle_export_json(self) -> None:
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        
        selected_ranges = self.results_table.table.selectedRanges()
        if not selected_ranges or not self.ranked_data:
            self.log_panel.add_message("WARN", "No strategy selected for JSON export.")
            QMessageBox.warning(self, "Export Failed", "Please select a strategy from the Results table first.")
            return
            
        row = selected_ranges[0].topRow()
        if not (0 <= row < len(self.ranked_data)):
            return
            
        strat_item = self.ranked_data[row]
        strategy = strat_item.get("strategy")
        if not strategy:
            self.log_panel.add_message("ERROR", "Selected item has no valid Strategy object.")
            return
        provenance = strat_item.get("provenance")

        import re
        
        raw_name = strategy.name if strategy and strategy.name else "strategy_export"
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', raw_name).replace(' ', '_').strip()
        if not safe_name:
            safe_name = "strategy_export"
            
        default_filename = f"{safe_name}.json" if not safe_name.endswith(".json") else safe_name

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Strategy JSON",
            default_filename,
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return

        if not file_path.lower().endswith(".json"):
            file_path += ".json"

        self.log_panel.add_message("INFO", f"Exporting Strategy JSON to: {file_path}")
        
        try:
            self.report_service.export_strategy_json(strategy, file_path, provenance=provenance)
            self.log_panel.add_message("INFO", f"Strategy JSON successfully exported to {file_path}")
            QMessageBox.information(
                self,
                "Export Successful",
                f"The Strategy JSON has been successfully exported to:\n{file_path}"
            )
        except Exception as e:
            self.log_panel.add_message("ERROR", f"Failed to export JSON: {e}")
            QMessageBox.critical(
                self,
                "Export Failed",
                f"An error occurred while exporting the JSON:\n{str(e)}"
            )

    def _handle_export_code(self) -> None:
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        
        selected_ranges = self.results_table.table.selectedRanges()
        if not selected_ranges or not self.ranked_data:
            self.log_panel.add_message("WARN", "No strategy selected for code export.")
            QMessageBox.warning(self, "Export Failed", "Please select a strategy from the Results table first.")
            return
            
        row = selected_ranges[0].topRow()
        if not (0 <= row < len(self.ranked_data)):
            return
            
        strat_item = self.ranked_data[row]
        strategy = strat_item.get("strategy")
        if not strategy:
            self.log_panel.add_message("ERROR", "Selected item has no valid Strategy object.")
            return

        import re
        
        raw_name = strategy.name if strategy and strategy.name else "strategy_export"
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', raw_name).replace(' ', '_').strip()
        if not safe_name:
            safe_name = "strategy_export"
            
        default_filename = f"{safe_name}.py" if not safe_name.endswith(".py") else safe_name

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Strategy Code",
            default_filename,
            "Python Files (*.py);;NinjaTrader C# (*.cs)"
        )
        
        if not file_path:
            return

        if selected_filter == "Python Files (*.py)" and not file_path.lower().endswith(".py"):
            file_path += ".py"
        elif selected_filter == "NinjaTrader C# (*.cs)" and not file_path.lower().endswith(".cs"):
            file_path += ".cs"

        self.log_panel.add_message("INFO", f"Exporting strategy code to: {file_path}")
        
        try:
            self.report_service.export_strategy_code(strategy, file_path)
            self.log_panel.add_message("INFO", f"Strategy code successfully exported to {file_path}")
            QMessageBox.information(
                self,
                "Export Successful",
                f"The strategy code has been successfully exported to:\n{file_path}"
            )
        except Exception as e:
            self.log_panel.add_message("ERROR", f"Failed to export code: {e}")
            QMessageBox.critical(
                self,
                "Export Failed",
                f"An error occurred while exporting the code:\n{str(e)}"
            )

    def _handle_export_archive(self) -> None:
        """Guard-first Export Archive handler — checks required inputs before calling service."""
        from PySide6.QtWidgets import QMessageBox

        # Guard 1: project root
        project_root = self._get_archive_project_root()
        if project_root is None:
            self.log_panel.add_message("WARN", "No project root — cannot export archive.")
            QMessageBox.warning(self, "Export Failed", "No project is loaded. Open a project first.")
            return

        # Guard 2: selected strategy
        selected_ranges = self.results_table.table.selectedRanges()
        if not selected_ranges or not self.ranked_data:
            self.log_panel.add_message("WARN", "No strategy selected for archive export.")
            QMessageBox.warning(self, "Export Failed", "Please select a strategy from the Results table first.")
            return

        row = selected_ranges[0].topRow()
        if not (0 <= row < len(self.ranked_data)):
            return

        strat_item = self.ranked_data[row]
        strategy = strat_item.get("strategy")
        if not strategy:
            self.log_panel.add_message("WARN", "Selected item has no valid strategy for archive export.")
            QMessageBox.warning(self, "Export Failed", "No valid strategy found for the selected row.")
            return

        # Guard 3: validation result present and passed
        if not hasattr(self, "latest_validation_result") or self.latest_validation_result is None:
            self.log_panel.add_message("WARN", "No validation result — archive export requires a passed validation.")
            QMessageBox.warning(self, "Export Failed", "This strategy has not been validated. Run validation first.")
            return

        valid = self.latest_validation_result
        elim = self._validation_field(valid, "elimination_result", {}) or {}
        if not elim.get("passed", False):
            self.log_panel.add_message("WARN", "Strategy failed validation — cannot export archive.")
            QMessageBox.warning(self, "Export Failed", "This strategy did not pass validation. Only passed strategies can be exported.")
            return

        # Guard 4: dataset snapshot path
        bm = self._validation_field(valid, "baseline_metrics", {}) or {}
        if not bm:
            self.log_panel.add_message("WARN", "No baseline metrics in validation result.")
            QMessageBox.warning(self, "Export Failed", "No backtest data found for this strategy.")
            return

        # -- All guards passed.  Proceed with export. --
        from pathlib import Path

        # Resolve strategy UID.
        srv = self._get_strategy_persistence_service()
        if srv is None:
            self.log_panel.add_message("ERROR", "Cannot archive export: no strategy persistence service.")
            QMessageBox.critical(self, "Export Failed", "Internal error: strategy service unavailable.")
            return

        strategy_uid, dataset_id = self._resolve_archive_strategy_record(
            strategy,
            srv.list_all_raw(),
        )

        if not strategy_uid:
            self.log_panel.add_message("WARN", "Could not resolve strategy UID for archive export.")
            QMessageBox.warning(self, "Export Failed", "Could not locate strategy UID in the project database.")
            return

        # Resolve dataset metadata.
        ds_raw = self.data_service.get_dataset_raw_by_id(dataset_id) if dataset_id else None
        if not ds_raw:
            self.log_panel.add_message("WARN", "No dataset metadata found for this strategy — cannot export archive.")
            QMessageBox.warning(self, "Export Failed", "No dataset metadata found for this strategy. Dataset metadata is required for archive export.")
            return

        snapshot_path_str = ds_raw.get("normalized_path", "")
        if not snapshot_path_str:
            self.log_panel.add_message("WARN", "Dataset snapshot path missing — cannot export archive.")
            QMessageBox.warning(self, "Export Failed", "Dataset snapshot path is missing. Re-run the backtest or import the dataset again.")
            return

        # Resolve relative path to absolute if needed.
        snapshot_path = Path(snapshot_path_str)
        if not snapshot_path.is_absolute():
            snapshot_path = Path(project_root) / snapshot_path

        if not snapshot_path.is_file():
            self.log_panel.add_message("WARN", f"Dataset snapshot file not found at {snapshot_path} — cannot export archive.")
            QMessageBox.warning(self, "Export Failed", f"Dataset OHLCV file not found at {snapshot_path}. Please re-run the backtest or import the dataset again.")
            return

        # Validation provider.
        validation_dict = self._coerce_archive_validation_result(
            self.latest_validation_result,
            strategy_uid,
        )
        if validation_dict is None:
            self.log_panel.add_message("WARN", "Validation result does not match selected strategy UID.")
            QMessageBox.warning(self, "Export Failed", "Validation result does not match the selected strategy.")
            return

        def _get_validation(uid: str) -> dict | None:
            if uid == strategy_uid:
                return validation_dict
            return None

        # Build data source and export service.
        from app.services.archive_project_data_source import ProjectArchiveDataSource
        from app.services.archive_export_service import ArchiveExportService

        adapter = ProjectArchiveDataSource(
            strategy_rows_provider=lambda: srv.list_all_raw(),
            dataset_rows_provider=lambda did: self.data_service.get_dataset_raw_by_id(did),
            validation_result_provider=_get_validation,
        )

        export_svc = ArchiveExportService(adapter)
        output_dir = Path(project_root) / "exports" / "archives" / strategy_uid

        try:
            archive_path = export_svc.export_strategy_archive(
                strategy_uid=strategy_uid,
                dataset_snapshot_path=str(snapshot_path),
                output_dir=output_dir,
                experiment_name=strategy.name,
            )
            self.log_panel.add_message("INFO", f"Archive successfully exported to {archive_path}")
            QMessageBox.information(self, "Export Successful", f"Archive exported to:\n{archive_path}")
        except Exception as exc:
            self.log_panel.add_message("ERROR", f"Failed to export archive: {exc}")
            QMessageBox.critical(self, "Export Failed", f"An error occurred while exporting the archive:\n{exc}")

    def _get_archive_project_root(self):
        """Return the active project root for archive export guards."""
        project_root = getattr(self, "_project_root", None)
        if project_root is not None:
            return project_root
        if self.project_service.is_project_active():
            project = self.project_service.get_active_project()
            if project is not None:
                return project.root_path
        return None

    @staticmethod
    def _validation_field(result, key: str, default=None):
        """Read a validation field from either PipelineResult or dict."""
        if result is None:
            return default
        if isinstance(result, dict):
            return result.get(key, default)
        return getattr(result, key, default)

    @staticmethod
    def _resolve_archive_strategy_record(strategy, rows: list[dict]) -> tuple[str | None, int | None]:
        """Resolve archive strategy UID and dataset ID from raw strategy rows."""
        import json

        strategy_name = getattr(strategy, "name", None)
        for row in rows:
            raw_payload = row.get("strategy_json", "{}")
            try:
                payload = json.loads(raw_payload) if isinstance(raw_payload, str) else raw_payload
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
            if not isinstance(payload, dict):
                continue
            row_name = payload.get("name") or row.get("name")
            if row_name == strategy_name:
                return payload.get("strategy_uid"), payload.get("dataset_id")
        return None, None

    @staticmethod
    def _coerce_archive_validation_result(result, strategy_uid: str) -> dict | None:
        """Return an archive validation dict, rejecting explicit UID mismatches."""
        from dataclasses import asdict, is_dataclass

        if result is None:
            return None
        if isinstance(result, dict):
            data = dict(result)
        elif is_dataclass(result):
            data = asdict(result)
        else:
            return None

        result_uid = data.get("strategy_uid")
        nested_strategy = data.get("strategy")
        if result_uid is None and isinstance(nested_strategy, dict):
            result_uid = nested_strategy.get("strategy_uid")
        if result_uid is not None and result_uid != strategy_uid:
            return None

        elimination = data.get("elimination_result") or {}
        if isinstance(elimination, dict):
            data.setdefault("passed", bool(elimination.get("passed", False)))
        return data

    def _handle_active_profile_changed(self, symbol: str) -> None:
        self.log_panel.add_message("INFO", f"Active instrument profile changed to: {symbol}")
        self._refresh_results_ranking()
        self.log_panel.add_message("INFO", f"Reran strategy backtests and updated ranking for {symbol}.")

    def _handle_elimination_config_changed(self, config_dict: dict) -> None:
        self.strategy_service.update_elimination_config(config_dict)
        self.log_panel.add_message("INFO", "Elimination rules updated. Refreshing ranking...")
        self._refresh_results_ranking()

    def _refresh_results_ranking(self) -> None:
        """Fetch ranked strategies from service, injecting GA/GP best and imported strategies."""
        active_profile = self.instrument_service.get_active_profile()
        injected = []
        if getattr(self, "_latest_ga_strategy", None) is not None:
            injected.append(self._latest_ga_strategy)
            
        if getattr(self, "_latest_gp_strategy", None) is not None:
            injected.append(self._latest_gp_strategy)
            
        if hasattr(self, "_imported_strategies") and self._imported_strategies:
            injected.extend(self._imported_strategies)

        # Re-fetch from strategy service (which runs backtests)
        self.ranked_data, is_mock = self.strategy_service.get_ranked_strategies(
            dataset_df=self._loaded_dataset,
            instrument=active_profile,
            injected_strategies=injected
        )
        # Force a rank sort just in case
        self.ranked_data = sorted(self.ranked_data, key=lambda x: x.get("fitness", 0), reverse=True)
        for i, item in enumerate(self.ranked_data):
            item["rank"] = i + 1

        self.results_table.set_ranking_data(self.ranked_data, is_mock=is_mock)
        if hasattr(self, "heatmap_widget"):
            self.heatmap_widget.set_data(self.ranked_data)

    def _handle_strategy_selection_changed(self) -> None:
        if hasattr(self, "btn_export_python"):
            self.btn_export_python.setEnabled(False)
        if hasattr(self, "btn_export_json"):
            self.btn_export_json.setEnabled(False)
        if hasattr(self, "btn_export_archive"):
            self.btn_export_archive.setEnabled(False)

        selected_ranges = self.results_table.table.selectedRanges()
        if not selected_ranges or not self.ranked_data:
            if hasattr(self, "strategy_detail"):
                self.strategy_detail.set_strategy_data(None)
            if hasattr(self, "trade_list"):
                self.trade_list.set_trades(None)
            if hasattr(self, "results_chart"):
                self.results_chart.clear()
            return
        
        row = selected_ranges[0].topRow()
        if 0 <= row < len(self.ranked_data):
            strat_item = self.ranked_data[row]
            equity_df = strat_item.get("equity_curve")
            drawdown_df = strat_item.get("drawdown_curve")
            trades = strat_item.get("trades")
            
            if equity_df is not None:
                is_mock = "Sample / Mock" in self.results_table.status_label.text()
                self.results_chart.set_data(equity_df, drawdown_df, is_mock=is_mock)

            if hasattr(self, "trade_list"):
                self.trade_list.set_trades(trades)
                
            if hasattr(self, "strategy_detail"):
                self.strategy_detail.set_strategy_data(strat_item)

            if hasattr(self, "btn_export_python"):
                self.btn_export_python.setEnabled(True)
            if hasattr(self, "btn_export_json"):
                self.btn_export_json.setEnabled(True)
            if hasattr(self, "btn_export_archive"):
                self.btn_export_archive.setEnabled(True)

    def _handle_add_custom_condition(self) -> None:
        """Handle request to add custom formula condition to selected strategy."""
        selected_ranges = self.results_table.table.selectedRanges()
        if not selected_ranges or not self.ranked_data:
            return
            
        row = selected_ranges[0].topRow()
        if not (0 <= row < len(self.ranked_data)):
            return
            
        strat_item = self.ranked_data[row]
        strategy = strat_item.get("strategy")
        if not strategy:
            return
            
        from app.widgets.formula_condition_editor import FormulaConditionDialog
        import copy
        
        dialog = FormulaConditionDialog(self)
        
        def on_condition_added(target_block_name: str, strategy_block) -> None:
            new_strat = copy.deepcopy(strategy)
            
            if target_block_name == "Long Entry":
                new_strat.long_entry.conditions.extend(strategy_block.conditions)
            elif target_block_name == "Long Exit":
                new_strat.long_exit.conditions.extend(strategy_block.conditions)
            elif target_block_name == "Short Entry":
                new_strat.short_entry.conditions.extend(strategy_block.conditions)
            elif target_block_name == "Short Exit":
                new_strat.short_exit.conditions.extend(strategy_block.conditions)
                
            new_strat.name = f"[Imported] {new_strat.name} (Custom)"
            
            if not hasattr(self, "_imported_strategies"):
                self._imported_strategies = []
                
            self._imported_strategies.append(new_strat)
            self.log_panel.add_message("INFO", f"Injected custom formula strategy: {new_strat.name}")
            self._refresh_results_ranking()
            
        dialog.condition_added.connect(on_condition_added)
        dialog.exec()

    def _handle_import_ohlcv_data(self) -> None:
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        import os
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Historical OHLCV Data File",
            "",
            "Text/CSV Files (*.txt *.csv);;All Files (*)"
        )
        
        if not file_path:
            return

        filename = os.path.basename(file_path)
        self.log_panel.add_message("INFO", f"Importing historical research data from: {file_path}...")
        self.btn_import_data.setEnabled(False)
        self.btn_import_data.setText("Importing...")
        QApplication.processEvents()
        
        try:
            # Import file through service layer (uses CsvImporter under the hood).
            df, meta, quality = self.data_service.import_file(file_path, symbol="TXF", timeframe="1min")
            
            # Log quality report results.
            if not quality.passed:
                for err in quality.errors:
                    self.log_panel.add_message("ERROR", f"Quality: {err}")
                self.log_panel.add_message(
                    "WARN",
                    f"Data quality check FAILED — see errors above. "
                    f"Chart may display suspect data."
                )
            elif quality.warnings:
                for w in quality.warnings:
                    self.log_panel.add_message("WARN", f"Quality: {w}")

            # Store dataset for validation pipeline use.
            self._loaded_dataset = df
            self._active_dataset_meta = meta
            self._active_dataset_quality = quality
            self._reset_validation_state()

            # Display normalized data in candlestick chart
            self.data_chart.set_data(df, is_mock=False)
            
            # Update status/labeling
            status_prefix = "✓" if quality.passed else "⚠"
            quality_str = "Passed" if quality.passed else f"Failed ({len(quality.errors)} errors)"
            if quality.warnings:
                quality_str += f" with {len(quality.warnings)} warnings"
            
            start_dt = str(meta.start_datetime)
            end_dt = str(meta.end_datetime)
            
            self.data_status_label.setText(
                f"{status_prefix} Active Dataset: {meta.name} | "
                f"Rows: {meta.row_count:,} | "
                f"Range: {start_dt} to {end_dt} | "
                f"Quality: {quality_str}"
            )
            if quality.passed:
                self.data_status_label.setStyleSheet("color: #26a69a; font-weight: bold; font-size: 12px;")
            else:
                self.data_status_label.setStyleSheet("color: #ef5350; font-weight: bold; font-size: 12px;")
            
            self.log_panel.add_message(
                "INFO",
                f"Successfully imported {len(df):,} rows of historical research data from {filename}."
            )
            QMessageBox.information(
                self,
                "Import Successful",
                f"Successfully imported {len(df):,} rows of historical research data from:\n{filename}"
            )
            
        except Exception as e:
            self._loaded_dataset = None
            self._active_dataset_meta = None
            self._active_dataset_quality = None
            self._reset_validation_state()
            self.data_status_label.setText("Historical Research Data: None loaded (Using default mock data)")
            self.data_status_label.setStyleSheet("color: #ffb300; font-weight: bold; font-size: 12px;")
            user_msg = DataService.get_actionable_import_error(e)
            self.log_panel.add_message("ERROR", f"Failed to import data file: {user_msg}")
            QMessageBox.critical(
                self,
                "Import Failed",
                user_msg
            )
        finally:
            self.btn_import_data.setEnabled(True)
            self.btn_import_data.setText("Import OHLCV Data File")

    def _handle_new_project(self) -> None:
        from PySide6.QtWidgets import QFileDialog, QMessageBox, QInputDialog
        from pathlib import Path
        
        name, ok = QInputDialog.getText(self, "New Project", "Enter Project Name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        
        project_dir = QFileDialog.getExistingDirectory(self, "Select Root Directory for Project", "")
        if not project_dir:
            return
            
        root_path = Path(project_dir) / name
        overwrite = False
        if root_path.exists():
            reply = QMessageBox.question(
                self,
                "Project Already Exists",
                f"The directory '{root_path.name}' already exists. Do you want to overwrite it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                overwrite = True
            else:
                return
                
        self.log_panel.add_message("INFO", f"Creating new project '{name}'...")
        try:
            meta = self.project_service.create_project(name, root_path, overwrite=overwrite)
            
            # Propagate path and db to services
            self.data_service.set_project_path(meta.root_path)
            self.data_service.set_db(self.project_service.repository.db)
            self.instrument_service.set_project_path(meta.root_path)
            self.instrument_editor.refresh_project_status()
            
            # Reset active dataset state upon successful project creation
            self._loaded_dataset = None
            self._active_dataset_meta = None
            self._active_dataset_quality = None
            self._reset_validation_state()
            self.data_status_label.setText("Historical Research Data: None loaded (Using default mock data)")
            self.data_status_label.setStyleSheet("color: #ffb300; font-weight: bold; font-size: 12px;")
            
            # Reset GA / GP / Imported strategy state for the new project
            self._latest_ga_strategy = None
            if hasattr(self, "ga_results_summary_label"):
                self.ga_results_summary_label.hide()
                
            self._latest_gp_strategy = None
            if hasattr(self, "gp_results_summary_label"):
                self.gp_results_summary_label.hide()
                
            self._imported_strategies = []
            
            self.log_panel.add_message("INFO", f"Successfully created and opened project '{meta.name}' at {meta.root_path}.")
            QMessageBox.information(
                self,
                "Project Created",
                f"Project '{meta.name}' has been successfully created and loaded at:\n{meta.root_path}"
            )
            
            # Rerun strategy ranking with the loaded project instruments
            active_profile = self.instrument_service.get_active_profile()
            if active_profile:
                self._handle_active_profile_changed(active_profile.symbol)
                
        except Exception as e:
            self.log_panel.add_message("ERROR", f"Failed to create project: {e}")
            QMessageBox.critical(
                self,
                "Creation Failed",
                f"An error occurred while creating the project:\n{str(e)}"
            )

    def _handle_open_project(self) -> None:
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        
        project_dir = QFileDialog.getExistingDirectory(self, "Open Existing Project Folder", "")
        if not project_dir:
            return
            
        self.log_panel.add_message("INFO", f"Opening existing project from: {project_dir}...")
        try:
            meta = self.project_service.open_project(project_dir)
            
            # Propagate path and db to services
            self.data_service.set_project_path(meta.root_path)
            self.data_service.set_db(self.project_service.repository.db)
            self.instrument_service.set_project_path(meta.root_path)
            self.instrument_editor.refresh_project_status()
            
            # Reset active dataset state upon successful project open
            self._loaded_dataset = None
            self._active_dataset_meta = None
            self._active_dataset_quality = None
            self._reset_validation_state()
            self.data_status_label.setText("Historical Research Data: None loaded (Using default mock data)")
            self.data_status_label.setStyleSheet("color: #ffb300; font-weight: bold; font-size: 12px;")
            
            # Reset GA / GP / Imported strategy state; load GA best from DB if present
            self._latest_ga_strategy = None
            if hasattr(self, "ga_results_summary_label"):
                self.ga_results_summary_label.hide()
                
            self._latest_gp_strategy = None
            if hasattr(self, "gp_results_summary_label"):
                self.gp_results_summary_label.hide()
                
            self._imported_strategies = []
                
            try:
                pers_svc = self._get_strategy_persistence_service()
                if pers_svc:
                    saved_strat = pers_svc.load_best_strategy(label="latest")
                    if saved_strat:
                        # Rename and inject it
                        import copy
                        ga_strat = copy.deepcopy(saved_strat)
                        # Ensure it has the [GA Best] prefix if it wasn't already added
                        if not ga_strat.name.startswith("[GA Best]"):
                            ga_strat.name = f"[GA Best] {ga_strat.name}"
                        self._latest_ga_strategy = ga_strat
                        
                        if hasattr(self, "ga_results_summary_label"):
                            self.ga_results_summary_label.setText(
                                f"<b>Loaded GA Best Strategy:</b> {ga_strat.name}  |  "
                                "<b>Score:</b> N/A (from DB)  |  <b>Source:</b> Project Database"
                            )
                            self.ga_results_summary_label.show()
                        self.log_panel.add_message("INFO", "Loaded previous GA best strategy from project.")
            except Exception as e:
                self.log_panel.add_message("WARN", f"Failed to load GA best strategy: {e}")

            self.log_panel.add_message("INFO", f"Successfully opened project '{meta.name}' from {meta.root_path}.")
            QMessageBox.information(
                self,
                "Project Opened",
                f"Project '{meta.name}' has been successfully opened and loaded."
            )
            
            # Rerun strategy ranking with the loaded project instruments
            active_profile = self.instrument_service.get_active_profile()
            if active_profile:
                self._handle_active_profile_changed(active_profile.symbol)
                
        except Exception as e:
            self.log_panel.add_message("ERROR", f"Failed to open project: {e}")
            QMessageBox.critical(
                self,
                "Open Failed",
                f"An error occurred while opening the project:\n{str(e)}"
            )

    def _get_strategy_persistence_service(self):
        """Return a StrategyPersistenceService if a project is open, else None."""
        if not self.project_service.is_project_active():
            return None
        from app.services.strategy_persistence_service import StrategyPersistenceService
        return StrategyPersistenceService(self.project_service.repository.db)

    def _disable_export_action(self, reason: str) -> None:
        """Disable export with an explanatory tooltip."""
        self.export_action.setEnabled(False)
        self.export_action.setToolTip(reason)

    def _enable_export_action(self) -> None:
        """Enable export after successful validation."""
        self.export_action.setEnabled(True)
        self.export_action.setToolTip("Export the latest validation report.")

    def _reset_validation_state(self) -> None:
        """Clear stale validation UI state when dataset or project changes."""
        self.validation_status_label.hide()
        self.validation_status_label.setText("")
        self.latest_validation_result = None
        self._disable_export_action("Run validation first to enable report export.")

    def _handle_run(self) -> None:
        """Execute the validation pipeline on current data/strategy."""
        import pandas as pd
        from core.models.strategy import Condition, Strategy, StrategyBlock

        self.log_panel.add_message("INFO", "Validation pipeline started.")

        # Show progress indicator.
        self.validation_status_label.setText("Validating...")
        self.validation_status_label.setStyleSheet(
            "color: #ffb300; font-weight: bold; font-size: 12px; padding: 4px 0;"
        )
        self.validation_status_label.show()
        QApplication.processEvents()

        # Disable Run and Export buttons to prevent concurrent launches.
        self.run_action.setEnabled(False)
        self._disable_export_action("Validating...")
        QApplication.processEvents()

        # Determine dataset — use loaded data or fall back to mock.
        df = self._loaded_dataset
        is_mock = df is None
        if is_mock:
            df = self.strategy_service.generate_deterministic_mock_ohlcv(count=300)
            self.log_panel.add_message("INFO", "Using deterministic mock data (no dataset loaded).")
            source_label = "Mock fallback"
        else:
            if self._active_dataset_quality and not self._active_dataset_quality.passed:
                self.log_panel.add_message("ERROR", "Validation pipeline aborted: Active dataset has failed quality checks.")
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "Pipeline Aborted",
                    "Cannot run validation pipeline. The active dataset has failed quality checks."
                )
                self.validation_status_label.hide()
                QApplication.processEvents()
                self.run_action.setEnabled(True)
                self._disable_export_action("Dataset failed quality checks. Re-import data before validation.")
                return
            source_label = self._active_dataset_meta.name if self._active_dataset_meta else "Loaded data"
            self.log_panel.add_message("INFO", f"Using active dataset: {source_label}")

        # Determine strategy — use a default SMA crossover.
        strategy = Strategy(
            name="pipeline_run",
            long_entry=StrategyBlock(conditions=[
                Condition(indicator="SMA", params={"period": 10}, operator=">"),
            ], logic="AND"),
            long_exit=StrategyBlock(conditions=[
                Condition(indicator="SMA", params={"period": 10}, operator="<"),
            ], logic="AND"),
        )

        active_profile = self.instrument_service.get_active_profile()
        self.log_panel.add_message("INFO", "Running split / backtest / stress / MC / WF / elimination...")

        calc_wfe = False
        if hasattr(self, "wfe_checkbox"):
            calc_wfe = self.wfe_checkbox.isChecked()

        run_remove_best_n = False
        remove_best_n_n = 3
        remove_best_n_threshold = 0.30
        if hasattr(self, "remove_best_n_checkbox"):
            run_remove_best_n = self.remove_best_n_checkbox.isChecked()
            remove_best_n_n = self.remove_best_n_n_spin.value()
            remove_best_n_threshold = self.remove_best_n_threshold_spin.value()

        run_bootstrap = False
        bootstrap_iterations = 200
        bootstrap_confidence = 0.95
        if hasattr(self, "bootstrap_checkbox"):
            run_bootstrap = self.bootstrap_checkbox.isChecked()
            bootstrap_iterations = self.bootstrap_iter_spin.value()
            bootstrap_confidence = self.bootstrap_conf_spin.value()

        run_price_noise = False
        price_noise_pct = 0.005
        price_noise_iterations = 50
        price_noise_seed = 42
        if hasattr(self, "price_noise_checkbox"):
            run_price_noise = self.price_noise_checkbox.isChecked()
            price_noise_pct = self.price_noise_pct_spin.value()
            price_noise_iterations = self.price_noise_iter_spin.value()
            price_noise_seed = self.price_noise_seed_spin.value()

        run_precheck = False
        fail_nonpositive = False
        if hasattr(self, "precheck_checkbox"):
            run_precheck = self.precheck_checkbox.isChecked()
            fail_nonpositive = run_precheck and self.precheck_nonpositive_checkbox.isChecked()

        try:
            result = run_validation_pipeline(
                df, strategy,
                config=PipelineConfig(
                    mc_iterations=15, calc_wfe=calc_wfe,
                    run_remove_best_n_trades_stress=run_remove_best_n,
                    remove_best_n_trades_n=remove_best_n_n,
                    remove_best_n_trades_degradation_threshold=remove_best_n_threshold,
                    run_bootstrap_monte_carlo=run_bootstrap,
                    bootstrap_iterations=bootstrap_iterations,
                    bootstrap_confidence_level=bootstrap_confidence,
                    run_price_noise_stress=run_price_noise,
                    price_noise_pct=price_noise_pct,
                    price_noise_iterations=price_noise_iterations,
                    price_noise_seed=price_noise_seed,
                    run_is_baseline_quality_precheck=run_precheck,
                    fail_is_baseline_on_nonpositive_pnl=fail_nonpositive,
                ),
                instrument=active_profile,
                data_source=source_label,
                commission=2.0,
            )

            self.latest_validation_result = result

            # Update the Validate page dashboard.
            self.validation_summary.update_from_result(result, source_label=source_label)

            # Log summary.
            self.log_panel.add_message("INFO", f"Split: train={result.split_metadata}")
            self.log_panel.add_message("INFO",
                f"Backtest: PnL={result.baseline_metrics.get('total_pnl', 0):.0f}, "
                f"PF={result.baseline_metrics.get('profit_factor', 0):.2f}, "
                f"Trades={result.baseline_metrics.get('total_trades', 0)}")
            if result.stress_results:
                comm_deg = result.stress_results[0].get("degradation", {})
                self.log_panel.add_message("INFO",
                    f"Stress (commission 2x): PnL degradation={comm_deg.get('total_pnl', 0):.1%}")
            if result.monte_carlo_summary:
                wc = result.monte_carlo_summary.get("worst_case", {})
                self.log_panel.add_message("INFO",
                    f"MC worst-case PnL: {wc.get('total_pnl', 0):.0f}")
            if result.walk_forward_summary:
                self.log_panel.add_message("INFO",
                    f"WF: {result.walk_forward_summary.get('pass_count', 0)}/"
                    f"{result.walk_forward_summary.get('window_count', 0)} windows passed "
                    f"({result.walk_forward_summary.get('pass_rate', 0):.1%})")
            if result.elimination_result:
                elim = result.elimination_result
                self.log_panel.add_message("INFO",
                    f"Elimination: {'PASSED' if elim['passed'] else 'FAILED — ' + ', '.join(elim['failed_rules'])}")

            if result.oos_metrics:
                oos = result.oos_metrics
                self.log_panel.add_message("INFO",
                    f"OOS: PnL={oos.get('total_pnl', 0):,.0f}, PF={oos.get('profit_factor', 0):.2f}, "
                    f"Trades={oos.get('total_trades', 0)}")

            self.log_panel.add_message("INFO",
                f"Validation pipeline completed successfully"
                f"{' (mock data)' if is_mock else ' (loaded data)'}.")
            # Clear progress indicator on success.
            self.validation_status_label.setText("Validation completed.")
            self.validation_status_label.setStyleSheet(
                "color: #4caf50; font-weight: bold; font-size: 12px; padding: 4px 0;"
            )
            QApplication.processEvents()
            self.inspector_label.setText(
                "Validate Inspector\n\n"
                f"Last run: {source_label},\n"
                f"{result.split_metadata.get('train_rows', 0)} train bars.\n"
                f"Baseline PnL: {result.baseline_metrics.get('total_pnl', 0):.0f}\n"
                f"Elimination: {'✓ Passed' if result.elimination_result and result.elimination_result['passed'] else '✗ Eliminated'}"
            )
            self._enable_export_action()
        except Exception as e:
            self.log_panel.add_message("ERROR", f"Validation pipeline failed: {e}")
            self.inspector_label.setText(
                "Validate Inspector\n\nValidation pipeline encountered an error.\n"
                f"Details: {e}"
            )
            # Show error state on status indicator.
            self.validation_status_label.setText(f"Validation failed: {e}")
            self.validation_status_label.setStyleSheet(
                "color: #ef5350; font-weight: bold; font-size: 12px; padding: 4px 0;"
            )
            QApplication.processEvents()
            self._disable_export_action("Validation failed. Run validation again to enable report export.")
        finally:
            self.run_action.setEnabled(True)
            QApplication.processEvents()

    def _handle_save(self) -> None:
        from PySide6.QtWidgets import QMessageBox
        
        if self.project_service.is_project_active():
            try:
                self.instrument_service._save_to_disk()
                self.log_panel.add_message("INFO", "Project settings and instrument profiles successfully saved to disk.")
                QMessageBox.information(
                    self,
                    "Project Saved",
                    "All project profiles and configuration files have been saved successfully."
                )
            except Exception as e:
                self.log_panel.add_message("ERROR", f"Failed to save project settings: {e}")
                QMessageBox.critical(
                    self,
                    "Save Failed",
                    f"An error occurred while saving the project:\n{str(e)}"
                )
        else:
            self.log_panel.add_message("WARN", "No active project open. Save action only supports active projects.")
            QMessageBox.warning(
                self,
                "Save Failed",
                "You must create or open a project before saving."
            )

    def _handle_run_ga(self) -> None:
        """Start a GA search in a background worker thread."""
        # ── Double-click guard ──────────────────────────────────────────────
        if hasattr(self, "_ga_worker") and self._ga_worker is not None and self._ga_worker.isRunning():
            self.log_panel.add_message("WARN", "GA search is already running.")
            return

        # ── Determine dataset ───────────────────────────────────────────────
        df = self._loaded_dataset
        is_mock = df is None
        if is_mock:
            df = self.strategy_service.generate_deterministic_mock_ohlcv(count=200)
            source_label = "Mock fallback"
            self.log_panel.add_message("INFO", "Using deterministic mock data (no dataset loaded).")
        else:
            if self._active_dataset_quality and not self._active_dataset_quality.passed:
                self.log_panel.add_message("ERROR", "GA search aborted: Active dataset has failed quality checks.")
                QMessageBox.warning(
                    self,
                    "GA Search Aborted",
                    "Cannot run GA search. The active dataset has failed quality checks.",
                )
                self.ga_build_panel.status_label.setText(
                    "GA search aborted: active dataset failed quality checks."
                )
                self.ga_build_panel.status_label.setStyleSheet(
                    "color: #ef5350; font-weight: bold; font-size: 12px;"
                )
                self.ga_build_panel.set_idle()
                return
            source_label = (
                self._active_dataset_meta.name
                if self._active_dataset_meta
                else "Loaded data"
            )
            self.log_panel.add_message("INFO", f"Using active dataset: {source_label}")

        # ── UI feedback ─────────────────────────────────────────────────────
        self.log_panel.add_message("INFO", "GA search started (background thread).")
        self.ga_build_panel.set_running()

        active_profile = self.instrument_service.get_active_profile()

        mtf_config = self.ga_build_panel.get_mtf_config_dict()

        cfg = GASearchConfig(
            population_size=8,
            max_generations=3,
            base_seed=42,
            allowed_timeframes=tuple(mtf_config["allowed_timeframes"]),
            mtf_probability=mtf_config["mtf_probability"],
        )

        # ── Launch worker ───────────────────────────────────────────────────
        from app.workers import GAWorker

        self._ga_worker = GAWorker(
            df, cfg, source_label,
            instrument=active_profile,
            parent=self,
            commission=2.0,
        )
        self._ga_worker.success.connect(self._on_ga_success)
        self._ga_worker.failure.connect(self._on_ga_failure)
        self._ga_worker.finished.connect(self._on_ga_finished)
        self._ga_worker.start()

    # ── GA worker signal handlers ───────────────────────────────────────────

    def _on_ga_success(self, result, source_label: str) -> None:
        """Handle successful GA worker completion."""
        import html

        self.ga_build_panel.update_from_result(result, source_label=source_label)

        # Store GA best strategy for injection into the Results ranking
        import copy
        ga_strat = copy.deepcopy(result.best_strategy)
        # We store the raw name to DB, then prefix it for UI.
        raw_name = ga_strat.name
        
        # 1. Save to SQLite via persistence service
        try:
            pers_svc = self._get_strategy_persistence_service()
            if pers_svc:
                pers_svc.save_best_strategy(result.best_strategy, label="latest")
                self.log_panel.add_message("INFO", f"Saved GA best strategy '{raw_name}' to project DB.")
        except Exception as e:
            self.log_panel.add_message("WARN", f"Failed to save GA best strategy: {e}")

        # 2. Add UI prefix and update UI
        ga_strat.name = f"[GA Best] {raw_name}"
        self._latest_ga_strategy = ga_strat

        # Update Results page summary label
        if hasattr(self, "ga_results_summary_label"):
            ga_name = html.escape(ga_strat.name)
            source = html.escape(str(source_label))
            self.ga_results_summary_label.setText(
                f"<b>GA Best Strategy:</b> {ga_name}  |  "
                f"<b>Score:</b> {result.best_score:.4f}  |  "
                f"<b>Source:</b> {source}  |  "
                f"<b>Generations:</b> {result.generation_count}"
            )
            self.ga_results_summary_label.show()

        # Re-run the ranking so the new GA strategy is evaluated against the current instrument profile
        self._refresh_results_ranking()

        self.log_panel.add_message(
            "INFO",
            f"GA search completed — {result.generation_count} generations, "
            f"pop={result.final_population_size}, "
            f"best score={result.best_score:.4f}, "
            f"best strategy={result.best_strategy.name}.",
        )
        self.inspector_label.setText(
            "Build Inspector\n\n"
            f"Last GA run: {source_label}\n"
            f"Generations: {result.generation_count}\n"
            f"Best score: {result.best_score:.4f}\n"
            f"Best strategy: {result.best_strategy.name}"
        )

    def _on_ga_failure(self, error_message: str) -> None:
        """Handle GA worker failure."""
        self.log_panel.add_message("ERROR", f"GA search failed: {error_message}")
        self.ga_build_panel.status_label.setText(f"GA search failed: {error_message}")
        self.ga_build_panel.status_label.setStyleSheet(
            "color: #ef5350; font-weight: bold; font-size: 12px;"
        )

    def _on_ga_finished(self) -> None:
        """Always called when the GA worker thread exits."""
        self.ga_build_panel.set_idle()
        self._ga_worker = None

    def _handle_run_gp(self) -> None:
        """Start a GP search in a background worker thread."""
        # ── Double-click guard ──────────────────────────────────────────────
        if hasattr(self, "_gp_worker") and self._gp_worker is not None and self._gp_worker.isRunning():
            self.log_panel.add_message("WARN", "GP search is already running.")
            return

        # ── Determine dataset ───────────────────────────────────────────────
        df = self._loaded_dataset
        is_mock = df is None
        if is_mock:
            df = self.strategy_service.generate_deterministic_mock_ohlcv(count=200)
            source_label = "Mock fallback"
            self.log_panel.add_message("INFO", "Using deterministic mock data (no dataset loaded).")
        else:
            if self._active_dataset_quality and not self._active_dataset_quality.passed:
                self.log_panel.add_message("ERROR", "GP search aborted: Active dataset has failed quality checks.")
                QMessageBox.warning(
                    self,
                    "GP Search Aborted",
                    "Cannot run GP search. The active dataset has failed quality checks.",
                )
                self.ga_build_panel.status_label.setText(
                    "GP search aborted: active dataset failed quality checks."
                )
                self.ga_build_panel.status_label.setStyleSheet(
                    "color: #ef5350; font-weight: bold; font-size: 12px;"
                )
                self.ga_build_panel.set_idle()
                return
            source_label = (
                self._active_dataset_meta.name
                if self._active_dataset_meta
                else "Loaded data"
            )
            self.log_panel.add_message("INFO", f"Using active dataset: {source_label}")

        # ── UI feedback ─────────────────────────────────────────────────────
        self.log_panel.add_message("INFO", "GP search started (background thread).")
        self.ga_build_panel.set_running(is_gp=True)

        active_profile = self.instrument_service.get_active_profile()

        from app.services.gp_service import GPSearchConfig
        mtf_config = self.ga_build_panel.get_mtf_config_dict()
        cfg = GPSearchConfig(
            population_size=8,
            max_generations=3,
            base_seed=42,
            allowed_timeframes=tuple(mtf_config["allowed_timeframes"]),
            mtf_probability=mtf_config["mtf_probability"],
        )

        # ── Launch worker ───────────────────────────────────────────────────
        from app.workers import GPWorker

        self._gp_worker = GPWorker(
            df, cfg, source_label,
            instrument=active_profile,
            parent=self,
            commission=2.0,
        )
        self._gp_worker.success.connect(self._on_gp_success)
        self._gp_worker.failure.connect(self._on_gp_failure)
        self._gp_worker.finished.connect(self._on_gp_finished)
        self._gp_worker.start()

    # ── GP worker signal handlers ───────────────────────────────────────────

    def _on_gp_success(self, result, source_label: str) -> None:
        """Handle successful GP worker completion."""
        self.ga_build_panel.update_from_result(result, source_label=source_label)

        # Store GP latest strategy for future Results page integration
        import copy
        import html
        
        gp_strat = copy.deepcopy(result.best_strategy)
        raw_name = gp_strat.name
        
        # We intentionally do not persist GP yet.
        # But we do inject it into UI state.
        gp_strat.name = f"[GP Best] {raw_name}"
        self._latest_gp_strategy = gp_strat

        if hasattr(self, "gp_results_summary_label"):
            gp_name = html.escape(gp_strat.name)
            source = html.escape(str(source_label))
            self.gp_results_summary_label.setText(
                f"<b>GP Best Strategy:</b> {gp_name}  |  "
                f"<b>Score:</b> {result.best_score:.4f}  |  "
                f"<b>Source:</b> {source}  |  "
                f"<b>Generations:</b> {result.generation_count}"
            )
            self.gp_results_summary_label.show()

        # Re-run the ranking so the new GP strategy is evaluated against the current instrument profile
        self._refresh_results_ranking()

        self.log_panel.add_message(
            "INFO",
            f"GP search completed — {result.generation_count} generations, "
            f"pop={result.final_population_size}, "
            f"best score={result.best_score:.4f}, "
            f"best strategy={result.best_strategy.name}.",
        )
        self.inspector_label.setText(
            "Build Inspector\n\n"
            f"Last GP run: {source_label}\n"
            f"Generations: {result.generation_count}\n"
            f"Best score: {result.best_score:.4f}\n"
            f"Best strategy: {result.best_strategy.name}"
        )

    def _on_gp_failure(self, error_message: str) -> None:
        """Handle GP worker failure."""
        self.log_panel.add_message("ERROR", f"GP search failed: {error_message}")
        self.ga_build_panel.status_label.setText(f"GP search failed: {error_message}")
        self.ga_build_panel.status_label.setStyleSheet(
            "color: #ef5350; font-weight: bold; font-size: 12px;"
        )

    def _on_gp_finished(self) -> None:
        """Always called when the GP worker thread exits."""
        self.ga_build_panel.set_idle()
        self._gp_worker = None
