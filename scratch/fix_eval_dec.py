import io
p = 'langid/scripts/eval_schemer.py'
s = io.open(p, encoding='utf-8').read()
anchor = '            pred_tags = [labels[j] for j in pred_ids]\n'
assert anchor in s
new = (anchor +
            '            # deterministic-constrained decoding: force B- at type transitions\n'
            '            prev = "O"\n'
            '            for k in range(len(pred_tags)):\n'
            '                if pred_tags[k].startswith("I-") and prev != "B-" + pred_tags[k][2:] and prev != "I-" + pred_tags[k][2:]:\n'
            '                    pred_tags[k] = "B-" + pred_tags[k][2:]\n'
            '                prev = pred_tags[k]\n')
s = s.replace(anchor, new, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('constrained decoding added')
