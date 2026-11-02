> Alpha.5 candidate override: Krishna Jayanthi is deferred and absent from the
> supported event inventory. The exploratory rule discussion below is research;
> its missing annual lunar-month selector prevents candidate support. All other
> calendar operations remain experimental with planned acceptance suites.

# Named Tamil observance subset v1

Status: independent observance fixture suite remains **planned** pending its
separate calendar-suite review. Numeric v0.3 approval does not activate it.

## Identity and scope

`thirukanitham-tamil-named-observances-v1` is a bounded toolkit collection of
separately named publisher/community rule variants, one selected method per
event. It accepts only the Thirukanitham definition, supported TN locations
using `Asia/Kolkata`, and Gregorian years 2025–2027. Nava supplies only the
Amavasya/Pournami, Sri Vaishnava Ekadashi, and Pradosham selectors attributed
to it below; other events cite their own named source in the rules and
canonical lexicon. The collection is not a single publisher's schedule. Its
calculation applies each selected rule to the toolkit's Thirukanitham
positions, and no rule is reused with Vakiya.

Nava's monthly Amavasya/Pournami pages in this source revision use their
Vakyakarana engine. The 13 Amavasya and 12 Pournami dates listed for Chennai
from November 2026 through October 2027 match the toolkit's Thirukanitham
output. These are cross-model date witnesses, not evidence that the underlying
engines or all publisher dates are equivalent.

The annual examples are for Chennai. Other supported TN coordinates use their
own sunrise, sunset, and astronomy; an output is not a statewide schedule.
SL, Ujjain/Vakiya, and any unlisted region return explicit unsupported errors.

Supported event IDs are `puthandu`, `bhogi_pandigai`, `pongal`,
`mattu_pongal`, `amavasya_tithi_day`, `pournami_tithi_day`,
`sri_vaishnava_ekadashi`, `nava_pradosham`, `sankatahara_chaturthi`,
`aadi_perukku`, `thai_poosam`, `panguni_uthiram`, `vaikasi_visakam`,
`arudra_darshan`, `karthigai_deepam`, `chitra_pournami`,
`vinayaka_chaturthi`, `sivarathri`, `deepavali`, `navaratri_ghatasthapana`,
`ayudha_puja`, `vijayadasami`, and `krishna_jayanthi`. Amavasya selection
follows Nava's published afternoon rule for the named date. Ekadashi is Nava's
published Sri Vaishnava day-selection rule; it does not represent Smartha,
ISKCON/Gauḍīya, or every Vaishnava family's calendar. Pradosham below is
specifically Nava's published 90-minute local-sunset selector. It is not
Dharmasindhu's distinct three-muhurta rule and does not claim to represent
every Shaiva family or temple. These labels do not select every family,
temple, or vrata date. Family-specific selectors below remain separate
bounded variants and do not establish one universal Tamil festival calendar.

## Rules

Every event has `{event_id, date, rule_id, tithi_index, source_ids}`. Dates
are local Gregorian dates and events sort by `(date, event_id)`. Solar events
have `tithi_index: null`; Amavasya and Pournami use indices 30 and 15.

1. `chithirai_month_day_one`: Puthandu is Chithirai 1 from the selected
   Thirukanitham month assignment. The Tamil rule uses same civil date for
   ingress before local sunset and next civil date for ingress at or after
   sunset. Sewell and Dikshit describe the after-sunrise/before-sunset Tamil
   rule; the Positional Astronomy Centre's Tamil rule covers the sunset
   cutoff. Drik's Chennai annual calendars independently witness 2025–2027
   Puthandu dates. The current profile also matches all twelve Tamil Nadu
   solar month starts in each inspected IMD cycle, 2025–2026 and 2026–2027;
   this does not reconcile the separate 2026 Gazette year-label conflict.
2. `thai_month_day_one`: Thai Pongal is the selected profile's Thai 1 date.
   The Drik Bhogi Pandigai page identifies the main Makara Sankranti day as
   Tamil Nadu's Pongal.
3. `day_before_thai_month_day_one`: Bhogi Pandigai is the civil day before
   Thai 1. `day_after_thai_month_day_one`: Mattu Pongal is the civil day after
   Thai 1. The named Drik sequence page describes Bhogi as one day before the
   main Sankranti day and Mattu Pongal as day 3; the Chennai annual lists are
   independent date witnesses for 2025–2027.
