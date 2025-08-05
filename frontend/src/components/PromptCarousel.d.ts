// src/components/PromptCarousel.d.ts

import { FC } from "react";

export interface Prompt {
  id: string;
  name: string;
  prompt: string;
  // 如果还有别的字段也在这里补上
}

export interface PromptCarouselProps {
  promptList: Prompt[];
  selectedPrompt: Prompt | null;
  setSelectedPrompt: (p: Prompt) => void;
  setPrompt: (text: string) => void;
}

declare const PromptCarousel: FC<PromptCarouselProps>;
export default PromptCarousel;
