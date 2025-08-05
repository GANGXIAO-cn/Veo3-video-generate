import React, { useState, useEffect, useRef } from "react";
import { ChevronLeft, ChevronRight, Copy, Check } from "lucide-react";

export default function PromptCarousel({ promptList, selectedPrompt, setSelectedPrompt, setPrompt }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const promptsPerPage = 3;
  const totalItems = promptList.length;
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (promptList.length > 0 && !selectedPrompt) {
      setSelectedPrompt(promptList[0]);
      setPrompt(promptList[0].prompt);
    }
  }, [promptList, selectedPrompt, setPrompt, setSelectedPrompt]);

  useEffect(() => {
    setExpanded(false);
  }, [selectedPrompt?.id]);

  if (!promptList || promptList.length === 0) {
    return <div className="text-gray-400 text-center my-4">暂无可用模板，请稍后再试。</div>;
  }

  const handleSelect = (item) => {
    setSelectedPrompt(item);
    setPrompt(item.prompt);
  };

  const handleNext = () => {
    setCurrentIndex((prev) => (prev + promptsPerPage) % totalItems);
  };

  const handlePrev = () => {
    setCurrentIndex((prev) => (prev - promptsPerPage + totalItems) % totalItems);
  };

  const getVisiblePrompts = () => {
    const visible = [];
    for (let i = 0; i < promptsPerPage; i++) {
      const index = (currentIndex + i) % totalItems;
      visible.push(promptList[index]);
    }
    return visible;
  };

  const visiblePrompts = getVisiblePrompts();
  const totalPages = Math.ceil(promptList.length / promptsPerPage);
  const currentPage = Math.floor(currentIndex / promptsPerPage);

  return (
    <div className="mb-6 w-full">
      <h2 className="text-xl font-bold mb-2">🎨 选择灵感模板</h2>
      <div className="mb-4 text-sm text-gray-400">请选择您要参考的广告模板</div>
      <div className="relative w-full">
        <div className="flex items-center gap-2 mb-2 w-full">
          <button onClick={handlePrev} className="p-3 text-white hover:text-blue-400 bg-gray-700 rounded-full shadow-lg">
            <ChevronLeft size={28} />
          </button>
          <div className="flex gap-4 overflow-hidden flex-1 justify-between items-stretch">
            {visiblePrompts.map((item) => (
              <PromptCard
                key={item.id}
                item={item}
                selected={selectedPrompt?.id === item.id}
                onSelect={handleSelect}
              />
            ))}
          </div>
          <button onClick={handleNext} className="p-3 text-white hover:text-blue-400 bg-gray-700 rounded-full shadow-lg">
            <ChevronRight size={28} />
          </button>
        </div>
        <div className="flex justify-center mt-2 gap-2">
          {Array.from({ length: totalPages }).map((_, i) => (
            <span
              key={i}
              className={`w-2 h-2 rounded-full ${currentPage === i ? "bg-white" : "bg-gray-500"}`}
            ></span>
          ))}
        </div>
      </div>

      {selectedPrompt && (
        <div className="mt-4 bg-gray-900 p-4 rounded-md">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-lg font-semibold text-white cursor-pointer select-none w-full text-left"
          >
            📋 选中模板提示词详情 {expanded ? "▲" : "▼"}
          </button>
          {expanded && (
            <div className="mt-4 bg-gray-800 p-4 rounded shadow relative">
              <p className="mb-1 text-yellow-400">
                <span className="mr-1">🎯</span>
                {selectedPrompt.name_cn || selectedPrompt.name}
              </p>
              <p className="mb-2 text-sm text-gray-400">
                <strong className="text-white">说明：</strong> {selectedPrompt.description}
              </p>
              <PromptObjectRenderer data={selectedPrompt.prompt} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function PromptCard({ item, selected, onSelect }) {
  const videoRef = useRef(null);

  useEffect(() => {
    if (selected) {
      videoRef.current?.play();
    } else {
      videoRef.current?.pause();
      videoRef.current.currentTime = 0;
    }
  }, [selected]);

  return (
    <div
      onClick={() => onSelect(item)}
      className={`w-full flex-1 min-w-0 border rounded-lg overflow-hidden cursor-pointer transition-all duration-200 ${selected ? "border-blue-500 ring-2 ring-blue-500" : "border-gray-700"}`}
    >
      <div className="relative aspect-video w-full">
        <video
          ref={videoRef}
          src={item.video_url}
          className="w-full h-full object-cover"
          muted
          loop
          playsInline
          preload="metadata"
          controls={selected}
        />
      </div>
      <div className="p-3 bg-gray-800">
        <h3 className="text-lg font-semibold text-white">{item.name_cn}</h3>
        <p className="text-sm text-gray-400 mt-1 whitespace-pre-line">{item.description}</p>
      </div>
    </div>
  );
}

function PromptObjectRenderer({ data, level = 0 }) {
  if (typeof data !== 'object' || data === null) {
    return <PromptRow label="value" value={data} level={level} />;
  }

  const entries = Array.isArray(data) ? data.map((v, i) => [i, v]) : Object.entries(data);
  return (
    <div className="space-y-1">
      {entries.map(([key, val]) => (
        <PromptRow key={key} label={String(key)} value={val} level={level} />
      ))}
    </div>
  );
}

function PromptRow({ label, value, level }) {
  const [hover, setHover] = useState(false);
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(
        typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)
      );
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    } catch (err) {
      console.error('Copy failed', err);
    }
  };

  const isObject = typeof value === 'object' && value !== null;

  return (
    <div
      className="group flex flex-col text-sm text-yellow-400 font-mono"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      <div className="flex items-start gap-2">
        <span className="min-w-[100px] text-white font-mono">{label}:</span>
        <span className="flex-1 break-words">
          {isObject ? (
            <span
              onClick={() => setExpanded(!expanded)}
              className="cursor-pointer text-yellow-300 hover:text-yellow-200"
            >
              {expanded ? '{…}' : '{…}'}
            </span>
          ) : (
            String(value)
          )}
        </span>
        {hover && (
          copied ? (
            <Check size={14} className="text-green-400" />
          ) : (
            <Copy size={14} className="text-gray-400 hover:text-white cursor-pointer" onClick={handleCopy} />
          )
        )}
      </div>
      {expanded && isObject && (
        <div className="pl-4 border-l border-gray-600 mt-1">
          <PromptObjectRenderer data={value} level={level + 1} />
        </div>
      )}
    </div>
  );
}