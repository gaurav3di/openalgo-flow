"""
Workflow Executor Service
Executes workflow nodes using the OpenAlgo Python SDK
"""
from datetime import datetime, time
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import asyncio
import re
import json

from app.core.database import async_session_maker
from app.core.openalgo import OpenAlgoClient
from app.core.scheduler import workflow_scheduler
from app.models.workflow import Workflow, WorkflowExecution
from app.models.settings import AppSettings

logger = logging.getLogger(__name__)


class WorkflowContext:
    """Context for storing variables during workflow execution"""

    def __init__(self):
        self.variables: Dict[str, Any] = {}

    def set_variable(self, name: str, value: Any):
        """Store a variable"""
        self.variables[name] = value

    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a variable value"""
        return self.variables.get(name, default)

    def _get_builtin_variable(self, name: str) -> Optional[str]:
        """Get built-in system variables"""
        now = datetime.now()
        builtins = {
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "year": now.strftime("%Y"),
            "month": now.strftime("%m"),
            "day": now.strftime("%d"),
            "hour": now.strftime("%H"),
            "minute": now.strftime("%M"),
            "second": now.strftime("%S"),
            "weekday": now.strftime("%A"),
            "iso_timestamp": now.isoformat(),
        }
        return builtins.get(name)

    def interpolate(self, text: str) -> str:
        """Replace {{variable}} patterns with actual values"""
        if not isinstance(text, str):
            return text

        def replacer(match):
            var_path = match.group(1).strip()

            # Check built-in variables first
            builtin_value = self._get_builtin_variable(var_path)
            if builtin_value is not None:
                return builtin_value

            # Then check user variables
            parts = var_path.split(".")
            value = self.variables

            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return match.group(0)  # Return original if not found

                if value is None:
                    return match.group(0)

            return str(value) if value is not None else match.group(0)

        return re.sub(r"\{\{([^}]+)\}\}", replacer, text)


async def get_openalgo_client() -> Optional[OpenAlgoClient]:
    """Get OpenAlgo client from settings"""
    async with async_session_maker() as db:
        result = await db.execute(select(AppSettings).limit(1))
        settings = result.scalar_one_or_none()

        if not settings or not settings.openalgo_api_key:
            return None

        return OpenAlgoClient(
            api_key=settings.openalgo_api_key, host=settings.openalgo_host
        )


def run_sync(coro):
    """Run async function synchronously (SDK methods are sync)"""
    return coro


class NodeExecutor:
    """Executes individual workflow nodes"""

    def __init__(self, client: OpenAlgoClient, context: WorkflowContext, logs: list):
        self.client = client
        self.context = context
        self.logs = logs

    def log(self, message: str, level: str = "info"):
        """Add log entry"""
        self.logs.append(
            {"time": datetime.utcnow().isoformat(), "message": message, "level": level}
        )
        if level == "error":
            logger.error(message)
        else:
            logger.info(message)

    def store_output(self, node_data: dict, result: Any):
        """Store result in output variable if configured"""
        output_var = node_data.get("outputVariable")
        if output_var and output_var.strip():
            self.context.set_variable(output_var.strip(), result)
            self.log(f"Stored result in variable: {output_var}")

    def execute_place_order(self, node_data: dict) -> dict:
        """Execute Place Order node"""
        self.log(
            f"Placing order: {node_data.get('symbol')} {node_data.get('action')} qty={node_data.get('quantity')}"
        )
        result = self.client.place_order(
            symbol=node_data.get("symbol", ""),
            exchange=node_data.get("exchange", "NSE"),
            action=node_data.get("action", "BUY"),
            quantity=int(node_data.get("quantity", 1)),
            price_type=node_data.get("priceType", "MARKET"),
            product=node_data.get("product", "MIS"),
            price=float(node_data.get("price", 0)),
            trigger_price=float(node_data.get("triggerPrice", 0)),
        )
        self.log(
            f"Order result: {result}",
            "info" if result.get("status") == "success" else "error",
        )
        self.store_output(node_data, result)
        return result

    def execute_smart_order(self, node_data: dict) -> dict:
        """Execute Smart Order node"""
        self.log(
            f"Placing smart order: {node_data.get('symbol')} {node_data.get('action')}"
        )
        result = self.client.place_smart_order(
            symbol=node_data.get("symbol", ""),
            exchange=node_data.get("exchange", "NSE"),
            action=node_data.get("action", "BUY"),
            quantity=int(node_data.get("quantity", 1)),
            position_size=int(node_data.get("positionSize", 0)),
            price_type=node_data.get("priceType", "MARKET"),
            product=node_data.get("product", "MIS"),
            price=float(node_data.get("price", 0)),
            trigger_price=float(node_data.get("triggerPrice", 0)),
        )
        self.log(
            f"Smart order result: {result}",
            "info" if result.get("status") == "success" else "error",
        )
        self.store_output(node_data, result)
        return result

    def execute_options_order(self, node_data: dict) -> dict:
        """Execute Options Order node"""
        self.log(
            f"Placing options order: {node_data.get('underlying')} {node_data.get('optionType')} {node_data.get('offset')}"
        )
        result = self.client.options_order(
            underlying=node_data.get("underlying", ""),
            exchange=node_data.get("exchange", "NSE_INDEX"),
            expiry_date=node_data.get("expiryDate", ""),
            offset=node_data.get("offset", "ATM"),
            option_type=node_data.get("optionType", "CE"),
            action=node_data.get("action", "BUY"),
            quantity=int(node_data.get("quantity", 1)),
            price_type=node_data.get("priceType", "MARKET"),
            product=node_data.get("product", "NRML"),
            splitsize=int(node_data.get("splitSize", 0)),
        )
        self.log(
            f"Options order result: {result}",
            "info" if result.get("status") == "success" else "error",
        )
        self.store_output(node_data, result)
        return result

    def execute_options_multi_order(self, node_data: dict) -> dict:
        """Execute Multi-Leg Options Order node"""
        self.log(
            f"Placing multi-leg options order: {node_data.get('underlying')} strategy={node_data.get('strategyType')}"
        )
        legs = node_data.get("legs", [])
        expiry_date = node_data.get("expiryDate")

        result = self.client.options_multi_order(
            underlying=node_data.get("underlying", ""),
            exchange=node_data.get("exchange", "NSE_INDEX"),
            legs=legs,
            expiry_date=expiry_date,
        )
        self.log(
            f"Multi-leg order result: {result}",
            "info" if result.get("status") == "success" else "error",
        )
        self.store_output(node_data, result)
        return result

    def execute_basket_order(self, node_data: dict) -> dict:
        """Execute Basket Order node"""
        orders = node_data.get("orders", [])
        self.log(f"Placing basket order with {len(orders)} orders")
        result = self.client.basket_order(orders=orders)
        self.log(
            f"Basket order result: {result}",
            "info" if result.get("status") == "success" else "error",
        )
        self.store_output(node_data, result)
        return result

    def execute_split_order(self, node_data: dict) -> dict:
        """Execute Split Order node"""
        self.log(
            f"Placing split order: {node_data.get('symbol')} qty={node_data.get('quantity')} split={node_data.get('splitSize')}"
        )
        result = self.client.split_order(
            symbol=node_data.get("symbol", ""),
            exchange=node_data.get("exchange", "NSE"),
            action=node_data.get("action", "BUY"),
            quantity=int(node_data.get("quantity", 1)),
            splitsize=int(node_data.get("splitSize", 10)),
            price_type=node_data.get("priceType", "MARKET"),
            product=node_data.get("product", "MIS"),
        )
        self.log(
            f"Split order result: {result}",
            "info" if result.get("status") == "success" else "error",
        )
        self.store_output(node_data, result)
        return result

    def execute_modify_order(self, node_data: dict) -> dict:
        """Execute Modify Order node"""
        order_id = self.context.interpolate(str(node_data.get("orderId", "")))
        self.log(f"Modifying order: {order_id}")
        result = self.client.modify_order(
            order_id=order_id,
            symbol=node_data.get("symbol", ""),
            exchange=node_data.get("exchange", "NSE"),
            action=node_data.get("action", "BUY"),
            quantity=int(node_data.get("quantity", 1)),
            price_type=node_data.get("priceType", "LIMIT"),
            product=node_data.get("product", "MIS"),
            price=float(node_data.get("price", 0)),
            trigger_price=float(node_data.get("triggerPrice", 0)),
        )
        self.log(
            f"Modify order result: {result}",
            "info" if result.get("status") == "success" else "error",
        )
        return result

    def execute_cancel_order(self, node_data: dict) -> dict:
        """Execute Cancel Order node"""
        order_id = self.context.interpolate(str(node_data.get("orderId", "")))
        self.log(f"Cancelling order: {order_id}")
        result = self.client.cancel_order(order_id=order_id)
        self.log(
            f"Cancel order result: {result}",
            "info" if result.get("status") == "success" else "error",
        )
        return result

    def execute_cancel_all_orders(self, node_data: dict) -> dict:
        """Execute Cancel All Orders node"""
        self.log("Cancelling all orders")
        result = self.client.cancel_all_orders()
        self.log(
            f"Cancel all result: {result}",
            "info" if result.get("status") == "success" else "error",
        )
        return result

    def execute_close_positions(self, node_data: dict) -> dict:
        """Execute Close Positions node"""
        self.log("Closing all positions")
        result = self.client.close_position()
        self.log(
            f"Close positions result: {result}",
            "info" if result.get("status") == "success" else "error",
        )
        return result

    def execute_get_quote(self, node_data: dict) -> dict:
        """Execute Get Quote node"""
        symbol = node_data.get("symbol", "")
        exchange = node_data.get("exchange", "NSE")
        self.log(f"Getting quote for: {symbol} ({exchange})")
        result = self.client.get_quotes(symbol=symbol, exchange=exchange)
        self.log(f"Quote result: {result}")
        self.store_output(node_data, result)
        return result

    def execute_multi_quotes(self, node_data: dict) -> dict:
        """Execute Multi Quotes node"""
        symbols = node_data.get("symbols", [])
        self.log(f"Getting quotes for {len(symbols)} symbols")
        result = self.client.get_multi_quotes(symbols=symbols)
        self.log(f"Multi quotes result: {result}")
        self.store_output(node_data, result)
        return result

    def execute_get_depth(self, node_data: dict) -> dict:
        """Execute Get Depth node"""
        symbol = node_data.get("symbol", "")
        exchange = node_data.get("exchange", "NSE")
        self.log(f"Getting depth for: {symbol} ({exchange})")
        result = self.client.get_depth(symbol=symbol, exchange=exchange)
        self.log(f"Depth result received")
        self.store_output(node_data, result)
        return result

    def execute_get_order_status(self, node_data: dict) -> dict:
        """Execute Get Order Status node"""
        order_id = self.context.interpolate(str(node_data.get("orderId", "")))
        self.log(f"Getting order status for: {order_id}")
        result = self.client.get_order_status(order_id=order_id)
        self.log(f"Order status result: {result}")
        self.store_output(node_data, result)
        return result

    def execute_open_position(self, node_data: dict) -> dict:
        """Execute Open Position node"""
        symbol = node_data.get("symbol", "")
        exchange = node_data.get("exchange", "NSE")
        product = node_data.get("product", "MIS")
        self.log(f"Getting open position for: {symbol}")
        result = self.client.get_open_position(
            symbol=symbol, exchange=exchange, product=product
        )
        self.log(f"Open position result: {result}")
        self.store_output(node_data, result)
        return result

    def execute_history(self, node_data: dict) -> dict:
        """Execute History node"""
        symbol = node_data.get("symbol", "")
        exchange = node_data.get("exchange", "NSE")
        interval = node_data.get("interval", "5m")
        start_date = node_data.get("startDate", "")
        end_date = node_data.get("endDate", "")
        self.log(f"Getting history for: {symbol} ({interval})")
        result = self.client.get_history(
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            start_date=start_date,
            end_date=end_date,
        )
        self.log(f"History data received")
        self.store_output(node_data, {"status": "success", "data": str(result)})
        return {"status": "success", "data": result}

    def execute_expiry(self, node_data: dict) -> dict:
        """Execute Expiry node"""
        symbol = node_data.get("symbol", "NIFTY")
        exchange = node_data.get("exchange", "NFO")
        instrument_type = node_data.get("instrumentType", "options")
        self.log(f"Getting expiry dates for: {symbol}")
        result = self.client.get_expiry(
            symbol=symbol, exchange=exchange, instrumenttype=instrument_type
        )
        self.log(f"Expiry result: {result}")
        self.store_output(node_data, result)
        return result

    def execute_telegram_alert(self, node_data: dict) -> dict:
        """Execute Telegram Alert node"""
        username = node_data.get("username", "")
        message = self.context.interpolate(node_data.get("message", ""))
        self.log(f"Sending Telegram alert to {username}: {message}")
        result = self.client.send_telegram(username=username, message=message)
        self.log(
            f"Telegram result: {result}",
            "info" if result.get("status") == "success" else "error",
        )
        return result

    def execute_delay(self, node_data: dict) -> dict:
        """Execute Delay node"""
        delay_ms = int(node_data.get("delay", 1000))
        self.log(f"Waiting for {delay_ms}ms")
        import time

        time.sleep(delay_ms / 1000)
        self.log(f"Delay complete")
        return {"status": "success", "message": f"Waited {delay_ms}ms"}

    def execute_log(self, node_data: dict) -> dict:
        """Execute Log node"""
        message = self.context.interpolate(node_data.get("message", ""))
        log_level = node_data.get("level", "info")
        self.log(f"[LOG] {message}", log_level)
        return {"status": "success", "message": message}

    def execute_variable(self, node_data: dict) -> dict:
        """Execute Variable node"""
        var_name = node_data.get("name", "")
        var_value = node_data.get("value", "")

        # Interpolate the value first
        var_value = self.context.interpolate(str(var_value))

        # Try to parse as JSON if it looks like JSON
        try:
            if var_value.startswith("{") or var_value.startswith("["):
                var_value = json.loads(var_value)
        except (json.JSONDecodeError, AttributeError):
            pass

        self.context.set_variable(var_name, var_value)
        self.log(f"Set variable {var_name} = {var_value}")
        return {"status": "success", "variable": var_name, "value": var_value}

    def execute_position_check(self, node_data: dict) -> dict:
        """Execute Position Check node - returns True/False for condition"""
        symbol = node_data.get("symbol", "")
        exchange = node_data.get("exchange", "NSE")
        product = node_data.get("product", "MIS")
        operator = node_data.get("operator", "gt")
        threshold = int(node_data.get("threshold", 0))

        self.log(f"Checking position for: {symbol}")
        result = self.client.get_open_position(
            symbol=symbol, exchange=exchange, product=product
        )

        quantity = int(result.get("quantity", 0))
        condition_met = self._evaluate_condition(quantity, operator, threshold)

        self.log(
            f"Position check: qty={quantity} {operator} {threshold} = {condition_met}"
        )
        return {"status": "success", "condition": condition_met, "quantity": quantity}

    def execute_fund_check(self, node_data: dict) -> dict:
        """Execute Fund Check node - returns True/False for condition"""
        operator = node_data.get("operator", "gt")
        threshold = float(node_data.get("threshold", 0))

        self.log("Checking funds")
        result = self.client.get_funds()

        available = float(result.get("data", {}).get("availablecash", 0))
        condition_met = self._evaluate_condition(available, operator, threshold)

        self.log(
            f"Fund check: available={available} {operator} {threshold} = {condition_met}"
        )
        return {
            "status": "success",
            "condition": condition_met,
            "available": available,
        }

    def execute_price_condition(self, node_data: dict) -> dict:
        """Execute Price Condition node - returns True/False for condition"""
        symbol = node_data.get("symbol", "")
        exchange = node_data.get("exchange", "NSE")
        operator = node_data.get("operator", "gt")
        threshold = float(node_data.get("threshold", 0))

        self.log(f"Checking price condition for: {symbol}")
        result = self.client.get_quotes(symbol=symbol, exchange=exchange)

        ltp = float(result.get("data", {}).get("ltp", 0))
        condition_met = self._evaluate_condition(ltp, operator, threshold)

        self.log(f"Price check: ltp={ltp} {operator} {threshold} = {condition_met}")
        return {"status": "success", "condition": condition_met, "ltp": ltp}

    def execute_time_window(self, node_data: dict) -> dict:
        """Execute Time Window node - returns True/False for condition"""
        start_time_str = node_data.get("startTime", "09:15")
        end_time_str = node_data.get("endTime", "15:30")

        now = datetime.now().time()
        start_parts = start_time_str.split(":")
        end_parts = end_time_str.split(":")

        start_time = time(int(start_parts[0]), int(start_parts[1]))
        end_time = time(int(end_parts[0]), int(end_parts[1]))

        condition_met = start_time <= now <= end_time

        self.log(
            f"Time window check: {start_time_str}-{end_time_str}, current={now.strftime('%H:%M')}, in_window={condition_met}"
        )
        return {
            "status": "success",
            "condition": condition_met,
            "current_time": now.strftime("%H:%M:%S"),
        }

    def _evaluate_condition(
        self, value: float, operator: str, threshold: float
    ) -> bool:
        """Evaluate a condition"""
        operators = {
            "gt": value > threshold,
            "gte": value >= threshold,
            "lt": value < threshold,
            "lte": value <= threshold,
            "eq": value == threshold,
            "neq": value != threshold,
        }
        return operators.get(operator, False)


async def execute_workflow(workflow_id: int) -> dict:
    """Execute a workflow"""
    async with async_session_maker() as db:
        result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
        workflow = result.scalar_one_or_none()

        if not workflow:
            return {"status": "error", "message": "Workflow not found"}

        execution = WorkflowExecution(
            workflow_id=workflow_id,
            status="running",
            started_at=datetime.utcnow(),
            logs=[],
        )
        db.add(execution)
        await db.commit()
        await db.refresh(execution)

        logs = []
        context = WorkflowContext()

        try:
            client = await get_openalgo_client()
            if not client:
                raise Exception("OpenAlgo not configured")

            executor = NodeExecutor(client, context, logs)
            executor.log(f"Starting workflow: {workflow.name}")

            nodes = workflow.nodes or []
            edges = workflow.edges or []

            start_node = next((n for n in nodes if n.get("type") == "start"), None)
            if not start_node:
                raise Exception("No start node found")

            # Build edge map for traversal
            edge_map: Dict[str, List[dict]] = {}
            for edge in edges:
                source = edge["source"]
                if source not in edge_map:
                    edge_map[source] = []
                edge_map[source].append(edge)

            # Execute nodes starting from start node
            await execute_node_chain(
                start_node["id"], nodes, edge_map, executor, context
            )

            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            execution.logs = logs
            await db.commit()

            return {
                "status": "success",
                "message": "Workflow executed successfully",
                "execution_id": execution.id,
            }

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            logs.append(
                {
                    "time": datetime.utcnow().isoformat(),
                    "message": f"Error: {str(e)}",
                    "level": "error",
                }
            )

            execution.status = "failed"
            execution.completed_at = datetime.utcnow()
            execution.error = str(e)
            execution.logs = logs
            await db.commit()

            return {"status": "error", "message": str(e), "execution_id": execution.id}


async def execute_node_chain(
    node_id: str,
    nodes: list,
    edge_map: Dict[str, List[dict]],
    executor: NodeExecutor,
    context: WorkflowContext,
):
    """Execute a chain of nodes starting from the given node"""
    node = next((n for n in nodes if n["id"] == node_id), None)
    if not node:
        return

    node_type = node.get("type")
    node_data = node.get("data", {})
    result = None

    # Execute the node based on its type
    if node_type == "start":
        executor.log("Workflow started")
    elif node_type == "placeOrder":
        result = executor.execute_place_order(node_data)
    elif node_type == "smartOrder":
        result = executor.execute_smart_order(node_data)
    elif node_type == "optionsOrder":
        result = executor.execute_options_order(node_data)
    elif node_type == "optionsMultiOrder":
        result = executor.execute_options_multi_order(node_data)
    elif node_type == "basketOrder":
        result = executor.execute_basket_order(node_data)
    elif node_type == "splitOrder":
        result = executor.execute_split_order(node_data)
    elif node_type == "modifyOrder":
        result = executor.execute_modify_order(node_data)
    elif node_type == "cancelOrder":
        result = executor.execute_cancel_order(node_data)
    elif node_type == "cancelAllOrders":
        result = executor.execute_cancel_all_orders(node_data)
    elif node_type == "closePositions":
        result = executor.execute_close_positions(node_data)
    elif node_type == "getQuote":
        result = executor.execute_get_quote(node_data)
    elif node_type == "multiQuotes":
        result = executor.execute_multi_quotes(node_data)
    elif node_type == "getDepth":
        result = executor.execute_get_depth(node_data)
    elif node_type == "getOrderStatus":
        result = executor.execute_get_order_status(node_data)
    elif node_type == "openPosition":
        result = executor.execute_open_position(node_data)
    elif node_type == "history":
        result = executor.execute_history(node_data)
    elif node_type == "expiry":
        result = executor.execute_expiry(node_data)
    elif node_type == "telegramAlert":
        result = executor.execute_telegram_alert(node_data)
    elif node_type == "delay":
        result = executor.execute_delay(node_data)
    elif node_type == "log":
        result = executor.execute_log(node_data)
    elif node_type == "variable":
        result = executor.execute_variable(node_data)
    elif node_type == "positionCheck":
        result = executor.execute_position_check(node_data)
    elif node_type == "fundCheck":
        result = executor.execute_fund_check(node_data)
    elif node_type == "priceCondition":
        result = executor.execute_price_condition(node_data)
    elif node_type == "timeWindow":
        result = executor.execute_time_window(node_data)
    elif node_type == "priceAlert":
        # Price alert is a trigger, just pass through
        executor.log("Price alert triggered")
    elif node_type == "group":
        # Group is just a container, pass through
        pass
    else:
        executor.log(f"Unknown node type: {node_type}", "warning")

    # Determine which edges to follow
    edges_to_follow = edge_map.get(node_id, [])

    # For condition nodes, check which path to take (Yes/No)
    if result and "condition" in result:
        condition_met = result.get("condition", False)
        filtered_edges = []
        for edge in edges_to_follow:
            source_handle = edge.get("sourceHandle", "")
            if condition_met and source_handle == "yes":
                filtered_edges.append(edge)
            elif not condition_met and source_handle == "no":
                filtered_edges.append(edge)
            elif source_handle not in ["yes", "no"]:
                # Default edges always follow
                filtered_edges.append(edge)
        edges_to_follow = filtered_edges

    # Execute connected nodes
    for edge in edges_to_follow:
        target_id = edge.get("target")
        if target_id:
            await execute_node_chain(target_id, nodes, edge_map, executor, context)


def execute_workflow_sync(workflow_id: int):
    """Synchronous wrapper for execute_workflow (for APScheduler)"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(execute_workflow(workflow_id))
        logger.info(f"Scheduled execution result: {result}")
    finally:
        loop.close()


