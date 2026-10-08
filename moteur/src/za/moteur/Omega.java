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
 * (omega.cle) et « systemes.omega: true ». Fournisseur au choix (omega.fournisseur : anthropic ou gemini), quota par jour
 * et par joueur, réponses en cache. Léa écrit sa chronique du soir à partir des vrais événements ; les PNJ importants
 * peuvent parler librement (/parler). Si l'appel échoue, rien ne casse : on retombe sur les textes écrits.
 * Appel HTTP direct (pas de dépendance à embarquer dans le plugin).
 */
public final class Omega {
    private final ZAMoteur z;
    private final HttpClient http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(15)).build();
    private int jourQuota = -1;
    private int appelsJour;
    private String derniereErreur = "";
    private String dernierTexte = "";
    private final Map<String, Integer> parJoueur = new java.util.HashMap<>();
    private final Map<String, String> cache = new LinkedHashMap<>();

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
        demander(null, systemeLea(), consigne, rappel);
    }

    private static String systemeLea() {
        return "Tu es Léa, animatrice d'une petite radio communautaire qui survit dans le Québec rural pendant une épidémie. "
                + "Ton ton est humain, fatigué, courageux. Jamais de gore gratuit, jamais de méta, pas de listes.";
    }

    /**
     * Un appel au modèle (IA-16). Le cerveau a déjà décidé QUOI dire ; le modèle ne fait que le formuler.
     * joueur : uuid pour le quota par joueur (null = système). Réponse mise en cache : même demande, même réponse.
     */
    public void demander(String joueur, String systeme, String consigne, Consumer<String> rappel) {
        if (!pret()) return;
        if (jourQuota != z.jour()) {
            jourQuota = z.jour();
            appelsJour = 0;
            parJoueur.clear();
        }
        String cle = Integer.toHexString((systeme + "\u0000" + consigne).hashCode());
        String deja = cache.get(cle);
        if (deja != null) {
            Bukkit.getScheduler().runTask(z, () -> rappel.accept(deja));
            return;
        }
        if (appelsJour >= z.getConfig().getInt("omega.quota_jour", 40)) return;
        if (joueur != null && parJoueur.merge(joueur, 1, Integer::sum) > z.getConfig().getInt("omega.quota_joueur", 8)) return;
        appelsJour++;
        String fournisseur = z.getConfig().getString("omega.fournisseur", "anthropic");
        String modele = z.getConfig().getString("omega.modele", "claude-haiku-4-5");
        if (fournisseur.equals("gemini") && modele.startsWith("claude")) modele = "gemini-2.0-flash";
        String sys = systeme + " Réponds en français québécois, deux phrases au maximum, sans rien d'autre que la réplique.";
        HttpRequest req;
        if (fournisseur.equals("gemini")) {
            String corps = "{\"systemInstruction\":{\"parts\":[{\"text\":" + json(sys) + "}]}"
                    + ",\"contents\":[{\"role\":\"user\",\"parts\":[{\"text\":" + json(consigne) + "}]}]"
                    + ",\"generationConfig\":{\"maxOutputTokens\":300}}";
            req = HttpRequest.newBuilder(URI.create("https://generativelanguage.googleapis.com/v1beta/models/" + modele + ":generateContent"))
                    .timeout(Duration.ofSeconds(60))
                    .header("content-type", "application/json")
                    .header("x-goog-api-key", cle())
                    .POST(HttpRequest.BodyPublishers.ofString(corps, StandardCharsets.UTF_8))
                    .build();
        } else {
            // Haiku 4.5 ne prend ni « effort » ni repli serveur : on ne les envoie qu'aux modèles qui les acceptent
            boolean recent = !modele.contains("haiku");
            String corps = "{\"model\":" + json(modele) + ",\"max_tokens\":1024"
                    + (recent ? ",\"output_config\":{\"effort\":\"low\"},\"fallbacks\":\"default\"" : "")
                    + ",\"system\":" + json(sys)
                    + ",\"messages\":[{\"role\":\"user\",\"content\":" + json(consigne) + "}]}";
            HttpRequest.Builder b = HttpRequest.newBuilder(URI.create(z.getConfig().getString("omega.url", "https://api.anthropic.com/v1/messages")))
                    .timeout(Duration.ofSeconds(120))
                    .header("content-type", "application/json")
                    .header("x-api-key", cle())
                    .header("anthropic-version", "2023-06-01");
            if (recent) b.header("anthropic-beta", "server-side-fallback-2026-07-01");
            req = b.POST(HttpRequest.BodyPublishers.ofString(corps, StandardCharsets.UTF_8)).build();
        }
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
                String texte = fournisseur.equals("gemini") ? texteGemini((Map<?, ?>) o) : texteClaude((Map<?, ?>) o);
                if (texte == null || texte.isEmpty()) return;
                // garde-fous : deux lignes, longueur bornée
                texte = texte.replace('\n', ' ').trim();
                if (texte.length() > 400) texte = texte.substring(0, 400);
                String fin = texte;
                cache.put(cle, fin);
                if (cache.size() > 300) cache.remove(cache.keySet().iterator().next());
                dernierTexte = fin;
                derniereErreur = "";
                Bukkit.getScheduler().runTask(z, () -> rappel.accept(fin));
            } catch (RuntimeException e) {
                derniereErreur = "réponse illisible : " + e.getMessage();
            }
        });
    }

    private String texteClaude(Map<?, ?> m) {
        if ("refusal".equals(m.get("stop_reason"))) {
            derniereErreur = "refus du modèle";
            return null;
        }
        StringBuilder t = new StringBuilder();
        Object c = m.get("content");
        if (c instanceof List) for (Object bloc : (List<?>) c) {
            if (bloc instanceof Map && "text".equals(((Map<?, ?>) bloc).get("type"))) t.append(((Map<?, ?>) bloc).get("text"));
        }
        return t.toString().trim();
    }

    private static String texteGemini(Map<?, ?> m) {
        Object c = m.get("candidates");
        if (!(c instanceof List) || ((List<?>) c).isEmpty()) return null;
        Object cand = ((List<?>) c).get(0);
        if (!(cand instanceof Map)) return null;
        Object contenu = ((Map<?, ?>) cand).get("content");
        if (!(contenu instanceof Map)) return null;
        Object parts = ((Map<?, ?>) contenu).get("parts");
        StringBuilder t = new StringBuilder();
        if (parts instanceof List) for (Object p : (List<?>) parts) if (p instanceof Map && ((Map<?, ?>) p).get("text") != null) t.append(((Map<?, ?>) p).get("text"));
        return t.toString().trim();
    }

    public List<String> etat() {
        List<String> r = new ArrayList<>();
        r.add("Ω : " + (z.actif("omega") ? "activé" : "désactivé") + (cle().isEmpty() ? ", sans clé" : ", clé présente")
                + ", " + z.getConfig().getString("omega.fournisseur", "anthropic") + ", appels aujourd'hui " + appelsJour + "/" + z.getConfig().getInt("omega.quota_jour", 40));
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
