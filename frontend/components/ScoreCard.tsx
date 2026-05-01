"use client";

import { CheckCircle, XCircle, ChevronDown } from "lucide-react";
import { useState } from "react";
import { EditParams, ScoreResult } from "@/lib/types";

function scoreColor(score: number) {
  if (score >= 7) return "text-emerald-400";
  if (score >= 4.5) return "text-amber-400";
  return "text-red-400";
}

function scoreRing(score: number) {
  if (score >= 7) return "stroke-emerald-400";
  if (score >= 4.5) return "stroke-amber-400";
  return "stroke-red-400";
}

function formatLabel(score: number) {
  if (score >= 7) return "Great shot";
  if (score >= 5.5) return "Good shot";
  if (score >= 4) return "Needs work";
  return "Skip it";
}

function formatValue(key: keyof EditParams, value: number | string) {
  if (key === "crop_ratio") return value as string;
  if (key === "rotation") return `${value}°`;
  const n = value as number;
  if (n === 0) return "0";
  return n > 0 ? `+${n}` : `${n}`;
}

function valueColor(key: keyof EditParams, value: number | string) {
  if (key === "crop_ratio" || key === "rotation") return "text-zinc-300";
  const n = value as number;
  if (n > 0) return "text-emerald-400";
  if (n < 0) return "text-red-400";
  return "text-zinc-500";
}

function formatFormat(fmt: string) {
  const map: Record<string, string> = {
    portrait_4_5: "4:5 Portrait",
    square_1_1: "1:1 Square",
    landscape_16_9: "16:9 Landscape",
  };
  return map[fmt] ?? fmt;
}

interface Props {
  result: ScoreResult;
  onApprove: () => void;
  approving: boolean;
  approved: boolean;
}

export default function ScoreCard({ result, onApprove, approving, approved }: Props) {
  const [notesOpen, setNotesOpen] = useState(false);
  const circumference = 2 * Math.PI * 40;
  const dash = (result.score / 10) * circumference;

  const editEntries = Object.entries(result.edit_params) as [keyof EditParams, number | string][];

  return (
    <div className="flex flex-col gap-4">

      {/* Score + badges */}
      <div className="bg-zinc-900 rounded-2xl p-5 flex items-center gap-6">
        {/* Circular score */}
        <div className="relative flex-shrink-0">
          <svg width="100" height="100" className="-rotate-90">
            <circle cx="50" cy="50" r="40" fill="none" stroke="#27272a" strokeWidth="8" />
            <circle
              cx="50" cy="50" r="40" fill="none"
              strokeWidth="8" strokeLinecap="round"
              strokeDasharray={`${dash} ${circumference}`}
              className={`transition-all duration-700 ${scoreRing(result.score)}`}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-2xl font-bold leading-none ${scoreColor(result.score)}`}>
              {result.score.toFixed(1)}
            </span>
            <span className="text-zinc-500 text-xs mt-0.5">/ 10</span>
          </div>
        </div>

        {/* Labels */}
        <div className="flex flex-col gap-2">
          <p className={`text-lg font-semibold ${scoreColor(result.score)}`}>
            {formatLabel(result.score)}
          </p>
          <div className="flex flex-wrap gap-2">
            <span className={`flex items-center gap-1 text-xs px-2.5 py-1 rounded-full font-medium
              ${result.post_worthy
                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                : "bg-red-500/10 text-red-400 border border-red-500/20"
              }`}>
              {result.post_worthy
                ? <><CheckCircle className="w-3 h-3" /> Post worthy</>
                : <><XCircle className="w-3 h-3" /> Skip</>
              }
            </span>
            <span className="text-xs px-2.5 py-1 rounded-full bg-zinc-800 text-zinc-300 border border-zinc-700">
              {formatFormat(result.recommended_format)}
            </span>
          </div>
          <p className="text-zinc-500 text-xs">{result.niche_fit}</p>
        </div>
      </div>

      {/* Edit params */}
      <div className="bg-zinc-900 rounded-2xl p-5">
        <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">
          Edit values
        </p>
        <div className="grid grid-cols-3 gap-3">
          {editEntries.map(([key, value]) => (
            <div key={key} className="bg-zinc-800/60 rounded-xl p-3 text-center">
              <p className="text-zinc-500 text-xs capitalize mb-1">
                {key === "crop_ratio" ? "Crop" : key}
              </p>
              <p className={`text-base font-semibold ${valueColor(key, value)}`}>
                {formatValue(key, value)}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Notes (collapsible) */}
      <div className="bg-zinc-900 rounded-2xl overflow-hidden">
        <button
          onClick={() => setNotesOpen(!notesOpen)}
          className="w-full flex items-center justify-between p-5 text-left hover:bg-zinc-800/50 transition-colors"
        >
          <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
            AI notes
          </p>
          <ChevronDown className={`w-4 h-4 text-zinc-500 transition-transform ${notesOpen ? "rotate-180" : ""}`} />
        </button>
        {notesOpen && (
          <div className="px-5 pb-5 flex flex-col gap-3 border-t border-zinc-800">
            {[
              { label: "Composition", text: result.composition_notes },
              { label: "Lighting", text: result.lighting_notes },
              { label: "Subject", text: result.subject_notes },
            ].map(({ label, text }) => (
              <div key={label} className="pt-3">
                <p className="text-xs text-zinc-500 mb-1">{label}</p>
                <p className="text-sm text-zinc-300 leading-relaxed">{text}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Approve button */}
      {!approved && (
        <button
          onClick={onApprove}
          disabled={approving}
          className="w-full py-3.5 rounded-2xl font-semibold text-white text-sm
            bg-gradient-to-r from-purple-600 to-pink-500
            hover:from-purple-500 hover:to-pink-400
            disabled:opacity-50 disabled:cursor-not-allowed
            transition-all duration-200 shadow-lg shadow-pink-500/10"
        >
          {approving ? "Approving..." : "Approve & Generate Caption →"}
        </button>
      )}
    </div>
  );
}
