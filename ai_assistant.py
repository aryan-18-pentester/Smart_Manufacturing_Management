# ai_assistant.py

import json
import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:1.5b"


def ask_ai(prompt):
    """
    Send a prompt to Ollama and return the AI response.
    """

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()

        data = response.json()
        return data.get("response", "").strip()

    except requests.exceptions.ConnectionError:
        return "ERROR: Ollama is not running."

    except requests.exceptions.Timeout:
        return "ERROR: AI request timed out."

    except requests.exceptions.RequestException as e:
        return f"ERROR: {e}"


def analyze_email(sender, subject, body):
    """
    Analyze a manufacturing-related email using AI.
    """

    prompt = f"""
You are an AI assistant for a Smart Manufacturing Management System.

Analyze the following email.

FROM:
{sender}

SUBJECT:
{subject}

EMAIL:
{body}

Return ONLY valid JSON in exactly this structure:

{{
    "category": "",
    "priority": "",
    "summary": "",
    "key_information": [],
    "suggestions": [],
    "recommended_action": ""
}}

Rules:

category must be one of:
Supplier, Customer, Order, Payment, Delivery,
Production, Complaint, Inventory, General

priority must be:
High, Medium, or Low

summary:
Give a short summary of the email.

key_information:
Extract important information such as:
product, quantity, price, dates, order number,
supplier name, customer name, delivery information,
or other important details.

suggestions:
Give practical suggestions relevant to the manufacturing system.

recommended_action:
Give the single most useful action the company should consider.

Do not invent information that is not present in the email.
"""

    result = ask_ai(prompt)

    if result.startswith("ERROR:"):
        return {
            "category": "General",
            "priority": "Low",
            "summary": result,
            "key_information": [],
            "suggestions": [],
            "recommended_action": ""
        }

    # Remove markdown code fences if the model adds them
    result = result.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(result)

    except json.JSONDecodeError:
        return {
            "category": "General",
            "priority": "Medium",
            "summary": result,
            "key_information": [],
            "suggestions": [],
            "recommended_action": ""
        }


def generate_reply(sender, subject, body):
    """
    Generate a professional reply to an email.
    """

    prompt = f"""
You are an AI email assistant for a manufacturing company.

Write a professional and concise reply to this email.

FROM:
{sender}

SUBJECT:
{subject}

EMAIL:
{body}

Requirements:
- Be professional.
- Keep the reply short.
- Do not invent information.
- Do not make promises that were not mentioned.
- Return only the email reply.
"""

    return ask_ai(prompt)


def summarize_email(body):
    """
    Generate a short summary of an email.
    """

    prompt = f"""
Summarize the following manufacturing-related email
in 2-4 sentences.

EMAIL:
{body}

Return only the summary.
"""

    return ask_ai(prompt)


def extract_information(body):
    """
    Extract useful manufacturing information from an email.
    """

    prompt = f"""
Extract important information from this manufacturing email.

EMAIL:
{body}

Return ONLY valid JSON:

{{
    "customer": "",
    "supplier": "",
    "product": "",
    "quantity": "",
    "unit_price": "",
    "order_id": "",
    "delivery_date": "",
    "other_information": []
}}

Do not invent information.
Use an empty string when information is not available.
"""

    result = ask_ai(prompt)

    result = result.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(result)

    except json.JSONDecodeError:
        return {
            "customer": "",
            "supplier": "",
            "product": "",
            "quantity": "",
            "unit_price": "",
            "order_id": "",
            "delivery_date": "",
            "other_information": []
        }


# -------------------------------------------------
# TEST
# -------------------------------------------------

if __name__ == "__main__":

    sender = "supplier@example.com"

    subject = "Steel delivery delayed"

    body = """
    Dear Sir,

    We would like to inform you that the delivery of
    500 kg of steel has been delayed by three days.
    The new expected delivery date is 25 August 2026.

    Regards,
    ABC Materials
    """

    print("\n--- EMAIL ANALYSIS ---")

    analysis = analyze_email(
        sender,
        subject,
        body
    )

    print(json.dumps(
        analysis,
        indent=4,
        ensure_ascii=False
    ))

    print("\n--- AI REPLY ---")

    reply = generate_reply(
        sender,
        subject,
        body
    )

    print(reply)

    print("\n--- EXTRACTED INFORMATION ---")

    information = extract_information(body)

    print(json.dumps(
        information,
        indent=4,
        ensure_ascii=False
    ))
