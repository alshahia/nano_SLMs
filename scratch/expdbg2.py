import sys, traceback
sys.path.insert(0, '.')
sys.argv = ['x', '--model', r'runs/langid_da2b/emo_transformer.pt']
import importlib.util
spec = importlib.util.spec_from_file_location('exp', 'langid/scripts/export_emo_tf.py')
m = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(m)
    with open('scratch/exp.err', 'w') as f: f.write('OK')
except Exception:
    with open('scratch/exp.err', 'w') as f: f.write(traceback.format_exc())