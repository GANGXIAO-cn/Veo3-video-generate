
import Sidebar from "./components/Sidebar";
import MainContent from "./components/MainContent";

import { useEffect } from "react";



export default function App() {
  useEffect(() => {
    const alreadyCleared = sessionStorage.getItem("keyCleared");

    if (!alreadyCleared) {
      localStorage.removeItem("geminiApiKey");       // 清除 key
      sessionStorage.setItem("keyCleared", "true");  // 标记已清除
    }
  }, []);
  return (
    <div className="flex min-h-screen bg-gray-900 text-white">
      <Sidebar />
      <MainContent />
    </div>
  );
}