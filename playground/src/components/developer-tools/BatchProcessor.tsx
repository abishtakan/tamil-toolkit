import { useState } from "react";
import { runBatchConvert } from "../../lib/worker-client";
import { useLanguage } from "../../lib/i18n";
import { Card } from "../ui/card";
import { Badge } from "../ui/badge";
import { UploadCloud, CheckCircle2, Download, AlertCircle } from "lucide-react";

export function BatchProcessor() {
  const { t, language } = useLanguage();

  const [fileName, setFileName] = useState<string | null>(null);
  const [fileSize, setFileSize] = useState<number>(0);
  const [progress, setProgress] = useState<number>(0);
  const [status, setStatus] = useState<"idle" | "processing" | "done" | "error">("idle");
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [latency, setLatency] = useState<number>(0);
  const [detectedCodec, setDetectedCodec] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string>("");

  const handleFile = async (file: File) => {
    setFileName(file.name);
    setFileSize(file.size);
    setProgress(0);
    setStatus("processing");
    setErrorMessage("");

    try {
      const text = await file.text();
      const jobId = `job_${Date.now()}`;

      const res = await runBatchConvert(jobId, text, "auto", (p) => {
        setProgress(p);
      });

      setDetectedCodec(res.detectedCodec);
      setLatency(res.durationMs);

      // Create download blob
      const blob = new Blob([res.convertedText], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      setDownloadUrl(url);
      setStatus("done");
      setProgress(100);
    } catch (err: unknown) {
      console.error("Batch processing error:", err);
      setStatus("error");
      setErrorMessage(err instanceof Error ? err.message : String(err));
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[var(--border-line)]">
        <div>
          <h2 className="text-xl sm:text-2xl font-tamil font-bold text-[var(--color-mai)]">
            {t.tools.batch.title}
          </h2>
          <p className="text-xs sm:text-sm text-[var(--color-muted)] font-tamil-sans mt-1">
            {t.tools.batch.desc}
          </p>
        </div>
      </div>

      {/* Drag & Drop Zone */}
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        className="rounded-3xl border-2 border-dashed border-[var(--border-line)] hover:border-[var(--color-semman)] bg-[var(--bg-canvas)] p-8 text-center transition-colors cursor-pointer"
        onClick={() => document.getElementById("file-input")?.click()}
      >
        <input
          id="file-input"
          type="file"
          accept=".txt,.csv"
          onChange={handleFileSelect}
          className="hidden"
        />

        <div className="max-w-md mx-auto space-y-3">
          <div className="w-14 h-14 rounded-2xl bg-[var(--color-semman-light)] text-[var(--color-semman)] flex items-center justify-center mx-auto">
            <UploadCloud className="w-7 h-7" />
          </div>
          <div>
            <h3 className="font-tamil font-bold text-base sm:text-lg text-[var(--color-mai)]">
              {t.tools.batch.dropzoneTitle}
            </h3>
            <p className="text-xs text-[var(--color-muted)] font-tamil-sans mt-1">
              {t.tools.batch.dropzoneSubtitle}
            </p>
          </div>
        </div>
      </div>

      {/* Status & Progress View */}
      {status !== "idle" && (
        <Card className="p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-[var(--border-line)] pb-3">
            <div>
              <p className="font-tamil font-semibold text-sm sm:text-base text-[var(--color-mai)]">
                {fileName}
              </p>
              <p className="text-xs text-[var(--color-muted)] font-mono-tamil">
                {(fileSize / 1024).toFixed(1)} KB
              </p>
            </div>

            {status === "done" && (
              <Badge variant="terracotta">
                {detectedCodec} ({latency.toFixed(0)} ms)
              </Badge>
            )}
          </div>

          {status === "processing" && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-tamil text-[var(--color-muted)]">
                <span>{t.tools.batch.progressLabel}</span>
                <span>{progress}%</span>
              </div>
              <div className="w-full h-2 rounded-full bg-[var(--bg-raised)] overflow-hidden">
                <div
                  className="h-full bg-[var(--color-semman)] transition-all duration-200"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {status === "done" && downloadUrl && (
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
              <div className="flex items-center gap-2 text-sm font-tamil text-[var(--color-semman)] font-medium">
                <CheckCircle2 className="w-5 h-5" />
                <span>{t.tools.batch.completedNotice}</span>
              </div>

              <a
                href={downloadUrl}
                download={`converted_${fileName}`}
                className="inline-flex items-center justify-center min-h-[44px] px-5 py-2 rounded-xl bg-[var(--color-semman)] text-[#faf7f2] font-tamil text-sm font-semibold hover:bg-[var(--color-semman-hover)] transition-colors shadow-sm"
              >
                <Download className="w-4 h-4 mr-2" />
                <span>{t.actions.downloadFile}</span>
              </a>
            </div>
          )}

          {status === "error" && (
            <div className="flex items-center gap-2 text-sm font-tamil text-red-600">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span>
                {language === "en"
                  ? `Error: ${errorMessage || "Failed to convert file"}`
                  : `பிழை: ${errorMessage || "கோப்பை மாற்ற முடியவில்லை"}`}
              </span>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
