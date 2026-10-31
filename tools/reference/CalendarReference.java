// Development-only ICU 79.1 / CLDR 49 calendar evidence, not a runtime adapter.
import com.ibm.icu.text.DateFormat;
import com.ibm.icu.text.DateFormatSymbols;
import com.ibm.icu.text.SimpleDateFormat;
import com.ibm.icu.util.GregorianCalendar;
import com.ibm.icu.util.LocaleData;
import com.ibm.icu.util.TimeZone;
import com.ibm.icu.util.ULocale;
import com.ibm.icu.util.VersionInfo;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.text.Normalizer;

class CalendarReference {
    static String q(String value) {
        StringBuilder b = new StringBuilder("\"");
        for (char c : Normalizer.normalize(value, Normalizer.Form.NFC).toCharArray()) {
            if (c == '"' || c == '\\') b.append('\\').append(c);
            else if (c < 32 || c > 126) b.append(String.format("\\u%04x", (int)c));
            else b.append(c);
        }
        return b.append('"').toString();
    }
    static String array(String[] values, int start, int end) {
        StringBuilder b = new StringBuilder("[");
        for (int i = start; i < end; i++) { if (i > start) b.append(','); b.append(q(values[i])); }
        return b.append(']').toString();
    }
    static final String[] STYLES = {"short", "medium", "long", "full"};
    static final int[] STYLE_CODES = {DateFormat.SHORT, DateFormat.MEDIUM, DateFormat.LONG, DateFormat.FULL};
    static ULocale locale(String region, String digits) {
        return new ULocale((region.equals("TN") ? "ta_IN" : "ta_LK") + "@calendar=gregorian;numbers=" + (digits.equals("latin") ? "latn" : "tamldec"));
    }
    static SimpleDateFormat formatter(String region, String digits, int style) {
        ULocale locale = locale(region, digits);
        SimpleDateFormat f = (SimpleDateFormat)DateFormat.getDateInstance(style, locale);
        GregorianCalendar calendar = new GregorianCalendar(TimeZone.getTimeZone("UTC"), locale);
        calendar.setGregorianChange(new java.util.Date(Long.MIN_VALUE));
        calendar.setLenient(false);
        f.setCalendar(calendar);
        f.setTimeZone(TimeZone.getTimeZone("UTC"));
        return f;
    }
    public static void main(String[] args) throws Exception {
        if (!LocaleData.getCLDRVersion().toString().startsWith("49.")) throw new Exception("Expected CLDR 49");
        StringBuilder data = new StringBuilder("{\"icu_version\":").append(q(VersionInfo.ICU_VERSION.toString()))
            .append(",\"cldr_version\":").append(q(LocaleData.getCLDRVersion().toString())).append(",\"profiles\":{");
        for (String region : new String[]{"TN", "SL"}) {
            if (region.equals("SL")) data.append(',');
            DateFormatSymbols s = new DateFormatSymbols(locale(region, "latin"));
            data.append(q(region)).append(":{\"months\":").append(array(s.getMonths(),0,12))
                .append(",\"abbreviated_months\":").append(array(s.getShortMonths(),0,12))
                .append(",\"weekdays\":").append(array(s.getWeekdays(),1,8)).append(",\"patterns\":{");
            for (int i=0;i<4;i++) { if(i>0)data.append(','); data.append(q(STYLES[i])).append(':').append(q(formatter(region,"latin",STYLE_CODES[i]).toPattern())); }
            data.append("}}");
        }
        Files.writeString(Path.of(args[1]),data.append("}}"),StandardCharsets.UTF_8);
        StringBuilder rows = new StringBuilder();
        for (String line : Files.readAllLines(Path.of(args[0]))) {
            LocalDate date = LocalDate.parse(line);
            rows.append("{\"year\":").append(date.getYear()).append(",\"month\":").append(date.getMonthValue()).append(",\"day\":").append(date.getDayOfMonth());
            for (String region : new String[]{"TN", "SL"}) {
                rows.append(',').append(q(region)).append(":{");
                for(int i=0;i<4;i++) {
                    if(i>0)rows.append(','); rows.append(q(STYLES[i])).append(":{");
                    for(String digits : new String[]{"latin","tamil"}) {
                        if(digits.equals("tamil"))rows.append(',');
                        SimpleDateFormat f = formatter(region,digits,STYLE_CODES[i]);
                        GregorianCalendar c = (GregorianCalendar)f.getCalendar();
                        c.clear(); c.set(date.getYear(),date.getMonthValue()-1,date.getDayOfMonth(),12,0,0);
                        rows.append(q(digits)).append(':').append(q(f.format(c.getTime())));
                    }
                    rows.append('}');
                }
                rows.append('}');
            }
            rows.append("}\n");
        }
        Files.writeString(Path.of(args[2]),rows,StandardCharsets.UTF_8);
    }
}
