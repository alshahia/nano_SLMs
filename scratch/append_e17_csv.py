import csv, io, pathlib
p = pathlib.Path("research/gate_results/gate_results.csv")
rows = [
    ["stage2final@2500", "fadel_test", 34.92621780201638, 34.94300468432749, 22.188204447712992, 1.0, "", "gate_probe-rescored", "pwsh-2"],
    ["stage2final@2500", "sadeed25", 47.78664045665898, 47.78664045665898, 33.02838997467206, 0.9998865913128946, "", "gate_probe-rescored", "pwsh-2"],
    ["stage2final@2500", "wikinews2024", 57.498116051243414, 57.498116051243414, 45.233609645817635, 1.0, "CONTAMINATED-gate", "gate_probe-rescored", "pwsh-2"],
    ["stage2final@2500", "wikinews2014", 49.58985015859127, 49.58985015859127, 33.637755660067814, 1.0, "", "gate_probe-rescored", "pwsh-2"],
]
rows += [
    ["stage2final@2500", "abdou_test", 49.40758910901402, 49.66505999625023, 33.29323167302044, 0.9845842968147824, "held-out-new", "eval.py compare scratch/stage2final/abdou_test_pred.txt", "pwsh-3"],
    ["stage2b2500@2500", "abdou_test", 41.643165531321, 41.956948003249794, 30.412942941066184, 0.9845842968147824, "held-out-never-trained", "eval.py compare scratch/stage2b2500/abdou_test_pred.txt", "pwsh-3"],
]
with p.open("a", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(rows)
print("appended", len(rows))
