import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from cluster_controller import choose_candidate,PLAN
class ClusterProtocolTests(unittest.TestCase):
 def test_reference_cannot_be_selected_as_methodological_candidate(self):
  self.assertEqual(choose_candidate({'reference':99.,'combined':3.,'action_memory':4.,'cost_aligned':2.}),'action_memory')
 def test_ties_follow_registered_order(self):
  self.assertEqual(choose_candidate({'reference':1.,'combined':3.,'action_memory':3.,'cost_aligned':3.}),'combined')
 def test_invalid_scores_block_selection(self):
  for scores in [{},{'reference':1.,'combined':float('nan'),'action_memory':3.,'cost_aligned':3.}]:
   with self.assertRaises(ValueError):choose_candidate(scores)
 def test_jobs_unique_and_scoped_to_authorized_storage(self):
  jobs=[]
  for host,entry in PLAN['hosts'].items():
   self.assertTrue(entry['root'].startswith(('/date/zyy/','/data/zyy/')))
   self.assertLessEqual(len(entry['jobs']),4 if entry.get('adopt_existing') else 2)
   jobs.extend(map(tuple,entry['jobs']))
  self.assertEqual(len(jobs),12);self.assertEqual(len(set(jobs)),12)
if __name__=='__main__':unittest.main()
