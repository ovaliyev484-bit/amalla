"""
mobile_panel.py — Malika Mobil Veb Panel
Telefon va boshqa qurilmalar uchun lokal veb interfeys.
Bir xil Wi-Fi tarmog'ida http://<IP>:5050 orqali kirish mumkin.
"""

import io
import json
import os
import socket
import sys
import threading
import time
from pathlib import Path

try:
    from flask import Flask, render_template_string, request, send_from_directory
    from flask_socketio import SocketIO, emit
    _FLASK = True
except ImportError:
    _FLASK = False

try:
    import qrcode
    _QRCODE = True
except ImportError:
    _QRCODE = False


PORT = 5050
_panel_instance = None


def _get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# ─── HTML Shablon ──────────────────────────────────────────────────────────────
_HTML = """<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
<title>Malika — Panel</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    color-scheme: dark;
    font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #020617;
    color: #f8fafc;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    min-height: 100vh;
    background: radial-gradient(circle at top, rgba(56, 189, 248, 0.18), transparent 28%),
      linear-gradient(180deg, #020617 0%, #071527 100%);
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 20px;
  }
  .panel {
    width: 100%;
    max-width: 580px;
    border-radius: 30px;
    background: rgba(8, 14, 28, 0.96);
    border: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: 0 34px 90px rgba(0, 0, 0, 0.45);
    overflow: hidden;
    backdrop-filter: blur(20px);
  }
  .hero {
    padding: 30px 28px 22px;
    display: grid;
    gap: 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    background: linear-gradient(180deg, rgba(255,255,255,0.05), transparent);
  }
  .hero h1 {
    margin: 0;
    font-size: 2rem;
    letter-spacing: 0.01em;
  }
  .hero p {
    margin: 0;
    color: #cbd5e1;
    line-height: 1.7;
  }
  .grid {
    display: grid;
    gap: 18px;
    padding: 22px 22px 28px;
  }
  .card {
    border-radius: 24px;
    background: rgba(14, 25, 44, 0.95);
    border: 1px solid rgba(148, 163, 184, 0.08);
    padding: 22px;
    display: grid;
    gap: 16px;
  }
  .card h2 {
    margin: 0;
    font-size: 1.1rem;
  }
  .card p, .card li, .card .field label, .card .tip {
    color: #cbd5e1;
    line-height: 1.75;
    font-size: 0.95rem;
  }
  .row {
    display: grid;
    gap: 14px;
  }
  .status-block {
    display: grid;
    gap: 10px;
  }
  .status-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    border-radius: 999px;
    border: 1px solid rgba(56, 189, 248, 0.18);
    width: fit-content;
  }
  .status-pill.online { background: rgba(16, 185, 129, 0.16); color: #a7f3d0; }
  .status-pill.offline { background: rgba(239, 68, 68, 0.16); color: #fecaca; border-color: rgba(239, 68, 68, 0.22); }
  .status-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    background: #22c55e;
    box-shadow: 0 0 8px rgba(34, 197, 94, 0.35);
  }
  .status-dot.offline {
    background: #f87171;
    box-shadow: 0 0 8px rgba(248, 113, 113, 0.35);
  }
  .field {
    display: grid;
    gap: 8px;
  }
  input {
    width: 100%;
    border: 1px solid rgba(148, 163, 184, 0.16);
    border-radius: 16px;
    padding: 16px 18px;
    background: rgba(255, 255, 255, 0.04);
    color: #f8fafc;
    font-size: 0.95rem;
    outline: none;
  }
  input:focus { border-color: #38bdf8; box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.14); }
  .input-row { display: grid; gap: 14px; grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .btn-row { display: grid; gap: 14px; grid-template-columns: repeat(2, minmax(0, 1fr)); }
  button {
    border: none;
    border-radius: 16px;
    padding: 16px 18px;
    cursor: pointer;
    font-weight: 700;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }
  button.primary {
    background: linear-gradient(135deg, #38bdf8, #0ea5e9);
    color: #fff;
    box-shadow: 0 16px 30px rgba(56, 189, 248, 0.24);
  }
  button.secondary {
    background: rgba(255, 255, 255, 0.08);
    color: #cbd5e1;
  }
  button:hover { transform: translateY(-1px); }
  .panel-url {
    width: 100%;
    padding: 16px 18px;
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.05);
    color: #f8fafc;
    border: 1px solid rgba(148, 163, 184, 0.12);
    overflow-wrap: anywhere;
  }
  .weather-result {
    min-height: 92px;
    padding: 18px;
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(148, 163, 184, 0.12);
    color: #e2e8f0;
    white-space: pre-line;
    line-height: 1.75;
  }
  .weather-result.active {
    animation: fadeIn 0.25s ease;
  }
  .weather-tip {
    color: #94a3b8;
    font-size: 0.93rem;
  }
  textarea {
    width: 100%;
    min-height: 130px;
    border: 1px solid rgba(148, 163, 184, 0.16);
    border-radius: 16px;
    padding: 16px 18px;
    background: rgba(255, 255, 255, 0.04);
    color: #f8fafc;
    font-size: 0.95rem;
    outline: none;
    resize: vertical;
  }
  textarea:focus { border-color: #38bdf8; box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.14); }
  .quick-buttons {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
    margin-top: 10px;
  }
  .quick-btn {
    background: rgba(255, 255, 255, 0.08);
    color: #cbd5e1;
    border-radius: 14px;
    padding: 12px 10px;
    font-weight: 600;
  }
  .message-card .field label {
    display: block;
    margin-bottom: 8px;
    color: #cbd5e1;
    font-size: 0.95rem;
  }
  .app-card .field label {
    display: block;
    margin-bottom: 8px;
    color: #cbd5e1;
    font-size: 0.95rem;
  }
  .app-card .btn-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .app-card select {
    width: 100%;
    border: 1px solid rgba(148, 163, 184, 0.16);
    border-radius: 16px;
    padding: 16px 18px;
    background: rgba(255, 255, 255, 0.04);
    color: #f8fafc;
    font-size: 0.95rem;
    outline: none;
  }
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .tip {
    padding: 14px 16px;
    border-radius: 18px;
    background: rgba(56, 189, 248, 0.1);
    border: 1px solid rgba(56, 189, 248, 0.14);
  }
  .result-text {
    min-height: 22px;
    color: #bfdbfe;
    font-size: 0.95rem;
  }
  .result-text.success { color: #86efac; }
  .result-text.error { color: #fca5a5; }
  .wide { grid-column: span 2; }
  .guide-card ol {
    margin: 0;
    padding-left: 18px;
    display: grid;
    gap: 10px;
  }
  .guide-card li { list-style-type: decimal; }
  .guide-card a { color: #38bdf8; text-decoration: none; }
  .guide-card a:hover { text-decoration: underline; }
  @media (max-width: 640px) {
    body { padding: 14px; }
    .panel { max-width: 100%; }
    .input-row, .btn-row { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>
<div class="panel">
  <div class="hero">
    <div>
      <p style="font-size: 0.9rem; color:#94a3b8; letter-spacing:0.12em; text-transform: uppercase; margin-bottom: 8px;">Malika Panel</p>
      <h1>Gemini API kaliti va lokal holat</h1>
      <p>Ushbu sahifa orqali API kalitini kiriting, saqlang va Malika panelining onlayn/uzilgan holatini kuzatib boring. Panel mahalliy tarmoqda ishlaydi, lekin Gemini API chaqiruvlari uchun internet kerak bo‘ladi.</p>
    </div>
    <div class="status-block">
      <div class="status-pill online" id="online-pill"><span class="status-dot" id="online-dot"></span> <span id="online-label">Ulanish kutilyapti</span></div>
    </div>
  </div>
  <div class="grid">
    <div class="card">
      <h2>Panel manzili</h2>
      <p>Malika panelini ochish uchun manzil qatorini ishlating.</p>
      <div class="panel-url" id="panel-url">http://127.0.0.1:5050</div>
      <div class="btn-row">
        <button class="button secondary" id="copy-url">Nusxalash</button>
        <button class="button primary" id="open-panel">Panelni ochish</button>
      </div>
    </div>

    <div class="card weather-card">
      <h2>Ob-havo ma'lumoti</h2>
      <p>Joriy yoki boshqa joyning ob-havosini so'rang; Malika ovozli javob ham beradi.</p>
      <div class="field">
        <label for="weather-location">Joy / shahar</label>
        <input id="weather-location" type="text" placeholder="Toshkent, Samarqand, Buxoro..." />
      </div>
      <div class="btn-row">
        <button class="button secondary" id="get-current-weather">Hozirgi ob-havo</button>
        <button class="button primary" id="get-other-weather">Boshqa joy ob-havosi</button>
      </div>
      <div class="btn-row">
        <button class="button primary" id="be-programmer">Dasturchi bo'l</button>
      </div>
      <div class="weather-result" id="weather-result">Ob-havo ma'lumotini olish uchun "Hozirgi ob-havo" ni bosing.</div>
      <div id="code-result" class="result-text"></div>
      <div class="weather-tip">Agar joy nomini kiritmasangiz, brauzer umumiy joyni aniqlashga harakat qiladi.</div>
    </div>

    <div class="card message-card">
      <h2>Xabar yuborish</h2>
      <p>Matn yozish rejimini tezlashtiring va tezkor tugmalar bilan xabar yuboring.</p>
      <div class="input-row">
        <div class="field">
          <label for="message-recipient">Kimga</label>
          <input id="message-recipient" type="text" placeholder="Odam ismi yoki guruh..." />
        </div>
        <div class="field">
          <label for="message-platform">Platforma</label>
          <select id="message-platform">
            <option value="telegram">Telegram</option>
            <option value="whatsapp">WhatsApp</option>
            <option value="instagram">Instagram</option>
          </select>
        </div>
      </div>
      <div class="field">
        <label for="message-text">Xabar matni</label>
        <textarea id="message-text" placeholder="Xabar yozing..."></textarea>
      </div>
      <div class="quick-buttons">
        <button class="button secondary quick-btn" data-text="Salom!">Salom</button>
        <button class="button secondary quick-btn" data-text="Rahmat!">Rahmat</button>
        <button class="button secondary quick-btn" data-text="Hozir uyg'onaman.">Hozir uyg'onaman</button>
        <button class="button secondary quick-btn" data-text="Tez orada javob beraman.">Tez orada</button>
        <button class="button secondary quick-btn" data-text="Ha, to'g'ri.">Ha</button>
        <button class="button secondary quick-btn" data-text="Yo'q, iltimos yana bir bor tekshirib ko'ring.">Yo'q</button>
      </div>
      <div class="btn-row">
        <button class="button secondary" id="clear-message">Tozalash</button>
        <button class="button primary" id="send-message">Xabar yuborish</button>
      </div>
      <div id="message-result" class="result-text"></div>
    </div>

    <div class="card app-card">
      <h2>Ilova kir</h2>
      <p>Ilovaga tez kirish va xabar yuborish jarayonini ko‘ring.</p>
      <div class="input-row">
        <div class="field">
          <label for="app-name">Ilova nomi</label>
          <select id="app-name">
            <option value="Telegram">Telegram</option>
            <option value="WhatsApp">WhatsApp</option>
            <option value="Instagram">Instagram</option>
            <option value="Chrome">Chrome</option>
            <option value="Edge">Microsoft Edge</option>
            <option value="VSCode">VSCode</option>
            <option value="Notepad">Notepad</option>
          </select>
        </div>
      </div>
      <div class="quick-buttons quick-app-buttons">
        <button class="button secondary quick-app-btn" data-app="Telegram">Telegram</button>
        <button class="button secondary quick-app-btn" data-app="WhatsApp">WhatsApp</button>
        <button class="button secondary quick-app-btn" data-app="Chrome">Chrome</button>
        <button class="button secondary quick-app-btn" data-app="VSCode">VSCode</button>
        <button class="button secondary quick-app-btn" data-app="YouTube">YouTube</button>
        <button class="button secondary quick-app-btn" data-app="Notepad">Notepad</button>
      </div>
      <div class="btn-row">
        <button class="button primary" id="open-app">Ilovaga kir</button>
      </div>
      <div id="app-result" class="result-text"></div>
    </div>

    <div class="card command-card">
      <h2>Buyruqlar</h2>
      <p>Buyruq yozing yoki tezkor tugmalardan foydalaning.</p>
      <div class="field">
        <label for="command-text">Buyruq</label>
        <input id="command-text" type="text" placeholder="Masalan: telegramni och, internetni tekshir" />
      </div>
      <div class="quick-buttons">
        <button class="button secondary quick-command-btn" data-command="Telegramni och">Telegramni och</button>
        <button class="button secondary quick-command-btn" data-command="Brauzerni och">Brauzerni och</button>
        <button class="button secondary quick-command-btn" data-command="Notepadni och">Notepadni och</button>
        <button class="button secondary quick-command-btn" data-command="Internetni tekshir">Internetni tekshir</button>
        <button class="button secondary quick-command-btn" data-command="Vaqtni ko'rsat">Vaqtni ko'rsat</button>
      </div>
      <div class="btn-row">
        <button class="button primary" id="send-command">Buyruq yubor</button>
      </div>
      <div id="command-result" class="result-text"></div>
    </div>

    <div class="card">
      <h2>Gemini API kaliti</h2>
      <div class="field">
        <label for="api-key">Kalit</label>
        <input id="api-key" type="text" placeholder="gemini-..." autocomplete="off" />
      </div>
      <div class="input-row">
        <div class="field">
          <label for="host">Host</label>
          <input id="host" type="text" placeholder="127.0.0.1" />
        </div>
        <div class="field">
          <label for="port">Port</label>
          <input id="port" type="text" placeholder="5050" />
        </div>
      </div>
      <button class="button primary" id="save-key">Saqlash</button>
      <div id="save-result" class="result-text"></div>
    </div>

    <div class="card remote-card">
      <h2>Masofaviy Boshqaruv (Global)</h2>
      <p>Uydan uzoqda bo'lganda boshqarish uchun quyidagi usullardan foydalaning:</p>
      <div class="status-pill" style="margin-bottom: 10px; background: rgba(56, 189, 248, 0.1);">
        <span>Lokal IP:</span>
        <code id="local-ip-display">--.---.--.--</code>
      </div>
      <div class="tip" style="font-size: 0.8rem; line-height: 1.4;">
        <strong>1-usul:</strong> Routeringizda 5050 portini Forwarding qiling.<br>
        <strong>2-usul:</strong> <code>ngrok http 5050</code> buyrug'idan foydalaning.<br>
    <div class="card vision-card wide">
      <h2>Vision AI — Realtime Monitor</h2>
      <p>Malika kameradan ko'rayotgan predmetlar va yuzlarni aniqlash.</p>
      <div id="vision-monitor" style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 16px; padding: 15px; min-height: 100px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: center;">
        <div id="vision-empty" style="color: #64748b; font-style: italic;">Hech narsa aniqlanmadi...</div>
      </div>
      <div class="tip" style="margin-top: 10px; font-size: 0.75rem;">YOLOv8n modeli orqali real-vaqtda tahlil qilinmoqda.</div>
    </div>

    <div class="card smart-home-card wide">
      <h2>Smart Home — 3D Hologram</h2>
      <p>Uy qurilmalarini golografik ko'rinishda kuzatish va masofadan boshqarish.</p>
      
      <div id="three-container" style="width: 100%; height: 300px; background: #000; border-radius: 20px; margin-bottom: 15px; position: relative; overflow: hidden; border: 1px solid rgba(56, 189, 248, 0.3);">
        <div id="three-loading" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #fff;">Gologramma yuklanmoqda...</div>
        <div id="scanline" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06)); background-size: 100% 4px, 3px 100%; pointer-events: none; z-index: 10;"></div>
      </div>

      <div class="btn-row">
        <button class="button secondary" id="scan-devices">Qurilmalarni qidirish</button>
        <button class="button primary" id="voice-control-btn">Ovozli boshqaruv</button>
      </div>
      
      <div id="smart-devices-list" class="grid" style="grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: 15px; padding: 0;">
        <!-- Qurilmalar shu yerga chiqadi -->
      </div>
      
      <div id="smart-result" class="result-text" style="margin-top: 10px;"></div>
    </div>

    <div class="card guide-card wide">
      <h2>Gemini kalitini olish</h2>
      <ol>
        <li>Google Cloud konsoliga kiring: <a href="https://console.cloud.google.com/apis/credentials" target="_blank" rel="noopener">Credentials</a>.</li>
        <li>Yangi API kalitini yarating va Gemini xizmatiga ruxsat bering.</li>
        <li>Kalitni pastdagi maydonga joylashtiring.</li>
        <li>Sozlamalarni saqlang va Malika dasturini qayta ishga tushiring.</li>
      </ol>
      <div class="tip">Panel mahalliy tarmoqda ishlashi mumkin, lekin Gemini API chaqiruvlari uchun internet kerak bo‘ladi.</div>
    </div>
  </div>
</div>
<script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
<script>
  const apiKeyField = document.getElementById('api-key');
  const hostField = document.getElementById('host');
  const portField = document.getElementById('port');
  const panelUrl = document.getElementById('panel-url');
  const saveResult = document.getElementById('save-result');
  const copyUrlBtn = document.getElementById('copy-url');
  const openPanelBtn = document.getElementById('open-panel');
  const weatherLocation = document.getElementById('weather-location');
  const getCurrentWeatherBtn = document.getElementById('get-current-weather');
  const getOtherWeatherBtn = document.getElementById('get-other-weather');
  const beProgrammerBtn = document.getElementById('be-programmer');
  const weatherResult = document.getElementById('weather-result');
  const codeResult = document.getElementById('code-result');
  const recipientField = document.getElementById('message-recipient');
  const platformField = document.getElementById('message-platform');
  const messageField = document.getElementById('message-text');
  const sendMessageBtn = document.getElementById('send-message');
  const clearMessageBtn = document.getElementById('clear-message');
  const quickButtons = document.querySelectorAll('.quick-btn');
  const quickAppButtons = document.querySelectorAll('.quick-app-btn');
  const messageResult = document.getElementById('message-result');
  const appNameField = document.getElementById('app-name');
  const openAppBtn = document.getElementById('open-app');
  const appResult = document.getElementById('app-result');
  const commandField = document.getElementById('command-text');
  const sendCommandBtn = document.getElementById('send-command');
  const quickCommandButtons = document.querySelectorAll('.quick-command-btn');
  const commandResult = document.getElementById('command-result');
  const onlineLabel = document.getElementById('online-label');
  const onlineDot = document.getElementById('online-dot');
  const onlinePill = document.getElementById('online-pill');

  const storage = window.localStorage;
  const keyName = 'malika_gemini_key';
  const hostName = 'malika_host';
  const portName = 'malika_port';

  function loadSettings() {
    apiKeyField.value = storage.getItem(keyName) || '';
    hostField.value = storage.getItem(hostName) || '127.0.0.1';
    portField.value = storage.getItem(portName) || '5050';
    updatePanelUrl();
    updateConnection(false, 'Ulanish kutilyapti');
  }

  function updatePanelUrl() {
    const host = hostField.value.trim() || '127.0.0.1';
    const port = portField.value.trim() || '5050';
    panelUrl.textContent = `http://${host}:${port}`;
  }

  function saveSettings() {
    storage.setItem(keyName, apiKeyField.value.trim());
    storage.setItem(hostName, hostField.value.trim() || '127.0.0.1');
    storage.setItem(portName, portField.value.trim() || '5050');
    updatePanelUrl();
    saveResult.textContent = 'Sozlamalar saqlandi. Dasturni qayta yuklang.';
    saveResult.className = 'result-text success';
  }

  function speakText(text) {
    if (!window.speechSynthesis) return;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'uz-UZ';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  }

  function renderWeather(text) {
    const result = document.getElementById('weather-result');
    result.textContent = text;
    result.classList.add('active');
    setTimeout(() => result.classList.remove('active'), 400);
  }

  async function fetchWeather(city, speak = true) {
    const result = document.getElementById('weather-result');
    renderWeather('Ob-havo ma’lumotini yuklayapman...');
    const url = `https://wttr.in/${encodeURIComponent(city)}?format=j1&lang=uz`;
    try {
      const response = await fetch(url, { cache: 'no-store' });
      if (!response.ok) throw new Error('Server javob bermadi');
      const data = await response.json();
      const current = data.current_condition?.[0] || {};
      const place = data.nearest_area?.[0]?.areaName?.[0]?.value || city;
      const desc = current.weatherDesc?.[0]?.value || 'ma’lumot yo‘q';
      const temp = current.temp_C || '—';
      const feels = current.FeelsLikeC || '—';
      const humidity = current.humidity || '—';
      const wind = current.windspeedKmph || '—';
      const chance = data.weather?.[0]?.hourly?.[0]?.chanceofrain || '—';
      const message = `${place} uchun hozirgi ob-havo: ${desc}. Havo harorati ${temp}°C, sezilishi ${feels}°C. Namlik ${humidity}%, shamol ${wind} km/soat. Yog‘in ehtimoli ${chance}%.
Agar boshqa joy ob-havosini ko‘rmoqchi bo‘lsangiz, so‘rashingiz mumkin.`;
      renderWeather(message);
      if (speak) speakText(message);
    } catch (err) {
      const errorMsg = 'Ob-havo ma’lumotini olishda xatolik yuz berdi. Iltimos, internet ulanishingizni tekshiring yoki joy nomini aniq kiriting.';
      renderWeather(errorMsg);
      if (speak) speakText(errorMsg);
    }
  }

  async function detectLocationAndFetch() {
    if (!navigator.geolocation) {
      renderWeather('Brauzeringiz geolokatsiyani qo‘llab-quvvatlamaydi. Iltimos, shahar nomini kiriting.');
      speakText('Brauzeringiz geolokatsiyani qo‘llab-quvvatlamaydi. Iltimos, shahar nomini kiriting.');
      return;
    }

    renderWeather('Joyni aniqlayapman...');
    navigator.geolocation.getCurrentPosition(async (position) => {
      const { latitude, longitude } = position.coords;
      try {
        const geoRes = await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${latitude}&lon=${longitude}`);
        const geoData = await geoRes.json();
        const city = geoData.address?.city || geoData.address?.town || geoData.address?.village || geoData.address?.state || geoData.display_name;
        if (!city) throw new Error('Joy aniqlanmadi');
        document.getElementById('weather-location').value = city;
        fetchWeather(city);
      } catch (err) {
        renderWeather('Joyni aniqlashda xatolik yuz berdi. Iltimos, shahar nomini kiriting.');
        speakText('Joyni aniqlashda xatolik yuz berdi. Iltimos, shahar nomini kiriting.');
      }
    }, () => {
      renderWeather('Joy aniqlash rad etildi. Iltimos, shahar nomini qo‘lda kiriting.');
      speakText('Joy aniqlash rad etildi. Iltimos, shahar nomini qo‘lda kiriting.');
    }, { timeout: 8000 });
  }

  function askOtherLocation() {
    const city = prompt('Qaysi shahar ob-havosini ko‘rishni xohlaysiz?');
    if (!city) return;
    document.getElementById('weather-location').value = city.trim();
    fetchWeather(city.trim());
  }

  function setCodeResult(text, success = true) {
    codeResult.textContent = text;
    codeResult.className = 'result-text' + (success ? ' success' : ' error');
  }

  function sendCodeToCursor(city) {
    const code = `import requests


def get_weather(city):
    url = f"https://wttr.in/{city}?format=j1&lang=uz"
    response = requests.get(url)
    return response.json()

weather = get_weather("${city}")
print(weather)`;
    socket.emit('write_code', { text: code });
  }

  async function writeCodeForWeather() {
    let location = weatherLocation.value.trim();
    if (!location) {
      location = prompt('Qaysi shahar uchun kod yozishni xohlaysiz?');
      if (!location) {
        setCodeResult('Kod yozilmadi. Joy nomi kiritilmadi.', false);
        return;
      }
      weatherLocation.value = location.trim();
    }

    fetchWeather(location, true);
    setCodeResult('Iltimos, kursorni kod yoziladigan oynada tuting...');
    sendCodeToCursor(location.trim());
  }

  function setMessageResult(text, success = true) {
    messageResult.textContent = text;
    messageResult.className = 'result-text' + (success ? ' success' : ' error');
  }

  function populateQuickMessage(text) {
    messageField.value = text;
    messageField.focus();
  }

  function setCommandResult(text, success = true) {
    commandResult.textContent = text;
    commandResult.className = 'result-text' + (success ? ' success' : ' error');
  }

  function clearMessage() {
    messageField.value = '';
    setMessageResult('Xabar maydoni tozalandi.', true);
  }

  function sendCommand() {
    const text = commandField.value.trim();
    if (!text) {
      setCommandResult('Buyruqni yozing.', false);
      return;
    }
    setCommandResult('Buyruq yuborildi...');
    socket.emit('user_command', { text });
  }

  function populateCommand(text) {
    commandField.value = text;
    commandField.focus();
    setCommandResult('');
  }

  function sendMessage() {
    const receiver = recipientField.value.trim();
    const platform = platformField.value.trim();
    const text = messageField.value.trim();
    if (!receiver) {
      setMessageResult('Kimga jo\'natishni xohlayotganingizni kiriting.', false);
      return;
    }
    if (!text) {
      setMessageResult('Xabar matnini kiriting.', false);
      return;
    }
    setMessageResult('Xabar yuborilishi boshlandi...');
    socket.emit('send_message', {
      receiver: receiver,
      platform: platform,
      message_text: text,
    });
  }

  function openApp() {
    const appName = appNameField.value.trim();
    if (!appName) {
      appResult.textContent = 'Iltimos, ilova nomini tanlang.';
      appResult.className = 'result-text error';
      return;
    }
    appResult.textContent = `"${appName}" ochilmoqda...`;
    appResult.className = 'result-text';
    socket.emit('open_app', { app_name: appName });
  }

  function openAppButton(event) {
    const appName = event.currentTarget.dataset.app;
    if (!appName) return;
    appNameField.value = appName;
    appResult.textContent = `"${appName}" ochilmoqda...`;
    appResult.className = 'result-text';
    socket.emit('open_app', { app_name: appName });
  }

  function getWeatherFromInput() {
    const location = weatherLocation.value.trim();
    if (location) {
      fetchWeather(location);
      return;
    }
    detectLocationAndFetch();
  }

  function copyUrl() {
    navigator.clipboard.writeText(panelUrl.textContent).then(() => {
      saveResult.textContent = 'Manzil nusxalandi.';
      saveResult.className = 'result-text success';
    });
  }

  function openPanel() {
    window.open(panelUrl.textContent, '_blank');
  }

  copyUrlBtn.addEventListener('click', copyUrl);
  openPanelBtn.addEventListener('click', openPanel);
  getCurrentWeatherBtn.addEventListener('click', getWeatherFromInput);
  getOtherWeatherBtn.addEventListener('click', askOtherLocation);
  beProgrammerBtn.addEventListener('click', writeCodeForWeather);
  sendMessageBtn.addEventListener('click', sendMessage);
  clearMessageBtn.addEventListener('click', clearMessage);
  openAppBtn.addEventListener('click', openApp);
  sendCommandBtn.addEventListener('click', sendCommand);
  quickButtons.forEach(btn => btn.addEventListener('click', () => populateQuickMessage(btn.dataset.text)));
  quickAppButtons.forEach(btn => btn.addEventListener('click', openAppButton));
  quickCommandButtons.forEach(btn => btn.addEventListener('click', () => populateCommand(btn.dataset.command)));
  hostField.addEventListener('input', updatePanelUrl);
  portField.addEventListener('input', updatePanelUrl);
  document.getElementById('save-key').addEventListener('click', saveSettings);

  loadSettings();

  const socket = io();
  socket.on('connect', () => {
    updateConnection(true, 'Panel onlayn');
    saveResult.textContent = '';
  });
  socket.on('disconnect', () => {
    updateConnection(false, 'Aloqa uzildi');
  });
  socket.on('status', data => {
    const text = String(data.text || '');
    updateConnection(!text.toLowerCase().includes('off'), text || 'Holat yangilandi');
  });
  socket.on('cmd_result', data => {
    const text = String(data.text || '');
    const success = !text.toLowerCase().includes('xatolik');
    setCodeResult(text, success);
  });
  socket.on('command_result', data => {
    const text = String(data.text || '');
    const success = !text.toLowerCase().includes('xatolik');
    setCommandResult(text, success);
  });
  socket.on('message_result', data => {
    const text = String(data.text || '');
    const success = !text.toLowerCase().includes('xatolik');
    setMessageResult(text, success);
  });
  // --- General UI ---
  const localIpDisplay = document.getElementById('local-ip-display');
  
  // Set local IP from current window location if available
  if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    localIpDisplay.textContent = window.location.hostname;
  }

  socket.on('app_result', data => {
    const text = String(data.text || '');
    const success = !text.toLowerCase().includes('xatolik');
    appResult.textContent = text;
    appResult.className = 'result-text' + (success ? ' success' : ' error');
  });

  // --- Smart Home Logic ---
  const scanDevicesBtn = document.getElementById('scan-devices');
  const smartDevicesList = document.getElementById('smart-devices-list');
  const smartResult = document.getElementById('smart-result');
  const voiceControlBtn = document.getElementById('voice-control-btn');
  let voiceActive = false;

  scanDevicesBtn.addEventListener('click', () => {
    smartResult.textContent = 'Qurilmalar qidirilmoqda...';
    socket.emit('smart_home_action', { action: 'discover' });
  });

  voiceControlBtn.addEventListener('click', () => {
    voiceActive = !voiceActive;
    voiceControlBtn.textContent = voiceActive ? 'Ovozni o\'chirish' : 'Ovozli boshqaruv';
    voiceControlBtn.style.background = voiceActive ? 'linear-gradient(135deg, #ef4444, #dc2626)' : '';
    if (voiceActive) {
      startVoiceRecognition();
    }
  });

  socket.on('smart_home_result', data => {
    if (data.status === 'success' && data.devices) {
      smartResult.textContent = `${data.found_count} ta qurilma topildi.`;
      smartDevicesList.innerHTML = '';
      data.devices.forEach(dev => {
        const div = document.createElement('div');
        div.className = 'status-pill';
        div.style.width = '100%';
        div.style.justifyContent = 'space-between';
        div.style.cursor = 'pointer';
        div.innerHTML = `
          <span>${dev.name}</span>
          <span class="status-dot ${dev.status === 'on' ? 'online' : 'offline'}"></span>
        `;
        div.onclick = () => {
          socket.emit('smart_home_action', { action: 'connect', device_id: dev.id });
        };
        smartDevicesList.appendChild(div);
      });
      updateThreeDevices(data.devices);
    } else if (data.status === 'connected') {
      smartResult.textContent = data.response;
      smartResult.className = 'result-text success';
    } else {
      smartResult.textContent = data.error || 'Xatolik yuz berdi.';
      smartResult.className = 'result-text error';
    }
  });

  socket.on('vision_update', (data) => {
    const visionMonitor = document.getElementById('vision-monitor');
    if (!data.items || data.items.length === 0) {
      visionMonitor.innerHTML = '<div id="vision-empty" style="color: #64748b; font-style: italic;">Hech narsa aniqlanmadi...</div>';
      return;
    }
    visionMonitor.innerHTML = '';
    data.items.forEach(item => {
      const badge = document.createElement('div');
      badge.className = 'status-pill';
      badge.style.background = 'rgba(56, 189, 248, 0.15)';
      badge.style.border = '1px solid rgba(56, 189, 248, 0.4)';
      badge.style.color = '#38bdf8';
      badge.style.fontWeight = '600';
      badge.style.padding = '6px 14px';
      badge.innerHTML = `<span style="margin-right: 5px;">👁️</span> ${item.toUpperCase()}`;
      visionMonitor.appendChild(badge);
    });
  });

  socket.on('device_update', (data) => {
    // MQTT orqali kelgan qurilma yangilanishi
    const dot = document.querySelector(`[data-device-id="${data.device_id}"] .status-dot`);
    if (dot) {
      dot.className = `status-dot ${data.status === 'on' ? 'online' : 'offline'}`;
    }
    if (deviceObjects[data.device_id]) {
      deviceObjects[data.device_id].material.color.setHex(data.status === 'on' ? 0x4caf50 : 0x334155);
    }
  });

  // --- Three.js 3D View ---
  let scene, camera, renderer, room;
  let deviceObjects = {};
  let connectionLines = [];

  function initThree() {
    const container = document.getElementById('three-container');
    const loading = document.getElementById('three-loading');
    
    // Check if THREE is available (async load)
    if (typeof THREE === 'undefined') {
      const script = document.createElement('script');
      script.src = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
      script.onload = () => {
        loading.remove();
        setupScene();
      };
      document.head.appendChild(script);
    } else {
      loading.remove();
      setupScene();
    }

    function setupScene() {
      scene = new THREE.Scene();
      scene.background = new THREE.Color(0x020617);
      
      camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
      camera.position.set(5, 5, 5);
      camera.lookAt(0, 0, 0);

      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      renderer.setSize(container.clientWidth, container.clientHeight);
      container.appendChild(renderer.domElement);

      const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
      scene.add(ambientLight);

      const pointLight = new THREE.PointLight(0x38bdf8, 1, 100);
      pointLight.position.set(10, 10, 10);
      scene.add(pointLight);

      // Simple room grid
      const grid = new THREE.GridHelper(10, 10, 0x334155, 0x1e293b);
      scene.add(grid);

      // Holographic Room Box (Wireframe)
      const geometry = new THREE.BoxGeometry(8, 4, 8);
      const material = new THREE.MeshPhongMaterial({ 
        color: 0x38bdf8, 
        transparent: true, 
        opacity: 0.2,
        wireframe: true,
        side: THREE.DoubleSide
      });
      room = new THREE.Mesh(geometry, material);
      room.position.y = 2;
      scene.add(room);

      // Inner glow box
      const innerGeom = new THREE.BoxGeometry(7.8, 3.8, 7.8);
      const innerMat = new THREE.MeshPhongMaterial({
        color: 0x0ea5e9,
        transparent: true,
        opacity: 0.05,
        side: THREE.BackSide
      });
      const innerRoom = new THREE.Mesh(innerGeom, innerMat);
      innerRoom.position.y = 2;
      scene.add(innerRoom);

      animate();
    }

    function animate() {
      requestAnimationFrame(animate);
      if (renderer) {
        renderer.render(scene, camera);
        
        const time = Date.now() * 0.0005;
        camera.position.x = Math.cos(time) * 7;
        camera.position.z = Math.sin(time) * 7;
        camera.lookAt(0, 1, 0);

        // Hologram Flicker
        if (room) {
          room.material.opacity = 0.15 + Math.random() * 0.1;
        }
        Object.values(deviceObjects).forEach(obj => {
          obj.material.opacity = 0.5 + Math.random() * 0.3;
          obj.rotation.y += 0.01;
        });

        // Connection Lines Pulse
        connectionLines.forEach(line => {
          line.material.opacity = 0.2 + Math.random() * 0.4;
        });
      }
    }
  }

  function updateThreeDevices(devices) {
    if (!scene) return;
    
    // Clear old objects
    Object.values(deviceObjects).forEach(obj => scene.remove(obj));
    connectionLines.forEach(line => scene.remove(line));
    deviceObjects = {};
    connectionLines = [];

    const masterPos = new THREE.Vector3(0, 0.5, 0);

    devices.forEach((dev, index) => {
      const color = dev.status === 'on' ? 0x22c55e : 0xf87171;
      const geometry = dev.type === 'light' ? new THREE.SphereGeometry(0.3, 16, 16) : new THREE.BoxGeometry(0.5, 0.5, 0.5);
      const material = new THREE.MeshPhongMaterial({ 
        color: color, 
        emissive: color, 
        emissiveIntensity: 0.8,
        transparent: true,
        opacity: 0.7,
        blending: THREE.AdditiveBlending
      });
      const mesh = new THREE.Mesh(geometry, material);
      
      // Add wireframe shell for hologram look
      const wireGeom = geometry.clone();
      const wireMat = new THREE.MeshBasicMaterial({ color: color, wireframe: true, transparent: true, opacity: 0.3 });
      const wireframe = new THREE.Mesh(wireGeom, wireMat);
      mesh.add(wireframe);
      
      // Arrange devices in the room
      const angle = (index / devices.length) * Math.PI * 2;
      const dist = 3;
      mesh.position.set(Math.cos(angle) * dist, 0.5, Math.sin(angle) * dist);
      
      scene.add(mesh);
      deviceObjects[dev.id] = mesh;

      // Draw connection line to center
      const points = [masterPos, mesh.position];
      const lineGeom = new THREE.BufferGeometry().setFromPoints(points);
      const lineMat = new THREE.LineBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.3 });
      const line = new THREE.Line(lineGeom, lineMat);
      scene.add(line);
      connectionLines.push(line);
    });
  }

  function startVoiceRecognition() {
    if (!('webkitSpeechRecognition' in window)) {
      alert("Sizning brauzeringiz ovozli boshqaruvni qo'llab-quvvatlamaydi.");
      return;
    }
    const recognition = new webkitSpeechRecognition();
    recognition.lang = 'uz-UZ';
    recognition.onresult = (event) => {
      const text = event.results[0][0].transcript;
      smartResult.textContent = `Eshitildi: "${text}"`;
      socket.emit('user_command', { text });
    };
    recognition.onend = () => {
      if (voiceActive) recognition.start();
    };
    recognition.start();
  }

  initThree();
</script>
</body>
</html>"""


