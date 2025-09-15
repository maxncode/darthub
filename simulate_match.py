# simulate_match.py
import time

class MatchSimulator:
    def __init__(self, player1, player2, legs_to_win=3):
        self.p1 = player1
        self.p2 = player2
        self.legs_to_win = legs_to_win
        self.legs = {player1.name: 0, player2.name: 0}

    def play_leg(self, starter_name):
        """
        Simuliere ein Leg komplett (nicht live). Gibt zurück: winner_name, leg_history (Liste strings), leg_180_counts dict.
        """
        scores = {self.p1.name: 501, self.p2.name: 501}
        current = starter_name
        leg_history = []
        leg_180s = {self.p1.name: 0, self.p2.name: 0}

        while True:
            player = self.p1 if current == self.p1.name else self.p2
            before = scores[player.name]
            visit = player.throw_visit(before)

            # 180 zählen
            if visit == 180:
                leg_180s[player.name] += 1

            # BUST: visit > before OR leaving 1 is impossible (bust)
            if visit > before or (before - visit) == 1:
                leg_history.append(f"{player.name} wirft {visit} -> BUST (Rest {before})")
                # score bleibt gleich
            else:
                # exact hit -> attempt checkout
                if visit == before:
                    success = player.attempt_checkout(before)
                    if success:
                        scores[player.name] = 0
                        self.legs[player.name] += 1
                        leg_history.append(f"{player.name} wirft {visit} -> Checkout erfolgreich! Leg gewonnen.")
                        return player.name, leg_history, leg_180s
                    else:
                        leg_history.append(f"{player.name} wirft {visit} -> Versuch gescheitert (BUST). Rest bleibt {before}")
                else:
                    scores[player.name] -= visit
                    leg_history.append(f"{player.name} wirft {visit}, Rest = {scores[player.name]}")

            # Wechsel
            current = self.p2.name if current == self.p1.name else self.p1.name

    def play_match(self):
        """
        Simuliere ein komplettes Match (non-live) — gibt winner_name, scoreline, match_history.
        match_history ist Liste von (starter, winner, leg_history, leg_180s)
        """
        starter = self.p1.name
        match_history = []
        # reset legs:
        self.legs = {self.p1.name: 0, self.p2.name: 0}
        while max(self.legs.values()) < self.legs_to_win:
            winner, leg_hist, leg_180s = self.play_leg(starter)
            match_history.append((starter, winner, leg_hist, leg_180s))
            starter = self.p2.name if starter == self.p1.name else self.p1.name
        final_winner = max(self.legs, key=lambda k: self.legs[k])
        scoreline = f"{self.legs[self.p1.name]}:{self.legs[self.p2.name]}"
        return final_winner, scoreline, match_history

    def play_match_live(self, delay=0.7):
        """
        Generator: yieldet Zeilen (strings) live. delay in Sekunden zwischen Visits.
        Best of Legs only (Sets können ergänzt werden).
        """
        starter = self.p1.name
        self.legs = {self.p1.name: 0, self.p2.name: 0}
        yield f"Match startet: {self.p1.name} vs {self.p2.name} — First to {self.legs_to_win} Legs"

        while max(self.legs.values()) < self.legs_to_win:
            yield f"--- Neues Leg (Starter: {starter}) ---"
            scores = {self.p1.name: 501, self.p2.name: 501}
            current = starter
            while True:
                player = self.p1 if current == self.p1.name else self.p2
                before = scores[player.name]
                visit = player.throw_visit(before)

                # count 180
                if visit == 180:
                    yield f"{player.name} wirft 180! (große Aufnahme)"
                # apply rules
                if visit > before or (before - visit) == 1:
                    yield f"{player.name} wirft {visit} -> BUST (Rest {before})"
                else:
                    if visit == before:
                        success = player.attempt_checkout(before)
                        if success:
                            scores[player.name] = 0
                            self.legs[player.name] += 1
                            yield f"✅ {player.name} wirft {visit} -> Checkout! {player.name} gewinnt das Leg ({self.legs[self.p1.name]}-{self.legs[self.p2.name]})"
                            break
                        else:
                            yield f"{player.name} wirft {visit} -> Versuch gescheitert (BUST). Rest bleibt {before}"
                    else:
                        scores[player.name] -= visit
                        yield f"{player.name} wirft {visit}, Rest = {scores[player.name]}"
                current = self.p2.name if current == self.p1.name else self.p1.name
                time.sleep(delay)
            starter = self.p2.name if starter == self.p1.name else self.p1.name

        final_winner = max(self.legs, key=lambda k: self.legs[k])
        scoreline = f"{self.legs[self.p1.name]}:{self.legs[self.p2.name]}"
        yield f"🏆 Match vorbei! {final_winner} gewinnt {scoreline}"
