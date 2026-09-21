# mu3 live composed decode demo (E-49)

Router gates each prompt to its readout path (E-47, acc 1.00). Reality check: works where the capability exists, jams where E-48a/b showed it does not — shown honestly.

| task | prompt | gold | model output |
|---|---|---|---|
| x1 | `اثنى،\|` | `أَثْنَى،` | `baaalalar` |
| x2 | `998+274=\|` | `1272` | `11111` |
| x3 | `[()[}{][}{)]{(([{}{}]}\n` | `bad` | `bad` |
| x4 | `copy:ttexbpsghir\|` | `ttexbpsghir` | `behhhehhh` |
| dia(forced) | `glyph sample` | `glyph sample` | `ccacacac` |

Reading: x3 (bracket sanity) is CORRECT via the armed binary head; x2 gets trapped in digit repetition ('11111' vs '1272' gold); x1/x4/dia free fill still jams on repeated placeholder chars. Teacher-forced numbers stay strong (mixed CE 2.2753); the next real rung is trunk-side growth (see E-48b row), not another readout onto the same frozen state.