4. `amavasya_aparahna_then_sunrise`: for each Amavasya tithi interval, test
   whether it intersects the local Aparahna window on each civil date.
   Aparahna is the fourth of five equal portions of computed daylight:
   `[sunrise + 3/5 daylight, sunrise + 4/5 daylight)`. Choose the latest date
   whose Aparahna window intersects the tithi. If none intersects, choose the
   civil date whose sunrise is covered by the tithi. If neither condition
   applies, emit no date for that tithi interval.
5. `pournami_aparahna_then_sunrise`: apply the same Aparahna, latest-day,
   sunrise-fallback, and no-selection rules to Pournami tithi intervals.
6. `nava_sri_vaishnava_arunodaya_defer`: evaluate Shukla Ekadashi (tithi
   index 11) and Krishna Ekadashi (index 26) intervals against local sunrise.
   Arunodaya is the instant 96 minutes before sunrise (four ghatis of 24
   minutes). If Ekadashi is present at exactly one Arunodaya instant, use that
   sunrise date. If Dashami remains at Arunodaya but Ekadashi is present at
   that date's sunrise, defer to the following civil date. If the same
   Ekadashi interval extends past the next morning's Arunodaya, defer to the
   date after that next morning. These branches are stated by Nava for its
   Sri Vaishnava schedule and are consistent with the primary
   Hari-bhakti-vilasa prohibition on Dashami-viddha Arunodaya and its
   Dvadashi fallback. If neither Arunodaya nor sunrise falls inside the
   Ekadashi interval, no observance date is emitted; this covers a skipped
   tithi that has no sunrise date reference in Rao's panchangam guide. Tithi
   intervals are half-open, so a transition exactly at Arunodaya belongs to
   the tithi that starts there. A repeated Arunodaya does not emit two fast
   dates.
7. `nava_pradosha_sunset_90min_later_if_repeated`: evaluate Shukla Trayodashi
   (index 13) and Krishna Trayodashi (index 28) intervals against each local
   sunset window `[sunset, sunset + 5,400 seconds)`. Emit a date when its
   window has positive overlap with that tithi. If the same tithi overlaps
   two evening windows, emit only the later date, as Nava states. If no
   evening window overlaps, emit no observance date; the method supplies no
   sunrise fallback. Both tithi and window intervals are half-open: a tithi
   beginning exactly at sunset qualifies, while one beginning exactly at the
   window end does not.

8. `dharmasindhu_krishna_chaturthi_moonrise_first_if_repeated_else_second`:
   evaluate Krishna Chaturthi (tithi index 19) at each local civil day's
   computed moonrise. Toolkit moonrise uses the selected Thirukanitham apparent
   lunar position and distance. It solves the geocentric center-altitude
   threshold `horizontal parallax - 34 arcminutes - lunar semidiameter -
   elevation horizon dip`, matching the USNO upper-limb convention under
   standard refraction. Tithi and moonrise instants are half-open-second
   resolved: a Chaturthi transition exactly at moonrise belongs to Chaturthi.
   If only one moonrise lies in the tithi interval, select that date. If two
   successive moonrises do, select the earlier date (the Tritiya-linked
   reading). If neither does, select the second civil date covered by the
   tithi. More than two moonrises, an unavailable moonrise, or an unsupported
   location returns an explicit unsupported error. The Dharmasindhu rule is a
   separate named variant; the astronomical threshold is a toolkit model, not
   a claim that religious observances are defined by one universal measured
   interval.

9. `udyog_smarta_janmashtami_nishita_rohini_then_second`: for each Krishna
   Ashtami interval (tithi index 23) in the requested Gregorian year, test the
   two consecutive local nights beginning on the local civil date on which
   the Ashtami interval starts. Nishita is the eighth of fifteen equal portions
   of the local night, represented as the half-open interval
   `[sunset + 7/15 night, sunset + 8/15 night)`. If Ashtami overlaps Nishita
   on exactly one of those nights, select that date. If it overlaps both,
   select the only night on which Rohini (nakshatra index 4) also overlaps
   Nishita; if neither or both nights have Rohini, select the second date. If
   neither night has Ashtami at Nishita, select the second date. Boundaries
   use integer UTC seconds and half-open intervals. This is the detailed
   Udyog Smarta selector named in its Janmashtami puja page; it is not the
   sunrise-based Vaishnava/ISKCON rule. Udyog's general Smarta/Vaishnava
   explainer describes a different larger-overlap tie rule. That publisher
   inconsistency is retained rather than merged into this selector.

   This is a separate current Nava method, not an interpretation of the
   historical Dharmasindhu selector. The Dharmasindhu 1888 edition, printed
   p. 20 (scan PDF p. 43), defines its Pradosha interval as three muhurtas
   after sunset and gives a separate two-day rule. Where the earlier evening
   has greater coverage, it permits choosing that day only when the excess is
   sufficient for both worship and the night meal; the text does not quantify
   that sufficiency. No Dharmasindhu-based selector is implemented.

