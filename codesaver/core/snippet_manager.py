# -*- coding: utf-8 -*-
# codesaver/core/snippet_manager.py
import json
import os

class SnippetManager:
    """
    Fast code snippets manager
    Storage structure: {"trigger_word": "actual code to replace"}
    """
    def __init__(self, config_path="snippets.json"):
        self.config_path = config_path
        # Default snippets that are always available
        self.snippets = {
            "pydoc": 'def ${1:func_name}(${2:args}):\n    """\n    ${3:description}\n    """\n    ${0:pass}',
            "html5": "<!DOCTYPE html>\n<html>\n<head>\n    <title>${1:Document}</title>\n</head>\n<body>\n    ${0}\n</body>\n</html>",
            "log": "print(f\"DEBUG: {${1:var}}\")",
            "react_fc": "import React from 'react';\n\nconst ${1:ComponentName} = () => {\n  return (\n    <div>\n      ${0}\n    </div>\n  );\n};\n\nexport default ${1:ComponentName};"
        }
        self.load_snippets()

    def load_snippets(self):
        """Load user's custom snippets from file"""
        if os.path.exists(self.config_path):
            try:
                # Use utf-8 to support special characters
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.snippets.update(json.load(f))
            except Exception as e:
                print(f"Error loading snippets: {e}")

    def save_snippets(self):
        """Save all snippets to file for persistence (required for settings window)"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.snippets, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving snippets: {e}")

    def add_snippet(self, trigger, code):
        """Add or edit a snippet and save it immediately"""
        self.snippets[trigger] = code
        self.save_snippets()

    def delete_snippet(self, trigger):
        """Delete a snippet and update the file"""
        if trigger in self.snippets:
            del self.snippets[trigger]
            self.save_snippets()

    def get_snippet(self, trigger):
        """Get the code associated with a trigger keyword"""
        return self.snippets.get(trigger)

    def trigger_on_space(self, editor, word):
        """If the user types a word and presses space, check if it's a snippet"""
        snippet = self.get_snippet(word)
        if snippet:
            # Clear the typed trigger word
            cursor = editor.textCursor()
            cursor.movePosition(cursor.Left, cursor.MoveAnchor, len(word) + 1)
            cursor.select(cursor.WordUnderCursor)
            cursor.removeSelectedText()
            
            # Insert the snippet
            cursor.insertText(snippet)
            return True
        return False