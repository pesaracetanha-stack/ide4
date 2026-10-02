# -*- coding: utf-8 -*-
# codesaver/tests/conftest.py
import sys
import os

tests_dir = os.path.dirname(os.path.abspath(__file__))
codesaver_dir = os.path.dirname(tests_dir)
project_root = os.path.dirname(codesaver_dir)

# معرفی هر دو مسیر به پایتون برای حل تداخلِ ایمپورت‌های نسبی و مطلق
sys.path.insert(0, codesaver_dir)
sys.path.insert(0, project_root)