For Amavasya and Pournami, the later day wins when an interval covers
Aparahna on two consecutive days; the sunrise date is a fallback only when no
Aparahna window is covered. Thus a repeated interval does not emit two
observance dates. A short tithi skipped across Aparahna uses sunrise if the
tithi is present there; if it is skipped at both Aparahna and sunrise, no
date is inferred. Nava's annual answer pages publish dates and interval
examples for Chennai from November 2026 through October 2027. Those pages
explicitly use Vakyakarana for their tithi schedule. The implementation
matches all 25 listed dates in this window; no equality of astronomy settings
or general publisher equivalence is inferred from those matches. The pages do
not independently witness expected monthly outputs outside that window.

For Sri Vaishnava Ekadashi, Nava's rolling Chennai schedule starts on
2026-11-05 and lists dates through 2027-10-26. The separate Drik ISKCON
Chennai list identifies its own community scope and independently lists
2026-10-06, 2026-10-22, 2026-11-05, and 2026-11-21. It is a cross-lineage
date check, not an ISKCON-equivalence claim for the Sri Vaishnava event. The
two sources agree on 2026-11-05. The retained Nava page does not list October
2026; October 22 carries only the separate Drik witness. Nava lists 2026-11-20 where
the Thirukanitham result and the ISKCON list give 2026-11-21; that difference
is retained and no publisher equivalence is inferred. Monthly Ekadashi
goldens query one Gregorian month so each independently sourced slice is
identifiable apart from annual derived output.

For `nava_pradosham`, the Nava rule page states 90 minutes after local sunset
and later-day precedence when Trayodashi touches two evening windows. Its
Chennai table covers 2026-11 through 2027-10 and uses Nava's Vaakya engine.
TamilCalendar.app separately publishes Chennai/Tamil Nadu month lists for
2026 and 2027 but does not state its selector. The Thirukanitham results match
all 25 TamilCalendar.app dates in each year. The November and December 2026
monthly vectors also match Nava's four listed dates. In February 2027 the
toolkit and TamilCalendar.app select Feb 3/18 while Nava lists Feb 4/18; in
October the toolkit and TamilCalendar.app select Oct 12/27 while Nava lists
Oct 13/27. These disagreements remain visible; neither engine nor rule
equivalence is asserted. Four monthly pradosham vectors keep Nov/Dec 2026 and
Feb/Oct 2027 separate from the annual derived outputs. Those annual queries
contain 24, 25, and 25 computed dates in 2025, 2026, and 2027. The 2025 dates
have no independent annual list in this source pack; the 2026/2027 matches
witness those exact listed dates only, not the complete annual selector or
other years.

The Aparahna boundaries use integer UTC seconds, with the start rounded down
and end rounded down from the exact daylight fifths. Tithi intervals and
daylight intervals are half-open. Sunrise fallback tests `start <= sunrise <
end`.

## Operation and validation

`calendar_observances` accepts exactly:

```json
{
  "definition_id": "thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2",
  "rule_set": "thirukanitham-tamil-named-observances-v1",
  "gregorian_year": 2026,
  "month": 11,
  "context": {
    "region": "TN",
    "latitude_microdegrees": 13087840,
    "longitude_microdegrees": 80278470,
    "elevation_meters": 14,
    "time_zone": "Asia/Kolkata"
  }
}
```

`month` is optional. When present it must be an integer from 1 through 12 and
the returned event list contains only events whose selected local Gregorian
date is in that month. Without it, the operation returns the full year.

The response returns the exact definition/rule-set identity, validated
context, rule scope, astronomy and reuse notes, source records, supported
event IDs, and sorted events.

Validation order is exact top-level shape and scalar types, definition ID,
rule-set ID, definition-specific context validation, supported definition,
TN-only scope, rule-set year coverage, then required sunrise/sunset and tithi
events. Stable errors include `invalid calendar input`,
`unsupported calendar definition`, `unsupported calendar observance rule set`,
`invalid calendar context`, `unsupported time zone`, `unsupported location`,
`observance rule set unsupported for calendar definition`,
`unsupported jurisdiction for observance rule set`,
`outside supported observance rule-set coverage`, and
`solar event unavailable`.

