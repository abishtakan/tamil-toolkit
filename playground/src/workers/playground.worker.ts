import { init } from "tamil-toolkit/web";
import * as tt from "tamil-toolkit/web";

let isReady = false;

async function ensureReady() {
  if (!isReady) {
    await init();
    isReady = true;
  }
}

self.onmessage = async (e: MessageEvent) => {
  const data = e.data;
  if (!data) return;

  try {
    await ensureReady();

    if (data.type === "INIT") {
      self.postMessage({ type: "INIT_SUCCESS" });
      return;
    }

    if (data.type === "BATCH_CONVERT_FILE") {
      const { jobId, text, targetCodec } = data;
      const t0 = performance.now();

      // Convert in chunks to report progress
      const lines = text.split("\n");
      const total = lines.length;
      const outputLines: string[] = [];
      const chunkSize = Math.max(1, Math.floor(total / 10));

      let codec = targetCodec;
      if (!codec || codec === "auto") {
        const encoder = new TextEncoder();
        const sampleBytes = encoder.encode(text.slice(0, 1000));
        const detected = tt.detect_encoding(sampleBytes);
        codec = detected?.encoding || "bamini-v1";
      }

      for (let i = 0; i < total; i++) {
        const line = lines[i];
        if (codec === "bamini-v1") {
          outputLines.push(tt.bamini_to_unicode(line));
        } else if (codec === "vanavil-avvaiyar-cid-v1") {
          outputLines.push(tt.vanavil_text_to_unicode(line));
        } else {
          outputLines.push(tt.bamini_to_unicode(line));
        }

        if (i % chunkSize === 0 || i === total - 1) {
          self.postMessage({
            type: "BATCH_PROGRESS",
            jobId,
            percent: Math.round(((i + 1) / total) * 100)
          });
        }
      }

      const elapsed = performance.now() - t0;
      self.postMessage({
        type: "BATCH_COMPLETE",
        jobId,
        detectedCodec: codec,
        convertedText: outputLines.join("\n"),
        durationMs: elapsed
      });
    }
  } catch (err: unknown) {
    self.postMessage({
      type: "BATCH_ERROR",
      jobId: data.jobId,
      error: err instanceof Error ? err.message : String(err)
    });
  }
};
