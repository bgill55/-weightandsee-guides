#!/usr/bin/env python3
"""Generate a categorized, visually engaging README and guides/index.html for the Weight and See Guides repo.

Automatically categorizes guides based on title/content keywords — no manual slug lists needed.
"""

import json
import os
import re
import sys
from datetime import datetime

# Allow running from pipeline (for auto-deploy) or from repo root
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
# Check if we're in the repo (has .git) or in pipeline
if os.path.exists(os.path.join(THIS_DIR, ".git")):
    REPO_DIR = THIS_DIR
elif os.path.exists(os.path.join(THIS_DIR, "..", "workspace", "runs", "_guides_repo", ".git")):
    REPO_DIR = os.path.join(THIS_DIR, "..", "workspace", "runs", "_guides_repo")
else:
    REPO_DIR = THIS_DIR  # fallback

GUIDES_DIR = os.path.join(REPO_DIR, "guides")

# Category definitions with keyword matching
CATEGORY_KEYWORDS = {
    "Benchmarks & Comparisons": {
        "desc": "Head-to-head model showdowns and real-world performance tests",
        "keywords": ["vs ", " versus ", "benchmark", "showdown", "comparison", "speed test", "faceoff", "head-to-head", " vs."],
    },
    "Model Deep Dives": {
        "desc": "In-depth analysis of cutting-edge AI models and architectures",
        "keywords": ["deep dive", "paper", "breakdown", "analysis", "architecture", "deep-dive", "technical deep", "model card"],
    },
    "Local AI & Self-Hosting": {
        "desc": "Run powerful AI models on your own hardware — no cloud required",
        "keywords": ["local", "offline", "self-host", "raspberry pi", "laptop", "selfhost", "homelab", "edge ai", "run on your", "air-gap"],
    },
    "AI Security": {
        "desc": "Threats, vulnerabilities, and defenses in the AI era",
        "keywords": ["security", "breach", "hack", "attack", "vulnerability", "firewall", "poison", "exploit", "adversarial", "forge"],
    },
    "Developer Tools & Agents": {
        "desc": "AI-powered coding assistants, agents, and developer workflows",
        "keywords": ["agent", "coding", "cursor", "ide", "developer", "copilot", "vscode", "build a", "hands-on tutorial", "tutorial"],
    },
    "Image & Vision": {
        "desc": "Image generation, computer vision, and visual AI",
        "keywords": ["image", "vision", "diffusion", "stable diffusion", "cad", "midjourney", "flux", "dalle", "text-to-cad", "vision"],
    },
    "No-Code & Automation": {
        "desc": "Build AI workflows without writing code",
        "keywords": ["no-code", "nocode", "automation", "workflow", "flowise", "n8n", "zapier", "make.com", "no code"],
    },
    "GPU & Hardware": {
        "desc": "GPU benchmarks, hardware analysis, and acceleration",
        "keywords": ["gpu", "nvidia", "rtx", "4090", "3090", "vram", "cuda", "hardware benchmark", "acceleration"],
    },
    "Audio & Voice": {
        "desc": "TTS, voice synthesis, and audio AI",
        "keywords": ["tts", "voice", "audio", "speech", "synthesis", "kokoro", "whisper", "elevenlabs", "text-to-speech"],
    },
}