## Sources and remaining source families

Canonical URLs, locators, page digests, and reuse status are in
`lexicon/calendar-observances.toml`. Annual source facts remain in planned
goldens and retained research pages under `tmp/research/`; no source page,
markup, image, event table, or long publisher prose is redistributed. Nava
and TamilCalendar.app reuse terms have not been established. Drik states its
data are copyrighted. The API does not claim publisher equivalence.

This is a finite source-backed subset, not milestone completion. The listed
required Tamil Nadu Thirukanitham families each have a named rule and sourced
selection/precedence conditions. Broader temple/community practice and
publisher acceptance remain open; this pack does not generalize its selectors
to all traditions. Vakiya sunset/location observance support also remains
unavailable until its own source equations are acquired; Thirukanitham is
never substituted for it.
The Nava Pradosham rule does not close the separate Dharmasindhu threshold
question or other Tamil temple/community practices.

Annual Chennai date-witness source IDs are attached only at the declared
Chennai reference context (13.087840 N, 80.278470 E, elevation 14 m). Other
locations retain the general rule citations without inheriting Chennai annual
date evidence. Annual goldens are derived whole-result regressions with only
partially independent event witnesses; they do not prove unwitnessed dates.

## Named Drik TN solar/nakshatra additions (2026-11-02)

The same finite Thirukanitham-only rule set now adds thirteen named Tamil festival
methods alongside the Nava rules above. Drik supplies several named methods;
separate Udaya, Anudina, and Pujadeep methods define day-selection precedence
where retained below. The three tithi families use source-named local windows.
Each event's `rule_id` and `source_ids` identify its selected method. No
publisher equivalence, TN-wide festival authority, or Vakiya support is
claimed.

| Event | Rule ID | Selection window and scope |
| --- | --- | --- |
| Aadi Perukku | `drik_aadi_month_day_eighteen` | Tamil Aadi month, day 18. |
| Thai Poosam | `pujadeep_thai_purnima_pushya_daytime_then_sunrise` | In Thai, prefer a local daytime overlap of Purnima and Pushya; if none, select Pushya at sunrise. Among eligible Pushya dates choose the one nearest Thai Purnima; an equal-distance tie is unsupported. |
| Panguni Uthiram | `udaya_panguni_uthiram_purnima_then_sunrise` | Prefer a local daytime overlap of Pournami and Uttara Phalguni in Panguni; otherwise choose the sunrise-Uthiram date nearest local Pournami. An equal-distance tie or no Pournami reference is unsupported. |
| Vaikasi Visakam | `drik_vaikasi_vishakha_at_sunrise` | Vishakha (Visakam) at local sunrise during Vaikasi. |
| Arudra Darshan | `anudina_margazhi_thiruvathirai_nearest_purnima` | Ardra (Thiruvathirai) at local sunrise during Margazhi. If two dates qualify, choose the one nearest local Purnima; an equal-distance tie is unsupported. Arunodaya is ritual timing, not the date selector. |
| Karthigai Deepam | `karthigai_krittika_pradosha_later_if_repeated` | Krittika (Karthigai) overlaps Pradosha, defined in this selected model as the first fifth of the local night beginning at sunset, within Karthigai month. If exactly two dates qualify, choose the later; zero or more than two is unsupported. |
| Chitra Pournami | `chithirai_pournami_at_sunrise` | Pournami tithi at local sunrise in Chithirai. The profile returns a date only when exactly one sunrise qualifies; a repeated or skipped sunrise is unsupported. |
| Vinayaka Chaturthi | `aavani_shukla_chaturthi_madhyahna_then_start` | Shukla Chaturthi (index 4) during the middle fifth of daylight in Aavani. If exactly one date qualifies, use it; if two dates qualify or none does, use the unique civil date on which the tithi begins. |
| Maha Sivaratri | `maasi_krishna_chaturdashi_nishita_then_sunset` | Krishna Chaturdashi (index 29) at the midpoint of local sunset to next sunrise during Maasi. If no Nishita midpoint qualifies, use the unique date on which Chaturdashi is present at sunset. |
| Tamil Deepavali | `drik_tn_chaturdashi_brahma_muhurta_unique` | Krishna Chaturdashi (index 29) overlaps the local 48-minute Brahma Muhurta (sunrise−96 to sunrise−48 minutes) in Aippasi. Exactly one date must qualify; repeated or skipped windows are unsupported. This is the named Drik Tamil Nadu rule, not a generic Diwali selector. |
| Navaratri Ghatasthapana | `drik_navaratri_pratipada_first_third_only` | Shukla Pratipada (index 1) overlaps the first third of local daylight in Purattasi. A unique date is required. The source names Abhijit as fallback; this finite rule does not implement that fallback, so zero or multiple first-third dates are unsupported. |
| Ayudha Puja | `drik_navaratri_navami_at_sunrise_unique` | Shukla Navami (index 9) prevails at local sunrise in the twelve-day window after the selected Navaratri start. The named Drik variant requires one unique sunrise date; repeated or skipped sunrise cases are unsupported. |
| Vijayadasami | `udyog_smarta_vijayadashami_aparahna_after_navarathiri` | Shukla Dashami (index 10) is selected in the twelve-day window after the selected Navaratri start by the Udyog Smarta rule: compare its overlap with the fourth fifth of local daylight on the two tithi days, treat differences under 24 minutes as equal, prefer full overlap to partial, choose the first day on a tie or when neither overlaps, then apply the stated next-day three-muhurta/Shravana exception. |

