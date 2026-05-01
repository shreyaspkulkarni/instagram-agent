"use client";

import { useState } from "react";
import Image from "next/image";
import { Loader2, RotateCcw, Sparkles } from "lucide-react";
import UploadZone from "@/components/UploadZone";
import ScoreCard from "@/components/ScoreCard";
import CaptionCard from "@/components/CaptionCard";
import { uploadAndScore, pollJob, approvePhoto, generateCaption } from "@/lib/api";
import { AppState } from "@/lib/types";

export default function Home() {
  const [state, setState] = useState<AppState>({ stage: "idle" });
  const [error, setError] = useState<string | null>(null);

  const handleFile = async (file: File) => {
    setError(null);
    const preview = URL.createObjectURL(file);
    setState({ stage: "uploading" });

    try {
      const jobId = await uploadAndScore(file);
      setState({ stage: "scoring", preview, filename: file.name });

      const result = await pollJob(jobId);
      setState({ stage: "scored", preview, result });
    } catch (e) {
      setError((e as Error).message);
      setState({ stage: "idle" });
    }
  };

  const handleApprove = async () => {
    if (state.stage !== "scored") return;
    const { preview, result } = state;
    setError(null);
    setState({ stage: "generating", preview, result });

    try {
      await approvePhoto(result.photo_id);
      const caption = await generateCaption(result.photo_id);
      setState({ stage: "done", preview, result, caption });
    } catch (e) {
      setError((e as Error).message);
      setState({ stage: "scored", preview, result });
    }
  };

  const reset = () => {
    setError(null);
    setState({ stage: "idle" });
  };

  return (
    <main className="min-h-screen bg-black text-white">

      {/* Header */}
      <header className="border-b border-zinc-900 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <span className="font-semibold text-white">GramScore</span>
        </div>
        {state.stage !== "idle" && (
          <button
            onClick={reset}
            className="flex items-center gap-1.5 text-zinc-500 hover:text-white text-sm transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            New photo
          </button>
        )}
      </header>

      {/* Body */}
      <div className="max-w-5xl mx-auto px-6 py-10">

        {/* Idle */}
        {state.stage === "idle" && (
          <div className="flex flex-col items-center gap-6 pt-16">
            <div className="text-center">
              <h1 className="text-3xl font-bold text-white">Score your photo</h1>
              <p className="text-zinc-500 mt-2 text-sm">
                Upload a photo — get an AI score, edit values, and a caption ready to post.
              </p>
            </div>
            {error && (
              <p className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 max-w-lg w-full text-center">
                {error}
              </p>
            )}
            <UploadZone onFile={handleFile} />
          </div>
        )}

        {/* Uploading / Scoring */}
        {(state.stage === "uploading" || state.stage === "scoring") && (
          <div className="flex flex-col lg:flex-row gap-8 items-start">
            <div className="w-full lg:w-1/2">
              <div className="relative aspect-[4/5] w-full rounded-2xl overflow-hidden bg-zinc-900">
                {"preview" in state && (
                  <Image src={state.preview} alt="Preview" fill className="object-cover opacity-40" />
                )}
              </div>
            </div>
            <div className="w-full lg:w-1/2 flex flex-col items-center justify-center gap-4 py-24">
              <Loader2 className="w-8 h-8 animate-spin text-pink-500" />
              <p className="text-white font-medium">
                {state.stage === "uploading" ? "Uploading..." : "Scoring with Gemini AI..."}
              </p>
              {state.stage === "scoring" && (
                <p className="text-zinc-600 text-sm text-center max-w-xs">
                  Analysing composition, lighting, and niche fit
                </p>
              )}
            </div>
          </div>
        )}

        {/* Scored / Generating / Done */}
        {(state.stage === "scored" || state.stage === "generating" || state.stage === "done") && (
          <div className="flex flex-col lg:flex-row gap-8 items-start">

            {/* Left — photo (sticky on desktop) */}
            <div className="w-full lg:w-1/2 lg:sticky lg:top-10">
              <div className="relative aspect-[4/5] w-full rounded-2xl overflow-hidden bg-zinc-900">
                <Image
                  src={state.preview}
                  alt={state.result.filename}
                  fill
                  className="object-cover"
                />
              </div>
              <p className="text-zinc-600 text-xs text-center mt-2 truncate">
                {state.result.filename}
              </p>
            </div>

            {/* Right — results */}
            <div className="w-full lg:w-1/2 flex flex-col gap-4">
              <ScoreCard
                result={state.result}
                onApprove={handleApprove}
                approving={state.stage === "generating"}
                approved={state.stage === "done"}
              />

              {state.stage === "generating" && (
                <div className="bg-zinc-900 rounded-2xl p-5 flex items-center gap-3">
                  <Loader2 className="w-4 h-4 animate-spin text-pink-500 flex-shrink-0" />
                  <p className="text-zinc-400 text-sm">Generating caption with Claude...</p>
                </div>
              )}

              {state.stage === "done" && <CaptionCard result={state.caption} />}

              {error && (
                <p className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3">
                  {error}
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
