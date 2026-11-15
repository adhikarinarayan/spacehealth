"""Audit scientific invariants separately from authorized presentation/export edits."""
import ast
import hashlib
import json
from pathlib import Path
from ..config import ROOT

def physiological_fingerprints(path):
    tree=ast.parse(Path(path).read_text());functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    fingerprint=lambda value:hashlib.sha256(ast.dump(value,include_attributes=False).encode()).hexdigest()
    result={name:fingerprint(functions[name]) for name in ('evaluate','production_results')}
    production=functions['evaluate_production'];prefix=[]
    for node in production.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='card' for t in node.targets):break
        prefix.append(node)
    result['production_decision_prefix']=fingerprint(ast.Module(body=prefix,type_ignores=[]))
    status=next(value for node in ast.walk(production) if isinstance(node,ast.Dict) for key,value in zip(node.keys,node.values) if isinstance(key,ast.Constant) and key.value=='status')
    result['production_status_expression']=fingerprint(status)
    return result

def verify_scientific_scope(frozen,scope):
    if frozen['configHash']!=scope['configHash']:raise ValueError('Scientific scope config mismatch')
    for relative,expected in scope['files'].items():
        if frozen['codeHashes'].get(relative)!=expected:raise ValueError('Scientific baseline hash mismatch')
        if hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()!=expected:raise ValueError(f'Frozen scientific code changed: {relative}')
    actual=physiological_fingerprints(ROOT/'model/spacehealth_model/modules/physiological.py')
    if actual!=scope['physiologicalAst']:raise ValueError('Frozen physiological decision logic changed')
