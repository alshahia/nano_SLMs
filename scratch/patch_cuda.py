import io
p = 'langid/scripts/train_rank.py'
s = io.open(p, encoding='utf-8').read()
anchor = '    torch.manual_seed(0)'
assert anchor in s
ins = '    device = "cuda" if torch.cuda.is_available() else "cpu"\n    print("device", device, flush=True)\n'
s = s.replace(anchor, anchor.replace(anchor, anchor) if False else anchor, 1)
anchor2 = '    params = list(emb.parameters()) + [bias_a, bias_b]'
s = s.replace(anchor2, '    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")\n    print("device", device, flush=True)\n    a_ids = a_off = b_ids = b_off = None\n    params = list(emb.parameters()) + [bias_a, bias_b]', 1)
s = s.replace('    a_ids, a_off = emo_model.encode_batch(tr_a)', '    a_ids, a_off = emo_model.encode_batch(tr_a)\n    a_ids, a_off = a_ids.to(device), a_off.to(device)', 1)
s = s.replace('    b_ids, b_off = emo_model.encode_batch(tr_b)', '    b_ids, b_off = emo_model.encode_batch(tr_b)\n    b_ids, b_off = b_ids.to(device), b_off.to(device)', 1)
s = s.replace('    emb = torch.nn.Embedding(65536, d)', '    emb = torch.nn.Embedding(65536, d)', 1)
anchor3 = '    os.makedirs(os.path.dirname(outp), exist_ok=True)'
s = s.replace(anchor3, anchor3 + '\n    emb.to(device)\n    bias_a = bias_a.to(device)\n    bias_b = bias_b.to(device)', 1)
s = s.replace('"emb": emb.weight.detach().half(),', '"emb": emb.weight.detach().half().cpu(),')
s = s.replace('"bias_a": bias_a.detach().half(),', '"bias_a": bias_a.detach().half().cpu(),')
s = s.replace('"bias_b": bias_b.detach().half(),', '"bias_b": bias_b.detach().half().cpu(),')
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('cuda patch applied')
