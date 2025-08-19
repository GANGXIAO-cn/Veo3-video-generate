// src/components/Sidebar.tsx
import React, { useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import AdUnit from "./AdUnit";

const Sidebar: React.FC = () => {
  const [geminiKey, setGeminiKey] = useState("");
  const [message, setMessage] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);

  // 从 Vite 环境变量里读 BASE_URL，打包时会替换
  const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

  const validateKeyFormat = (key: string) => {
    return key.startsWith("AI") && key.length > 30;
  };

  const verifyKeyWithServer = async (key: string): Promise<boolean> => {
    try {
      const res = await fetch(`${API_BASE}/verify-key`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key }),
      });
      if (!res.ok) {
        console.error("服务器返回错误：", res.status, await res.text());
        return false;
      }
      const data = (await res.json()) as { valid: boolean };
      return data.valid === true;
    } catch (err) {
      console.error("服务器验证出错：", err);
      return false;
    }
  };

  const handleSave = async () => {
    if (!geminiKey) {
      setMessage("❌ API Key 不能为空！");
      return;
    }
    if (!validateKeyFormat(geminiKey)) {
      setMessage("❌ API Key 格式无效，应以 AI 开头，长度超过 30 位。");
      return;
    }

    setIsVerifying(true);
    const isValid = await verifyKeyWithServer(geminiKey);
    setIsVerifying(false);

    if (!isValid) {
      setMessage("❌ API Key 验证失败，请检查输入是否正确。");
      return;
    }

    sessionStorage.setItem("geminiApiKey", geminiKey);
    window.dispatchEvent(new Event("storage")); // 通知 MainContent 读取新 Key
    setMessage("✅ API Key 已成功保存！");
  };

  return (
    <div className="w-64 bg-gray-800 text-white p-6">
      <h2 className="text-xl font-bold mb-6">🔑 API 配置</h2>

      <label className="block text-sm mb-1">输入 Gemini API Key</label>
      <div className="relative mb-2">
        <input
          type={showKey ? "text" : "password"}
          className="w-full p-2 pr-10 rounded bg-gray-700 text-white"
          placeholder="请输入你的 Gemini API Key"
          value={geminiKey}
          onChange={(e) => {
            setGeminiKey(e.target.value);
            setMessage("");
          }}
        />
        <button
          type="button"
          className="absolute right-2 top-2 text-gray-400 hover:text-white"
          onClick={() => setShowKey((p) => !p)}
        >
          {showKey ? <EyeOff size={18} /> : <Eye size={18} />}
        </button>
      </div>

      <button
        onClick={handleSave}
        disabled={isVerifying}
        className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded mb-2 disabled:opacity-50"
      >
        {isVerifying ? "正在验证..." : "保存"}
      </button>

      {message && (
        <p
          className={`text-sm ${
            message.startsWith("✅") ? "text-green-400" : "text-red-400"
          }`}
        >
          {message}
        </p>
      )}
       <div className="mb-4">
          <AdUnit
            adSlot="XXXXX" // ← 第二个广告的 slot
            className="w-full"
          />
        </div>
    </div>
     
     
  );
};

export default Sidebar;
