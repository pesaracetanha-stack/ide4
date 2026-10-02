# -*- coding: utf-8 -*-
# codesaver/tests/test_lsp_provider.py
import pytest
from PySide6.QtWidgets import QTextEdit
from core.lsp_provider import PythonLSP

def test_lsp_survives_extreme_syntax_errors():
    """تست فوق‌سخت‌گیرانه: کدی که از نظر سینتکس فاجعه است و دارای حروف فارسی است"""
    
    # 1. Arrange: ساختن یک ادیتور مجازی برای اینکه LSP روی آن نصب شود
    dummy_editor = QTextEdit()
    
    chaos_code = """
def متغیر_فارسی():
    broken_list = [1, 2, 3
    if True
        return broken_list
"""
    # ریختن کد خراب داخل ادیتور
    dummy_editor.setPlainText(chaos_code)
    
    # متصل کردن LSP به ادیتور مجازی (دقیقاً همان‌طور که در نرم‌افزار کار می‌کند)
    provider = PythonLSP(dummy_editor, file_path="fake_script.py")
    
    # 2. Act: فراخوانی مستقیمِ هسته‌ی بررسی (بدون hasattr)
    # اگر LSP نتواند سینتکس خراب را هندل کند، همین‌جا کِرَش می‌کند
    provider.run_diagnostics()
    
    # 3. Assert: آیا با وجود کد خراب، همچنان می‌تواند متغیرهای خودِ ادیتور را برای پیشنهاد استخراج کند؟
    # (ما متد اصلی آپدیت پاپ‌آپ را با force=True صدا می‌زنیم)
    provider._handle_autocomplete_popup(force=True)
    
    # بررسی می‌کنیم که آیا مدلِ پیشنهادات (QStringListModel) کرش نکرده باشد
    assert provider.word_model is not None, "LSP Model completely failed on broken syntax!"