
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(sys.path[0]))  # noqa: allow omen_side_build import below
import random
from omen_side_build import VARIANTS, DOMAINS, DOMAIN_KEYS, TONES, PLAN, _bounds_check
from ui.src.validate import validate_spec, validate_chain
from ui.src.chain import spec_to_chain, chain_to_spec

g = random.Random(240924)
fails = collections.Counter()
samples = {}
for arch, count in PLAN:
    variants = VARIANTS[arch]
    for i in range(count):
        variant = variants[i % len(variants)]
        domain = DOMAIN_KEYS[(i // len(variants)) % len(DOMAIN_KEYS)]
        tone = TONES[i % len(TONES)]
        D = DOMAINS[domain]
        spec, tasks = variant(g, D)
        task = tasks[tone]
        problems = [str(p) for p in validate_spec(spec) if p is not None]
        problems += _bounds_check(spec)
        chain = spec_to_chain(spec, task)
        problems += [str(p) for p in validate_chain(chain) if p is not None]
        spec2, l1 = chain_to_spec(chain)
        problems += [str(p) for p in l1 if p is not None]
        if spec2 != spec:
            problems.append("roundtrip_mismatch")
        if problems:
            key = arch + "#v" + str(i % len(variants))
            signature = tuple(sorted(set(problems)))
            fails[(key, signature)] += 1
            samples.setdefault((key, signature), task[:50])

for (key, sig), n in sorted(fails.items()):
    print(key, n, "->", "; ".join(sig))
    print("   sample:", samples[(key, sig)])
