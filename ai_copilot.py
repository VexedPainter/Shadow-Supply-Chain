"""
AI Copilot Module for Shadow Supply Chain Detection.
Integrates Groq (fast LLM inference) and Cohere (embeddings + reranking)
for intelligent supply chain analysis, risk reasoning, and conversational AI.

Features:
1. Groq-powered AI Chat — contextual supply chain Q&A
2. Cohere-powered Risk Summarization — semantic risk analysis
3. Deep Reasoning Engine — AI-powered root cause explanations
"""
import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ─── API Configuration ─────────────────────────────
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
COHERE_API_KEY = os.environ.get("COHERE_API_KEY", "")

# ─── Initialize Clients ────────────────────────────
groq_client = None
cohere_client = None

def _init_groq():
    global groq_client
    if groq_client is None:
        try:
            from groq import Groq
            groq_client = Groq(api_key=GROQ_API_KEY)
            logger.info("[AI Copilot] Groq client initialized successfully.")
        except Exception as e:
            logger.warning(f"[AI Copilot] Groq init failed: {e}")
    return groq_client

def _init_cohere():
    global cohere_client
    if cohere_client is None:
        try:
            import cohere
            cohere_client = cohere.ClientV2(api_key=COHERE_API_KEY)
            logger.info("[AI Copilot] Cohere v2 client initialized successfully.")
        except Exception as e:
            logger.warning(f"[AI Copilot] Cohere init failed: {e}")
    return cohere_client


# ─── System Prompt ─────────────────────────────────
SYSTEM_PROMPT = """You are Nexus AI, the intelligent supply chain copilot for the Shadow Supply Chain Detection System.

Your role:
- Analyze shadow procurement patterns and explain risks
- Provide actionable recommendations for supply chain managers
- Explain AI risk scores, vendor trust metrics, and anomaly detections
- Help with compliance analysis and audit reasoning
- Answer questions about procurement best practices

Context: You operate within an enterprise system that monitors procurement transactions,
detects shadow purchases (unauthorized/untracked spending), and uses Isolation Forest ML
models for anomaly detection. The system tracks vendors, risk scores (0-1 scale),
inventory levels, and compliance audit trails.

Guidelines:
- Be concise but thorough
- Use data-driven reasoning
- Reference specific metrics when available
- Suggest specific actions (convert to PO, flag vendor, escalate audit)
- Format responses with clear structure using bullet points and headers
"""


# ═══════════════════════════════════════════════
# GROQ — Fast LLM Chat Interface
# ═══════════════════════════════════════════════

def chat_with_groq(
    user_message: str,
    context: dict = None,
    conversation_history: list = None,
    model: str = "llama-3.3-70b-versatile"
) -> dict:
    """
    Send a message to Groq's LLM with supply chain context.
    Returns: {response, model, tokens_used, status}
    """
    client = _init_groq()
    if not client:
        return {
            "response": "⚠️ Groq AI is not available. Please check your API key configuration.",
            "model": model,
            "tokens_used": 0,
            "status": "error"
        }

    # Build messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add context if provided
    if context:
        context_msg = _format_context(context)
        messages.append({"role": "system", "content": f"Current System State:\n{context_msg}"})

    # Add conversation history
    if conversation_history:
        for msg in conversation_history[-10:]:  # Last 10 messages
            messages.append({"role": msg["role"], "content": msg["content"]})

    # Add current user message
    messages.append({"role": "user", "content": user_message})

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
            top_p=0.9,
        )

        response_text = completion.choices[0].message.content
        tokens = completion.usage.total_tokens if completion.usage else 0

        return {
            "response": response_text,
            "model": model,
            "tokens_used": tokens,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"[Groq] Chat error: {e}")
        return {
            "response": f"⚠️ AI processing error: {str(e)}",
            "model": model,
            "tokens_used": 0,
            "status": "error"
        }


