import { format_date, format_fraction, get_letters, type DateStyle, type Locale } from "tamil-toolkit";
import { init, to_words } from "tamil-toolkit/web";

const locale: Locale = "SL";
const style: DateStyle = "full";
const date: string = format_date(2024, 2, 29, locale, style, "tamil");
const fraction: string = format_fraction(2, 4);
const letters: string[] = get_letters("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd");
const ready: ReturnType<typeof init> = init();
const words: string = to_words(1025, locale);
void [date, fraction, letters, ready, words];
