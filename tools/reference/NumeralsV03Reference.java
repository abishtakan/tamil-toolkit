// Development-only independent oracle: ICU interprets pinned CLDR 49 RBNF.
import com.ibm.icu.text.RuleBasedNumberFormat;
import com.ibm.icu.util.ULocale;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.text.Normalizer;

class NumeralsV03Reference {
    static String quote(String value) {
        StringBuilder result = new StringBuilder("\"");
        for (char c : Normalizer.normalize(value, Normalizer.Form.NFC).toCharArray()) {
            if (c == '"' || c == '\\') result.append('\\').append(c);
            else if (c < 32 || c > 126) result.append(String.format("\\u%04x", (int)c));
            else result.append(c);
        }
        return result.append('"').toString();
    }

    static RuleBasedNumberFormat formatter(Path rules, String locale) throws Exception {
        return new RuleBasedNumberFormat(Files.readString(rules), new ULocale(locale));
    }

    static String values(Path input, RuleBasedNumberFormat tn, RuleBasedNumberFormat sl,
                         String ruleset) throws Exception {
        StringBuilder output = new StringBuilder();
        for (String line : Files.readAllLines(input)) {
            long value = Long.parseLong(line);
            output.append("{\"value\":").append(value)
                .append(",\"TN\":").append(quote(tn.format(value, ruleset)))
                .append(",\"SL\":").append(quote(sl.format(value, ruleset))).append("}\n");
        }
        return output.toString();
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 7) throw new IllegalArgumentException("expected seven paths");
        RuleBasedNumberFormat root = formatter(Path.of(args[0]), "root");
        RuleBasedNumberFormat tn = formatter(Path.of(args[1]), "ta");
        RuleBasedNumberFormat sl = formatter(Path.of(args[2]), "ta");
        String ordinals = values(Path.of(args[3]), tn, sl, "%spellout-ordinal");
        StringBuilder traditionalRows = new StringBuilder();
        for (String line : Files.readAllLines(Path.of(args[4]))) {
            long value = Long.parseLong(line);
            traditionalRows.append("{\"value\":").append(value)
                .append(",\"formatted\":").append(quote(root.format(value, "%tamil")))
                .append("}\n");
        }
        Files.writeString(Path.of(args[5]), ordinals, StandardCharsets.UTF_8);
        Files.writeString(Path.of(args[6]), traditionalRows.toString(), StandardCharsets.UTF_8);
    }
}
