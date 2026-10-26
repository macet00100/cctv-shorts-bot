@echo off
chcp 65001 >nul
title 24/7 CCTV & Found Footage Automation Bot (Muse AI)

echo ======================================================================
echo 🎬 BOT TỰ ĐỘNG HÓA RENDER & ĐĂNG VIDEO 24/24 (MUSE AI 31B TOKEN)
echo ======================================================================
echo 🕒 Cơ chế: Mỗi ngày random 1 khung giờ vàng quốc tế (US/EU Peak Viral)
echo 🌙 Ban đêm: Tự động render bối cảnh ban đêm + giờ thực tế
echo ☀️ Ban ngày: Tự động render bối cảnh ban ngày + giờ thực tế
echo 🛑 Đang lắng nghe và kiểm tra mỗi 15 phút...
echo ======================================================================

:loop
python -m src.pipeline
echo.
echo [BOT 24/24] Nghỉ 15 phút trước lần kiểm tra tiếp theo...
timeout /t 900 /nobreak >nul
goto loop