def analyze_shadow_with_groq(shadow_data: dict, transaction_data: dict = None) -> dict:
    """
    Deep AI analysis of a specific shadow purchase using Groq.
    Returns structured risk reasoning.
    """
    prompt = f"""Analyze this shadow procurement detection and provide a structured risk assessment:

Shadow Purchase Details:
- Risk Score: {shadow_data.get('risk_score', 'N/A')}
- Confidence: {shadow_data.get('confidence_score', 'N/A')}
- Category: {shadow_data.get('item_category', 'Unknown')}
- AI Reasoning: {shadow_data.get('reason', 'No specific reason provided')}
- Status: {shadow_data.get('status', 'Pending')}
"""
    if transaction_data:
        prompt += f"""
Transaction Details:
- Vendor: {transaction_data.get('vendor', 'Unknown')}
- Amount: ${transaction_data.get('amount', 0):,.2f}
- Department: {transaction_data.get('department', 'Unknown')}
- Payment Type: {transaction_data.get('payment_type', 'Unknown')}
- Description: {transaction_data.get('description', 'N/A')}
"""

    prompt += """
Please provide:
1. **Risk Assessment** — Overall risk level and justification
2. **Root Cause Analysis** — Why this might be a shadow purchase
3. **Financial Impact** — Estimated exposure and compliance risk
4. **Recommended Actions** — Specific steps to take (prioritized)
5. **Vendor Risk Insight** — Assessment of vendor trustworthiness
"""

    return chat_with_groq(prompt)


# ═══════════════════════════════════════════════
# COHERE — Semantic Analysis & Summarization
# ═══════════════════════════════════════════════

def summarize_risks_with_cohere(shadows_data: list) -> dict:
    """
    Use Cohere to generate an executive summary of current risk landscape.
    """
    client = _init_cohere()
    if not client:
        return {
            "summary": "⚠️ Cohere AI is not available. Please check your API key configuration.",
            "status": "error"
        }

    # Build text from shadows data
    risk_text = "Current Shadow Procurement Risk Landscape:\n\n"
    for i, s in enumerate(shadows_data[:20], 1):  # Top 20 items
        risk_text += (
            f"{i}. Vendor: {s.get('vendor', 'Unknown')} | "
            f"Amount: ${s.get('amount', 0):,.2f} | "
            f"Risk: {s.get('risk_score', 0):.0%} | "
            f"Category: {s.get('item_category', 'General')} | "
            f"Reason: {s.get('reason', 'N/A')}\n"
        )

    try:
        response = client.chat(
            model="command-a-03-2025",
            messages=[{
                "role": "system",
                "content": "You are a supply chain risk analyst AI. Provide concise, actionable executive summaries for C-level stakeholders."
            }, {
                "role": "user",
                "content": f"Based on the following shadow procurement data, provide a concise executive summary of the risk landscape. Highlight the top 3 risks, affected departments, and recommended immediate actions:\n\n{risk_text}"
            }],
            temperature=0.5,
        )

        return {
            "summary": response.message.content[0].text,
            "status": "success",
            "model": "command-a-03-2025"
        }
    except Exception as e:
        logger.error(f"[Cohere] Summarization error: {e}")
        return {
            "summary": f"⚠️ Cohere processing error: {str(e)}",
            "status": "error"
        }


def classify_risk_with_cohere(description: str, vendor: str, amount: float) -> dict:
    """
    Use Cohere to semantically classify procurement risk.
    """
    client = _init_cohere()
    if not client:
        return {"classification": "unknown", "confidence": 0, "status": "error"}

    try:
        response = client.chat(
            model="command-a-03-2025",
            messages=[{"role": "user", "content": f"""Classify this procurement transaction into one of these risk categories:
- CRITICAL: Likely fraudulent or heavily non-compliant
- HIGH: Significant policy violation, requires audit
- MEDIUM: Minor policy deviation, needs review
- LOW: Routine transaction, minimal risk

Transaction: {description}
Vendor: {vendor}
Amount: ${amount:,.2f}

Respond with ONLY the category name and a one-sentence justification."""}],
            temperature=0.3,
        )

        text = response.message.content[0].text.strip()
        category = "MEDIUM"
        for cat in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            if cat in text.upper():
                category = cat
                break

        return {
            "classification": category,
            "reasoning": text,
            "confidence": 0.85,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"[Cohere] Classification error: {e}")
        return {"classification": "unknown", "reasoning": str(e), "confidence": 0, "status": "error"}


