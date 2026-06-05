"""Service layer for report export operations — Task 007."""

from __future__ import annotations

import logging
import os
from core.models.strategy import Strategy
from core.models.backtest_result import BacktestResult
from reports import generate_markdown_report, generate_html_report

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.services.multi_instrument_service import MultiInstrumentBacktestResult

# Set up logging
logger = logging.getLogger(__name__)


class ReportService:
    """Orchestrates strategy report exports to Markdown or HTML files.
    
    Acts as a clean service boundary, keeping UI widgets decoupled from report formatting and file writing.
    """

    def __init__(self) -> None:
        pass

    def export_report(
        self,
        strategy: Strategy,
        result: BacktestResult,
        file_path: str,
        provenance: dict | None = None,
        is_mock: bool = False,
        validation_result: dict | None = None,
        multi_instrument_result: "MultiInstrumentBacktestResult" | None = None,
    ) -> None:
        """Export the backtest result of a strategy to a file.
        
        Detects destination format based on the file_path extension:
        - .html / .htm -> HTML format.
        - Other (e.g. .md, .markdown) -> Markdown format.
        
        Args:
            strategy: Strategy model definition.
            result: BacktestResult output.
            file_path: Absolute destination file path.
            provenance: Dict of strategy generation metadata (seed, parameters).
            is_mock: Boolean indicating if this is internal sample/mock data.
        """
        _, ext = os.path.splitext(file_path.lower())
        
        try:
            if ext in (".html", ".htm"):
                content = generate_html_report(strategy, result, provenance,
                                               is_mock=is_mock,
                                               validation_result=validation_result,
                                               multi_instrument_result=multi_instrument_result)
                os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
            elif ext == ".pdf":
                content = generate_html_report(strategy, result, provenance,
                                               is_mock=is_mock,
                                               validation_result=validation_result,
                                               multi_instrument_result=multi_instrument_result)
                os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
                
                from PySide6.QtGui import QTextDocument, QPdfWriter, QPageSize
                doc = QTextDocument()
                doc.setHtml(content)
                writer = QPdfWriter(file_path)
                writer.setPageSize(QPageSize(QPageSize.A4))
                doc.print_(writer)
            else:
                content = generate_markdown_report(strategy, result, provenance,
                                                   is_mock=is_mock,
                                                   validation_result=validation_result,
                                                   multi_instrument_result=multi_instrument_result)
                os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                
            logger.info(f"Report successfully exported to: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to export report to {file_path}: {e}")
            raise IOError(f"Failed to export report: {e}") from e

    def export_strategy_json(
        self,
        strategy: Strategy,
        file_path: str,
        provenance: dict | None = None,
    ) -> None:
        """Export the Strategy object to a JSON file.

        Only the strategy definition and optional provenance are exported.
        Backtest metrics, trades, curves, and validation results are intentionally
        excluded so this remains a strategy-definition export.
        """
        import json
        from dataclasses import asdict
        
        data = asdict(strategy)
        
        # Ranking entries carry provenance separately from Strategy.
        if provenance:
            data["provenance"] = dict(provenance)
        elif hasattr(strategy, "provenance") and strategy.provenance:
            try:
                data["provenance"] = asdict(strategy.provenance) if hasattr(strategy.provenance, "__dataclass_fields__") else dict(strategy.provenance)
            except Exception:
                pass
                
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        logger.info(f"Strategy JSON successfully exported to: {file_path}")

    def preview_strategy_json(self, file_path: str) -> dict:
        """Read a Strategy JSON file and validate it can reconstruct a Strategy object.
        
        Returns:
            dict: {
                "passed": bool,
                "strategy": Strategy | None,
                "errors": list[str],
                "provenance": dict | None,
            }
        """
        import json
        from core.models.strategy import Strategy, StrategyBlock, Condition

        result = {
            "passed": False,
            "strategy": None,
            "errors": [],
            "provenance": None,
        }

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            result["errors"].append(f"Malformed JSON: {e}")
            return result
        except Exception as e:
            result["errors"].append(f"Failed to read file: {e}")
            return result

        if not isinstance(data, dict):
            result["errors"].append("JSON root must be an object.")
            return result

        if "name" not in data:
            result["errors"].append("Missing required field: 'name'.")
        elif not isinstance(data["name"], str) or not data["name"].strip():
            result["errors"].append("Field 'name' must be a non-empty string.")
            
        provenance = data.get("provenance")
        if provenance is not None and not isinstance(provenance, dict):
            result["errors"].append("Field 'provenance' must be an object if provided.")
        else:
            result["provenance"] = provenance

        def _parse_block(block_name: str, block_data: dict | None) -> StrategyBlock | None:
            if block_data is None:
                result["errors"].append(f"Missing required block: '{block_name}'.")
                return None
            
            if not isinstance(block_data, dict):
                result["errors"].append(f"Block '{block_name}' must be an object.")
                return None
                
            logic = block_data.get("logic", "AND")
            if logic not in ("AND", "OR"):
                result["errors"].append(f"Block '{block_name}' logic must be 'AND' or 'OR'.")
            conditions_data = block_data.get("conditions", [])
            
            if not isinstance(conditions_data, list):
                result["errors"].append(f"Block '{block_name}' conditions must be a list.")
                return None
                
            parsed_conditions = []
            for i, c_data in enumerate(conditions_data):
                if not isinstance(c_data, dict):
                    result["errors"].append(f"Block '{block_name}' condition {i} must be an object.")
                    continue
                    
                missing = []
                for req in ["indicator", "params", "operator"]:
                    if req not in c_data:
                        missing.append(req)
                
                if missing:
                    result["errors"].append(f"Block '{block_name}' condition {i} missing fields: {', '.join(missing)}.")
                    continue

                if not isinstance(c_data["indicator"], str) or not c_data["indicator"].strip():
                    result["errors"].append(f"Block '{block_name}' condition {i} field 'indicator' must be a non-empty string.")
                    continue
                if not isinstance(c_data["params"], dict):
                    result["errors"].append(f"Block '{block_name}' condition {i} field 'params' must be an object.")
                    continue
                if not isinstance(c_data["operator"], str) or c_data["operator"] not in (">", "<"):
                    result["errors"].append(f"Block '{block_name}' condition {i} field 'operator' must be '>' or '<'.")
                    continue
                    
                c = Condition(
                    indicator=c_data["indicator"],
                    params=c_data["params"],
                    operator=c_data["operator"],
                    left=c_data.get("left", "close"),
                    right=c_data.get("right", 0.0)
                )
                parsed_conditions.append(c)
                
            return StrategyBlock(conditions=parsed_conditions, logic=logic)

        le = _parse_block("long_entry", data.get("long_entry"))
        lx = _parse_block("long_exit", data.get("long_exit"))
        se = _parse_block("short_entry", data.get("short_entry"))
        sx = _parse_block("short_exit", data.get("short_exit"))

        from core.models.strategy import RiskManagement
        from core.serialization.strategy_serializer import risk_management_from_dict, SerializationError
        
        rm = RiskManagement()
        if "risk_management" in data:
            try:
                rm = risk_management_from_dict(data.get("risk_management"), strict=True)
            except SerializationError as e:
                result["errors"].append(str(e))

        if not result["errors"]:
            strategy = Strategy(
                name=data["name"],
                long_entry=le or StrategyBlock(),
                long_exit=lx or StrategyBlock(),
                short_entry=se or StrategyBlock(),
                short_exit=sx or StrategyBlock(),
                risk_management=rm
            )
            if result["provenance"]:
                strategy.provenance = result["provenance"]
                
            result["strategy"] = strategy
            result["passed"] = True
            
        return result

    def export_strategy_code(self, strategy: Strategy, file_path: str) -> None:
        """Export the strategy object to a research/reference script (.py or .cs)."""
        _, ext = os.path.splitext(file_path.lower())
        
        if ext == ".cs":
            from reports.ninjatrader_exporter import export_strategy_to_ninjatrader
            content = export_strategy_to_ninjatrader(strategy)
        else:
            from reports.python_exporter import export_strategy_to_python
            content = export_strategy_to_python(strategy)
        
        # Write to file
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        logger.info(f"Strategy code successfully exported to: {file_path}")

    def export_mock_report(self, file_path: str,
                            validation_result: dict | None = None) -> None:
        """Construct the deterministic mock backtest payload and export it as a labeled sample report."""
        from app.services.strategy_service import StrategyService
        from backtest_engine.runner import run_backtest

        strategy_service = StrategyService()
        ranked_data, _ = strategy_service.get_ranked_strategies()

        if not ranked_data:
            raise ValueError("No mock strategies generated.")

        top_strategy_data = ranked_data[0]
        strategy = top_strategy_data["strategy"]
        provenance = top_strategy_data["provenance"]

        # Generate deterministic mock OHLCV dataset
        mock_dataset = strategy_service.generate_deterministic_mock_ohlcv()

        # Run the backtest to get a full BacktestResult (with trades, curves, assumptions, warnings)
        backtest_res = run_backtest(
            strategy=strategy,
            df=mock_dataset,
            initial_capital=100_000.0,
            commission=2.0,
            slippage_ticks=1.0,
            tick_size=0.1
        )

        # Export the report, forcing is_mock=True
        self.export_report(
            strategy=strategy,
            result=backtest_res,
            file_path=file_path,
            provenance=provenance,
            is_mock=True,
            validation_result=validation_result,
        )
