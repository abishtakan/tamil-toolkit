# Thiruvalluvar year convention v1

Status: planned calendar contract. The operation is a named profile convention,
not an official-date lookup, and its suite requires the separate calendar-owner
review.

## Convention and domain

`thiruvalluvar_year_info` accepts exactly
`{convention_id,date,context}`. The only supported convention is
`tn-thiruvalluvar-thai1-thirukanitham-v1`. It requires a valid Thirukanitham
TN context and a Gregorian date in 2025–2027. Dates outside that finite span,
SL contexts, Vākyakaraṇa contexts, and unknown convention IDs fail explicitly.

The named convention follows the stated 31 BCE era anchor and treats Thai 1 as
its year boundary. It resolves that boundary using month 10 (`Thai`) from the
selected Thirukanitham definition and TN location. It returns Gregorian year
plus 30 before that profile boundary, and Gregorian year plus 31 on or after
it. The API returns the computed `thai1_date`, `boundary_status`, the profile
definition and context, an explicit `official_equivalence: "not_established"`,
and source locators.

This is not a claim that Thirukanitham v1 reproduces every Tamil Nadu official
date. The official Gazette issue 2, Part I witness for 2026-01-14 identifies
Margazhi 30 and Thiruvalluvar 2056, while the Thirukanitham TN profile starts
Thai 1 on that Gregorian date. Issue 31 on 2026-01-23 is Thai 9 / year 2057.
The two Gazette dates do not pin the exact official Thai-1 boundary. The API
returns both witnesses and this source conflict; its 2026-01-14 label must not
be represented as the official Gazette year. A future official lookup needs
an authoritative, versioned boundary source and annual date observations.

## Sources and limits

The Mayiladuthurai District Administration's Tamil Development page identifies
G.O.(Ms) No. 91, Personnel and Administrative Department, 1981-02-03, as the
order for use of the Thiruvalluvar year in official proceedings; that locator
does not state its day boundary. The Tamil Nadu Governor's Address (2008),
printed page 35, states the 31 BCE anchor and Thai 1 as the start of the Tamil
year. Official Gazette records verify year labels on discrete dates but do not
by themselves prove a universal rule for every civil date.

The Thirukanitham calculation uses the already contracted finite profile and
does not add an independent astronomy model. This era convention is TN-only,
not a Sri Lankan regional rule. It does not infer a boundary from the Thai 2
Thiruvalluvar Day holiday. New vectors must include 2025 before/on/after the
profile boundary, the known 2026 Gazette conflict, invalid region/profile and
unsupported years; expected outputs from the profile are tagged as derived
regressions.

The independent review also identified the 2011 repeal record
(<https://www.indiacode.nic.in/handle/123456789/19525?locale=en>) as a
required current-authority check. The 2008 address is historical evidence;
this implementation has not reconciled the later enactment with the era
boundary. Neither the repeal alone nor the astronomical profile establishes
the current official Thiruvalluvar-year rule. Calendar activation remains
pending this evidence review.
