package za.moteur;

import org.bukkit.Bukkit;

import java.util.ArrayDeque;
import java.util.Deque;

/**
 * Pont Java -> Skript (bible F1) : le moteur appelle Skript par des commandes console « zaevt ... ».
 * Les commandes sont mises en file et exécutées sur le fil principal, avec un budget par tick.
 */
public final class Pont {
    private final Deque<String> file = new ArrayDeque<>();
    public long envoyees;

    /** sûr depuis n'importe quel fil */
    public void zaevt(String ligne) {
        synchronized (file) {
            if (file.size() < 2000) file.add("zaevt " + nettoyer(ligne));
        }
    }

    public void console(String ligne) {
        synchronized (file) {
            if (file.size() < 2000) file.add(nettoyer(ligne));
        }
    }

    public void sms(String uuid, String de, String texte) {
        zaevt("sms " + uuid + " " + de.replace(' ', '_') + " " + texte);
    }

    public void radio(String station, String texte) {
        zaevt("radio " + station + " " + texte);
    }

    public void journal(String texte) {
        zaevt("journal " + texte);
    }

    /** {za::mot::<var>} = valeur côté Skript */
    public void set(String var, String valeur) {
        zaevt("set " + var + " " + valeur);
    }

    private static String nettoyer(String s) {
        return s.replace('\n', ' ').replace('\r', ' ');
    }

    /** sur le fil principal, à chaque tick */
    public void vider(int max) {
        for (int i = 0; i < max; i++) {
            String c;
            synchronized (file) {
                c = file.poll();
            }
            if (c == null) return;
            try {
                Bukkit.dispatchCommand(Bukkit.getConsoleSender(), c);
                envoyees++;
            } catch (RuntimeException e) {
                ZAMoteur.log().warning("Commande refusée : " + c + " (" + e.getMessage() + ")");
            }
        }
    }
}
