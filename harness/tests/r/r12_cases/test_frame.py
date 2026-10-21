"""Freeze provided R12 capabilities/models separately from five learner bodies."""
import ast
import hashlib
from pathlib import Path
import fvh_r.engine as engine

FRAME_SHA256='7edc16f0410cfda68608e13dc0748bb438b4cfee7fe31192641a1e4600182fe4'

def test_original_models_protocol_bridge_and_independent_guard_are_fixed():
 tree=ast.parse(Path(engine.__file__).read_text())
 allowed={'result_stream','localize','drive_r12','_transition','render_hint_r12'}
 found=[]
 for node in ast.walk(tree):
  if isinstance(node,ast.FunctionDef) and node.name in allowed:
   first=node.body[:1]
   doc=first if first and isinstance(first[0],ast.Expr) and isinstance(first[0].value,ast.Constant) and isinstance(first[0].value.value,str) else []
   node.body=doc+[ast.Pass()];found.append(node.name)
 assert set(found)==allowed and len(found)==5
 assert hashlib.sha256(ast.dump(tree,include_attributes=False).encode()).hexdigest()==FRAME_SHA256
