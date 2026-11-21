import { useState, useEffect, useRef } from "react";
import { runBatchConvert } from "../../lib/worker-client";
import { useLanguage } from "../../lib/i18n";
import { ToolHeader } from "../common/ToolHeader";
import { Card } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { UploadCloud, CheckCircle2, Download, AlertCircle } from "lucide-react";

const ENCODING_OPTIONS = [
  { id: "auto", labelEn: "Auto-Detect", labelTa: "தானியங்கி" },
  { id: "bamini-v1", labelEn: "Bamini", labelTa: "பாமினி" },
  { id: "tscii-1.7-v1", labelEn: "TSCII", labelTa: "TSCII" },
  { id: "tab-v1", labelEn: "TAB", labelTa: "TAB" },
  { id: "tam-v1", labelEn: "TAM", labelTa: "TAM" },
  { id: "anjal-v1", labelEn: "Anjal", labelTa: "அஞ்சல்" },
  { id: "vanavil-avvaiyar-cid-v1", labelEn: "Vanavil", labelTa: "வானவில்" },
  { id: "lt-tm-cid-v1", labelEn: "LT-TM", labelTa: "LT-TM" },
] as const;

export function BatchProcessor() {
  const { t, language } = useLanguage();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [sourceCodec, setSourceCodec] = useState<string>("auto");
  const [isDragging, setIsDragging] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [fileSize, setFileSize] = useState<number>(0);
  const [progress, setProgress] = useState<number>(0);
  const [status, setStatus] = useState<"idle" | "processing" | "done" | "error">("idle");
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [latency, setLatency] = useState<number>(0);
  const [detectedCodec, setDetectedCodec] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string>("");

  useEffect(() => {
    return () => {
      if (downloadUrl) {
        URL.revokeObjectURL(downloadUrl);
      }
    };
  }, [downloadUrl]);

  const handleFile = async (file: File) => {
    if (downloadUrl) {
      URL.revokeObjectURL(downloadUrl);
      setDownloadUrl(null);
    }

    setFileName(file.name);
    setFileSize(file.size);
    setProgress(0);
    setStatus("processing");
    setErrorMessage("");

    try {
      const text = await file.text();
      const jobId = `job_${Date.now()}`;

      const res = await runBatchConvert(jobId, text, sourceCodec, (p) => {
        setProgress(p);
      });

      setDetectedCodec(res.detectedCodec);
      setLatency(res.durationMs);

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
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      void handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      void handleFile(e.target.files[0]);
    }
  };

  const handleReset = () => {
    if (downloadUrl) {
      URL.revokeObjectURL(downloadUrl);
    }
    setDownloadUrl(null);
    setFileName(null);
    setFileSize(0);
    setProgress(0);
    setStatus("idle");
    setErrorMessage("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="space-y-6">
      <ToolHeader
        title={t.tools.batch.title}
        description={t.tools.batch.desc}
      />

      {/* Source Encoding Selector */}
      <div className="flex flex-wrap items-center gap-2">
        <label htmlFor="batch-codec-select" className="text-xs font-semibold text-[var(--color-mai)]">
          {t.tools.batch.encodingLabel}
        </label>
        <select
          id="batch-codec-select"
          value={sourceCodec}
          onChange={(e) => setSourceCodec(e.target.value)}
          className="min-h-[38px] px-3 py-1.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-surface)] text-xs font-medium text-[var(--color-mai)] focus-visible:outline-none focus-visible:border-[var(--color-semman)]"
        >
          {ENCODING_OPTIONS.map((opt) => (
            <option key={opt.id} value={opt.id}>
              {language === "ta" ? opt.labelTa : opt.labelEn}
            </option>
          ))}
        </select>
      </div>

      {/* Drag & Drop Zone */}
      <div
        role="button"
        tabIndex={0}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            fileInputRef.current?.click();
          }
        }}
        className={`rounded-2xl border-2 border-dashed p-8 text-center transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-semman)] ${
          isDragging
            ? "border-[var(--color-semman)] bg-[var(--color-semman-light)]/40"
            : "border-[var(--border-line)] hover:border-[var(--color-semman)] bg-[var(--bg-surface)]"
        }`}
      >
        <input
          ref={fileInputRef}
          id="file-input"
          type="file"
          accept=".txt,.csv"
          onChange={handleFileSelect}
          className="hidden"
        />

        <div className="max-w-md mx-auto space-y-3">
          <div className="w-12 h-12 rounded-xl bg-[var(--color-semman-light)] text-[var(--color-semman)] flex items-center justify-center mx-auto">
            <UploadCloud className="w-6 h-6" />
          </div>
          <div>
            <h2 className="font-tamil font-bold text-base sm:text-lg text-[var(--color-mai)]">
              {t.tools.batch.dropzoneTitle}
            </h2>
            <p className="text-xs text-[var(--color-muted)] mt-1">
              {t.tools.batch.dropzoneSubtitle}
            </p>
          </div>
        </div>
      </div>

      {/* Status & Progress View */}
      {status !== "idle" && (
        <Card className="p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-[var(--border-line)] pb-3 gap-2">
            <div className="min-w-0">
              <p className="font-semibold text-sm sm:text-base text-[var(--color-mai)] truncate">
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
              <div className="flex items-center justify-between text-xs text-[var(--color-muted)]">
                <span>{t.tools.batch.progressLabel}</span>
                <span className="font-mono-tamil">{progress}%</span>
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
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
              <div className="flex items-center gap-2 text-sm text-[var(--color-semman)] font-medium">
                <CheckCircle2 className="w-5 h-5 shrink-0" />
                <span>{t.tools.batch.completedNotice}</span>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <Button type="button" variant="outline" size="md" onClick={handleReset}>
                  {t.tools.batch.convertAnother}
                </Button>
                <a
                  href={downloadUrl}
                  download={`converted_${fileName}`}
                  className="inline-flex items-center justify-center min-h-[44px] px-5 py-2 rounded-xl bg-[var(--color-semman)] text-[#faf7f2] text-sm font-semibold hover:bg-[var(--color-semman-hover)] transition-colors"
                >
                  <Download className="w-4 h-4 mr-2" />
                  <span>{t.actions.downloadFile}</span>
                </a>
              </div>
            </div>
          )}

          {status === "error" && (
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-sm text-red-600 dark:text-red-400">
                <AlertCircle className="w-5 h-5 shrink-0" />
                <span>
                  {t.tools.dispatcher.statusError}: {errorMessage || t.tools.batch.formatError}
                </span>
              </div>
              <Button type="button" variant="outline" size="sm" onClick={handleReset}>
                {t.actions.clear}
              </Button>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
