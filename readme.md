# Malika AI OS

**Malika AI OS** is a fully autonomous, distributed, Jarvis-class Artificial Intelligence Operating System designed for Windows, mobile, and IoT environments.

## 🚀 Key Features

- **Kubernetes (K8s) Cluster Ready**: Deploys as a distributed cluster with auto-scaling (HPA) and self-healing across Brain, Vision, Voice, and Action nodes.
- **Autonomous Mastermind Cycle**: Proactive reasoning loop allowing the AI to execute multi-step tasks, find freelance jobs, and manage social media without constant human prompting.
- **Computer & Vision Control**: AI-powered screen analysis, autonomous mouse/keyboard control, and "Game Mode" for playing games like CS 1.6 independently.
- **Mobile & Remote Panel**: A Flask + Socket.IO powered mobile web panel to control the AI OS remotely from anywhere.
- **Smart Home & MQTT (IoT)**: Direct integration with ESP32 and other IoT devices via MQTT for complete home automation.
- **Hacker Toolkit & Defensive Security**: Network monitoring, vulnerability scanning, and proactive system defense.
- **Mobile ADB Control**: Directly manage Android devices over USB (app launching, typing, screen capture).
- **Pro Memory System**: Advanced Semantic, Long-term, and Short-term vector memory to learn user preferences and habits continuously.
- **Emotion Engine**: Dynamic voice and persona adaptation based on user mood and environmental context.

## 🏗️ Architecture

- **Layer 1: Interface** - `ui.py` (Local UI), `mobile_panel.py` (Remote), Web Panel.
- **Layer 2: AI Core** - `brain/`, `emotions/`, `memory/` (Gemini & Ollama Fallback).
- **Layer 3: Agent System** - `automation/`, `actions/` (Tools & execution).
- **Layer 4: Safety & Security** - `security/`, `voice_guard/` (Double-launch protection, safe mode).
- **Layer 5: Hardware & IoT** - `robotics/`, MQTT, ADB.

## ⚙️ Quick Start

**Local Development:**
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the main AI OS loop
python main.py
```

**Kubernetes Deployment:**
```bash
# Deploy to K8s cluster
bash k8s/deploy.sh
```

## 🔑 Configuration & Secrets

Set your API keys via:
1. Environment variables: `GEMINI_API_KEY`
2. Kubernetes Secrets: `k8s/03-secrets.yaml`
3. Local config file: `config/api_keys.json`

## 🧠 Notes

- **Offline Mode**: Malika will automatically fall back to local offline commands (opening apps, power control, local scripts) if the internet drops.
- **Vision Dependency**: If `ultralytics` or `opencv` is missing, the Vision module will automatically degrade gracefully into a "Stub Mode" to prevent system crashes.
- Designed primarily for Windows with full Python 3.10+ support.
