"""
Tool Definitions and Implementations for BVRIT Chatbot
=======================================================
Provides fee_calculator, date_checker, and percentage_calculator tools
with JSON schemas for LLM function calling, plus input validation.
"""

import json
from datetime import datetime, date
from typing import Any


# ============================================================
# Exercise 1: Tool Definitions (JSON Schemas)
# ============================================================

FEE_CALCULATOR_TOOL = {
    "type": "function",
    "function": {
        "name": "fee_calculator",
        "description": (
            "Compute total BVRIT college fees across multiple years, "
            "apply scholarship discounts on tuition, or combine hostel + tuition costs. "
            "Use this ONLY when the user asks for fee totals, multi-year calculations, "
            "scholarship discounts on fees, or combined cost breakdowns. "
            "Do NOT use for simple lookup of a single year's fee — use RAG for that. "
            "Annual tuition for B.Tech at BVRIT is approximately 120000 per year. "
            "Hostel fee is approximately 60000 per year."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["total_tuition", "total_hostel", "combined_cost", "apply_scholarship"],
                    "description": (
                        "The type of fee calculation to perform. CRITICAL: You MUST set this to one of the valid values. "
                        "• 'total_tuition' = annual_fee * years (requires annual_fee and years) "
                        "• 'total_hostel' = annual_hostel * years (requires annual_hostel and years) "
                        "• 'combined_cost' = (annual_fee + annual_hostel) * years (requires annual_fee, annual_hostel, years) "
                        "• 'apply_scholarship' = annual_fee * (1 - scholarship_percentage/100) (requires annual_fee and scholarship_percentage)"
                    ),
                },
                "annual_fee": {
                    "type": "number",
                    "description": "Annual tuition fee amount in rupees (e.g., 120000 for B.Tech). Must be positive.",
                    "minimum": 1000,
                    "maximum": 500000,
                },
                "annual_hostel": {
                    "type": "number",
                    "description": "Annual hostel fee amount in rupees (e.g., 60000). Must be positive.",
                    "minimum": 1000,
                    "maximum": 500000,
                },
                "years": {
                    "type": "integer",
                    "description": "Number of academic years. Must be between 1 and 6.",
                    "minimum": 1,
                    "maximum": 6,
                },
                "scholarship_percentage": {
                    "type": "number",
                    "description": "Scholarship discount percentage (0 to 100). Must be between 0 and 100.",
                    "minimum": 0,
                    "maximum": 100,
                },
            },
            "required": ["operation", "annual_fee"],
        },
    },
}


DATE_CHECKER_TOOL = {
    "type": "function",
    "function": {
        "name": "date_checker",
        "description": (
            "Compare a deadline or event date against today's date and return "
            "whether it is past, upcoming, or how many days remain. "
            "Use this ONLY when the user asks if a deadline has passed, "
            "how many days until an event, or whether a date is upcoming. "
            "Do NOT use for simply retrieving a date from the document — use RAG for that. "
            "This tool expects a single date string to compare against the current date."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "date_string": {
                    "type": "string",
                    "description": (
                        "The date to check, in format DD-MM-YYYY (e.g., '15-06-2026'). "
                        "Extract this from the user's query or retrieved document context."
                    ),
                    "pattern": "^\\d{2}-\\d{2}-\\d{4}$",
                },
                "event_name": {
                    "type": "string",
                    "description": "A short name for the event or deadline being checked (e.g., 'EAMCET Counselling Deadline').",
                },
            },
            "required": ["date_string", "event_name"],
        },
    },
}


