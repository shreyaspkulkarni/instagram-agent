"use client";

import { Upload } from "lucide-react";
import { useRef, useState } from "react";

interface Props {
  onFile: (file: File) => void;
  disabled?: boolean;
}

export default function UploadZone({ onFile, disabled }: Props) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handle = (file: File) => {
    if (file.type.startsWith("image/")) onFile(file);
  };

  return (
    <div
      onClick={() => !disabled && inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        const file = e.dataTransfer.files[0];
        if (file) handle(file);
      }}
      className={`
        relative flex flex-col items-center justify-center gap-5
        w-full max-w-lg aspect-[4/3] rounded-2xl cursor-pointer
        border-2 border-dashed transition-all duration-200
        ${dragging
          ? "border-pink-500 bg-pink-500/5"
          : "border-zinc-700 hover:border-zinc-500 bg-zinc-900/50 hover:bg-zinc-900"
        }
        ${disabled ? "opacity-50 cursor-not-allowed" : ""}
      `}
    >
      <div className="flex flex-col items-center gap-3 text-center px-8">
        <div className="p-4 rounded-full bg-zinc-800">
          <Upload className="w-7 h-7 text-zinc-400" />
        </div>
        <div>
          <p className="text-white font-medium">Drop your photo here</p>
          <p className="text-zinc-500 text-sm mt-1">or click to browse</p>
        </div>
        <p className="text-zinc-600 text-xs">JPEG · PNG · WEBP · HEIC · up to 20MB</p>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        disabled={disabled}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handle(file);
        }}
      />
    </div>
  );
}