TITLE_OVERRIDES = {
    "autovision-vs-stable-diffusion-31-edge-image-generation-showdown": "AutoVision vs Stable Diffusion 3.1 — Edge Image Generation Showdown",
    "build-a-gemini-optimized-app-on-apple-silicon-hands-on-tutorial": "Build a Gemini-Optimized App on Apple Silicon",
    "build-a-nocode-claude-fable-5-agent-in-5-minutes-no-coding-required": "Build a No-Code Claude FABLE 5 Agent in 5 Minutes",
    "cad-gpt-20-generating-production-ready-step-files-in-seconds": "CAD-GPT 2.0 — Generating Production-Ready STEP Files in Seconds",
    "claude-fable-5-desktop-test-realworld-speed-on-a-hyperv-vm": "Claude FABLE 5 Desktop — Real-World Speed on a Hyper-V VM",
    "deep-dive-into-adahmpleng-50m-5ep-1e-4-64b-efficient-smallscale-english-model": "Deep Dive into AdaHmpLEng — Efficient Small-Scale English Model",
    "diffusiongemma-26b-a4bit-the-new-fast-local-image-generator-for-creators": "DiffusionGemma 26B A4Bit — Fast Local Image Generator for Creators",
    "diffusiongemma-4x-faster-text-generation-how-the-new-model-breaks-speed-limits": "DiffusionGemma 4x Faster Text Generation — Speed Limits Broken",
    "gemma-4-vs-gpt55-deepseekv4-realworld-12b-benchmark-showdown": "Gemma 4 vs GPT-5.5 vs DeepSeek V4 — Real-World 12B Benchmark Showdown",
    "gemma412bit-vs-llama4-the-lightweight-coding-ai-showdown": "Gemma 4 12-Bit vs Llama 4 — The Lightweight Coding AI Showdown",
    "gpt4o-vs-claude-35-vs-gemini-20-realworld-office-task-benchmark-june-2026": "GPT-4o vs Claude 3.5 vs Gemini 2.0 — Real-World Office Task Benchmark",
    "hustlegemini-vs-cursor-6-the-agentic-coding-showdown": "HustleGemini vs Cursor 6 — The Agentic Coding Showdown",
    "inside-the-microsoft-ai-tool-breach-timeline-exploits-and-patch-rollout": "Inside the Microsoft AI Tool Breach — Timeline, Exploits & Patches",
    "is-outlines-30-the-ultimate-ai-firewall": "Is Outlines 3.0 the Ultimate AI Firewall?",
    "llama-4-cad-generate-engineering-grade-parts-offline": "Llama 4 CAD — Generate Engineering-Grade Parts Offline",
    "llama-4-turbo-local-the-48gb-vram-reality-check": "Llama 4 Turbo Local — The 48GB VRAM Reality Check",
    "metavision-20-api-deep-dive-is-the-new-multimodal-model-worth-the-hype": "MetaVision 2.0 API Deep Dive — Is It Worth the Hype?",
    "nocode-ai-orchestrators-faceoff-flowise-20-vs-n8n-ai-30-vs-autogptstudio": "No-Code AI Orchestrators Face-Off — Flowise vs n8n vs AutoGPT Studio",
    "ollama-07-offline-13b-llm-on-an-8-gb-laptop-does-it-really-work": "Ollama 0.7 — Offline 13B LLM on an 8GB Laptop",
    "qwen-3-72b-vs-llama-4-scout-realworld-macos-container-machine-benchmark-on-m3-ma": "Qwen 3 72B vs Llama 4 Scout — macOS Container Benchmark on M3",
    "qwen-3-72b-vs-llama-4-scout-realworld-speed-test-on-a-500-gpu": r"Qwen 3 72B vs Llama 4 Scout — Speed Test on a $500 GPU",
    "run-claude-35-offline-for-free-opencode-full-setup-on-a-500-pc": r"Run Claude 3.5 Offline for Free — Full Setup on a $500 PC",
    "run-gpt55-on-a-raspberry-pi-zero-the-ultimate-lowcost-local-ai-hack": "Run GPT-5.5 on a Raspberry Pi Zero — The Ultimate Low-Cost AI Hack",
    "running-ideogram-4-fp8-locally-fp8-quantization-benchmarks-and-cost-analysis": "Running Ideogram 4 FP8 Locally — Quantization Benchmarks & Cost",
    "running-llms-offline-a-stepbystep-guide": "Running LLMs Offline — A Step-by-Step Guide",
    "text-to-cad-just-got-real-the-caddy-model-breakdown": "Text-to-CAD Just Got Real — The CADDY Model Breakdown",
    "the-microsoft-ai-forge-hack-how-they-stole-your-api-keys": "The Microsoft AI Forge Hack — How They Stole Your API Keys",
    "the-omnivision-7-paper-why-ai-finally-understands-motion": "The OmniVision 7 Paper — Why AI Finally Understands Motion",
    "the-poise-attack-i-poisoned-an-ai-agent-in-real-time": "The POISE Attack — I Poisoned an AI Agent in Real Time",
    "unchaining-ai-is-qwen-36-aggressive-the-ultimate-local-powerhouse": "Unchaining AI — Is Qwen 3.6 Aggressive the Ultimate Local Powerhouse?",
    "unicad-7b-vs-cloud-giants-can-local-ai-engineer-real-parts": "UniCAD 7B vs Cloud Giants — Can Local AI Engineer Real Parts?",
    "unlocking-ai-voice-synthesis-a-deep-dive-into-sundaycoiltext-to-speech-converter": "Unlocking AI Voice Synthesis — A Deep Dive into sundaycoil/text-to-speech",
    "visionaryai-2026-review-8k-images-on-a-laptop-gpu": "VisionaryAI 2026 Review — 8K Images on a Laptop GPU",
    "whispersmallhi-the-tiny-transcriber-that-beats-cloud-apis": "WhisperSmall-Hi — The Tiny Transcriber That Beats Cloud APIs",
}