PERCENTAGE_CALCULATOR_TOOL = {
    "type": "function",
    "function": {
        "name": "percentage_calculator",
        "description": (
            "Compute percentage values such as scholarship percentages, "
            "placement rates, admission cutoff conversions, or any percentage "
            "calculation related to BVRIT college data. "
            "Use this when the user asks for percentage-based calculations like "
            "'what is X% of Y' or 'convert this ratio to percentage'. "
            "Do NOT use for simple fee calculations — use fee_calculator for that."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["percentage_of", "percentage_change", "ratio_to_percent"],
                    "description": (
                        "Type of percentage calculation: "
                        "'percentage_of' = (value / total) * 100, "
                        "'percentage_change' = ((new - old) / old) * 100, "
                        "'ratio_to_percent' = ratio * 100"
                    ),
                },
                "value": {
                    "type": "number",
                    "description": "The numerator or current value. Must be non-negative.",
                    "minimum": 0,
                },
                "total": {
                    "type": "number",
                    "description": "The denominator or original value. Must be positive.",
                    "minimum": 0.01,
                },
                "ratio": {
                    "type": "number",
                    "description": "A decimal ratio (e.g., 0.85 for 85%). Must be between 0 and 1.",
                    "minimum": 0,
                    "maximum": 1,
                },
            },
            "required": ["operation"],
        },
    },
}


# All tool definitions in a list for the API call
TOOL_DEFINITIONS = [FEE_CALCULATOR_TOOL, DATE_CHECKER_TOOL, PERCENTAGE_CALCULATOR_TOOL]


# ============================================================
# Exercise 2 & 3: Tool Implementations with Validation
# ============================================================

def fee_calculator(**kwargs) -> dict:
    """
    Execute fee calculations with input validation.
    
    Args:
        operation: str - type of calculation
        annual_fee: float - annual tuition fee
        annual_hostel: float - annual hostel fee
        years: int - number of years
        scholarship_percentage: float - discount percentage
    
    Returns:
        dict with result, breakdown, and any warnings
    """
    operation = kwargs.get("operation")
    warnings = []
    
    # --- Input Validation (Exercise 3) ---
    
    # Validate annual_fee
    annual_fee = kwargs.get("annual_fee")
    if annual_fee is not None:
        if annual_fee <= 0:
            return {
                "error": f"Invalid annual fee: {annual_fee}. Fee must be a positive number.",
                "result": None,
            }
        if annual_fee > 500000:
            warnings.append(f"Warning: Annual fee of ₹{annual_fee:,.0f} seems unusually high.")
    else:
        annual_fee = 0
    
    # Validate annual_hostel
    annual_hostel = kwargs.get("annual_hostel")
    if annual_hostel is not None:
        if annual_hostel <= 0:
            return {
                "error": f"Invalid annual hostel fee: {annual_hostel}. Hostel fee must be positive.",
                "result": None,
            }
    else:
        annual_hostel = 0
    
    # Validate years (Exercise 3 - E1: zero years)
    years = kwargs.get("years")
    if years is not None:
        if years <= 0:
            return {
                "error": f"Invalid number of years: {years}. Years must be between 1 and 6.",
                "result": None,
                "suggestion": "Did you mean 1 year? Please specify a positive number of years.",
            }
        if years > 6:
            warnings.append(f"Warning: {years} years is unusually long for a B.Tech program (standard is 4).")
    else:
        years = 1
    
    # Validate scholarship_percentage (Exercise 3 - E3: impossible percentage)
    scholarship_pct = kwargs.get("scholarship_percentage")
    if scholarship_pct is not None:
        if scholarship_pct < 0:
            return {
                "error": f"Invalid scholarship percentage: {scholarship_pct}%. Percentage cannot be negative.",
                "result": None,
            }
        if scholarship_pct > 100:
            return {
                "error": f"Invalid scholarship percentage: {scholarship_pct}%. Scholarship cannot exceed 100%. "
                         f"A 100% scholarship means the fee is fully waived.",
                "result": None,
            }
        if scholarship_pct > 50:
            warnings.append(f"Note: A {scholarship_pct}% scholarship is quite high. Please verify this is correct.")
    
    # --- Calculations ---
    if operation == "total_tuition":
        total = annual_fee * years
        return {
            "result": total,
            "breakdown": {
                "operation": "Total Tuition Fee",
                "annual_fee": annual_fee,
                "years": years,
                "total": total,
            },
            "formatted": f"Total tuition for {years} year(s): ₹{total:,.0f} (₹{annual_fee:,.0f}/year × {years} years)",
            "warnings": warnings,
        }
    
    elif operation == "total_hostel":
        total = annual_hostel * years
        return {
            "result": total,
            "breakdown": {
                "operation": "Total Hostel Fee",
                "annual_hostel": annual_hostel,
                "years": years,
                "total": total,
            },
            "formatted": f"Total hostel fee for {years} year(s): ₹{total:,.0f} (₹{annual_hostel:,.0f}/year × {years} years)",
            "warnings": warnings,
        }
    
    elif operation == "combined_cost":
        total = (annual_fee + annual_hostel) * years
        return {
            "result": total,
            "breakdown": {
                "operation": "Combined Cost (Tuition + Hostel)",
                "annual_fee": annual_fee,
                "annual_hostel": annual_hostel,
                "years": years,
                "total": total,
            },
            "formatted": (
                f"Total combined cost for {years} year(s): ₹{total:,.0f}\n"
                f"  • Tuition: ₹{annual_fee:,.0f}/year\n"
                f"  • Hostel: ₹{annual_hostel:,.0f}/year\n"
                f"  • Years: {years}"
            ),
            "warnings": warnings,
        }
    
    elif operation == "apply_scholarship":
        discount = annual_fee * (scholarship_pct / 100)
        discounted_fee = annual_fee - discount
        return {
            "result": discounted_fee,
            "breakdown": {
                "operation": "Fee After Scholarship Discount",
                "original_fee": annual_fee,
                "scholarship_percentage": scholarship_pct,
                "discount_amount": discount,
                "final_fee": discounted_fee,
            },
            "formatted": (
                f"Annual fee after {scholarship_pct}% scholarship: ₹{discounted_fee:,.0f}\n"
                f"  • Original fee: ₹{annual_fee:,.0f}\n"
                f"  • Discount ({scholarship_pct}%): ₹{discount:,.0f}"
            ),
            "warnings": warnings,
        }
    
    else:
        return {"error": f"Unknown operation: {operation}", "result": None}