Vaikasi Visakam requires the target nakshatra at local sunrise; zero or multiple
qualifying sunrise dates returns `unsupported observance nakshatra selection`.
Panguni Uthiram follows Udaya's stated precedence: a unique local daytime
Pournami/Uthiram overlap wins; if there is none, the sunrise-Uthiram date
nearest local Pournami wins under Anudina's repeated-star rule. An equal-distance
tie or missing Pournami reference is unsupported. Arudra's date is
also the nakshatra running at sunrise, but
its source adds a repeated-star precedence: when two dates qualify in Margazhi,
choose the sunrise date nearest a local daytime Purnima date. An equal-distance
tie or no Purnima reference date is unsupported. Arunodaya is the ritual time,
not the date selector.

Thai Poosam uses the separately named Udaya/Pujadeep precedence. First choose
the date on which Purnima and Pushya overlap during local daytime. If no such
date exists, use dates with Pushya at sunrise. From eligible dates choose the
one with minimum civil-day distance to a local daytime Purnima date; an
equal-distance tie or no Purnima reference date returns
`unsupported observance nakshatra selection`. This retains the source's
full-moon association and its explicit sunrise fallback rather than silently
choosing the first or last repeated Pushya.

Karthigai uses the local Pradosha interval from sunset through the first fifth
of the remaining night. This matches the interval shown in the retained
Pujadeep timing examples and lets a star that begins shortly after sunset
qualify. Its selected repeated-day rule chooses the later of exactly two
qualifying evenings, near the Karthigai full moon. Anudina describes a different
first-evening precedence; the named rule here follows Pujadeep. A month with no
qualifying Pradosha overlap or more than two is unsupported. These named source
methods remain distinct from the independent annual date witnesses.

Chitra Pournami uses the full-moon tithi at local sunrise inside the selected
Thirukanitham Chithirai month. Zero or multiple sunrise dates return
`unsupported observance tithi selection`; the selector does not add an
unpublished Aparahna or evening choice. Vinayaka Chaturthi uses Madhyahna as the
third of five equal parts of local daylight (the interval from two-fifths to
three-fifths after sunrise). The unique-Madhyahna case selects that day; if the
tithi hits two Madhyahnas or neither, the selected source rule uses the tithi's
start date, following the special Ganesh Chaturthi precedence attributed to
Hemadri. If the selected start date is missing or ambiguous inside Aavani, the
query is unsupported. This named rule does not imply all local Vinayaka customs
use the same tithi decision.

Tamil Deepavali selects the unique Aippasi civil day whose fixed 48-minute Brahma Muhurta, from 96 to 48 minutes before local sunrise, overlaps Krishna Chaturdashi. Drik’s Chennai Tamil Deepavali page distinguishes the Tamil Nadu Chaturdashi-at-Brahma-Muhurta day from the rest-of-India Amavasya-at-Pradosh day; the selected rule is therefore named and regional. Repeated or skipped qualifying muhurta windows return `unsupported observance tithi selection`; no fallback to a generic Amavasya date is inferred. The retained Aṣṭāṅga Hṛdayam Sūtrasthāna 2.1 source defines this particular window. The Chennai Drik annual lists witness 2025-10-20, 2026-11-08 and 2027-10-28.


