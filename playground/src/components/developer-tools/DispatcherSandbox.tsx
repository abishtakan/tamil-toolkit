import { useState, useEffect, useCallback } from "react";
import { isEngineReady, tt } from "../../lib/engine";
import { useLanguage } from "../../lib/i18n";
import { ToolHeader } from "../common/ToolHeader";
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
        input: { text: "jkpo; nkhop" },
      },
      null,
      2
    ),
  },
  {
    name: "Number to Words",
    payload: JSON.stringify(
      {
        op: "to_words",
        input: { value: 125000, locale: "TN" },
      },
      null,
      2
    ),
  },
  {
    name: "Currency INR (TN)",
    payload: JSON.stringify(
      {
        op: "currency_to_words",
        input: { amount_minor: 12500000, currency: "INR", locale: "TN" },
      },
      null,
      2
    ),
  },
  {
    name: "Currency LKR (SL)",
    payload: JSON.stringify(
      {
        op: "currency_to_words",
        input: { amount_minor: 12500000, currency: "LKR", locale: "SL" },
      },
      null,
      2
    ),
  },
  {
    name: "Traditional Numeral",
    payload: JSON.stringify(
      {
        op: "format_traditional_integer",
        input: { value: 1250 },
      },
      null,
      2
    ),
  },
  {
    name: "Panchangam (Jaffna)",
    payload: JSON.stringify(
      {
        op: "panchangam_day",
        input: {
          definition_id: "thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2",
          date: { year: 2026, month: 4, day: 14 },
          context: {
            region: "SL",
            latitude_microdegrees: 9661500,
            longitude_microdegrees: 80025500,
            elevation_meters: 5,
            time_zone: "Asia/Colombo",
          },
        },
      },
      null,
      2
    ),
  },
  {
    name: "Observances (2026)",
    payload: JSON.stringify(
      {
        op: "calendar_observances",
        input: {
          definition_id: "thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2",
          rule_set: "thirukanitham-tamil-named-observances-v1",
          gregorian_year: 2026,
          month: 4,
          context: {
            region: "TN",
            latitude_microdegrees: 13087840,
            longitude_microdegrees: 80278470,
            elevation_meters: 14,
            time_zone: "Asia/Kolkata",
          },
        },
      },
      null,
      2
    ),
  },
  {
    name: "Lexicon Lookup",
    payload: JSON.stringify(
      {
        op: "lexicon_lookup",
        input: "நன்றி",
      },
      null,
      2
    ),
  },
  {
    name: "Hyphenate Word",
    payload: JSON.stringify(
      {
        op: "hyphenate_word",
        input: { word: "திருவள்ளுவர்", delimiter: "-", left_min: 2, right_min: 2 },
      },
      null,
      2
    ),
  },
  {
    name: "Repair Tamil Text",
    payload: JSON.stringify(
      {
        op: "repair_tamil_text",
        input: { text: "தமிழ்" },
      },
      null,
      2
    ),
  },
  {
    name: "Search Fold",
    payload: JSON.stringify(
      {
        op: "fold_for_search",
        input: { text: "பழம்", profile: "comprehensive" },
      },
      null,
      2
    ),
  },
  {
    name: "Agara Collation",
    payload: JSON.stringify(
      {
        op: "sort_words",
        input: ["பாரதி", "அகத்தியர்", "கம்பர்"],
      },
      null,
      2
    ),
  },
  {
    name: "Inspect String",
    payload: JSON.stringify(
      {
        op: "inspect_tamil_string",
        input: "தமிழ்",
      },
      null,
      2
    ),
  },
];

interface DispatcherSandboxProps {
  engineReady?: boolean;
}