async def activate_workflow(workflow_id: int, db: AsyncSession) -> dict:
    """Activate a workflow and schedule it"""
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()

    if not workflow:
        return {"status": "error", "message": "Workflow not found"}

    nodes = workflow.nodes or []
    start_node = next((n for n in nodes if n.get("type") == "start"), None)

    if not start_node:
        return {"status": "error", "message": "No start node found"}

    start_data = start_node.get("data", {})
    schedule_type = start_data.get("scheduleType", "daily")
    time_str = start_data.get("time", "09:15")
    days = start_data.get("days", [])
    execute_at = start_data.get("executeAt")

    try:
        job_id = workflow_scheduler.add_workflow_job(
            workflow_id=workflow_id,
            schedule_type=schedule_type,
            time_str=time_str,
            days=days,
            execute_at=execute_at,
            func=execute_workflow_sync,
        )

        workflow.is_active = True
        workflow.schedule_job_id = job_id
        await db.commit()

        next_run = workflow_scheduler.get_next_run_time(job_id)
        return {
            "status": "success",
            "message": "Workflow activated",
            "job_id": job_id,
            "next_run": next_run.isoformat() if next_run else None,
        }

    except Exception as e:
        logger.error(f"Failed to activate workflow: {e}")
        return {"status": "error", "message": str(e)}


async def deactivate_workflow(workflow_id: int, db: AsyncSession) -> dict:
    """Deactivate a workflow and remove from scheduler"""
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = result.scalar_one_or_none()

    if not workflow:
        return {"status": "error", "message": "Workflow not found"}

    if workflow.schedule_job_id:
        workflow_scheduler.remove_job(workflow.schedule_job_id)

    workflow.is_active = False
    workflow.schedule_job_id = None
    await db.commit()

    return {"status": "success", "message": "Workflow deactivated"}
