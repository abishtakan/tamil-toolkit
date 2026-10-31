// Development-only independent oracle: ICU interprets the frozen CLDR rules.
import com.ibm.icu.text.DecimalFormat;
import com.ibm.icu.text.DecimalFormatSymbols;
import com.ibm.icu.text.RuleBasedNumberFormat;
import com.ibm.icu.util.ULocale;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.text.Normalizer;

class NumeralReference {
    static String quote(String value) {
        StringBuilder result = new StringBuilder("\"");
        for (char c : Normalizer.normalize(value, Normalizer.Form.NFC).toCharArray()) {
            if (c == '"' || c == '\\') result.append('\\').append(c);
            else if (c < 32 || c > 126) result.append(String.format("\\u%04x", (int)c));
            else result.append(c);
        }
        return result.append('"').toString();
    }
    static RuleBasedNumberFormat formatter(String path) throws Exception {
        return new RuleBasedNumberFormat(Files.readString(Path.of(path)), new ULocale("ta"));
    }
    public static void main(String[] args) throws Exception {
        RuleBasedNumberFormat tn = formatter(args[0]);
        RuleBasedNumberFormat sl = formatter(args[1]);
        StringBuilder integers = new StringBuilder();
        for (String line : Files.readAllLines(Path.of(args[2]))) {
            long value = Long.parseLong(line);
            integers.append("{\"value\":").append(value);
            for (int i = 0; i < 2; i++) {
                RuleBasedNumberFormat fmt = i == 0 ? tn : sl;
                integers.append(i == 0 ? ",\"TN\":{" : ",\"SL\":{")
                    .append("\"numbering\":").append(quote(fmt.format(value, "%spellout-numbering")))
                    .append(",\"cardinal\":").append(quote(fmt.format(value, "%spellout-cardinal"))).append('}');
            }
            integers.append("}\n");
        }
        DecimalFormat digits = new DecimalFormat("#,##,##0.00", new DecimalFormatSymbols(ULocale.ROOT));
        StringBuilder money = new StringBuilder();
        for (String line : Files.readAllLines(Path.of(args[3]))) {
            long value = Long.parseLong(line);
            long absolute = Math.abs(value);
            money.append("{\"value\":").append(value).append(",\"formatted\":")
                .append(quote(digits.format(BigDecimal.valueOf(value, 2))));
            for (int i = 0; i < 2; i++) {
                RuleBasedNumberFormat fmt = i == 0 ? tn : sl;
                money.append(i == 0 ? ",\"TN\":{" : ",\"SL\":{")
                    .append("\"major\":").append(quote(fmt.format(absolute / 100, "%spellout-cardinal")))
                    .append(",\"minor\":").append(quote(fmt.format(absolute % 100, "%spellout-cardinal"))).append('}');
            }
            money.append("}\n");
        }
        Files.writeString(Path.of(args[4]), integers, StandardCharsets.UTF_8);
        Files.writeString(Path.of(args[5]), money, StandardCharsets.UTF_8);
    }
}