export function DispatcherSandbox({ engineReady }: DispatcherSandboxProps) {
  const { t } = useLanguage();
  const ready = engineReady ?? isEngineReady();

  const [activePresetIdx, setActivePresetIdx] = useState<number | null>(0);
  const [requestJson, setRequestJson] = useState(PRESETS[0].payload);
  const [responseJson, setResponseJson] = useState("");
  const [latency, setLatency] = useState(0);
  const [isError, setIsError] = useState(false);

  const executePayload = useCallback((rawJson: string) => {
    if (!isEngineReady()) return;
    try {
      const parsed = JSON.parse(rawJson);
      setIsError(false);

      let requestPayload: { op: string; input: unknown } = parsed;
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
        if (!parsed.op) {
          throw new Error("Missing 'op' operation name field in request JSON");
        }
        if (parsed.input === undefined) {
          const { op, ...rest } = parsed;
          if (op === "bamini_to_unicode" && rest.text) {
            requestPayload = { op, input: { text: rest.text } };
          } else if (op === "to_words" && (rest.value !== undefined || rest.amount !== undefined)) {
            requestPayload = {
              op,
              input: { value: rest.value ?? rest.amount, locale: rest.locale || "TN" },
            };
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
  }, []);

  useEffect(() => {
    if (ready) {
      executePayload(requestJson);
    }
  }, [ready]);

  const handleSelectPreset = (index: number) => {
    setActivePresetIdx(index);
    const payload = PRESETS[index].payload;
    setRequestJson(payload);
    executePayload(payload);
  };

  return (
    <div className="space-y-6">
      <ToolHeader
        title={t.tools.dispatcher.title}
        description={t.tools.dispatcher.desc}
      />

      {/* Preset Chips */}
      <div className="flex items-center gap-1.5 flex-wrap">
        {PRESETS.map((p, i) => (
          <Button
            key={p.name}
            type="button"
            variant={activePresetIdx === i ? "primary" : "outline"}
            size="sm"
            onClick={() => handleSelectPreset(i)}
            className="text-xs"
          >
            {p.name}
          </Button>
        ))}
      </div>

      {/* Request & Response Editor */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div className="space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[var(--color-mai)] flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5 text-[var(--color-semman)]" />
              <span>{t.tools.dispatcher.payloadLabel}</span>
            </span>
            <span className="text-[11px] text-[var(--color-muted)]">
              {t.tools.dispatcher.shortcutHint}
            </span>
          </div>
          <Textarea
            value={requestJson}
            onChange={(e) => {
              setActivePresetIdx(null);
              setRequestJson(e.target.value);
            }}
            onKeyDown={(e) => {
              if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
                e.preventDefault();
                executePayload(requestJson);
              }
            }}
            className="font-mono-tamil text-xs leading-relaxed min-h-[260px]"
            spellCheck={false}
          />
          <Button
            type="button"
            variant="primary"
            size="md"
            disabled={!ready}
            onClick={() => executePayload(requestJson)}
            className="w-full"
          >
            <Send className="w-4 h-4 mr-2" />
            <span>{t.tools.dispatcher.sendRequest}</span>
          </Button>
        </div>

        <div className="space-y-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-[var(--color-mai)]">
                {t.tools.dispatcher.responseLabel}
              </span>
              {responseJson &&
                (isError ? (
                  <Badge variant="outline" className="text-red-600 border-red-300">
                    {t.tools.dispatcher.statusError}
                  </Badge>
                ) : (
                  <Badge variant="terracotta">
                    {t.tools.dispatcher.statusSuccess}
                  </Badge>
                ))}
            </div>
            {latency > 0 && <Badge variant="mono">{latency.toFixed(2)} ms</Badge>}
          </div>

          <div className="relative">
            <Textarea
              readOnly
              value={responseJson || t.tools.dispatcher.responsePlaceholder}
              className="font-mono-tamil text-xs leading-relaxed min-h-[260px] bg-[var(--bg-raised)]/50 text-[var(--color-mai)]"
              spellCheck={false}
            />
            {responseJson && (
              <div className="absolute bottom-3 right-3">
                <CopyButton text={responseJson} size="sm" variant="outline" />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
