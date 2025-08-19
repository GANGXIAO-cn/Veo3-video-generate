# app.py
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from prompt_library import PROMPT_LIBRARY
from dotenv import load_dotenv
import os, json, traceback, asyncio, requests
from main import run_workflow
from google import genai
import re
import threading, time
from datetime import datetime, timezone

# —— 留言板存储（可改成环境变量）——
FEEDBACK_STORE = os.getenv("FEEDBACK_STORE", "feedback_store.json")
FEEDBACK_LOCK = threading.Lock()

# 简单的按 IP 限流：同一 IP 60 秒内最多 1 次
RATE_LIMIT_WINDOW_SEC = 60
_ip_last_post = {}

# 如果你还有 google.genai.types 用到，就保留下面这一行
# from google.genai import types
# 1. 错误映射表
ERROR_MAPPING = {
    'INVALID_ARGUMENT': {
        'http_code': 400,
        'status': 'INVALID_ARGUMENT',
        'description': '请求正文格式不正确。',
        'example': '您的请求中存在拼写错误或缺少必填字段。',
        'solution': '如需了解请求格式、示例和支持的版本，请参阅 API 参考文档。如果使用较新 API 版本中的功能，但端点版本较旧，可能会导致错误。'
    },
    'FAILED_PRECONDITION': {
        'http_code': 400,
        'status': 'FAILED_PRECONDITION',
        'description': 'Gemini API 免费层级尚未在您所在的国家/地区推出。请在 Google AI Studio 中为您的项目启用结算功能。',
        'example': '您正在不受支持免费层级的区域中发出请求，并且尚未在 Google AI Studio 中为项目启用结算功能。',
        'solution': '如需使用 Gemini API，您需要使用 Google AI Studio 设置付费方案。'
    },
    'PERMISSION_DENIED': {
        'http_code': 403,
        'status': 'PERMISSION_DENIED',
        'description': '您的 API 密钥不具备所需权限。',
        'example': '您使用的 API 密钥有误；您尝试使用经过调优的模型，但未通过适当的身份验证。',
        'solution': '检查您的 API 密钥是否已设置且拥有适当的访问权限。请务必完成适当的身份验证，才能使用调优后的模型。'
    },
    'NOT_FOUND': {
        'http_code': 404,
        'status': 'NOT_FOUND',
        'description': '找不到所请求的资源。',
        'example': '找不到您的请求中引用的图片、音频或视频文件。',
        'solution': '检查您的请求中所有参数对于您的 API 版本是否有效。'
    },
    'RESOURCE_EXHAUSTED': {
        'http_code': 429,
        'status': 'RESOURCE_EXHAUSTED',
        'description': '您已超出速率限制。',
        'example': '您在使用免费层级的 Gemini API 时，每分钟发送的请求过多。',
        'solution': '验证您是否在模型的速率限制范围内。如有需要，请申请增加配额。'
    },
    'INTERNAL': {
        'http_code': 500,
        'status': 'INTERNAL',
        'description': 'Google 方面出现了意外错误。',
        'example': '您的输入内容过长。',
        'solution': '减少输入上下文，或暂时切换到其他模型（例如从 Gemini 1.5 Pro 切换到 Gemini 1.5 Flash），看看是否有效。或者稍等片刻，然后重试您的请求。'
    },
    'UNAVAILABLE': {
        'http_code': 503,
        'status': 'UNAVAILABLE',
        'description': '服务可能暂时过载或关闭。',
        'example': '服务暂时容量不足。',
        'solution': '暂时切换到其他模型，或者稍后重试；如果问题持续，请使用 Google AI Studio 中的反馈按钮报告问题。'
    },
    'DEADLINE_EXCEEDED': {
        'http_code': 504,
        'status': 'DEADLINE_EXCEEDED',
        'description': '服务无法在截止期限内完成处理。',
        'example': '您的提示（或上下文）过大，无法及时处理。',
        'solution': '在客户端请求中设置更长的超时，以避免此错误。'
    },
}

load_dotenv()