CATEGORY_OVERRIDES = {
    "build-a-gemini-optimized-app-on-apple-silicon-hands-on-tutorial": "Developer Tools & Agents",
    "build-a-nocode-claude-fable-5-agent-in-5-minutes-no-coding-required": "No-Code & Automation",
    "claude-fable-5-desktop-test-realworld-speed-on-a-hyperv-vm": "Developer Tools & Agents",
    "run-claude-35-offline-for-free-opencode-full-setup-on-a-500-pc": "Local AI & Self-Hosting",
    "running-llms-offline-a-stepbystep-guide": "Local AI & Self-Hosting",
    "run-gpt55-on-a-raspberry-pi-zero-the-ultimate-lowcost-local-ai-hack": "Local AI & Self-Hosting",
    "nocode-ai-orchestrators-faceoff-flowise-20-vs-n8n-ai-30-vs-autogptstudio": "No-Code & Automation",
    "cad-gpt-20-generating-production-ready-step-files-in-seconds": "Image & Vision",
    "llama-4-cad-generate-engineering-grade-parts-offline": "Image & Vision",
    "text-to-cad-just-got-real-the-caddy-model-breakdown": "Image & Vision",
    "diffusiongemma-26b-a4bit-the-new-fast-local-image-generator-for-creators": "Image & Vision",
    "autovision-vs-stable-diffusion-31-edge-image-generation-showdown": "Image & Vision",
}


def slug_to_title(slug):
    if slug in TITLE_OVERRIDES:
        return TITLE_OVERRIDES[slug]
    return slug.replace("-", " ").title()


def get_guide_title_and_text(slug):
    html_path = os.path.join(GUIDES_DIR, slug, "index.html")
    try:
        if os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            title_match = re.search(r"<title>([^<]+)</title>", content)
            title = title_match.group(1).split("|")[0].strip() if title_match else slug_to_title(slug)
            body_match = re.search(r"<body[^>]*>(.*?)</body>", content, re.DOTALL)
            body_text = body_match.group(1) if body_match else content[:2000]
            body_text = re.sub(r"<[^>]+>", " ", body_text)
            return title, body_text[:2000].lower()
    except Exception as e:
        print(f"[Warning] Failed to read {html_path}: {e}")
    return slug_to_title(slug), ""


def categorize_slug(slug):
    if slug in CATEGORY_OVERRIDES:
        return CATEGORY_OVERRIDES[slug]
    
    title, body_text = get_guide_title_and_text(slug)
    text = f"{title} {body_text}".lower()
    
    for cat_name, cat_data in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in cat_data["keywords"]):
            return cat_name
    
    return "More Guides"


def get_guide_datetime(slug):
    html_path = os.path.join(GUIDES_DIR, slug, "index.html")
    try:
        if os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})', content)
            if match:
                return match.group(1)
            match = re.search(r'(\d{4}-\d{2}-\d{2})', content)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"[Warning] Failed to read datetime for {html_path}: {e}")
    return "0000-00-00 00:00"


