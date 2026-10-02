# -*- coding: utf-8 -*-
# codesaver/widgets/ai_tools/worker.py
import openai
import json
import os
import re
from PySide6.QtCore import QThread, Signal

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
            client_kwargs = {
                "api_key": self.api_key,
                "timeout": 30.0,      # حداکثر ۳۰ ثانیه انتظار برای جواب
                "max_retries": 2      # در صورت قطعی لحظه‌ای، ۲ بار به صورت خودکار تلاش مجدد می‌کند
            }
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
            
            client = openai.OpenAI(**client_kwargs)
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
                
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=messages
                )

                final_text = response.choices[0].message.content or ""
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
        except openai.AuthenticationError:
            self.error_occurred.emit("🔑 Authentication Error: Your API Key is invalid or expired.")
        except openai.RateLimitError:
            self.error_occurred.emit("⏱️ Rate Limit Exceeded: Please wait a few moments and try again.")
        except openai.APITimeoutError:
            self.error_occurred.emit("🌐 Connection Timeout: The AI server took too long to respond. Check your network/proxy.")
        except openai.APIConnectionError:
            self.error_occurred.emit("🔌 Connection Error: Could not reach the AI server. Are you connected to the internet?")
        except Exception as e:
            self.error_occurred.emit(f"⚠️ Unexpected Error: {str(e)}")
        finally:
            self.finished_task.emit()