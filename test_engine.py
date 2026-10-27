import tempfile,unittest
from pathlib import Path
from engine import extract,plan,create,undo,dedupe
class EngineTests(unittest.TestCase):
 def test_literal(self):
  self.assertEqual(extract('A, B\nC','literal')[0],['A','B','C'])
 def test_smart_negative(self):
  names,_,excluded=extract('Kitchen\nLiving room\nDon\'t make garage')
  self.assertEqual(names,['Kitchen','Living room']);self.assertEqual(len(excluded),1)
 def test_safe(self):
  with tempfile.TemporaryDirectory() as d:
   made,skipped,errors=create(['A','B'],d);self.assertEqual(len(made),2)
   made2,skipped2,_=create(['A'],d);self.assertEqual(len(skipped2),1)
   (Path(d)/'A'/'file.txt').write_text('hi')
   removed,failed=undo(made);self.assertEqual(len(removed),1);self.assertEqual(len(failed),1)
 def test_names(self):
  self.assertEqual(dedupe(['A','a','/bad','B']),['A','B'])
if __name__=='__main__':unittest.main()
