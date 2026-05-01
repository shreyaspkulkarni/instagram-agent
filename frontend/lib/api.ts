import { CaptionResult, ScoreResult } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function uploadAndScore(file: File): Promise<string> {
  const formData = new FormData();
  formData.append("files", file);

  const res = await fetch(`${API_URL}/photos/score`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to upload photo");
  }

  const data = await res.json();
  return data.jobs[0].job_id;
}

export async function pollJob(
  jobId: string,
  onTimeout?: () => void
): Promise<ScoreResult> {
  const POLL_INTERVAL = 2000;
  const MAX_ATTEMPTS = 30; // 60 seconds

  for (let i = 0; i < MAX_ATTEMPTS; i++) {
    await new Promise((r) => setTimeout(r, POLL_INTERVAL));

    const res = await fetch(`${API_URL}/photos/jobs/${jobId}`);
    const data = await res.json();

    if (data.status === "completed") return data.result as ScoreResult;
    if (data.status === "failed") throw new Error(data.error || "Scoring failed");
  }

  onTimeout?.();
  throw new Error("Timed out. Is the Celery worker running?");
}

export async function approvePhoto(photoId: string): Promise<void> {
  const res = await fetch(`${API_URL}/photos/${photoId}/status?status=approved`, {
    method: "PATCH",
  });
  if (!res.ok) throw new Error("Failed to approve photo");
}

export async function generateCaption(photoId: string): Promise<CaptionResult> {
  const res = await fetch(`${API_URL}/captions/${photoId}`, { method: "POST" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to generate caption");
  }
  return res.json();
}
