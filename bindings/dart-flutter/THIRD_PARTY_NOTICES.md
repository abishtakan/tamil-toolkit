# Third-party notices

Original tamil-toolkit code is MIT licensed. The following upstream data and
mapping notices retain their original terms; the project MIT license does not
replace them. Generated lexicon copies are checked against the canonical data.

Unicode 17 and CLDR 49 data: https://www.unicode.org/ and https://cldr.unicode.org/
Bamini mapping sources: https://github.com/ag-sanjjeev/app-tamil-fonts-unicode-converter
and https://github.com/Pakeetharan/unicode-bamini-converter
TSCII mapping source: https://github.com/mayooresan/Android-TamilUtil
LT-TM and Vanavil mapping references: Azhagi+ Portable configurations; source
digests and scope are recorded in docs/specs/codec-lt-tm.md and
docs/specs/codec-vanavil.md. Their bundled terms remain applicable to the
derived mapping tables.
Tamil calendar display labels are extracted as short factual name lists from
Tamil Virtual Academy's educational page; its reuse terms were not stated, so
no license or permission is asserted and no prose or page/table image is copied.
Tamil Gregorian weekday labels are from CLDR 49 under Unicode data terms.
The Latin transliterations of the seven weekday names are from Vidya Mohan and
Rajiv Ranjan, *Basic Tamil* (2024), chapter 6.1, under CC BY-NC 4.0; attribution
and the noncommercial condition remain applicable. No images or surrounding
text from the book are included.
Historical Vakyakarana solar-transit, Bhupadi correction, and Candra-vakya
values are transcribed as mathematical facts from *Vakyakarana with
Sundararaja's Laghuprakashika*, eds. T. S. Kuppanna Sastri and K. V. Sarma,
1962, printed English translation pp. 251-253 and Appendix II pp. 125-134.
No source prose or scan images are included; the publication's redistribution
terms were not established. See docs/specs/calendar-vakya-solar-v1.md and
docs/specs/calendar-vakya-moon-v1.md before redistributing this data.
The Ujjain mean-sunrise civil profile uses the same 1962 source, Bag (2001)
for the Kali epoch's Gregorian equivalence, Pai (2019) as an independent
transit-method cross-check, and IMD station metadata. It does not include
source prose or page images; see docs/specs/calendar-vakya-civil-v1.md. The
1962 source's redistribution terms remain unresolved.
The Thirukanitham Drik profile depends on Rust `astro` 2.0.0 by Saurav
Sachidanand, distributed under the MIT license; its complete upstream license
text is copied below. GeoNames city-point coordinates are attributed to
GeoNames and used under CC BY 4.0. Drik Panchang, IMD, and Nava Panchangam
provide factual date and rule witnesses in planned calendar suites. The named
Nava observance subset records its published Aparahna-then-sunrise selection
rule and factual annual dates; Nava's annual tithi pages use Vakyakarana, so
their match to Thirukanitham is not a publisher-equivalence claim. Reuse terms
for these page tables are not established, and no source page or markup is
copied. Exact sources, locators, coverage, and retained-page digests are in
lexicon/calendar-observances.toml and docs/specs/calendar-observances-v1.md.
Exact sources, revisions, digests and profile limits are recorded at:
https://github.com/abishtakan/tamil-toolkit/tree/HEAD/tests/reference
and https://github.com/abishtakan/tamil-toolkit/tree/HEAD/docs/specs

Binary distributions also include THIRD_PARTY_LICENSES.txt, generated from the
locked Rust dependency graph with the complete upstream license texts.

## Unicode License V3

```text
UNICODE LICENSE V3

COPYRIGHT AND PERMISSION NOTICE

Copyright © 1991-2026 Unicode, Inc.

NOTICE TO USER: Carefully read the following legal agreement. BY
DOWNLOADING, INSTALLING, COPYING OR OTHERWISE USING DATA FILES, AND/OR
SOFTWARE, YOU UNEQUIVOCALLY ACCEPT, AND AGREE TO BE BOUND BY, ALL OF THE
TERMS AND CONDITIONS OF THIS AGREEMENT. IF YOU DO NOT AGREE, DO NOT
DOWNLOAD, INSTALL, COPY, DISTRIBUTE OR USE THE DATA FILES OR SOFTWARE.

Permission is hereby granted, free of charge, to any person obtaining a
copy of data files and any associated documentation (the "Data Files") or
software and any associated documentation (the "Software") to deal in the
Data Files or Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, and/or sell
copies of the Data Files or Software, and to permit persons to whom the
Data Files or Software are furnished to do so, provided that either (a)
this copyright and permission notice appear with all copies of the Data
Files or Software, or (b) this copyright and permission notice appear in
associated Documentation.

THE DATA FILES AND SOFTWARE ARE PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT OF
THIRD PARTY RIGHTS.

IN NO EVENT SHALL THE COPYRIGHT HOLDER OR HOLDERS INCLUDED IN THIS NOTICE
BE LIABLE FOR ANY CLAIM, OR ANY SPECIAL INDIRECT OR CONSEQUENTIAL DAMAGES,
OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION,
ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THE DATA
FILES OR SOFTWARE.

Except as contained in this notice, the name of a copyright holder shall
not be used in advertising or otherwise to promote the sale, use or other
dealings in these Data Files or Software without prior written
authorization of the copyright holder.
```

## ag-sanjjeev Bamini source (MIT)

```text
MIT License

Copyright (c) 2023 ag-sanjjeev

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Pakeetharan Balasubramaniam Bamini reference (MIT)

```text
MIT License

Copyright (c) 2025 Pakeetharan Balasubramaniam

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Jay Mayu Android TamilUtil reference (MIT)

```text
The MIT License (MIT)

Copyright (c) 2016 Jay Mayu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Above license is for Tamil-Utill only. We do not offer fonts used in the example under the same license.
```

## astro 2.0.0 by Saurav Sachidanand (MIT)

```text
Copyright (c) 2015, 2016 Saurav Sachidanand

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

