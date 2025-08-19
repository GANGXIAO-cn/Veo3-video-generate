// src/components/AdUnit.tsx
import { useEffect, useRef } from "react";

declare global {
  interface Window {
    adsbygoogle: any[];
  }
}

type Props = {
  adSlot: string;                  // 你的广告单元 ID（数字）
  className?: string;
  // 可选：固定尺寸位（例如 320x100、728x90），不填则用自适应
  style?: React.CSSProperties;
};

export default function AdUnit({ adSlot, className, style }: Props) {
  const insRef = useRef<HTMLModElement | null>(null);

  useEffect(() => {
    // 某些广告拦截器可能阻止 adsbygoogle 变量，需 try/catch
    try {
      if (window && (window.adsbygoogle = window.adsbygoogle || [])) {
        window.adsbygoogle.push({});
      }
    } catch (e) {
      // 静默失败即可
    }
  }, [adSlot]);

  return (
    <ins
      ref={insRef as any}
      className={`adsbygoogle ${className || ""}`}
      style={style || { display: "block" }}
      data-ad-client="XXXXX"     // ← 换成你的 Publisher ID
      data-ad-slot={adSlot}                     // ← 换成你的广告单元 ID
      data-ad-format="auto"
      data-full-width-responsive="true"
    />
  );
}
