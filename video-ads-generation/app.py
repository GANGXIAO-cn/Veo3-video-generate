# app.py
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from prompt_library import PROMPT_LIBRARY
from dotenv import load_dotenv
import os, json, traceback, asyncio, requests
from main import run_workflow
from google import genai

# 如果你还有 google.genai.types 用到，就保留下面这一行
# from google.genai import types

load_dotenv()

app = Flask(__name__)
CORS(app)  # 允许跨域：前端 fetch("/api/...") 时不用写完整地址

# ——— 提示词相关 —————————————————————————————————————————————
@app.route("/api/prompt-library", methods=["GET"])
def get_prompt_library():
    return jsonify(PROMPT_LIBRARY)

@app.route("/api/prompts", methods=["GET"])
def get_prompts():
    prompts = []
    for idx, item in enumerate(PROMPT_LIBRARY):
        prompts.append({
            "id": str(idx),
            "name": item.get("name_cn", item["name"]),
            "name_cn": item.get("name_cn", item["name"]),
            "description": item.get("description", ""),
            "prompt": item.get("prompt", ""),
            "video_url": item.get("video_url", "")
        })
    return jsonify(prompts)

# ——— 视频生成接口 —————————————————————————————————————————————
@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json()
    inputs = {
        "ad_idea":    data.get("ad_idea"),
        "prompt":     data.get("prompt"),
        "model":      data.get("model"),
        "resolution": data.get("resolution"),
        "key":        data.get("key"),
    }
    print("📩 收到参数：", json.dumps(inputs, ensure_ascii=False, indent=2))

    try:
        result = asyncio.run(run_workflow(inputs))
        print("✅ run_workflow 返回：", result)

        if not result or not result.get("video_url"):
            raise RuntimeError(f"视频生成失败，后端返回：{result}")

        # 直接返回 { title, prompt, video_url }
        return jsonify(result)

    except Exception as e:
        print("🔥 生成接口异常：", e)
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# ——— 视频流代理 —————————————————————————————————————————————
@app.route("/api/video/<string:file_name>", methods=["GET"])
def stream_video(file_name):
    api_key = request.headers.get("X-Goog-Api-Key")
    if not api_key:
        return jsonify({"error": "API Key 缺失"}), 401

    google_url = (
        f"https://generativelanguage.googleapis.com/"
        f"v1beta/files/{file_name}:download?alt=media"
    )
    try:
        r = requests.get(google_url, headers={"x-goog-api-key": api_key}, stream=True)
        if r.status_code != 200:
            return jsonify({"error": "Google 拉流失败", "status": r.status_code}), r.status_code

        return Response(r.iter_content(1024*1024),
                        content_type=r.headers.get("Content-Type", "application/octet-stream"))
    except Exception as e:
        print("❌ 代理流异常：", e)
        traceback.print_exc()
        return jsonify({"error": "内部错误"}), 500

# ——— API Key 验证 —————————————————————————————————————————————
@app.route("/api/verify-key", methods=["POST"])
def verify_key():
    key = request.get_json().get("key", "")
    try:
        client = genai.Client(api_key=key)
        # 简单调用，检验是否合法
        resp = client.models.generate_content(model="gemini-2.0-flash-lite", contents="hi")
        valid = bool(resp and resp.text)
    except Exception:
        valid = False
    return jsonify({"valid": valid})

if __name__ == "__main__":
    # 生产环境用 gunicorn 或类似方案；本地调试这样就行
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5001)), debug=True)
