import { tt } from "./engine";

let workerInstance: Worker | null = null;
let execCounter = 0;

function getWorker(): Worker {
  if (!workerInstance) {
    workerInstance = new Worker(
      new URL("../workers/playground.worker.ts", import.meta.url),
      { type: "module" }
    );
  }
  return workerInstance;
}

export interface BatchConvertResult {
  jobId: string;
  detectedCodec: string;
  convertedText: string;
  durationMs: number;
}

export function runBatchConvert(
  jobId: string,
  text: string,
  targetCodec: string = "auto",
  onProgress?: (percent: number) => void
): Promise<BatchConvertResult> {
  return new Promise((resolve, reject) => {
    const worker = getWorker();

    const handler = (e: MessageEvent) => {
      const data = e.data;
      if (!data || data.jobId !== jobId) return;

      if (data.type === "BATCH_PROGRESS") {
        onProgress?.(data.percent);
      } else if (data.type === "BATCH_COMPLETE") {
        worker.removeEventListener("message", handler);
        resolve({
          jobId: data.jobId,
          detectedCodec: data.detectedCodec,
          convertedText: data.convertedText,
          durationMs: data.durationMs
        });
      } else if (data.type === "BATCH_ERROR") {
        worker.removeEventListener("message", handler);
        reject(new Error(data.error));
      }
    };

    worker.addEventListener("message", handler);
    worker.postMessage({
      type: "BATCH_CONVERT_FILE",
      jobId,
      text,
      targetCodec
    });
  });
}

export async function runWorkerExecute<T>(op: string, input: unknown): Promise<T> {
  if (typeof Worker === "undefined") {
    return tt.execute({ op, input }) as T;
  }

  const jobId = `exec_${++execCounter}_${Date.now()}`;
  return new Promise<T>((resolve, reject) => {
    const worker = getWorker();

    const cleanup = () => {
      worker.removeEventListener("message", handleMessage);
      worker.removeEventListener("error", handleError);
    };

    const handleMessage = (e: MessageEvent) => {
      const data = e.data;
      if (!data || data.jobId !== jobId) return;

      if (data.type === "EXECUTE_COMPLETE") {
        cleanup();
        resolve(data.result as T);
      } else if (data.type === "EXECUTE_ERROR") {
        cleanup();
        reject(new Error(data.error || "Worker execution error"));
      }
    };

    const handleError = (err: ErrorEvent) => {
      cleanup();
      reject(new Error(err.message || "Worker runtime error"));
    };

    worker.addEventListener("message", handleMessage);
    worker.addEventListener("error", handleError);
    worker.postMessage({
      type: "EXECUTE",
      jobId,
      op,
      input,
    });
  });
}