def get_guide_date(slug):
    dt = get_guide_datetime(slug)
    if dt != "0000-00-00 00:00":
        return dt.split()[0]
    return None


def get_all_categorized_guides():
    if not os.path.exists(GUIDES_DIR):
        return {}
    
    all_guides = [d.name for d in os.scandir(GUIDES_DIR) if d.is_dir() and d.name != "index.html"]
    
    categorized = {cat: {"desc": data["desc"], "slugs": []} for cat, data in CATEGORY_KEYWORDS.items()}
    categorized["More Guides"] = {"desc": "Recently published and uncategorized guides", "slugs": []}
    
    for slug in all_guides:
        cat = categorize_slug(slug)
        categorized[cat]["slugs"].append(slug)
    
    for cat_data in categorized.values():
        cat_data["slugs"].sort(key=lambda s: get_guide_datetime(s), reverse=True)
        
    return {k: v for k, v in categorized.items() if v["slugs"]}


def generate_readme():
    CATEGORIES = get_all_categorized_guides()
    lines = []

    lines.append('<div align="center">')
    lines.append('')
    lines.append('<img src="assets/hero-banner.png" width="100%" alt="Weight and See Guides Wiki">')
    lines.append('')
    lines.append('</div>')
    lines.append('')
    lines.append('---')
    lines.append('')

    total_guides = sum(len(cat["slugs"]) for cat in CATEGORIES.values())
    categories_count = len(CATEGORIES)
    lines.append('<div align="center">')
    lines.append('')
    month_year = datetime.now().strftime("%B %Y").upper()
    lines.append(f'![Guides](https://img.shields.io/badge/{total_guides}_GUIDES-blue?style=for-the-badge&logo=booktype&logoColor=white)')
    lines.append(f'![Categories](https://img.shields.io/badge/{categories_count}_CATEGORIES-green?style=for-the-badge&logo=folder-open&logoColor=white)')
    lines.append(f'![Updated](https://img.shields.io/badge/UPDATED_{month_year.replace(" ", "_")}-orange?style=for-the-badge&logo=simpleicons&logoColor=white)')
    lines.append('')
    lines.append('</div>')
    lines.append('')
    lines.append('---')
    lines.append('')

    all_slugs_with_time = []
    for cat_data in CATEGORIES.values():
        for slug in cat_data["slugs"]:
            dt = get_guide_datetime(slug)
            all_slugs_with_time.append((slug, dt))
    all_slugs_with_time.sort(key=lambda x: x[1], reverse=True)

    lines.append('## Latest Guides')
    lines.append('')
    lines.append('<table><tr>')
    for slug, _ in all_slugs_with_time[:3]:
        title = slug_to_title(slug)
        url = f"https://bgill55.github.io/-weightandsee-guides/guides/{slug}/"
        thumb_path = os.path.join(GUIDES_DIR, slug, "thumbnail.jpg")
        if os.path.exists(thumb_path):
            lines.append(f'<td align="center" width="33%">')
            lines.append(f'<a href="{url}">')
            lines.append(f'<img src="guides/{slug}/thumbnail.jpg" width="300" alt="{title}"><br>')
            lines.append(f'<b>{title}</b>')
            lines.append(f'</a>')
            lines.append(f'</td>')
    lines.append('</tr></table>')
    lines.append('')
    lines.append('---')
    lines.append('')

    lines.append('## Quick Navigation')
    lines.append('')
    lines.append('| Category | Count |')
    lines.append('|----------|-------|')
    for cat_name, cat_data in CATEGORIES.items():
        count = len(cat_data["slugs"])
        lines.append(f'| **{cat_name}** | ![{count}](https://img.shields.io/badge/{count}-blue?style=flat-square) |')
    lines.append('')
    lines.append('---')
    lines.append('')

    for cat_name, cat_data in CATEGORIES.items():
        lines.append(f'## {cat_name}')
        lines.append('')
        lines.append(f'*{cat_data["desc"]}*')
        lines.append('')

        for slug in cat_data["slugs"]:
            title = slug_to_title(slug)
            url = f"https://bgill55.github.io/-weightandsee-guides/guides/{slug}/"
            date = get_guide_date(slug)
            date_str = f" — {date}" if date else ""
            lines.append(f'- **[{title}]({url})**{date_str}')

        lines.append('')
        lines.append('---')
        lines.append('')

    lines.append('<div align="center">')
    lines.append('')
    lines.append('### 📺 Watch the Videos')
    lines.append('')
    lines.append('Each guide corresponds to a video on the [Weight and See](https://youtube.com/@WeightnSee) YouTube channel.')
    lines.append('Watch the video for visual walkthroughs, then use the guide for code snippets and step-by-step instructions.')
    lines.append('')
    lines.append('[![YouTube](https://img.shields.io/badge/YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://youtube.com/@WeightnSee)')
    lines.append('')
    lines.append('</div>')

    return "\n".join(lines)


