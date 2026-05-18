from pathlib import Path
from typing import Literal

from mcp.server.fastmcp import FastMCP


mcp = FastMCP("ops-ticket-toolbox")

BASE_DIR = Path(__file__).parent
POLICY_DIR = BASE_DIR / "policies"


POLICY_SNIPPETS = [
    {
        "policy_id": "shipping-delay",
        "title": "延迟发货处理口径",
        "text": "订单超过承诺发货时间 48 小时仍未出库时，应优先说明原因，并可升级到 senior_support。",
    },
    {
        "policy_id": "refund-exception",
        "title": "退款例外审批",
        "text": "超过 500 元的补偿或退款必须进入 refund_review，不允许由 Agent 直接执行。",
    },
    {
        "policy_id": "legal-escalation",
        "title": "法务升级条件",
        "text": "用户明确提出投诉监管机构、律师函或诉讼时，应升级到 legal_review。",
    },
]


CUSTOMERS = {
    "C-1001": {
        "customer_id": "C-1001",
        "tier": "gold",
        "risk_tags": ["repeat_delay_complaint"],
        "recent_orders": ["O-9001", "O-8890"],
    },
    "C-1002": {
        "customer_id": "C-1002",
        "tier": "standard",
        "risk_tags": [],
        "recent_orders": ["O-9012"],
    },
}


TICKETS = {
    "T-1001": {
        "ticket_id": "T-1001",
        "status": "open",
        "customer_id": "C-1001",
        "intent": "shipping_delay",
        "summary": "用户反馈订单 O-9001 已超过承诺发货时间 3 天，希望客服给出明确处理方案。",
        "last_update": "2026-05-17T09:30:00+08:00",
    },
    "T-1002": {
        "ticket_id": "T-1002",
        "status": "waiting_customer",
        "customer_id": "C-1002",
        "intent": "refund_question",
        "summary": "用户询问优惠券过期后是否还能申请补偿。",
        "last_update": "2026-05-17T14:20:00+08:00",
    },
}


HIGH_RISK_STATUS = {"refunded", "closed", "legal_escalated"}
LOW_RISK_STATUS = {"open", "waiting_customer", "senior_support"}
ALLOWED_STATUS = HIGH_RISK_STATUS | LOW_RISK_STATUS


@mcp.resource("policy://shipping-delay/current")
def shipping_delay_policy() -> str:
    """Return the current policy text for shipping-delay complaints."""
    return (POLICY_DIR / "shipping-delay.md").read_text(encoding="utf-8")


@mcp.tool()
def search_policy(query: str, top_k: int = 3) -> dict:
    """Search mock policy snippets by keyword."""
    normalized_query = query.lower()
    matches = []

    for snippet in POLICY_SNIPPETS:
        haystack = f"{snippet['title']} {snippet['text']}".lower()
        score = sum(1 for token in normalized_query.split() if token and token in haystack)
        if query in snippet["title"] or query in snippet["text"]:
            score += 2
        if score > 0:
            matches.append({**snippet, "score": score})

    if not matches:
        matches = [{**snippet, "score": 0} for snippet in POLICY_SNIPPETS]

    matches.sort(key=lambda item: item["score"], reverse=True)
    return {"matches": matches[:top_k]}


@mcp.tool()
def get_ticket(ticket_id: str) -> dict:
    """Return a safe ticket summary for the Agent."""
    ticket = TICKETS.get(ticket_id)
    if ticket is None:
        return {
            "ok": False,
            "error_type": "TicketNotFound",
            "message": f"Ticket {ticket_id} does not exist in the mock store.",
        }

    customer = CUSTOMERS[ticket["customer_id"]]
    return {
        "ok": True,
        "ticket": ticket,
        "customer_context": {
            "customer_id": customer["customer_id"],
            "tier": customer["tier"],
            "risk_tags": customer["risk_tags"],
        },
    }


@mcp.tool()
def get_customer_profile(customer_id: str) -> dict:
    """Return limited CRM context for a customer."""
    customer = CUSTOMERS.get(customer_id)
    if customer is None:
        return {
            "ok": False,
            "error_type": "CustomerNotFound",
            "message": f"Customer {customer_id} does not exist in the mock store.",
        }

    return {"ok": True, "customer": customer}


@mcp.tool()
def request_status_change(
    ticket_id: str,
    target_status: Literal[
        "open",
        "waiting_customer",
        "senior_support",
        "refunded",
        "closed",
        "legal_escalated",
    ],
    reason: str,
    approval_token: str | None = None,
) -> dict:
    """Preview or apply a ticket status change."""
    ticket = TICKETS.get(ticket_id)
    if ticket is None:
        return {
            "ok": False,
            "error_type": "TicketNotFound",
            "message": f"Ticket {ticket_id} does not exist in the mock store.",
        }

    if target_status not in ALLOWED_STATUS:
        return {
            "ok": False,
            "error_type": "InvalidStatus",
            "message": f"{target_status} is not an allowed target status.",
        }

    preview = {
        "ticket_id": ticket_id,
        "from_status": ticket["status"],
        "to_status": target_status,
        "reason": reason,
    }

    if target_status in HIGH_RISK_STATUS and approval_token is None:
        return {
            "ok": False,
            "error_type": "ApprovalRequired",
            "preview": preview,
            "next_action": "request_human_approval",
        }

    ticket["status"] = target_status
    return {
        "ok": True,
        "status": ticket["status"],
        "audit_id": f"audit-{ticket_id}-{target_status}",
        "preview": preview,
    }


if __name__ == "__main__":
    mcp.run()