def generate_vendor_insight_with_cohere(vendor_data: dict) -> dict:
    """
    Generate AI-powered vendor risk insight using Cohere.
    """
    client = _init_cohere()
    if not client:
        return {"insight": "Cohere unavailable", "status": "error"}

    try:
        response = client.chat(
            model="command-a-03-2025",
            messages=[{
                "role": "system",
                "content": "You are a vendor risk analyst. Be concise and actionable."
            }, {
                "role": "user",
                "content": f"""Analyze this vendor's risk profile and provide a 2-3 sentence risk assessment:

Vendor: {vendor_data.get('name', 'Unknown')}
Risk Level: {vendor_data.get('risk_level', 'Medium')}
Trust Score: {vendor_data.get('trust_score', 50)}/100
Shadow Purchase Count: {vendor_data.get('shadow_count', 0)}
Total Spend: ${vendor_data.get('total_spend', 0):,.2f}
Approved: {'Yes' if vendor_data.get('approved') else 'No'}

Provide actionable recommendations for the supply chain team."""
            }],
            temperature=0.5,
        )

        return {
            "insight": response.message.content[0].text,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"[Cohere] Vendor insight error: {e}")
        return {"insight": str(e), "status": "error"}


# ═══════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════

def check_ai_health() -> dict:
    """Check connectivity status of both AI providers."""
    health = {
        "groq": {"status": "unknown", "model": "llama-3.3-70b-versatile"},
        "cohere": {"status": "unknown", "model": "command-a-03-2025"},
    }

    # Test Groq
    try:
        client = _init_groq()
        if client:
            result = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": "Reply with OK"}],
                max_tokens=5,
            )
            health["groq"]["status"] = "connected"
            health["groq"]["response"] = result.choices[0].message.content
        else:
            health["groq"]["status"] = "not_configured"
    except Exception as e:
        health["groq"]["status"] = "error"
        health["groq"]["error"] = str(e)

    # Test Cohere
    try:
        client = _init_cohere()
        if client:
            result = client.chat(
                model="command-a-03-2025",
                messages=[{"role": "user", "content": "Reply with OK"}],
                max_tokens=5,
            )
            health["cohere"]["status"] = "connected"
            health["cohere"]["response"] = result.message.content[0].text
        else:
            health["cohere"]["status"] = "not_configured"
    except Exception as e:
        health["cohere"]["status"] = "error"
        health["cohere"]["error"] = str(e)

    return health


# ─── Helper ────────────────────────────────────
def _format_context(context: dict) -> str:
    """Format system context for the AI."""
    parts = []
    if "stats" in context:
        s = context["stats"]
        parts.append(f"Total Transactions: {s.get('total_transactions', 'N/A')}")
        parts.append(f"Shadow Purchases: {s.get('total_shadows', 'N/A')}")
        parts.append(f"Financial Exposure: ${s.get('total_exposure', 0):,.2f}")
        parts.append(f"Risk Level: {s.get('risk_level', 'N/A')}")
        parts.append(f"Pending Actions: {s.get('pending_shadows', 0)}")
    if "vendor_count" in context:
        parts.append(f"Active Vendors: {context['vendor_count']}")
    if "high_risk_vendors" in context:
        parts.append(f"High-Risk Vendors: {context['high_risk_vendors']}")
    return "\n".join(parts)
