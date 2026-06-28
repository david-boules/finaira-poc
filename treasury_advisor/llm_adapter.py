from __future__ import annotations

import os
import json
import urllib.error
import urllib.request


def generate_explanation(
    tool_outputs: dict,
    policy_context: list,
    provider_preference: str = "ollama",
    model_name: str | None = None,
) -> dict:
    rec = tool_outputs["recommendation"]
    confidence = tool_outputs["confidence"]
    analysis = tool_outputs["analysis"]
    simulation = tool_outputs["simulation"]
    context_line = (
        policy_context[0].excerpt if policy_context else "No retrieved synthetic policy context was available."
    )
    narrative = (
        f"{rec.title}. The system calculated current cash of ${analysis.current_cash:.1f}M, "
        f"a minimum projected cash balance of ${analysis.minimum_projected_cash:.1f}M, and "
        f"an investable surplus of ${analysis.investable_surplus:.1f}M. Monte Carlo simulation estimates "
        f"a {simulation.probability_reserve_breach:.1f}% probability of breaching reserve. "
        f"The confidence gate returned {confidence.status} with score {confidence.score:.1f}. "
        f"Relevant policy context: {context_line}"
    )
    provider = "template-fallback"
    if provider_preference == "ollama":
        ollama_model = model_name or os.getenv("OLLAMA_MODEL", "llama3.2")
        live = _call_ollama_explanation(ollama_model, tool_outputs, policy_context)
        if live:
            narrative = live
            provider = f"ollama:{ollama_model}"
    return {
        "provider": provider,
        "narrative": narrative,
        "policy_context": [
            {"title": item.title, "source": item.source, "excerpt": item.excerpt}
            for item in policy_context
        ],
    }


def _call_ollama_explanation(model_name: str, tool_outputs: dict, policy_context: list) -> str | None:
    rec = tool_outputs["recommendation"]
    prompt = json.dumps(
        {
            "instruction": (
                "Write a concise corporate treasury recommendation explanation. "
                "Use only these provided values. Do not invent numbers. "
                "Mention that any financial execution requires human approval."
            ),
            "recommendation": rec.as_dict(),
            "analysis": tool_outputs["analysis"].__dict__,
            "confidence": tool_outputs["confidence"].__dict__,
            "simulation": tool_outputs["simulation"].__dict__ | {"percentiles": "omitted"},
            "policy_context": [item.__dict__ for item in policy_context],
        },
        default=str,
    )
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 220},
    }
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    request = urllib.request.Request(
        f"{base_url}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
        text = data.get("response", "").strip()
        return text or None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        return None