def generate_index_html():
    """Generate modern, interactive guides/index.html web page."""
    if not os.path.exists(GUIDES_DIR):
        all_slugs = []
    else:
        all_slugs = [d.name for d in os.scandir(GUIDES_DIR) if d.is_dir() and d.name != "index.html"]
    
    guides_data = []
    for slug in all_slugs:
        raw_title, _ = get_guide_title_and_text(slug)
        title = slug_to_title(slug)
        if title == slug.replace("-", " ").title() and raw_title and len(raw_title) > 5:
            title = raw_title
        category = categorize_slug(slug)
        dt = get_guide_datetime(slug)
        date = dt.split()[0] if dt != "0000-00-00 00:00" else ""
        has_thumb = os.path.exists(os.path.join(GUIDES_DIR, slug, "thumbnail.jpg"))
        
        guides_data.append({
            "slug": slug,
            "title": title,
            "category": category,
            "date": date,
            "datetime": dt,
            "hasThumbnail": has_thumb,
            "url": f"./{slug}/"
        })
    
    # Sort newest first initially
    guides_data.sort(key=lambda x: x["datetime"], reverse=True)

    json_payload = json.dumps(guides_data, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weight and See - Video Guides & Resources</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-main: #0b0c10;
            --bg-surface: #13151c;
            --bg-card: #1a1d27;
            --bg-card-hover: #222634;
            --border-color: #2a2e3d;
            --border-hover: #6366f1;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --text-dim: #6b7280;
            --accent-primary: #6366f1;
            --accent-glow: rgba(99, 102, 241, 0.25);
            --accent-secondary: #818cf8;
            --badge-bg: rgba(99, 102, 241, 0.15);
            --badge-text: #a5b4fc;
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg-main);
            color: var(--text-main);
            min-height: 100vh;
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
        }}

        .site-header {{
            position: sticky;
            top: 0;
            z-index: 100;
            background: rgba(19, 21, 28, 0.88);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-color);
            padding: 16px 24px;
        }}

        .header-inner {{
            max-width: 1280px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 20px;
            flex-wrap: wrap;
        }}

        .brand {{
            display: flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
            color: var(--text-main);
        }}

        .brand-icon {{
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #6366f1, #a855f7);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 20px;
            color: white;
            box-shadow: 0 4px 14px var(--accent-glow);
        }}

        .brand-text h1 {{
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, #ffffff, #c7d2fe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .brand-text p {{
            font-size: 0.75rem;
            color: var(--text-muted);
        }}

        .search-box {{
            position: relative;
            flex: 1;
            max-width: 480px;
            min-width: 260px;
        }}

        .search-icon {{
            position: absolute;
            left: 14px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-dim);
            pointer-events: none;
            width: 16px;
            height: 16px;
        }}

        .search-input {{
            width: 100%;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 10px 16px 10px 40px;
            color: var(--text-main);
            font-size: 0.9rem;
            font-family: inherit;
            outline: none;
            transition: all 0.2s ease;
        }}

        .search-input:focus {{
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 3px var(--accent-glow);
            background: #1e2230;
        }}

        .main-container {{
            max-width: 1280px;
            margin: 0 auto;
            padding: 28px 24px 60px;
        }}

        .categories-section {{
            margin-bottom: 28px;
        }}

        .categories-scroll {{
            display: flex;
            gap: 8px;
            overflow-x: auto;
            padding-bottom: 8px;
            scrollbar-width: thin;
            scrollbar-color: var(--border-color) transparent;
        }}

        .category-pill {{
            background: var(--bg-surface);
            border: 1px solid var(--border-color);
            color: var(--text-muted);
            padding: 7px 14px;
            border-radius: 20px;
            font-size: 0.82rem;
            font-weight: 500;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 6px;
            user-select: none;
        }}

        .category-pill:hover {{
            border-color: var(--accent-primary);
            color: var(--text-main);
        }}

        .category-pill.active {{
            background: var(--accent-primary);
            border-color: var(--accent-primary);
            color: white;
            box-shadow: 0 4px 14px var(--accent-glow);
        }}

        .category-pill .count {{
            font-size: 0.72rem;
            opacity: 0.8;
            background: rgba(255, 255, 255, 0.15);
            padding: 1px 6px;
            border-radius: 10px;
        }}

        .toolbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 24px;
            flex-wrap: wrap;
            gap: 16px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 16px;
        }}

        .stats-text {{
            font-size: 0.9rem;
            color: var(--text-muted);
            font-weight: 500;
        }}

        .sort-control {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.85rem;
            color: var(--text-muted);
        }}

        .sort-select {{
            background: var(--bg-surface);
            border: 1px solid var(--border-color);
            color: var(--text-main);
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 0.85rem;
            font-family: inherit;
            outline: none;
            cursor: pointer;
        }}

        .featured-section {{
            margin-bottom: 36px;
        }}

        .section-title {{
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--text-main);
        }}

        .featured-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
        }}

        .featured-card {{
            background: linear-gradient(145deg, #1e2230, #151822);
            border: 1px solid rgba(99, 102, 241, 0.35);
            border-radius: 16px;
            overflow: hidden;
            text-decoration: none;
            color: var(--text-main);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            flex-direction: column;
            position: relative;
        }}

        .featured-card:hover {{
            transform: translateY(-4px);
            border-color: var(--accent-primary);
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.5), 0 0 20px var(--accent-glow);
        }}

        .featured-badge {{
            position: absolute;
            top: 12px;
            left: 12px;
            background: linear-gradient(135deg, #ef4444, #f97316);
            color: white;
            font-size: 0.7rem;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 6px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            z-index: 2;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.4);
        }}

        .guides-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
            gap: 20px;
        }}

        .guide-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 14px;
            overflow: hidden;
            text-decoration: none;
            color: var(--text-main);
            transition: all 0.25s ease;
            display: flex;
            flex-direction: column;
        }}

        .guide-card:hover {{
            transform: translateY(-3px);
            background: var(--bg-card-hover);
            border-color: var(--accent-primary);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4), 0 0 15px var(--accent-glow);
        }}

        .card-thumb-wrap {{
            position: relative;
            width: 100%;
            aspect-ratio: 16/9;
            background: var(--bg-surface);
            overflow: hidden;
        }}

        .card-thumb {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
            transition: transform 0.3s ease;
        }}

        .guide-card:hover .card-thumb {{
            transform: scale(1.03);
        }}

        .card-thumb-placeholder {{
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #1e1b4b, #311b92);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #818cf8;
            font-weight: 600;
            font-size: 0.85rem;
            padding: 16px;
            text-align: center;
        }}

        .card-body {{
            padding: 16px;
            display: flex;
            flex-direction: column;
            flex: 1;
        }}

        .card-meta {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            margin-bottom: 10px;
            font-size: 0.75rem;
        }}

        .cat-tag {{
            background: var(--badge-bg);
            color: var(--badge-text);
            padding: 3px 10px;
            border-radius: 6px;
            font-weight: 600;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 180px;
        }}

        .card-date {{
            color: var(--text-dim);
            font-weight: 500;
        }}

        .card-title {{
            font-size: 0.95rem;
            font-weight: 600;
            line-height: 1.4;
            color: var(--text-main);
            margin-bottom: 12px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            flex: 1;
        }}

        .card-footer {{
            margin-top: auto;
            font-size: 0.8rem;
            color: var(--accent-secondary);
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 4px;
        }}

        .empty-state {{
            grid-column: 1 / -1;
            text-align: center;
            padding: 60px 20px;
            background: var(--bg-surface);
            border: 1px dashed var(--border-color);
            border-radius: 16px;
        }}

        .empty-state h3 {{
            font-size: 1.1rem;
            margin-bottom: 6px;
            color: var(--text-main);
        }}

        .empty-state p {{
            color: var(--text-muted);
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <header class="site-header">
        <div class="header-inner">
            <a href="./" class="brand">
                <div class="brand-icon">W</div>
                <div class="brand-text">
                    <h1>Weight and See</h1>
                    <p>Video Guides & Resources</p>
                </div>
            </a>
            <div class="search-box">
                <svg class="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                </svg>
                <input type="text" id="searchInput" class="search-input" placeholder="Search 150+ guides by title, model, or topic...">
            </div>
        </div>
    </header>

    <main class="main-container">
        <div class="categories-section">
            <div class="categories-scroll" id="categoriesBar">
                <!-- Dynamically populated category chips -->
            </div>
        </div>

        <!-- Featured / Latest Section -->
        <div class="featured-section" id="featuredSection">
            <h2 class="section-title">✨ Latest Releases</h2>
            <div class="featured-grid" id="featuredGrid">
                <!-- Dynamically populated top 3 guides -->
            </div>
        </div>

        <div class="toolbar">
            <div class="stats-text" id="statsText">Showing all guides</div>
            <div class="sort-control">
                <label for="sortSelect">Sort by:</label>
                <select id="sortSelect" class="sort-select">
                    <option value="newest">Newest First</option>
                    <option value="oldest">Oldest First</option>
                    <option value="az">Title (A-Z)</option>
                </select>
            </div>
        </div>

        <div class="guides-grid" id="guidesGrid">
            <!-- Dynamically populated guide cards -->
        </div>
    </main>

    <script>
        const GUIDES_DATA = {json_payload};

        let currentCategory = "All";
        let searchQuery = "";
        let sortBy = "newest";

        const searchInput = document.getElementById("searchInput");
        const categoriesBar = document.getElementById("categoriesBar");
        const featuredSection = document.getElementById("featuredSection");
        const featuredGrid = document.getElementById("featuredGrid");
        const guidesGrid = document.getElementById("guidesGrid");
        const statsText = document.getElementById("statsText");
        const sortSelect = document.getElementById("sortSelect");

        function getCategoryCounts() {{
            const counts = {{ "All": GUIDES_DATA.length }};
            GUIDES_DATA.forEach(g => {{
                counts[g.category] = (counts[g.category] || 0) + 1;
            }});
            return counts;
        }}

        function buildCategoriesBar() {{
            const counts = getCategoryCounts();
            const categories = ["All", ...Object.keys(counts).filter(c => c !== "All")];
            
            categoriesBar.innerHTML = categories.map(cat => `
                <button class="category-pill ${{cat === currentCategory ? 'active' : ''}}" onclick="setCategory('${{cat}}')">
                    ${{cat}} <span class="count">${{counts[cat]}}</span>
                </button>
            `).join('');
        }}

        function setCategory(cat) {{
            currentCategory = cat;
            buildCategoriesBar();
            render();
        }}

        function buildFeaturedSection() {{
            const latest = [...GUIDES_DATA].slice(0, 3);
            featuredGrid.innerHTML = latest.map(g => `
                <a href="${{g.url}}" class="featured-card">
                    <span class="featured-badge">NEW</span>
                    <div class="card-thumb-wrap">
                        ${{g.hasThumbnail ? 
                            `<img src="./${{g.slug}}/thumbnail.jpg" class="card-thumb" alt="${{g.title}}" loading="lazy">` : 
                            `<div class="card-thumb-placeholder">${{g.title}}</div>`
                        }}
                    </div>
                    <div class="card-body">
                        <div class="card-meta">
                            <span class="cat-tag">${{g.category}}</span>
                            ${{g.date ? `<span class="card-date">${{g.date}}</span>` : ''}}
                        </div>
                        <h3 class="card-title">${{g.title}}</h3>
                        <div class="card-footer">View guide &rarr;</div>
                    </div>
                </a>
            `).join('');
        }}

        function getFilteredAndSortedGuides() {{
            let list = GUIDES_DATA.filter(g => {{
                const matchesCat = (currentCategory === "All") || (g.category === currentCategory);
                const query = searchQuery.toLowerCase().trim();
                const matchesQuery = !query || 
                    g.title.toLowerCase().includes(query) || 
                    g.slug.toLowerCase().includes(query) || 
                    g.category.toLowerCase().includes(query);
                return matchesCat && matchesQuery;
            }});

            if (sortBy === "newest") {{
                list.sort((a, b) => b.datetime.localeCompare(a.datetime));
            }} else if (sortBy === "oldest") {{
                list.sort((a, b) => a.datetime.localeCompare(b.datetime));
            }} else if (sortBy === "az") {{
                list.sort((a, b) => a.title.localeCompare(b.title));
            }}

            return list;
        }}

        function render() {{
            const list = getFilteredAndSortedGuides();

            // Hide featured section if searching or filtering category
            if (currentCategory !== "All" || searchQuery.length > 0) {{
                featuredSection.style.display = "none";
            }} else {{
                featuredSection.style.display = "block";
            }}

            statsText.textContent = `Showing ${{list.length}} of ${{GUIDES_DATA.length}} guides`;

            if (list.length === 0) {{
                guidesGrid.innerHTML = `
                    <div class="empty-state">
                        <h3>No guides found</h3>
                        <p>No guides match your search query "${{searchQuery}}". Try resetting search or category filters.</p>
                    </div>
                `;
                return;
            }}

            guidesGrid.innerHTML = list.map(g => `
                <a href="${{g.url}}" class="guide-card">
                    <div class="card-thumb-wrap">
                        ${{g.hasThumbnail ? 
                            `<img src="./${{g.slug}}/thumbnail.jpg" class="card-thumb" alt="${{g.title}}" loading="lazy">` : 
                            `<div class="card-thumb-placeholder">${{g.title}}</div>`
                        }}
                    </div>
                    <div class="card-body">
                        <div class="card-meta">
                            <span class="cat-tag">${{g.category}}</span>
                            ${{g.date ? `<span class="card-date">${{g.date}}</span>` : ''}}
                        </div>
                        <h3 class="card-title">${{g.title}}</h3>
                        <div class="card-footer">View guide &rarr;</div>
                    </div>
                </a>
            `).join('');
        }}

        searchInput.addEventListener("input", (e) => {{
            searchQuery = e.target.value;
            render();
        }});

        sortSelect.addEventListener("change", (e) => {{
            sortBy = e.target.value;
            render();
        }});

        // Initialize page
        buildCategoriesBar();
        buildFeaturedSection();
        render();
    </script>
</body>
</html>
"""
    return html


if __name__ == "__main__":
    readme = generate_readme()
    readme_path = os.path.join(REPO_DIR, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme)
    
    CATEGORIES = get_all_categorized_guides()
    total = sum(len(c['slugs']) for c in CATEGORIES.values())
    print(f"README.md generated with {total} guides in {len(CATEGORIES)} categories")

    index_html_content = generate_index_html()
    os.makedirs(GUIDES_DIR, exist_ok=True)
    index_html_path = os.path.join(GUIDES_DIR, "index.html")
    with open(index_html_path, "w", encoding="utf-8") as f:
        f.write(index_html_content)
    print(f"guides/index.html generated successfully at {index_html_path}")