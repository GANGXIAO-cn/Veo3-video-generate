import time
import asyncio
import json
from google import genai
from google.genai import types
from datetime import datetime
import re # <--- 新增：导入正则表达式模块
# ✅ 初始化客户端（每次传入 key）
def get_client(api_key):
    print("🔑 正在初始化 Gemini 客户端...")
    return genai.Client(api_key=api_key)

# ✅ 启动视频生成任务
def start_video_generation(client, prompt: str):
    print("🎬 正在发起视频生成任务...")
    operation = client.models.generate_videos(
        model="veo-3.0-generate-preview",
        prompt=prompt,
        config=types.GenerateVideosConfig(
            negative_prompt="low quality, cartoon",
            person_generation="allow_all"
        ),
    )
    print(f"📨 任务已提交，任务 ID: {operation.name}")
    return operation

# ✅ 轮询等待任务完成
def wait_for_completion(client, operation, interval: int = 10):
    print("⏳ 开始轮询等待任务完成...")
    if isinstance(operation, str):
        operation = types.GenerateVideosOperation(name=operation)

    while not operation.done:
        print("⌛ 正在生成中...等待下一轮轮询")
        time.sleep(interval)
        operation = client.operations.get(operation)

    print("✅ 视频生成完成！")
    return operation.response

# ✅ 直接返回视频 URL
def get_video_url(video_response):
    print("🌐 获取视频链接...")
    video = video_response.generated_videos[0]
    print(f"🎞️ 视频链接为: {video.video.uri}")
    return video.video.uri

# ✅ LLM 同步调用
from google.genai.types import GenerationConfig

def ainvoke_llm(client, model, system_prompt, user_message, response_format=None, temperature=0.3):
    print("🧠 正在调用 LLM 生成提示词...")

    prompt = system_prompt.strip() + "\n\n" + user_message.strip()

    response = client.models.generate_content(
        model=model,
        contents=prompt
    )

    text = response.text.strip()

    if response_format:
        try:
            return json.loads(text)
        except Exception as e:
            print("❌ JSON parse error:", e)
            print("Raw output:", text)
            raise e

    return text



# ✅ 异步封装
 
async def ainvoke_llm_async(client, model, system_prompt, user_message, temperature=0.3, response_format=None):
    """
    异步调用 LLM 接口生成提示词，并解析返回结果
    """
    prompt = system_prompt.strip() + "\n\n" + user_message.strip()

    print(f"🧠 正在调用 LLM 生成提示词，Model: {model}, 输入: {user_message}")

    try:
        start_time = time.time()

        response = await asyncio.to_thread(
            lambda: client.models.generate_content(
                model=model,
                contents=prompt
            )
        )

        print(f"🕒 LLM 调用完成，耗时 {time.time() - start_time:.2f} 秒")

        raw_response = response.text.strip()
        print(f"LLM 原始响应：{raw_response}")

        if not raw_response:
            raise ValueError("LLM 返回空内容")

        # --- START: 核心修正逻辑 ---
        # 使用正则表达式从可能包含Markdown标记的文本中提取JSON对象
        # re.DOTALL 标志让 '.' 可以匹配包括换行符在内的任意字符
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)

        if not json_match:
            # 如果找不到被花括号包裹的内容，说明返回格式严重错误
            print(f"❌ 在LLM响应中未找到有效的JSON对象。原始响应: {raw_response}")
            raise ValueError("在LLM响应中未找到有效的JSON对象")
            
        json_string = json_match.group(0)
        # --- END: 核心修正逻辑 ---

        # 现在，我们解析这个被清理过的、纯净的JSON字符串
        try:
            result = json.loads(json_string)
        except json.JSONDecodeError as e:
            print(f"❌ 清理后仍然无法解析JSON: {e}")
            print(f"待解析的字符串: {json_string}")
            raise ValueError("JSON 解析错误，LLM 返回数据无法解析为 JSON")

        if not isinstance(result, dict) or 'title' not in result or 'prompt' not in result:
            raise ValueError(f"LLM 返回的数据格式不正确: {result}")

        print(f"📘 生成的提示词: {result}")
        return result

    except Exception as e:
        print(f"❌ 调用 LLM 生成提示词时发生错误: {str(e)}")
        # 为了更好地调试，可以考虑重新抛出异常或返回更详细的错误信息
        # return {"error": f"LLM 生成提示词失败: {str(e)}"}
        raise  # 重新抛出异常，让上层调用者知道确切的错误

# ✅ 时间戳
def get_current_date():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"🕒 当前时间: {now}")
    return now
