import { useState, useEffect } from "react";
import { tt } from "../../lib/engine";
import { useLanguage } from "../../lib/i18n";
import { Textarea } from "../ui/textarea";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { CopyButton } from "../common/CopyButton";
import { Send, Terminal } from "lucide-react";

const PRESETS = [
  {
    name: "Bamini to Unicode",
    payload: JSON.stringify(
      {
        op: "bamini_to_unicode",
        input: { text: "jkpo; nkhop" }
      },
      null,
      2
    )
  },
  {
    name: "Number to Words",
    payload: JSON.stringify(
      {
        op: "to_words",
        input: { value: 125000, locale: "TN" }
      },
      null,
      2
    )
  },
  {
    name: "Currency to Words",
    payload: JSON.stringify(
      {
        op: "currency_to_words",
        input: { amount_minor: 12500000, currency: "INR", locale: "TN" }
      },
      null,
      2
    )
  },
  {
    name: "Agara Collation",
    payload: JSON.stringify(
      {
        op: "sort_words",
        input: ["பாரதி", "அகத்தியர்", "கம்பர்"]
      },
      null,
      2
    )
  },
  {
    name: "Inspect String",
    payload: JSON.stringify(
      {
        op: "inspect_tamil_string",
        input: "தமிழ்"
      },
      null,
      2
    )
  }
];

export function DispatcherSandbox() {
  const { t, language } = useLanguage();

  const [requestJson, setRequestJson] = useState(PRESETS[0].payload);
  const [responseJson, setResponseJson] = useState("");
  const [latency, setLatency] = useState(0);
  const [isError, setIsError] = useState(false);

  const executePayload = (rawJson: string) => {
    try {
      const parsed = JSON.parse(rawJson);
      setIsError(false);

      // Intelligent normalization: Ensure dispatcher request format { op, input }
      let requestPayload: { op: string; input: unknown } = parsed;
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
        if (!parsed.op) {
          throw new Error("Missing 'op' operation name field in request JSON");
        }
        if (parsed.input === undefined) {
          // If user didn't wrap parameters in 'input', adaptively map them
          const { op, ...rest } = parsed;
          if (op === "bamini_to_unicode" && rest.text) {
            requestPayload = { op, input: { text: rest.text } };
          } else if (op === "to_words" && (rest.value !== undefined || rest.amount !== undefined)) {
            requestPayload = { op, input: { value: rest.value ?? rest.amount, locale: rest.locale || "TN" } };
          } else if (op === "sort_words" && rest.words) {
            requestPayload = { op, input: rest.words };
          } else if (op === "inspect_tamil_string" && rest.text) {
            requestPayload = { op, input: rest.text };
          } else {
            requestPayload = { op, input: rest };
          }
        }
      }

      const t0 = performance.now();
      const res = tt.execute(requestPayload);
      const elapsed = performance.now() - t0;
      setLatency(elapsed);
      setResponseJson(JSON.stringify(res, null, 2));
    } catch (err: unknown) {
      setIsError(true);
      const msg = err instanceof Error ? err.message : String(err);
      setResponseJson(JSON.stringify({ error: "Execution error", details: msg }, null, 2));
    }
  };

  const handleSendRequest = () => {
    executePayload(requestJson);
  };

  const handleSelectPreset = (payload: string) => {
    setRequestJson(payload);
    executePayload(payload);
  };

  // Run the default preset on first load
  useEffect(() => {
    executePayload(PRESETS[0].payload);
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[var(--border-line)]">
        <div>
          <h2 className="text-xl sm:text-2xl font-tamil font-bold text-[var(--color-mai)]">
            {t.tools.dispatcher.title}
          </h2>
          <p className="text-xs sm:text-sm text-[var(--color-muted)] font-tamil-sans mt-1">
            {t.tools.dispatcher.desc}
          </p>
        </div>

        <div className="flex items-center gap-1.5 flex-wrap">
          {PRESETS.map((p, i) => (
            <Button
              key={i}
              variant="outline"
              size="sm"
              onClick={() => handleSelectPreset(p.payload)}
              className="text-xs font-tamil hover:border-[var(--color-semman)]"
            >
              <span>{p.name}</span>
            </Button>
          ))}
        </div>
      </div>

      {/* Request & Response Editor */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[var(--color-mai)] font-tamil flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5 text-[var(--color-semman)]" />
              <span>{language === "en" ? "JSON Request Payload:" : "JSON கோரிக்கை (Request Payload):"}</span>
            </span>
          </div>
          <Textarea
            value={requestJson}
            onChange={(e) => setRequestJson(e.target.value)}
            className="font-mono-tamil text-xs leading-relaxed min-h-[260px] bg-[var(--bg-canvas)]"
            spellCheck={false}
          />
          <Button
            variant="primary"
            size="md"
            onClick={handleSendRequest}
            className="w-full font-tamil font-semibold min-h-[44px]"
          >
            <Send className="w-4 h-4 mr-2" />
            <span>{t.tools.dispatcher.sendRequest}</span>
          </Button>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-[var(--color-mai)] font-tamil">
                {t.tools.dispatcher.responseLabel}:
              </span>
              {isError ? (
                <Badge variant="outline" className="text-red-600 border-red-300">
                  {language === "en" ? "Error" : "பிழை"}
                </Badge>
              ) : (
                <Badge variant="terracotta">
                  {language === "en" ? "Success" : "வெற்றி"}
                </Badge>
              )}
            </div>
            {latency > 0 && <Badge variant="mono">{latency.toFixed(2)} ms</Badge>}
          </div>

          <div className="relative">
            <Textarea
              readOnly
              value={responseJson || (language === "en" ? "Response will appear here (Click 'Send Request')" : "முடிவு இங்கே தோன்றும் (Click 'Send Request')")}
              className="font-mono-tamil text-xs leading-relaxed min-h-[260px] bg-[var(--bg-raised)]/70 text-[var(--color-mai)]"
              spellCheck={false}
            />
            {responseJson && (
              <div className="absolute bottom-3 right-3">
                <CopyButton text={responseJson} size="sm" variant="ghost" />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
