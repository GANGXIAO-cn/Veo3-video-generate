// src/components/MainContent.tsx
import { useState, useEffect, useRef } from "react";
import PromptCarousel from "./PromptCarousel"; // 路径按你的目录调整

// 从 Vite 环境变量里读取后端基址（在 .env.production 中设置 VITE_API_BASE_URL），
// 如果为空，则回退到当前域的 /api
const rawBase = import.meta.env.VITE_API_BASE_URL || "";
const API_BASE = rawBase.replace(/\/+$/, "") || "/api";

export default function MainContent() {
  const [adIdea, setAdIdea] = useState("");
  const [prompt, setPrompt] = useState("");
  const [model, setModel] = useState("veo-3.0-fast-generate-preview");
  const [resolution, setResolution] = useState("720p");
  const [promptList, setPromptList] = useState<any[]>([]);
  const [selectedPrompt, setSelectedPrompt] = useState<any>(null);
  const [apiKey, setApiKey] = useState("");
  const [videoResult, setVideoResult] = useState<{
    title: string;
    prompt: string;
    video_url: string;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const resultRef = useRef<HTMLDivElement>(null);

  // 加载可用模板
  useEffect(() => {
    fetch(`${API_BASE}/prompts`)
      .then((res) => res.json())
      .then(setPromptList)
      .catch((err) => console.error("获取 prompt 列表失败:", err));
  }, []);

  // 监听并显示存储的 API Key
  useEffect(() => {
    const loadKey = () => {
      setApiKey(sessionStorage.getItem("geminiApiKey") || "");
    };
    loadKey();
    window.addEventListener("storage", loadKey);
    return () => window.removeEventListener("storage", loadKey);
  }, []);

  // 生成完成后滚动到结果区
  useEffect(() => {
    if (videoResult) {
      resultRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [videoResult]);

const handleGenerate = async () => {
  const key = sessionStorage.getItem("geminiApiKey");
  if (!key) {
    return alert("❌ 请先输入并验证 API Key！");
  }
  if (!adIdea) {
    return alert("❌ 请填写你的广告创意");
  }
  if (!selectedPrompt) {
    return alert("❌ 请选择一个提示词模板");
  }

  setLoading(true);
  setVideoResult(null);

  try {
    // 1. 发起生成任务（不管状态码，先拿到 JSON）
    const genRes = await fetch(`${API_BASE}/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ad_idea: adIdea,
        prompt,
        model,
        resolution,
        key,
      }),
    });
    const result = await genRes.json();

    // 2. 如果 HTTP 非 2xx 或返回了结构化 error，就显示细化错误
    if (!genRes.ok || result.error) {
      const err = result.error || {
        status: `HTTP_${genRes.status}`,
        description: `服务器返回了状态码 ${genRes.status}`,
        solution: "请稍后重试或联系管理员。",
      };
      return alert(
        `❌ ${err.status}：${err.description}\n💡 解决方案：${err.solution}`
      );
    }

    // 3. 成功拿到 video_url，开始代理拉流
    const parts = result.video_url.split("/");
    const fileName = parts[parts.length - 1].split(":")[0];
    const vidRes = await fetch(`${API_BASE}/video/${fileName}`, {
      headers: { "X-Goog-Api-Key": key },
    });
    if (!vidRes.ok) {
      throw new Error("视频代理拉流失败");
    }
    const blob = await vidRes.blob();

    // 4. 更新状态，展示视频
    setVideoResult({
      title: result.title,
      prompt: result.prompt,
      video_url: URL.createObjectURL(blob),
    });
  } catch (e: any) {
    console.error("操作流程出错:", e);
    alert("❌ 操作失败: " + e.message);
  } finally {
    setLoading(false);
  }
};


  return (
    <div className="flex-1 bg-gray-900 text-white p-8 overflow-y-auto">
      {/* 标题 & API Key */}
      <h1 className="text-3xl font-bold mb-6">🎬 AI 视频广告生成器</h1>
      <div className="mb-4 text-sm text-gray-400">
        当前已保存的 API Key:{" "}
        <span className="text-yellow-300">{apiKey || "未设置"}</span>
      </div>
      <p className="mb-4 text-gray-300">
        请输入 API Key 并选择模型与分辨率，点击按钮生成视频。
       
      </p>
      <p className="mb-4 text-gray-300"> 注意！veo3模型属于付费层级模型，只有绑定支付方式后才可以调用，生成过程中会附带调用gemini 2.0模型进行提示词处理，所以每次生成会产生一些额外费用。</p>

      {/* 输入区域 + 模板轮播 + 配置 + 生成按钮 */}
      <div className="bg-gray-800 rounded-lg p-6 shadow-md mb-6">
        {/* 广告创意 */}
        <div className="relative mb-6">
          <h2 className="text-2xl font-bold mb-2">💡 广告创意</h2>
          <textarea
            value={adIdea}
            onChange={(e) => setAdIdea(e.target.value)}
            placeholder="例如：新款 Mercedes F1 赛车发布广告"
            rows={6}
            className="w-full p-3 rounded-md bg-gray-800 text-white border border-gray-700 focus:ring-2 focus:ring-blue-500 resize-y"
          />
          <p className="absolute bottom-2 right-3 text-xs text-gray-400">
            按 <kbd className="font-mono">⌘</kbd>+<kbd className="font-mono">Enter</kbd> 生成
          </p>
        </div>

        {/* 模板轮播：始终在按钮上方 */}
        <PromptCarousel
          promptList={promptList}
          selectedPrompt={selectedPrompt}
          setSelectedPrompt={setSelectedPrompt}
          setPrompt={setPrompt}
        />

        {/* 模型 & 分辨率 */}
        <div className="mb-4 grid grid-cols-2 gap-4">
          <div>
            <label className="block mb-2 text-sm">选择模型</label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full p-2 bg-gray-700 rounded text-white"
            >
              <option value="veo-3.0-fast-generate-preview">Veo 3.0 fast</option>
              <option value="veo-3.0-generate-preview">Veo 3.0</option>
              <option value="veo-2.0-generate-001">Veo 2.0</option>
            </select>
          </div>
          <div>
            <label className="block mb-2 text-sm">分辨率</label>
            <select
              value={resolution}
              onChange={(e) => setResolution(e.target.value)}
              className="w-full p-2 bg-gray-700 rounded text-white"
            >
              <option value="720p">720p</option>
              <option value="1080p">1080p</option>
            </select>
          </div>
        </div>

        {/* 生成按钮 */}
        <button
          onClick={handleGenerate}
          disabled={loading}
          className={`w-full py-2 rounded font-bold ${
            loading ? "bg-blue-400 cursor-not-allowed opacity-75" : "bg-blue-600 hover:bg-blue-700"
          }`}
        >
          {loading ? "⏳ 生成中..." : "🚀 生成视频"}
        </button>
      </div>

      {/* 结果区（包含下载提示、标题、说明、视频播放器） */}
      <div ref={resultRef} className="mt-6 border-t border-gray-700 pt-4">
        <h2 className="text-xl font-semibold mb-2">🎞️ 生成结果</h2>
        {loading ? (
          <div className="text-gray-400">⏳ 正在生成视频，请稍候...</div>
        ) : videoResult ? (
          <div className="bg-gray-800 p-4 rounded space-y-3">
            <p className="text-sm text-gray-400">
              点击视频右下角三个点下载，或：
            </p>
            <a
              href={videoResult.video_url}
              download="ad_video.mp4"
              className="text-blue-400 hover:underline"
            >
              💾 直接下载视频
            </a>
            <div className="text-lg text-yellow-300 font-bold">
              {videoResult.title}
            </div>
            <div className="text-sm text-gray-400">
              {videoResult.prompt}
            </div>
            <video
              controls
              className="mt-3 rounded shadow-md w-full"
              src={videoResult.video_url}
            >
              Your browser does not support the video tag.
            </video>
          </div>
        ) : (
          <div className="bg-gray-800 p-4 rounded text-gray-500">
            尚未生成任何视频
          </div>
        )}
      </div>
    </div>
  );
}
