# Desert-Ant data catalog (2026-09-21, 4 subagent surveys, web-verified)
Authoritative per-domain CSVs (full header name,source_url,domain_group,languages,size,license,access_status,download_method,notes,use_for_us):
1. audio_speech_datasets.csv        - mid-size/derivative audio (34 rows, agent 72b435eb)
2. audio_speech_datasets_2_raw.csv  (31 rows, agent f0db6c77) - complementary SADA/QASR/MGB/ADI17/NADI/Casablanca/ARCADE/SCC/MIXAT...
3. NEGATIVE_FINDINGS_AUDIO.md       - verified non-existent corpora (GigaSpeech-ar, UAE Audiobook, VoxPopuli-ar, MINA-ar, Arabic filler-annotated corpora DON'T EXIST)
4. arm_datasets_emoji_title_schema.csv (28 rows, agent fed85d45) - DA-2/DA-8/DA-9/DA-7 + pretraining
5. arabic_text_pashto_datasets_raw.csv — Pashto wiki+OPUS packs, Arabic news/topic, NER/PII gold, dialect text, emoji lexicons

Highest-leverage finds: (a) Pashto: wikimedia 20231101.ps + OPUS-NLLB en-ps 11.3M pairs = DA-1 G3 fix; (b) ANERcorp/CLEANANERCorp/Wojood-Fine real DATE/numeric NER = DA-9 E-58 TIME fix; (c) fixie-ai/common_voice_17_0 open mirror = DA-5/6 without MDC gate; (d) SANAD (Mendeley CC BY 4.0) for DA-3/DA-8 title; (e) mabahboh/sitr-arabic-pii Apache-2.0 for DA-7.
Open gaps after survey: no Arabic filler-annotated corpus ANYWHERE; no Arabic Hijri date/TE dataset; no VoxPopuli-ar; TTS repos silky1708/ArabicVoice + MBZUAI/AraVoice 401-unverified.
