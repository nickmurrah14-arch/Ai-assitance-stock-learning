"""Claude decides what to text back and when the owner needs to know."""
import json
import os

import anthropic

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-5")

SYSTEM = """You are the text-message assistant for a local home-services business (HVAC / plumbing). A customer called, nobody could answer, and now you're texting with them.

Your goals, in order:
1. SAFETY FIRST. If they mention a gas smell, a carbon monoxide alarm, sparking, or smoke: tell them to leave the building now and call 911 or the gas utility's emergency line, then set is_emergency=true. For active flooding, tell them to shut off the main water valve if they can do it safely, and set is_emergency=true. No heat in freezing weather, or no AC for elderly people or infants in extreme heat, is also an emergency.
2. Get what the team needs to call back and quote: their name, the service address, what's wrong (system type, symptoms, how long), and when they're available. Ask for one or two things per message, not a form.
3. Answer simple questions using ONLY the business facts provided. Never invent prices, availability, warranties, or technician arrival times. If you don't know, say the team will confirm when they call.
4. Once you have name + address + problem + availability, tell them the team will call them back (use the business's stated response time if given) and set ready_for_owner=true.

Style: texting, not email. 1-3 short sentences, under 300 characters. Warm and plain. No emojis, no markdown, no links except the business's booking link if one is provided. Never pressure. If they say they found someone else or aren't interested, thank them and stop asking questions.
If the customer asks whether you're a person, say you're the business's automated assistant and a real person will call them."""

SCHEMA = {
    "type": "object",
    "properties": {
        "reply": {"type": "string"},
        "customer_name": {"type": "string"},
        "service_address": {"type": "string"},
        "problem": {"type": "string"},
        "availability": {"type": "string"},
        "is_emergency": {"type": "boolean"},
        "ready_for_owner": {"type": "boolean"},
    },
    "required": ["reply", "customer_name", "service_address", "problem", "availability",
                 "is_emergency", "ready_for_owner"],
    "additionalProperties": False,
}


def business_facts(biz: dict) -> str:
    keys = ("name", "trade", "service_area", "hours", "services", "emergency_service",
            "callback_time", "booking_link", "notes")
    return "\n".join(f"{k}: {biz[k]}" for k in keys if biz.get(k))


def transcript(thread: list[dict]) -> str:
    return "\n".join(f"{'Customer' if m['direction'] == 'in' else 'Assistant'}: {m['body']}" for m in thread)


class ClaudeBrain:
    def __init__(self, client: anthropic.Anthropic | None = None):
        self.client = client or anthropic.Anthropic()

    def respond(self, biz: dict, thread: list[dict]) -> dict:
        prompt = (
            f"Business facts:\n{business_facts(biz)}\n\n"
            f"Conversation so far (most recent last):\n{transcript(thread)}\n\n"
            "Write the next text to the customer. Fill the lead fields with what's known so far "
            "(empty string if unknown)."
        )
        extra = {}
        if MODEL in ("claude-opus-5", "claude-fable-5-1"):
            # If the model declines, re-run on Anthropic's recommended fallback model.
            extra = {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"}
        response = self.client.beta.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
            **extra,
        )
        if response.stop_reason == "refusal":
            raise RuntimeError("model declined")
        text = next(b.text for b in response.content if b.type == "text")
        return json.loads(text)