The added Navaratri/Ayudha/Vijayadasami method pack is deliberately finite.
Ghatasthapana follows Drik’s Pratipada-at-first-third selector but omits its
Abhijit fallback. Ayudha Puja follows Drik’s Navami-at-sunrise variant. The
TamilCalendar.com statewide 2026 list places Ayudha Puja on 2026-10-19, while
Drik’s Chennai Tamil festival list and its Navami-at-sunrise variant place it
on 2026-10-20; both exact source dates remain visible, and only the matching
source date is attached to an event. Vijayadasami follows Udyog’s published
Smarta rule and its limited repeated/skipped conditions; it does not claim
parity with every regional panchangam. Chennai Drik date lists give
Navaratri 2025-09-22, 2026-10-11, 2027-09-30; Ayudha Puja 2025-10-01,
2026-10-20, 2027-10-09; and Vijayadasami 2025-10-02, 2026-10-20,
2027-10-09. TamilCalendar.com independently lists Navaratri 2026-10-11 and
Vijayadasami 2026-10-20.

Maha Sivaratri checks Krishna Chaturdashi at the midpoint from local sunset to
the following sunrise, the source-defined Nishita instant. Only when no
Nishita midpoint falls in the tithi does the rule fall back to Chaturdashi at
sunset; repeated or missing dates in the selected tier are unsupported. The
solar-month restriction is Maasi for this finite TN rule set. Chennai's Drik
pages list Maha Sivaratri on 2025-02-26, 2026-02-15 and 2027-03-06; the
TamilCalendar.com 2026 list independently gives 2026-02-15. Chitra Pournami
dates are 2025-05-12, 2026-05-01 and 2027-04-20 from the Chennai Drik pages;
TamilCalendar.com independently witnesses 2026-05-01. Vinayaka Chaturthi's
Chennai Drik page lists 2025-08-27, 2026-09-14 and 2027-09-04, with the
2026 TamilCalendar.com date list independently witnessing 2026-09-14.
Panjangam's Chennai 2025 Panguni Uthiram page lists 2025-04-11. NammaCalendar
lists Karthigai Deepam on 2025-12-03 under its explicitly named Vakya
panchangam; this is a cross-profile date witness only. These independent month
vectors remain distinct from whole-year astronomy-derived regressions.

Thai Poosam's sunrise/full-moon precedence is stated in the Udaya and Pujadeep
method pages; the 2024 Udaya example demonstrates selecting the Purnima day
when Pushya reaches the following sunrise, and Pujadeep specifies nearest-day
selection. The sunrise date selector is separately stated by Udaya for
Thiruvathirai in Margazhi; Anudina supplies the repeated-star rule choosing the
occurrence nearest Purnima. These sources distinguish the event date from the
small-hours darshan. Udaya states Panguni precedence as Pournami with Uthiram;
Anudina supplies the nearest-full-moon rule when the star repeats. The Karthigai rule combines Drik's
Tamil-month/Ratrimana description with Pujadeep's explicit evening (Pradosha)
selection and later-day tie rule. Pujadeep's displayed clock examples are for
Washington DC and are not used as Chennai astronomical inputs. The 2026
Chennai independent date list from TamilCalendar.com is an independent
publication and says its calculations use Swiss Ephemeris with Lahiri ayanamsa;
it is a date witness only, not an algorithm input. The witnessed dates are
Thai Poosam 2026-02-01, Panguni Uthiram 2026-04-01, Vaikasi Visakam 2026-05-30,
Aadi Perukku 2026-08-03, and Arudhra Darisanam 2026-01-03 and 2026-12-24.
Karthigai Deepam 2026-11-24 is also listed. The Drik Chennai annual list gives
the same dates. Source IDs with Chennai in their name attach only to the exact
Chennai reference coordinates, and their observed date lists are limited to
the dates actually listed by that source. The independent vectors remain
planned; full-year event outputs are profile-derived regressions.

Krishna Jayanthi is the named Udyog Smarta Nishita selector above. Three
separate Chennai month slices record the 2025, 2026, and 2027 results. Drik's
Chennai pages list 2025-08-15, 2026-09-04, and 2027-08-25; the 2026
TamilCalendar.com list independently gives 2026-09-04. The selected
Thirukanitham rule's 2027 result is recorded as a profile result and the
Drik/selected-rule date difference remains visible. Udyog also publishes a
2027 result for Kanchipuram, which is a different location and is not attached
as a Chennai witness. These month slices remain planned; annual calendar
outputs remain derived regressions.

The rule pack remains incomplete: these bounded methods do not resolve all
temple/community variants, broader holiday acceptance, Smartha Ekadashi, or
Vakiya observances. No universal festival calendar or Vakiya-equivalent date
is implied by this addition.
