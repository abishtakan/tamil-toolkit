# TSCII byte-inventory audit

The IANA draft identifies 80 as Tamil digit zero, 86 as Grantha HA, 87 as
KSHA, 8B/8C as their pure consonants, 92–94 as quotation marks, 95 as Tamil
digit six, A1–A8/AA as vowel glyphs, and A9 as copyright. A0 and FF are
unassigned in that table. Unicode scalar values follow the Unicode Tamil chart.
The TamilUtil encoder's doubled 86 spelling for HA and HA-AA is an error:
the draft assigns HA to the single byte 86 and HA-pulli to 8B. The
source also incorrectly spells HA-pulli as 8B 8B 20. Consequently 86 86
represents two letters and 8B 8B 20 represents two HA-pulli letters and a space. Golden cases capture this correction before the implementation.

Visual-order KSHA forms use the same A1–A8/AA vowel positions as the adjacent
Grantha consonants. Aril's A6 87 C7 AU spelling conflicts with IANA: C7 is LLA,
while AA is the AU length mark; interpret the former as KSHA-E followed by LLA.
Coverage must distinguish the audit's assigned bytes from all possible historic
font variants and from contextual sequences; do not claim complete standard
conformance without independent exhaustive evidence.

Sources: https://data.iana.org/archive/ietf-charsets/pdf00000.pdf pages 10–13;
https://www.unicode.org/charts/PDF/U0B80.pdf;
https://github.com/digital-tamil/aril (TSCII comparison).

The updated profile maps every assigned single-byte position in the IANA table;
A0 and FF are unassigned. It also includes 11 vowel forms each for HA and KSHA, and tests six
preposed-vowel forms across all 23 consonant bases.
