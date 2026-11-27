import dataclasses
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from gate import DelayedGate


class GateTests(unittest.TestCase):
    def test_feedback_cannot_arrive_early(self):
        g = DelayedGate(); p = g.issue(0, 4, 0, 0, 1, 0)
        with self.assertRaises(ValueError): g.settle(p.identifier, 0, 3)
        self.assertEqual(g.scores, {}); self.assertIn(p.identifier, g.pending)
        g.settle(p.identifier, 0, 4)
        self.assertLess(g.weight(0, 0, 4), .5)

    def test_predictions_are_immutable(self):
        g = DelayedGate(); p = g.issue(0, 1, 0, 0, 1, 0)
        with self.assertRaises(dataclasses.FrozenInstanceError): p.memory = 0
        g.settle(p.identifier, 0, 1)
        self.assertEqual(p.value, .5)

    def test_context_and_action_isolation(self):
        g = DelayedGate(); p = g.issue(0, 1, 1, 0, 1, 0); g.settle(p.identifier, 0, 1)
        self.assertLess(g.weight(1, 0, 1), .5)
        self.assertEqual(g.weight(0, 0, 1), .5)
        self.assertEqual(g.weight(1, 1, 1), .5)

    def test_duplicate_and_nonfinite_labels_rejected(self):
        g = DelayedGate(); p = g.issue(0, 1, 0, 0, 1, 0)
        with self.assertRaises(ValueError): g.settle(p.identifier, float('nan'), 1)
        self.assertIn(p.identifier, g.pending)
        g.settle(p.identifier, 0, 1)
        with self.assertRaises(KeyError): g.settle(p.identifier, 0, 1)

    def test_future_tail_does_not_change_prefix(self):
        def run(tail):
            g = DelayedGate(); result=[]
            for t,y in enumerate([0,1,0,1]+tail):
                p=g.issue(2*t,2*t+1,0,0,1,0); result.append(p.value)
                g.settle(p.identifier,y,2*t+1)
            return result
        self.assertEqual(run([0,0])[:4],run([100,-100])[:4])

    def test_one_key_matches_global_baseline(self):
        a,b=DelayedGate(),DelayedGate(conditional=False)
        for t in range(20):
            pa=a.issue(2*t,2*t+1,0,0,1,0);pb=b.issue(2*t,2*t+1,0,0,1,0)
            self.assertEqual(pa.value,pb.value)
            a.settle(pa.identifier,t%2,2*t+1);b.settle(pb.identifier,t%2,2*t+1)

    def test_stale_evidence_returns_to_neutral(self):
        g=DelayedGate();p=g.issue(0,1,0,0,1,0);g.settle(p.identifier,0,1)
        self.assertLess(g.weight(0,0,1),.5)
        self.assertAlmostEqual(g.weight(0,0,10000),.5)

    def test_older_delayed_evidence_has_less_mass(self):
        a,b=DelayedGate(),DelayedGate()
        p=a.issue(0,64,0,0,1,0);q=b.issue(63,64,0,0,1,0)
        a.settle(p.identifier,0,64);b.settle(q.identifier,0,64)
        self.assertGreater(a.weight(0,0,64),b.weight(0,0,64))

    def test_clock_cannot_go_backward(self):
        g=DelayedGate();g.issue(5,6,0,0,1,0)
        with self.assertRaises(ValueError):g.issue(4,6,0,0,1,0)


if __name__ == '__main__': unittest.main()
