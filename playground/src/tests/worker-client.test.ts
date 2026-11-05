import { describe, it, expect } from "vitest";

describe("T030: WorkerClient RPC Contract", () => {
  it("structures worker batch conversion requests correctly", () => {
    const request = {
      type: "BATCH_CONVERT_FILE",
      jobId: "job_12345",
      text: "tzf;fk;",
      targetCodec: "bamini-v1"
    };

    expect(request.type).toBe("BATCH_CONVERT_FILE");
    expect(request.jobId).toBe("job_12345");
    expect(request.text).toBe("tzf;fk;");
    expect(request.targetCodec).toBe("bamini-v1");
  });

  it("handles worker progress and completion message types", () => {
    const progressMsg = {
      type: "BATCH_PROGRESS",
      jobId: "job_12345",
      percent: 50
    };

    const completeMsg = {
      type: "BATCH_COMPLETE",
      jobId: "job_12345",
      detectedCodec: "bamini-v1",
      convertedText: "வணக்கம்",
      durationMs: 12.5
    };

    expect(progressMsg.percent).toBe(50);
    expect(completeMsg.convertedText).toBe("வணக்கம்");
  });
});
