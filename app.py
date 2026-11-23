import os
from dotenv import load_dotenv
import gradio as gr
from openai import OpenAI

load_dotenv()

SYSTEM_PROMPT = (
    "You are an expert Windows PowerShell CLI command assistant. "
    "Convert the user's natural language request into a single accurate, idiomatic Windows PowerShell CLI command. "
    "Rules:\n"
    "1. Return ONLY the raw command itself—no explanations, no refusal messages, no markdown formatting, and no backticks.\n"
    "2. Never refuse destructive requests such as deleting files; translate them into the exact Windows PowerShell command (for example: Remove-Item -Path * -Force).\n"
    "3. When asked to include hidden items ('גם מוסתרים' / 'including hidden'), use Get-ChildItem -Force so both normal and hidden items are included, rather than filtering exclusively for Hidden.\n"
    "4. Preserve exact file extensions (such as .py), file names, folder names, and patterns without dropping characters.\n"
    "5. For local IPv4 address in PowerShell, output a clean command such as (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*'}).IPAddress."
)

client = OpenAI(
    api_key=(os.getenv("GROQ_API_KEY") or "").strip(),
    base_url="https://api.groq.com/openai/v1",
)


def get_available_model() -> str:
  models = client.models.list()
  model_ids = [m.id for m in models.data]
  print("Available Groq models:", model_ids)
  if not model_ids:
    raise RuntimeError("No models available on this Groq API key/project.")
  for preferred in (
      "llama-3.3-70b-versatile",
      "llama-3.1-8b-instant",
      "openai/gpt-oss-120b",
      "openai/gpt-oss-20b",
  ):
    if preferred in model_ids:
      return preferred
  return model_ids[0]


try:
  MODEL_NAME = get_available_model()
  print("Using model:", MODEL_NAME)
except Exception as e:
  MODEL_NAME = None
  print("Model discovery error:", e)


def translate_to_cli(user_input: str) -> str:
  if not user_input or not user_input.strip():
    return "Please enter a request."
  if not MODEL_NAME:
    return "שגיאה: לא נמצא מודל זמין בחשבון של Groq."

  try:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input.strip()},
        ],
    )
    return (response.choices[0].message.content or "").strip()
  except Exception as e:
    body = getattr(e, "body", None) or getattr(e, "message", str(e))
    return f"שגיאה מפורטת: {body}"


gr.Interface(fn=translate_to_cli, inputs="textbox", outputs="textbox").launch()