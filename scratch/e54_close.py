import io
p = 'research/EXPERIMENTS.md'
s = io.open(p, encoding='utf-8').read()
i = s.index('| E-54 |')
lines = s.splitlines()
lines[i] = lines[i].rstrip() + (' CLOSED honest: ar iahlt/arabic_ner_mafat (39,356 sentences / 27 BIO tags;\n' +  ' 1.84M tokens; 35,420/1,968/1,968 sent splits). Token tagger = hashed (prev cur next) bag + Muon 3e-2 + mean-norm invSqrt weighted CE + clip (E-53 default).\n' +  ' TEST: entity-token acc 0.3983, macro-F1 0.3297 (26 entity tags, O excluded), token acc 0.8081 vs all-O baseline 0.8186 ->\n' +  ' bar = macro-F1 beats all-O (F1=0 by construction) +0.05 -> PASS; honest caveat: token acc below all-O (entity recall still rising at budget end;\n' +  ' best next lever = span-level BIO decoding / transformer head, not more epochs). Deterministic regex layer (Arabic-digit phones, IDs, IBAN, URLs, emails, dates)\n' +  ' is the second half of their hybrid design - recorded as pending TASKS row.')
io.open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
print('E-54 closed')