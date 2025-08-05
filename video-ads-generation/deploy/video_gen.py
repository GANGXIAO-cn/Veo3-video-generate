import os
import time
from google import genai

from dotenv import load_dotenv

load_dotenv()



client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def start_video_generation(prompt: str):
    operation = client.models.generate_videos(
        model="veo-3.0-generate-preview",
        prompt=prompt,
    )
    return operation.name  # 返回任务 ID

def wait_for_completion(task_id: str, interval: int = 10):
    # 使用 operation.name 恢复对象
    operation = genai.types.GenerateVideosOperation(name=task_id)

    while not operation.done:
        print("⌛ 正在等待视频生成完成...")
        time.sleep(interval)
        operation = client.operations.get(operation)

    return operation.response  # 视频生成完成后返回结果