def date_checker(**kwargs) -> dict:
    """
    Compare a date against today's date.
    
    Args:
        date_string: str in DD-MM-YYYY format
        event_name: str - name of the event
    
    Returns:
        dict with status, days_remaining, etc.
    """
    date_string = kwargs.get("date_string")
    event_name = kwargs.get("event_name", "Event")
    
    # Validate date_string presence
    if not date_string:
        return {
            "error": "No date provided. Please specify a date in DD-MM-YYYY format.",
            "result": None,
            "formatted": "No date provided. Please specify a date in DD-MM-YYYY format (e.g., 15-06-2026).",
        }
    
    # Parse and validate date format
    try:
        target_date = datetime.strptime(date_string, "%d-%m-%Y").date()
    except ValueError:
        return {
            "error": f"Invalid date format: '{date_string}'. Expected format: DD-MM-YYYY (e.g., 15-06-2026).",
            "result": None,
            "formatted": f"Invalid date format: '{date_string}'. Please use DD-MM-YYYY format (e.g., 15-06-2026).",
        }
    
    today = date.today()
    
    # Compute difference
    delta = target_date - today
    days_remaining = delta.days
    
    if days_remaining < 0:
        status = "past"
        abs_days = abs(days_remaining)
        if abs_days == 0:
            message = f"'{event_name}' was today."
        elif abs_days == 1:
            message = f"'{event_name}' was yesterday."
        else:
            message = f"'{event_name}' was {abs_days} days ago (on {date_string})."
    elif days_remaining == 0:
        status = "today"
        message = f"'{event_name}' is TODAY ({date_string})!"
    else:
        status = "upcoming"
        if days_remaining == 1:
            message = f"'{event_name}' is tomorrow! ({days_remaining} day remaining)"
        else:
            message = f"'{event_name}' is in {days_remaining} days (on {date_string})."
    
    return {
        "result": {
            "status": status,
            "days_remaining": days_remaining,
            "target_date": date_string,
            "today": today.strftime("%d-%m-%Y"),
        },
        "formatted": message,
        "is_past": status == "past",
        "days_remaining": days_remaining,
    }


