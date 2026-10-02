# -*- coding: utf-8 -*-
# codesaver/widgets/ai_tools/worker.py
import httpx
import os
import re
import time
from PySide6.QtCore import QThread, Signal

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_TIMEOUT = 30.0
MAX_HTTP_RETRIES = 2
RETRY_BACKOFF_SECONDS = 1.0


def chat_completions(base_url, api_key, model, messages, timeout=DEFAULT_TIMEOUT):
    """Call an OpenAI-compatible chat/completions endpoint via httpx.

    Minimal vendor-neutral replacement for the openai SDK
    (see docs/decisions/0000-initial-decisions.md, Decision 4).
    Will migrate into the Phase D core/ai/ ModelAdapter.

    Args:
        base_url: API root, e.g. "https://api.openai.com/v1". Falls back
            to DEFAULT_BASE_URL when empty (matches the old SDK default).
        api_key: Bearer token.
        model: Model identifier, e.g. "gpt-4o-mini".
        messages: OpenAI chat messages list.
        timeout: Per-request timeout in seconds.

    Returns:
        The assistant message content string ("" if the API returned none).

    Raises:
        httpx.HTTPStatusError: on non-retryable HTTP error status.
        httpx.TimeoutException: on timeout.
        httpx.TransportError: on connection failure.
        ValueError: on a malformed (choices-less) response body.
    """
    url = (base_url or DEFAULT_BASE_URL).rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"model": model, "messages": messages}
    # Connection-level retries (connect phase only), mirroring the old
    # SDK's max_retries=2 behavior.
    transport = httpx.HTTPTransport(retries=2)

    with httpx.Client(timeout=timeout, transport=transport) as client:
        for attempt in range(MAX_HTTP_RETRIES + 1):
            response = client.post(url, json=payload, headers=headers)
            # Retry transient failures (429 / 5xx) with a short backoff.
            if (response.status_code == 429 or response.status_code >= 500) and attempt < MAX_HTTP_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS)
                continue
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices") or []
            if not choices or "message" not in choices[0]:
                raise ValueError(
                    "Malformed API response: missing choices[0].message: "
                    + str(data)[:200]
                )
            return choices[0]["message"].get("content") or ""


class ApiWorker(QThread):
    response_received = Signal(str)
    error_occurred = Signal(str)
    status_update = Signal(str)
    auto_inject_requested = Signal(str, str)
    finished_task = Signal()

    def __init__(self, api_settings, prompt, project_root, tree_context, active_file_name="", active_file_content="", images=None):
        super().__init__()
        self.api_key = api_settings.get("api_key", "")
        self.base_url = api_settings.get("base_url", "")
        self.model_name = api_settings.get("model_name", "gpt-4o-mini")
        self.prompt = prompt
        self.project_root = project_root
        self.tree_context = tree_context
        self.active_file_name = active_file_name
        self.active_file_content = active_file_content
        self.images = images or []

    def read_local_file(self, file_path):
        if not self.project_root:
            return "Error: No project open."
        abs_path = os.path.join(self.project_root, file_path)
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return "Error reading file: " + str(e)

    def run(self):
        if not self.api_key:
            self.error_occurred.emit("Authentication Error: API key is not set. Please go to AI Settings.")
            self.finished_task.emit()
            return

        try:
            # 🚀 FIX 1: Network Resilience (Timeouts & Auto-Retries)
            # Handled inside chat_completions(): 30s timeout, 2 connection
            # retries plus a 429/5xx retry loop with 1s backoff.
            bt = chr(96) * 3

            sys_prompt = (
                "You are an expert AI Developer Assistant integrated directly into an IDE.\n"
                "CRITICAL RULES:\n"
                "1. Answer questions using ONLY the provided context.\n"
                "2. DO NOT use JSON tool calls or <function> tags.\n"
                "3. To READ a file, output ONLY this exact text on a new line: READ_FILE: <file_path>\n"
                "4. To CREATE/MODIFY a file, output the COMPLETE new source code in a Markdown block.\n"
                "5. You MUST include a comment on the FIRST LINE of the code block indicating the file path:\n"
                + bt + "python\n# FILE: path/to/file.py\n...code...\n" + bt + "\n"
                "Project Context:\n" + str(self.tree_context)
            )

            if self.active_file_name and self.active_file_content:
                sys_prompt += (
                    f"\n\n[USER CURRENTLY OPEN FILE: {self.active_file_name}]\n"
                    "Primary context:\n" + bt + "\n" + str(self.active_file_content) + "\n" + bt + "\n"
                )

            user_content = []
            if self.prompt:
                user_content.append({"type": "text", "text": self.prompt})

            for img_base64 in self.images:
                user_content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}})

            if not self.prompt and self.images:
                user_content.append({"type": "text", "text": "Please analyze this image."})

            messages = [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_content if self.images else self.prompt}
            ]

            # 🚀 FIX 2: Prevent AI Infinite Loops
            seen_files = set()
            max_read_attempts = 3

            for attempt in range(max_read_attempts):
                self.status_update.emit(f"Thinking... (Step {attempt + 1})")

                final_text = chat_completions(
                    self.base_url, self.api_key, self.model_name, messages
                )
                messages.append({"role": "assistant", "content": final_text})

                # Check for READ_FILE request
                read_match = re.search(r'READ_FILE:\s*([a-zA-Z0-9_/\.\-]+)', final_text)
                if read_match:
                    filepath = read_match.group(1).strip()

                    # Prevent AI from reading the exact same file in a loop
                    if filepath in seen_files:
                        self.status_update.emit(f"AI requested {filepath} again. Forcing stop to save tokens.")
                        break

                    seen_files.add(filepath)
                    self.status_update.emit("Reading local file: " + filepath)
                    content = self.read_local_file(filepath)

                    messages.append({
                        "role": "user",
                        "content": f"Content of {filepath}:\n" + bt + "\n" + content + "\n" + bt + "\nNow continue."
                    })
                    continue

                # Check for code injection blocks
                pattern = r"" + bt + r"(?:[a-zA-Z0-9\-\+]+)?\n(.*?)" + bt
                blocks = re.findall(pattern, final_text, flags=re.DOTALL)

                for block in blocks:
                    block = block.strip()
                    lines = block.split('\n')
                    if lines and 'FILE:' in lines[0]:
                        match = re.search(r'FILE:\s*([a-zA-Z0-9_/\.\-]+)', lines[0])
                        if match:
                            filepath = match.group(1).strip()
                            code_to_save = '\n'.join(lines[1:]).strip()
                            self.status_update.emit("Preparing file: " + filepath)
                            self.auto_inject_requested.emit(filepath, code_to_save)

                self.response_received.emit(final_text)
                break

        # 🚀 FIX 3: Granular Error Handling
        # Note: TimeoutException must be caught before TransportError
        # (it is a TransportError subclass).
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status in (401, 403):
                self.error_occurred.emit("🔑 Authentication Error: Your API Key is invalid or expired.")
            elif status == 429:
                self.error_occurred.emit("⏱️ Rate Limit Exceeded: Please wait a few moments and try again.")
            else:
                self.error_occurred.emit(f"⚠️ Unexpected Error: HTTP {status} - {e.response.text[:200]}")
        except httpx.TimeoutException:
            self.error_occurred.emit("🌐 Connection Timeout: The AI server took too long to respond. Check your network/proxy.")
        except httpx.TransportError:
            self.error_occurred.emit("🔌 Connection Error: Could not reach the AI server. Are you connected to the internet?")
        except Exception as e:
            self.error_occurred.emit(f"⚠️ Unexpected Error: {str(e)}")
        finally:
            self.finished_task.emit()
