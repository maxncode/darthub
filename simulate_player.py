# simulate_player.py
import random

class SimulatedPlayer:
    def __init__(self, name, avg, checkout_pct, form=5, max_checkout=170, stats=None):
        """
        avg: drei-dart average (z.B. 97.5)
        checkout_pct: Prozent (z.B. 42.0)
        form: 0-10 Skala
        stats: optional dict mit historischen Werten, z.B. {"p180_per_leg": 0.12, "total_180s": 50, "matches": 10}
        """
        self.name = name
        self.avg = float(avg)
        self.checkout_pct = float(checkout_pct)
        self.form = float(form)
        self.max_checkout = int(max_checkout)
        self.stats = stats or {}

        # p180: Wahrscheinlichkeit eine komplette Aufnahme =180 zu werfen (per visit)
        if "p180_per_leg" in self.stats:
            try:
                self.p180 = float(self.stats["p180_per_leg"])
            except:
                self.p180 = None
        else:
            self.p180 = None

        # wenn keine explizite p180 vorhanden -> schätze aus Average
        if not self.p180:
            # konservative Schätzung: bei avg 85 => ~0.05, bei avg 100 => ~0.25
            est = 0.03 + max(0.0, (self.avg - 80.0)) * 0.008
            self.p180 = min(max(est, 0.005), 0.30)

    def throw_visit(self, remaining=None):
        """
        Simuliere eine 'Aufnahme' (3 Darts).
        Wenn remaining gegeben ist und <= max_checkout, versucht der Spieler öfter
        aufs Auschecken; sonst normale Scoring-Aufnahme.
        Gibt integer Punkte (0..180) zurück.
        """
        # wenn gezielt aufs Checkout (remaining <= max_checkout), erhöhe Chance, das exakte Restscore zu versuchen
        if remaining is not None and remaining <= self.max_checkout and remaining > 1:
            # Spieler versucht häufiger das Finish: Heuristisch
            try_checkout_prob = 0.55  # Anteil der Besuche, in denen gezielt aufs Finish gegangen wird (heuristisch)
            if random.random() < try_checkout_prob:
                # Versuchen, das Finish zu treffen: mit gewisser Wahrscheinlichkeit Erfolg,
                # sonst ein normaler (kleinerer) Score (Miss)
                success_prob = (self.checkout_pct / 100.0) * (1.0 + (self.form - 5.0) / 25.0)
                success_prob = min(max(success_prob, 0.02), 0.95)
                if random.random() < success_prob:
                    # Wir modellieren Erfolg als exakte Auszahlung (visit == remaining)
                    return int(remaining)
                else:
                    # Miss beim Checkout: plausible kleine bis mittlere Aufnahme (z. B. 40-140)
                    mu = max(20.0, self.avg * 0.6)
                    score = int(round(random.gauss(mu, 12)))
                    return max(0, min(180, score))

        # Normale Aufnahme (Scoring)
        if random.random() < self.p180:
            return 180

        # ansonsten normal verteilt um das Average (three-dart average)
        mu = self.avg
        score = int(round(random.gauss(mu, 12)))
        # clamp
        if score < 0:
            score = 0
        if score > 180:
            score = 180
        return score

    def attempt_checkout(self, remaining):
        """
        Wenn ein Spieler eine Aufnahme exakt auf 0 bringt (visit == remaining), entscheidet
        attempt_checkout, ob das Auschecken realistisch gelingt (berücksichtigt checkout_pct, form).
        """
        if remaining <= 0 or remaining > self.max_checkout:
            return False
        if remaining == 1:
            return False  # niemals möglich
        base = (self.checkout_pct / 100.0)
        modifier = 1.0 + (self.form - 5.0) / 25.0
        prob = base * modifier
        prob = min(max(prob, 0.01), 0.95)
        return random.random() < prob
