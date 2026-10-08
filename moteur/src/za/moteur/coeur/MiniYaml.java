package za.moteur.coeur;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Petit lecteur YAML (sous-ensemble) pour que le cœur et le simulateur tournent sans Bukkit :
 * cartes imbriquées par indentation, listes « - valeur », listes de cartes « - cle: valeur », listes en ligne [a, b],
 * chaînes entre guillemets, commentaires #. Suffisant pour graphe.yml et reactions.yml.
 */
public final class MiniYaml {
    private MiniYaml() {
    }

    private static final class Ligne {
        final int ind;
        final String txt;

        Ligne(int ind, String txt) {
            this.ind = ind;
            this.txt = txt;
        }
    }

    public static Map<String, Object> lire(Path p) throws IOException {
        List<Ligne> l = new ArrayList<>();
        for (String s : Files.readAllLines(p, StandardCharsets.UTF_8)) {
            String t = sansCommentaire(s);
            if (t.trim().isEmpty()) continue;
            int ind = 0;
            while (ind < t.length() && t.charAt(ind) == ' ') ind++;
            l.add(new Ligne(ind, t.trim()));
        }
        int[] pos = {0};
        Object o = bloc(l, pos, 0);
        if (o instanceof Map) {
            @SuppressWarnings("unchecked")
            Map<String, Object> m = (Map<String, Object>) o;
            return m;
        }
        return new LinkedHashMap<>();
    }

    private static String sansCommentaire(String s) {
        boolean g = false;
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '"') g = !g;
            if (c == '#' && !g && (i == 0 || s.charAt(i - 1) == ' ')) return s.substring(0, i);
        }
        return s;
    }

    private static Object bloc(List<Ligne> l, int[] pos, int ind) {
        if (pos[0] >= l.size()) return new LinkedHashMap<String, Object>();
        if (l.get(pos[0]).txt.startsWith("- ") || l.get(pos[0]).txt.equals("-")) return liste(l, pos, l.get(pos[0]).ind);
        return carte(l, pos, l.get(pos[0]).ind);
    }

    private static List<Object> liste(List<Ligne> l, int[] pos, int ind) {
        List<Object> r = new ArrayList<>();
        while (pos[0] < l.size()) {
            Ligne a = l.get(pos[0]);
            if (a.ind != ind || !a.txt.startsWith("-")) break;
            String v = a.txt.length() > 1 ? a.txt.substring(1).trim() : "";
            pos[0]++;
            int k = cle(v);
            // un élément est une carte seulement si sa clé ressemble à un identifiant (pas une phrase)
            if (k > 0 && !v.substring(0, k).trim().matches("[A-Za-z0-9_.\\-]+")) k = -1;
            if (k > 0) {
                // élément carte : la première paire sur la ligne du tiret, les suivantes indentées
                Map<String, Object> m = new LinkedHashMap<>();
                String c = v.substring(0, k).trim();
                String reste = v.substring(k + 1).trim();
                if (reste.isEmpty() && pos[0] < l.size() && l.get(pos[0]).ind > ind) m.put(c, bloc(l, pos, l.get(pos[0]).ind));
                else m.put(c, scalaire(reste));
                if (pos[0] < l.size() && l.get(pos[0]).ind > ind && !l.get(pos[0]).txt.startsWith("-")) {
                    Map<String, Object> m2 = carte(l, pos, l.get(pos[0]).ind);
                    m.putAll(m2);
                }
                r.add(m);
            } else {
                r.add(scalaire(v));
            }
        }
        return r;
    }

    private static Map<String, Object> carte(List<Ligne> l, int[] pos, int ind) {
        Map<String, Object> m = new LinkedHashMap<>();
        while (pos[0] < l.size()) {
            Ligne a = l.get(pos[0]);
            if (a.ind < ind) break;
            if (a.ind > ind) {
                pos[0]++;
                continue;
            }
            if (a.txt.startsWith("-")) break;
            int k = cle(a.txt);
            if (k < 0) {
                pos[0]++;
                continue;
            }
            String c = deguillemeter(a.txt.substring(0, k).trim());
            String v = a.txt.substring(k + 1).trim();
            pos[0]++;
            if (v.isEmpty()) {
                if (pos[0] < l.size() && (l.get(pos[0]).ind > ind || (l.get(pos[0]).ind == ind && l.get(pos[0]).txt.startsWith("-"))))
                    m.put(c, bloc(l, pos, l.get(pos[0]).ind));
                else m.put(c, "");
            } else {
                m.put(c, scalaire(v));
            }
        }
        return m;
    }

    /** position du « : » qui sépare la clé (hors guillemets), -1 sinon */
    private static int cle(String s) {
        boolean g = false;
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '"') g = !g;
            if (c == ':' && !g && (i + 1 == s.length() || s.charAt(i + 1) == ' ')) return i;
        }
        return -1;
    }

    private static Object scalaire(String v) {
        if (v.startsWith("[") && v.endsWith("]")) {
            List<Object> r = new ArrayList<>();
            String in = v.substring(1, v.length() - 1).trim();
            if (in.isEmpty()) return r;
            StringBuilder b = new StringBuilder();
            boolean g = false;
            for (char c : in.toCharArray()) {
                if (c == '"') g = !g;
                if (c == ',' && !g) {
                    r.add(scalaire(b.toString().trim()));
                    b.setLength(0);
                } else b.append(c);
            }
            if (b.length() > 0) r.add(scalaire(b.toString().trim()));
            return r;
        }
        return deguillemeter(v);
    }

    private static String deguillemeter(String v) {
        if (v.length() >= 2 && ((v.startsWith("\"") && v.endsWith("\"")) || (v.startsWith("'") && v.endsWith("'")))) {
            return v.substring(1, v.length() - 1).replace("\\\"", "\"").replace("\\\\", "\\");
        }
        return v;
    }

    // ---------------------------------------------------------------- accès typés

    public static String txt(Object o, String d) {
        return o == null ? d : String.valueOf(o);
    }

    public static double num(Object o, double d) {
        if (o == null) return d;
        try {
            return Double.parseDouble(String.valueOf(o).trim());
        } catch (NumberFormatException e) {
            return d;
        }
    }

    public static boolean vrai(Object o) {
        return o != null && String.valueOf(o).trim().equalsIgnoreCase("true");
    }

    @SuppressWarnings("unchecked")
    public static Map<String, Object> carte(Object o) {
        return o instanceof Map ? (Map<String, Object>) o : new LinkedHashMap<>();
    }

    @SuppressWarnings("unchecked")
    public static List<Object> liste(Object o) {
        return o instanceof List ? (List<Object>) o : new ArrayList<>();
    }
}