app = Flask(__name__)
CORS(app)  # 允许跨域：前端 fetch("/api/...") 时不用写完整地址
def parse_google_error(err_str: str) -> dict:
    """
    从类似 "400 INVALID_ARGUMENT" 的片段提取 code 和 status，
    并在 ERROR_MAPPING 中查找对应的描述信息。
    """
    m = re.search(r'(\d{3})\s+([A-Z_]+)', err_str)
    if not m:
        # 无法解析时，返回最基础的格式
        return {
            'http_code': 500,
            'status': 'UNKNOWN_ERROR',
            'description': '未知错误',
            'example': err_str,
            'solution': '请联系管理员或稍后重试。'
        }
    code = int(m.group(1))
    status = m.group(2)
    info = ERROR_MAPPING.get(status)
    if not info:
        return {
            'http_code': code,
            'status': status,
            'description': 'Google API 返回未识别的错误类型。',
            'example': err_str,
            'solution': '请检查错误详情，或联系管理员。'
        }
    return info

#————留言板——————
def _load_feedback():
    if not os.path.exists(FEEDBACK_STORE):
        return []
    try:
        with open(FEEDBACK_STORE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _save_feedback(items):
    with open(FEEDBACK_STORE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def _now_iso():
    return datetime.now(timezone.utc).isoformat()

def _sanitize_text(s: str, max_len: int):
    # 基础清洗：去掉首尾空白、限制长度
    s = (s or "").strip()
    if len(s) > max_len:
        s = s[:max_len]
    return s
# ——— 公开留言板 —————————————————————————————————————————————
@app.route("/api/feedback", methods=["GET"])
def list_feedback():
    """公开获取留言列表（最新在前）"""
    with FEEDBACK_LOCK:
        items = _load_feedback()
    # 按时间倒序
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return jsonify(items)

@app.route("/api/feedback", methods=["POST"])
def post_feedback():
    """发布留言（公开，不需要登录）"""
    # 速率限制（按 IP）
    ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "0.0.0.0"
    now = time.time()
    last = _ip_last_post.get(ip, 0)
    if now - last < RATE_LIMIT_WINDOW_SEC:
        return jsonify({"error": "提交过于频繁，请稍后再试。"}), 429

    try:
        data = request.get_json(force=True) or {}
    except Exception:
        return jsonify({"error": "请求体需为 JSON"}), 400

    nickname = _sanitize_text(data.get("nickname", "匿名用户"), 24) or "匿名用户"
    message  = _sanitize_text(data.get("message", ""), 800)

    if not message:
        return jsonify({"error": "message 不能为空"}), 400

    item = {
        "id": os.urandom(12).hex(),
        "nickname": nickname,
        "message": message,
        "created_at": _now_iso(),   # ISO 时间，前端可直接 toLocaleString()
    }

    with FEEDBACK_LOCK:
        items = _load_feedback()
        items.append(item)
        _save_feedback(items)

    _ip_last_post[ip] = now
    return jsonify(item), 201
# ——— 管理端留言板（需要 API Key） —————————————————————————————

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

        # 如果后端明确返回了 error 字段，则按我们定义的映射细化后返回
        if isinstance(result, dict) and result.get("error"):
            err_info = parse_google_error(result["error"])
            return jsonify({"error": err_info}), err_info['http_code']

        # 正常流程：必须包含 video_url
        if not result or not result.get("video_url"):
            return jsonify({
                "error": {
                    "http_code": 500,
                    "status": "UNKNOWN_ERROR",
                    "description": "视频生成失败，未返回有效的 video_url。",
                    "example": str(result),
                    "solution": "请稍后重试或联系管理员。"
                }
            }), 500

        return jsonify(result)

    except Exception as e:
        # 捕获其他异常，统一按 500 返回
        print("🔥 生成接口异常：", e)
        traceback.print_exc()
        return jsonify({
            "error": {
                "http_code": 500,
                "status": "SERVER_EXCEPTION",
                "description": "服务器内部异常。",
                "example": str(e),
                "solution": "请稍后重试，或查看后端日志进行排查。"
            }
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
