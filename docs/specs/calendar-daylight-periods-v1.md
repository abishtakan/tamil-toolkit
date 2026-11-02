# Daylight periods v1

Status: source-derived Thirukanitham operation; golden suite planned and not
calendar activation approval. Vakiya returns an explicit unavailable error for
this operation because the bounded 1962 civil profile does not derive a local
sunset.

`calendar_daylight_periods` accepts exactly
`{definition_id,date,context}`. Under the bounded Thirukanitham definition it
uses that profile's computed apparent sunrise and sunset for the local civil
date. It divides the daylight duration into eight equal temporal parts and
returns three half-open intervals, sorted by start time: Rahukalam, Yamagandam,
and Kuligai. Weekday assignment is by the report civil date. Each boundary is
rounded down to the nearest second after dividing the profile's integer-second
daylight span by eight; displayed times include seconds. The result reports the
weekday, one-based part index, daylight endpoints, rule ID, source description,
and source digest. It makes no claim about whether a period is auspicious.

The weekday part arrays (Sunday through Saturday) are respectively
Rahu `[8,2,7,5,6,4,3]`, Kuligai/Gulika `[7,6,5,4,3,2,1]`, and Yamagandam
`[5,4,3,2,1,7,6]`. These reproduce the printed 06:00–18:00 table in S.
Narasimha Rao, *Basics of Panchangam*, reprint from *Achara Vichara Monthly*,
2005, printed p. 35 / PDF p. 35. That page says each slot is one eighth of
daylight and directs the reader to correct the illustration using the actual
sunrise and sunset. Source PDF SHA-256:
`4716fae5ca5634f9a88be5482e7335e3cbe5bc4df27a31923f2e8946d3e9e750`.

The source's sample clock table is explanatory, not used as a fixed 06:00
sunrise. The operation does not compute night intervals. Vakiya is not given
synthetic sunset data: its source-defined local horizon correction remains
unavailable, so requests for Vakiya return
`source-defined local sunset unavailable for this calendar definition`.
No observance, activity recommendation, or holiday is inferred from these
intervals.
