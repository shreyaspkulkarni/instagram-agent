export interface EditParams {
  rotation: number;
  brightness: number;
  contrast: number;
  saturation: number;
  sharpness: number;
  crop_ratio: string;
}

export interface ScoreResult {
  photo_id: string;
  filename: string;
  score: number;
  post_worthy: boolean;
  recommended_format: string;
  composition_notes: string;
  lighting_notes: string;
  subject_notes: string;
  niche_fit: string;
  edit_suggestions: string[];
  edit_params: EditParams;
}

export interface CaptionResult {
  post_id: string;
  caption: string;
  hashtags: string[];
  style_notes: string;
}

export type AppState =
  | { stage: "idle" }
  | { stage: "uploading" }
  | { stage: "scoring"; preview: string; filename: string }
  | { stage: "scored"; preview: string; result: ScoreResult }
  | { stage: "generating"; preview: string; result: ScoreResult }
  | { stage: "done"; preview: string; result: ScoreResult; caption: CaptionResult };
