"use client";

import { Copy, Check } from "lucide-react";
import { useState } from "react";
import { CaptionResult } from "@/lib/types";

interface Props {
  result: CaptionResult;
}

export default function CaptionCard({ result }: Props) {
  const [copied, setCopied] = useState(false);

  const fullText = `${result.caption}\n\n${result.hashtags.map((h) => `#${h}`).join(" ")}`;

  const copy = async () => {
    await navigator.clipboard.writeText(fullText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-zinc-900 rounded-2xl p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
          Caption
        </p>
        <button
          onClick={copy}
          className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg
            bg-zinc-800 hover:bg-zinc-700 text-zinc-300 hover:text-white
            border border-zinc-700 transition-all duration-150"
        >
          {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          {copied ? "Copied!" : "Copy all"}
        </button>
      </div>

      <p className="text-white text-sm leading-relaxed whitespace-pre-wrap">
        {result.caption}
      </p>

      <div className="flex flex-wrap gap-2">
        {result.hashtags.map((tag) => (
          <span
            key={tag}
            className="text-xs px-2.5 py-1 rounded-full
              bg-purple-500/10 text-purple-300 border border-purple-500/20"
          >
            #{tag}
          </span>
        ))}
      </div>

      <p className="text-xs text-zinc-600 italic border-t border-zinc-800 pt-3">
        {result.style_notes}
      </p>
    </div>
  );
}