class MobilePanel:
    """Malika uchun lokal Flask web paneli."""

    def __init__(self, jarvis_ref=None, port: int = PORT):
        self.port = port
        self.jarvis = jarvis_ref      # JarvisLive instance (keyinroq set qilinadi)
        self.ip = _get_local_ip()
        self.app = None
        self.sio = None
        self._thread = None
        self._running = False

    def set_jarvis(self, jarvis):
        self.jarvis = jarvis

    def broadcast_log(self, text: str, tag: str = "sys"):
        """Barcha ulangan telefon/brauzerlarga log yubor."""
        if self.sio:
            try:
                self.sio.emit("log", {"tag": tag, "text": text})
            except Exception:
                pass

    def broadcast_status(self, text: str):
        """Holat matnini yangilashtir."""
        if self.sio:
            try:
                self.sio.emit("status", {"text": text})
            except Exception:
                pass

    def broadcast_vision(self, items):
        """Kamera orqali aniqlangan predmetlarni tarqatish."""
        if self.sio:
            self.sio.emit("vision_update", {"items": items})

    def broadcast_device(self, device_id, status, data=None):
        """Qurilmalar holatini (MQTT) tarqatish."""
        if self.sio:
            self.sio.emit("device_update", {
                "device_id": device_id,
                "status": status,
                "data": data or {}
            })

    def _build_app(self):
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "malika-mobile-secret"
        sio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
        self.sio = sio

        @app.route("/")
        def index():
            return render_template_string(_HTML)

        @app.route("/static/<path:filename>")
        def static_files(filename):
            return send_from_directory(os.path.join(os.getcwd(), "static"), filename)

        @sio.on("connect")
        def on_connect():
            print(f"[MobilePanel] 📱 Telefon ulandi: {request.remote_addr}")
            sio.emit("status", {"text": "ONLINE"}, to=request.sid)

        @sio.on("ping_check")
        def on_ping_check(data):
            sio.emit("pong_check", {"ts": data.get("ts", 0)}, to=request.sid)

        @sio.on("disconnect")
        def on_disconnect():
            print(f"[MobilePanel] 📴 Telefon uzildi: {request.remote_addr}")

        @sio.on("user_command")
        def on_command(data):
            text = str(data.get("text", "")).strip()
            if not text:
                return
            print(f"[MobilePanel] 📩 Buyruq: {text}")
            # Malikaning session'iga matn yuborish
            if self.jarvis and self.jarvis.session and self.jarvis._loop:
                import asyncio
                try:
                    asyncio.run_coroutine_threadsafe(
                        self.jarvis.session.send_client_content(
                            turns=[{"parts": [{"text": text}]}],
                            turn_complete=True,
                        ),
                        self.jarvis._loop,
                    )
                    sio.emit("command_result", {"text": f"Yuborildi: {text}"}, to=request.sid)
                    sio.emit("cmd_result", {"text": f"Yuborildi: {text}"}, to=request.sid)
                except Exception as e:
                    sio.emit("command_result", {"text": f"Xatolik: {e}"}, to=request.sid)
                    sio.emit("cmd_result", {"text": f"Xatolik: {e}"}, to=request.sid)
            elif self.jarvis:
                # OFFLINE REJIMDA LOKAL BOSHQARISH
                print(f"[MobilePanel] 📡 Offline buyruq bajarilmoqda: {text}")
                result = self.jarvis.handle_offline_command(text)
                sio.emit("command_result", {"text": f"Offline: {result}"}, to=request.sid)
                sio.emit("cmd_result", {"text": f"Offline: {result}"}, to=request.sid)
            else:
                sio.emit("command_result",
                         {"text": "Malika hali ulanmagan. Biroz kuting..."},
                         to=request.sid)
                sio.emit("cmd_result",
                         {"text": "Malika hali ulanmagan. Biroz kuting..."},
                         to=request.sid)

        @sio.on("write_code")
        def on_send_message(data):
            receiver = str(data.get("receiver", "")).strip()
            platform = str(data.get("platform", "telegram")).strip().lower()
            message_text = str(data.get("message_text", "")).strip()
            if not receiver or not message_text:
                sio.emit("message_result", {"text": "Xatolik: Iltimos, kimga va xabar matnini to‘liq kiriting."}, to=request.sid)
                return
            sio.emit("message_result", {"text": "Xabar yuborish jarayoni boshlandi..."}, to=request.sid)
            print(f"[MobilePanel] 📩 Xabar yuborilmoqda: {receiver} via {platform}")
            try:
                from actions.send_message import send_message
                result = send_message({"receiver": receiver, "platform": platform, "message_text": message_text})
                sio.emit("message_result", {"text": result}, to=request.sid)
            except Exception as e:
                sio.emit("message_result", {"text": f"Xatolik: {e}"}, to=request.sid)

        @sio.on("open_app")
        def on_open_app(data):
            app_name = str(data.get("app_name", "")).strip()
            if not app_name:
                sio.emit("app_result", {"text": "Xatolik: Iltimos, ilova nomini kiriting."}, to=request.sid)
                return
            sio.emit("app_result", {"text": f"{app_name} ochilmoqda..."}, to=request.sid)
            print(f"[MobilePanel] 🔓 Ilova ochilmoqda: {app_name}")
            try:
                from actions.open_app import open_app
                result = open_app({"app_name": app_name})
                sio.emit("app_result", {"text": result}, to=request.sid)
            except Exception as e:
                sio.emit("app_result", {"text": f"Xatolik: {e}"}, to=request.sid)

        @sio.on("smart_home_action")
        def on_smart_home(data):
            action = data.get("action")
            device_id = data.get("device_id")
            from actions.smart_home import smart_home
            res_str = smart_home({"action": action, "device_id": device_id}, player=self.jarvis.ui if self.jarvis else None)
            try:
                res_data = json.loads(res_str)
                sio.emit("smart_home_result", res_data, to=request.sid)
            except Exception:
                sio.emit("smart_home_result", {"error": res_str}, to=request.sid)

        return app, sio

    def start(self):
        if not _FLASK:
            print("[MobilePanel] ⚠️  Flask o'rnatilmagan. pip install flask flask-socketio")
            return

        self.app, self.sio = self._build_app()

        def _run():
            self._running = True
            print(f"[MobilePanel] 🌐 Panel ishga tushdi: http://{self.ip}:{self.port}")
            print(f"[MobilePanel] 📱 Telefon bilan ulanish: http://{self.ip}:{self.port}")
            self.sio.run(
                self.app,
                host="0.0.0.0",
                port=self.port,
                debug=False,
                use_reloader=False,
                log_output=False,
                allow_unsafe_werkzeug=True,
            )

        self._thread = threading.Thread(target=_run, daemon=True, name="MobilePanel")
        self._thread.start()

    def get_url(self) -> str:
        return f"http://{self.ip}:{self.port}"

    def generate_qr(self) -> bytes | None:
        """QR kod PNG bytes qaytaradi."""
        if not _QRCODE:
            return None
        try:
            qr = qrcode.QRCode(box_size=6, border=2)
            qr.add_data(self.get_url())
            qr.make(fit=True)
            img = qr.make_image(fill_color="#00d4ff", back_color="#000a0e")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
        except Exception as e:
            print(f"[MobilePanel] QR error: {e}")
            return None


# ── Global singleton ────────────────────────────────────────────────────────────
_panel_instance: MobilePanel | None = None


def get_panel() -> MobilePanel | None:
    return _panel_instance


def start_panel(jarvis_ref=None, port: int = PORT) -> MobilePanel:
    global _panel_instance
    if _panel_instance is None:
        _panel_instance = MobilePanel(jarvis_ref=jarvis_ref, port=port)
        _panel_instance.start()
    elif jarvis_ref is not None:
        _panel_instance.set_jarvis(jarvis_ref)
    return _panel_instance
