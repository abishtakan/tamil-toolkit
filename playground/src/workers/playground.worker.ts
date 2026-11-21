import { init } from "tamil-toolkit/web";
import * as tt from "tamil-toolkit/web";
import { stringToLatin1Bytes } from "../lib/engine";

let isReady = false;

async function ensureReady() {
  if (!isReady) {
    await init();
    isReady = true;
  }
}

function decodeLineWithCodec(line: string, codec: string): string {
  switch (codec) {
    case "bamini-v1":
      return tt.bamini_to_unicode(line);
    case "tscii-1.7-v1":
      return tt.tscii_bytes_to_unicode(stringToLatin1Bytes(line));
    case "tab-v1":
      return tt.tab_bytes_to_unicode(stringToLatin1Bytes(line));
    case "tam-v1":
      return tt.tam_bytes_to_unicode(stringToLatin1Bytes(line));
    case "anjal-v1":
      return tt.anjal_bytes_to_unicode(stringToLatin1Bytes(line));
    case "vanavil-avvaiyar-cid-v1":
      return tt.vanavil_text_to_unicode(line);
    case "lt-tm-cid-v1":
      return tt.lt_tm_text_to_unicode(line);
    default:
      return tt.bamini_to_unicode(line);
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

    if (data.type === "EXECUTE") {
      try {
        const result = tt.execute({ op: data.op, input: data.input });
        self.postMessage({
          type: "EXECUTE_COMPLETE",
          jobId: data.jobId,
          result,
        });
      } catch (err: unknown) {
        self.postMessage({
          type: "EXECUTE_ERROR",
          jobId: data.jobId,
          error: err instanceof Error ? err.message : String(err),
        });
      }
      return;
    }

    if (data.type === "BATCH_CONVERT_FILE") {
      const { jobId, text, targetCodec } = data;
      const t0 = performance.now();

      const lines = text.split("\n");
      const total = lines.length;
      const outputLines: string[] = [];
      const chunkSize = Math.max(1, Math.floor(total / 10));

      let codec = targetCodec;
      if (!codec || codec === "auto") {
        const sample = text.slice(0, 1000);
        const sampleBytes = /[^\x00-\xff]/.test(sample)
          ? new TextEncoder().encode(sample)
          : stringToLatin1Bytes(sample);
        const detected = tt.detect_encoding(sampleBytes);
        codec = detected?.encoding || "bamini-v1";
      }

      for (let i = 0; i < total; i++) {
        outputLines.push(decodeLineWithCodec(lines[i], codec));

        if (i % chunkSize === 0 || i === total - 1) {
          self.postMessage({
            type: "BATCH_PROGRESS",
            jobId,
            percent: Math.round(((i + 1) / total) * 100),
          });
        }
      }

      const elapsed = performance.now() - t0;
      self.postMessage({
        type: "BATCH_COMPLETE",
        jobId,
        detectedCodec: codec,
        convertedText: outputLines.join("\n"),
        durationMs: elapsed,
      });
    }
  } catch (err: unknown) {
    self.postMessage({
      type: "BATCH_ERROR",
      jobId: data.jobId,
      error: err instanceof Error ? err.message : String(err),
    });
  }
};
