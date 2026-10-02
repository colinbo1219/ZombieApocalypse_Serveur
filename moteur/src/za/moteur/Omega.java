package za.moteur;

import org.bukkit.Bukkit;
import za.moteur.coeur.Evenement;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;

/**
 * Ω — le narrateur facultatif (bible IA-15). DÉSACTIVÉ par défaut ; il faut une clé d'API dans config.yml
 * (omega.cle) et « systemes.omega: true ». Quelques appels par jour au plus (omega.quota_jour) : Léa écrit sa chronique
 * du soir à partir des vrais événements de la Chronique. Si l'appel échoue, rien ne casse : Léa garde ses textes fixes.
 * Appel HTTP direct à l'API Messages (pas de dépendance à embarquer dans le plugin).
 */
public final class Omega {
    private final ZAMoteur z;
    private final HttpClient http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(15)).build();
    private int jourQuota = -1;
    private int appelsJour;
    private String derniereErreur = "";
    private String dernierTexte = "";

    Omega(ZAMoteur z) {
        this.z = z;
    }

    private String cle() {
        return z.getConfig().getString("omega.cle", "");
    }

    private boolean pret() {
        return z.actif("omega") && !cle().isEmpty();
    }

    /** une fois par jour : la chronique du soir de Léa */
    void jour() {
        if (!pret() || z.lea.silence) return;
        List<Evenement> l;
        synchronized (z.monde) {
            l = z.monde.chronique.derniers(40);
        }
        StringBuilder b = new StringBuilder();
        for (Evenement e : l) if (e.gravite >= 2 && e.jour >= z.jour() - 1) b.append("- ").append(e.ligne()).append(" (lieu : ").append(z.nomLieu(e)).append(")\n");
        if (b.length() == 0) return;
        String consigne = "Voici les événements des dernières 24 heures dans la région de Saint-Aurèle (Québec), pendant une épidémie de morts-vivants. "
                + "Les événements marqués (faux) sont des rumeurs : présente-les comme non confirmées.\n\n" + b
                + "\nÉcris la chronique radio du soir de Léa : 3 à 5 phrases courtes, en français québécois sobre, avec les accents, "
                + "sans inventer de lieu ni de mort qui ne soient pas dans la liste. Réponds uniquement par le texte lu à l'antenne.";
        demander(consigne, t -> {
            for (String phrase : t.split("(?<=[.!?…])\\s+")) if (!phrase.isBlank()) z.pont.radio("lea", phrase.trim());
        });
    }

    /** un appel ; le rappel s'exécute sur le fil principal */
    public void demander(String consigne, Consumer<String> rappel) {
        if (!pret()) return;
        if (jourQuota != z.jour()) {
            jourQuota = z.jour();
            appelsJour = 0;
        }
        if (appelsJour >= z.getConfig().getInt("omega.quota_jour", 4)) return;
        appelsJour++;
        String modele = z.getConfig().getString("omega.modele", "claude-opus-5-5");
        String systeme = "Tu es Léa, animatrice d'une petite radio communautaire qui survit dans le Québec rural pendant une épidémie. "
                + "Ton ton est humain, fatigué, courageux. Jamais de gore gratuit, jamais de méta, pas de listes.";
        String corps = "{\"model\":" + json(modele) + ",\"max_tokens\":1024"
                + ",\"output_config\":{\"effort\":\"low\"},\"fallbacks\":\"default\""
                + ",\"system\":" + json(systeme)
                + ",\"messages\":[{\"role\":\"user\",\"content\":" + json(consigne) + "}]}";
        HttpRequest req = HttpRequest.newBuilder(URI.create(z.getConfig().getString("omega.url", "https://api.anthropic.com/v1/messages")))
                .timeout(Duration.ofSeconds(120))
                .header("content-type", "application/json")
                .header("x-api-key", cle())
                .header("anthropic-version", "2023-06-01")
                .header("anthropic-beta", "server-side-fallback-2026-07-01")
                .POST(HttpRequest.BodyPublishers.ofString(corps, StandardCharsets.UTF_8))
                .build();
        http.sendAsync(req, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8)).whenComplete((rep, err) -> {
            if (err != null) {
                derniereErreur = err.getClass().getSimpleName() + " : " + err.getMessage();
                return;
            }
            try {
                Object o = new Json(rep.body()).valeur();
                if (rep.statusCode() != 200 || !(o instanceof Map)) {
                    derniereErreur = "HTTP " + rep.statusCode() + " " + rep.body().substring(0, Math.min(200, rep.body().length()));
                    return;
                }
                Map<?, ?> m = (Map<?, ?>) o;
                if ("refusal".equals(m.get("stop_reason"))) {
                    derniereErreur = "refus du modèle";
                    return;
                }
                StringBuilder t = new StringBuilder();
                Object c = m.get("content");
                if (c instanceof List) for (Object bloc : (List<?>) c) {
                    if (bloc instanceof Map && "text".equals(((Map<?, ?>) bloc).get("type"))) t.append(((Map<?, ?>) bloc).get("text"));
                }
                String texte = t.toString().trim();
                if (texte.isEmpty()) return;
                dernierTexte = texte;
                derniereErreur = "";
                Bukkit.getScheduler().runTask(z, () -> rappel.accept(texte));
            } catch (RuntimeException e) {
                derniereErreur = "réponse illisible : " + e.getMessage();
            }
        });
    }

    public List<String> etat() {
        List<String> r = new ArrayList<>();
        r.add("Ω : " + (z.actif("omega") ? "activé" : "désactivé") + (cle().isEmpty() ? ", sans clé" : ", clé présente")
                + ", appels aujourd'hui " + appelsJour + "/" + z.getConfig().getInt("omega.quota_jour", 4));
        if (!derniereErreur.isEmpty()) r.add("Dernière erreur : " + derniereErreur);
        if (!dernierTexte.isEmpty()) r.add("Dernier texte : " + dernierTexte);
        return r;
    }

    // ---------------------------------------------------------------- JSON minimal

    static String json(String s) {
        StringBuilder b = new StringBuilder("\"");
        for (char c : s.toCharArray()) {
            switch (c) {
                case '"':
                    b.append("\\\"");
                    break;
                case '\\':
                    b.append("\\\\");
                    break;
                case '\n':
                    b.append("\\n");
                    break;
                case '\r':
                    b.append("\\r");
                    break;
                case '\t':
                    b.append("\\t");
                    break;
                default:
                    if (c < 0x20) b.append(String.format("\\u%04x", (int) c));
                    else b.append(c);
            }
        }
        return b.append('"').toString();
    }

    /** lecteur JSON minimal (objets, listes, chaînes, nombres, booléens, null) */
    static final class Json {
        private final String s;
        private int i;

        Json(String s) {
            this.s = s;
        }

        private void blancs() {
            while (i < s.length() && Character.isWhitespace(s.charAt(i))) i++;
        }

        Object valeur() {
            blancs();
            if (i >= s.length()) throw new IllegalStateException("fin inattendue");
            char c = s.charAt(i);
            if (c == '{') {
                i++;
                Map<String, Object> m = new LinkedHashMap<>();
                blancs();
                if (s.charAt(i) == '}') {
                    i++;
                    return m;
                }
                while (true) {
                    blancs();
                    String k = chaine();
                    blancs();
                    i++; // ':'
                    m.put(k, valeur());
                    blancs();
                    char d = s.charAt(i++);
                    if (d == '}') return m;
                }
            }
            if (c == '[') {
                i++;
                List<Object> l = new ArrayList<>();
                blancs();
                if (s.charAt(i) == ']') {
                    i++;
                    return l;
                }
                while (true) {
                    l.add(valeur());
                    blancs();
                    char d = s.charAt(i++);
                    if (d == ']') return l;
                }
            }
            if (c == '"') return chaine();
            if (s.startsWith("true", i)) {
                i += 4;
                return Boolean.TRUE;
            }
            if (s.startsWith("false", i)) {
                i += 5;
                return Boolean.FALSE;
            }
            if (s.startsWith("null", i)) {
                i += 4;
                return null;
            }
            int d = i;
            while (i < s.length() && "+-0123456789.eE".indexOf(s.charAt(i)) >= 0) i++;
            return Double.parseDouble(s.substring(d, i));
        }

        private String chaine() {
            i++; // '"'
            StringBuilder b = new StringBuilder();
            while (true) {
                char c = s.charAt(i++);
                if (c == '"') return b.toString();
                if (c != '\\') {
                    b.append(c);
                    continue;
                }
                char e = s.charAt(i++);
                switch (e) {
                    case 'n':
                        b.append('\n');
                        break;
                    case 't':
                        b.append('\t');
                        break;
                    case 'r':
                        b.append('\r');
                        break;
                    case 'b':
                        b.append('\b');
                        break;
                    case 'f':
                        b.append('\f');
                        break;
                    case 'u':
                        b.append((char) Integer.parseInt(s.substring(i, i + 4), 16));
                        i += 4;
                        break;
                    default:
                        b.append(e);
                }
            }
        }
    }
}