def percentage_calculator(**kwargs) -> dict:
    """
    Compute percentage-based calculations with validation.
    
    Args:
        operation: str - percentage_of, percentage_change, or ratio_to_percent
        value: float - numerator/current value
        total: float - denominator/original value
        ratio: float - decimal ratio between 0 and 1
    
    Returns:
        dict with result and formatted string
    """
    operation = kwargs.get("operation")
    warnings = []
    
    if operation == "percentage_of":
        value = kwargs.get("value")
        total = kwargs.get("total")
        
        if value is None or total is None:
            return {"error": "Both 'value' and 'total' are required for percentage_of.", "result": None}
        if total <= 0:
            return {"error": "Total must be positive for percentage calculation.", "result": None}
        if value < 0:
            return {"error": "Value cannot be negative.", "result": None}
        
        pct = (value / total) * 100
        return {
            "result": round(pct, 2),
            "formatted": f"{value} is {pct:.2f}% of {total}",
            "warnings": warnings,
        }
    
    elif operation == "percentage_change":
        old_val = kwargs.get("total")  # reuse 'total' as old value
        new_val = kwargs.get("value")  # reuse 'value' as new value
        
        if old_val is None or new_val is None:
            return {"error": "Both 'value' (new) and 'total' (old) are required for percentage_change.", "result": None}
        if old_val <= 0:
            return {"error": "Old value must be positive.", "result": None}
        
        change = ((new_val - old_val) / old_val) * 100
        direction = "increase" if change >= 0 else "decrease"
        return {
            "result": round(change, 2),
            "formatted": f"{direction} of {abs(change):.2f}% (from {old_val} to {new_val})",
            "warnings": warnings,
        }
    
    elif operation == "ratio_to_percent":
        ratio = kwargs.get("ratio")
        if ratio is None:
            return {"error": "A 'ratio' value is required for ratio_to_percent.", "result": None}
        if ratio < 0 or ratio > 1:
            return {"error": f"Ratio must be between 0 and 1. Got {ratio}.", "result": None}
        
        pct = ratio * 100
        return {
            "result": round(pct, 2),
            "formatted": f"{ratio} = {pct:.2f}%",
            "warnings": warnings,
        }
    
    else:
        return {"error": f"Unknown operation: {operation}", "result": None}


# ============================================================
# Tool Router: Map tool name to implementation
# ============================================================

TOOL_FUNCTIONS = {
    "fee_calculator": fee_calculator,
    "date_checker": date_checker,
    "percentage_calculator": percentage_calculator,
}


def execute_tool_call(tool_call: dict) -> dict:
    """
    Execute a tool call from the LLM response.
    
    Args:
        tool_call: dict with 'name' and 'args' or 'arguments' (LangChain uses 'args', OpenAI API uses 'arguments')
    
    Returns:
        dict with 'tool' name and 'result' of execution
    """
    name = tool_call.get("name", "")
    # LangChain tool_calls use 'args' (dict), OpenAI API responses use 'arguments' (JSON string)
    arguments = tool_call.get("args", tool_call.get("arguments", {}))
    
    # If it's a string, parse as JSON
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            return {
                "tool": name,
                "error": f"Failed to parse arguments: {arguments}",
                "result": None,
            }
    
    if name not in TOOL_FUNCTIONS:
        return {
            "tool": name,
            "error": f"Unknown tool: {name}",
            "result": None,
        }
    
    try:
        result = TOOL_FUNCTIONS[name](**arguments)
        return {
            "tool": name,
            "arguments": arguments,
            **result,
        }
    except Exception as e:
        return {
            "tool": name,
            "arguments": arguments,
            "error": f"Tool execution failed: {str(e)}",
            "result": None,
        }