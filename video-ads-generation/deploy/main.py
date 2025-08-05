import os
import time
import asyncio
from dotenv import load_dotenv
from typing import Annotated, TypedDict

from utils import (
    get_client,
    ainvoke_llm_async,
    get_current_date,
    start_video_generation,
    wait_for_completion,
    get_video_url
)
from db_utils import log_to_db, init_db
from prompt_library import PROMPT_LIBRARY


# ✅ 类型约束（用于解析结构化 LLM 输出）
class VideoDetails(TypedDict):
    title: str
    prompt: str

import json
from typing import TypedDict

# 定义返回的 VideoDetails 类型
class VideoDetails(TypedDict):
    title: str
    prompt: str

 
import json
async def generate_veo3_video_prompt(client, ad_idea: str, prompt: str) -> VideoDetails:
    print(f"🧠 Generating prompt for idea: '{ad_idea}'")
    
    system_prompt = """
    You are a helpful assistant. Given a creative ad idea and an inspiration prompt,
    return a structured JSON object with:
    - title: title of the video
    - prompt: visual and stylistic prompt used for video generation

    Respond ONLY in this format:
    {
      "title": "...",
      "prompt": "..."
    }
    """
    
    user_message = f"Ad Idea: {ad_idea}\n\nInspiration Prompt:\n{prompt}"

    try:
        # 调用 LLM 异步生成提示词
        # ainvoke_llm_async 现在直接返回一个解析好的字典
        result_dict = await ainvoke_llm_async(
            client=client,
            model="gemini-2.5-flash", # 你日志中用的是 gemini-2.5-flash
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=0.3,
            response_format=VideoDetails
        )
        
        # 检查响应内容 (这是很好的调试习惯)
        if isinstance(result_dict, dict) and 'title' in result_dict:
            print(f"LLM 调用完成，成功解析响应内容：{json.dumps(result_dict, indent=2, ensure_ascii=False)}")
            # 直接返回成功解析后的字典
            return result_dict
        else:
            # 如果返回的不是预期的字典格式，则抛出错误
            print(f"❌ LLM 返回了非预期的格式: {result_dict}")
            raise ValueError("LLM did not return the expected dictionary format.")

    except Exception as e:
        # 捕获来自 ainvoke_llm_async 的异常或本函数内的异常
        print(f"❌ 在提示词生成流程中发生错误: {str(e)}")
        # 返回一个统一的错误格式
        return {"error": "Prompt generation failed", "message": str(e)}

async def run_workflow(inputs):
    log_entry = {
        "title": "",
        "prompt": "",
        "status": "in_progress",
        "created_at": get_current_date(),
        "video_url": None,
        "error": None,
    }

    row_id = None

    try:
        api_key = inputs.get("key")
        if not api_key:
            raise ValueError("❌ API Key is required")

        client = get_client(api_key)

        print(f"🚀 开始运行 workflow，输入参数为: {inputs}")

        # 第一步：生成提示词
        try:
            video_details = await generate_veo3_video_prompt(
                client,
                inputs["ad_idea"],
                inputs["prompt"]
            )
            log_entry["title"] = video_details["title"]
            log_entry["prompt"] = video_details["prompt"]
        except Exception as e:
            log_entry["status"] = "failed"
            log_entry["error"] = f"🧠 Prompt generation failed: {str(e)}"
            row_id = log_to_db(log_entry)
            return {"error": log_entry["error"]}

        row_id = log_to_db(log_entry)
        print(f"📘 Prompt 生成成功，Log ID: {row_id}")

        # 第二步：启动视频任务
        try:
            task = start_video_generation(client, video_details["prompt"])
            log_entry["task_id"] = task.name
        except Exception as e:
            log_entry["status"] = "failed"
            log_entry["error"] = f"🎬 Video generation task failed: {str(e)}"
            log_to_db(log_entry, row_id)
            return {"error": log_entry["error"]}

        log_to_db(log_entry, row_id)
        print(f"🎬 任务启动成功: {task.name}")

        # 第三步：轮询结果
        try:
            result = wait_for_completion(client, task)
        except Exception as e:
            log_entry["status"] = "failed"
            log_entry["error"] = f"⏳ Polling failed: {str(e)}"
            log_to_db(log_entry, row_id)
            return {"error": log_entry["error"]}

        # 第四步：解析视频 URL
        try:
            video_url = get_video_url(result)
            log_entry["status"] = "completed"
            log_entry["video_url"] = video_url
            print(f"✅ 视频生成成功: {video_url}")
        except Exception as e:
            log_entry["status"] = "failed"
            log_entry["error"] = f"📥 Failed to extract video URL: {str(e)}"
            print(log_entry["error"])

        # 最后写入 DB 并返回
        log_to_db(log_entry, row_id)

        if log_entry["status"] == "completed":
            return {
                "title": log_entry["title"],
                "prompt": log_entry["prompt"],
                "video_url": log_entry["video_url"]
            }
        else:
            return {"error": log_entry["error"]}

    except Exception as e:
        # 外部意外错误也记录
        if row_id:
            log_entry["status"] = "failed"
            log_entry["error"] = f"🔥 Unexpected error: {str(e)}"
            log_to_db(log_entry, row_id)
        print(f"🔥 run_workflow 致命错误: {str(e)}")
        return {"error": str(e)}


if __name__ == "__main__":
    load_dotenv()
    init_db()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("❌ GEMINI_API_KEY environment variable not set")

    ad_idea = "I want an ad for the launch of the new Mercedes Formula 1 car"
    prompt = PROMPT_LIBRARY[-1]["prompt"]

    inputs = {
        "ad_idea": ad_idea,
        "prompt": prompt,
        "key": api_key
    }

    asyncio.run(run_workflow(inputs))
