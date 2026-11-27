"""Prequential paired-error weighting baseline; no novelty or coverage claim."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Prediction:
    identifier: int
    issued_at: int
    available_at: int
    context: int
    action: int
    memory: float
    fallback: float
    weight: float
    value: float


class DelayedGate:
    def __init__(self, conditional=True, half_life=64, temperature=.1, loss_clip=4):
        if not all(math.isfinite(x) and x > 0 for x in [half_life, temperature, loss_clip]):
            raise ValueError('Gate scales must be positive and finite')
        self.conditional = conditional
        self.half_life, self.temperature, self.loss_clip = half_life, temperature, loss_clip
        self.pending, self.scores = {}, {}
        self.clock, self.counter = -1, 0

    def advance(self, now):
        if not isinstance(now, int) or now < self.clock:
            raise ValueError('Monotone integer clock required')
        self.clock = now

    def key(self, context, action):
        return (context, action) if self.conditional else (0, 0)

    def weight(self, context, action, now):
        self.advance(now)
        total, mass, last = self.scores.get(self.key(context, action), (0., 0., now))
        decay = 2.0**(-(now-last)/self.half_life)
        # Decay confidence toward the neutral prior when feedback becomes stale.
        score = total*decay/(1+mass*decay)
        z = max(-40., min(40., score/self.temperature))
        return 1/(1+math.exp(z))

    def issue(self, now, available_at, context, action, memory, fallback):
        if not isinstance(available_at, int) or available_at <= now:
            raise ValueError('Outcome must arrive strictly after the prediction')
        if not all(math.isfinite(x) for x in [memory, fallback]):
            raise ValueError('Predictions must be finite')
        w = self.weight(context, action, now)
        p = Prediction(self.counter, now, available_at, context, action,
                       float(memory), float(fallback), w, w*memory+(1-w)*fallback)
        self.pending[p.identifier] = p; self.counter += 1
        return p

    def settle(self, identifier, outcome, now):
        p = self.pending[identifier]
        if now < self.clock or now < p.available_at:
            raise ValueError('Future or out-of-order feedback cannot be consumed')
        if not math.isfinite(outcome): raise ValueError('Outcome must be finite')
        self.advance(now)
        memory_loss = min(abs(p.memory-outcome), math.sqrt(self.loss_clip))**2
        fallback_loss = min(abs(p.fallback-outcome), math.sqrt(self.loss_clip))**2
        key = self.key(p.context, p.action)
        total, mass, last = self.scores.get(key, (0., 0., now))
        decay = 2.0**(-(now-last)/self.half_life)
        # Event-time age matters: delayed arrival does not make an old example fresh.
        age_weight = 2.0**(-(now-p.issued_at)/self.half_life)
        self.scores[key] = (total*decay+age_weight*(memory_loss-fallback_loss),
                            mass*decay+age_weight, now)
        del self.pending[identifier]
