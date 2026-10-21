"""SA-6 (PLAN.md section 11.3): RLOO reinforcement learning for SmolLM2-135M + LoRA on the playground.

Port of glm-5.3-flash-from-scratch/scripts/train_rl.py to a HF causal LM. The reward
(`reward_for`: sandboxed evaluator, case-fraction or binary, invalid penalty) and the advantage
(`leave_one_out`) are imported from that script, not copied, so the two lines score identically.
What changes: rollouts come from `model.generate`, log-probabilities from HF logits, and only a
fresh LoRA adapter (default r16 on q/k/v/o, same as the SFT recipe) is trained on top of a merged
`final` dir.

Tasks use the playground `rl` split (seed 6733), which is disjoint from `dev` (ladder, during
runs) and `final` (gates only). RL needs pass@k > 0 on a task to give it any signal, so start from
the best SFT/RFT checkpoint, not the base.

Safety: --vram-cap-gib is a hard allocator ceiling (no shared-memory spill); the free-RAM guard
aborts before host RAM gets tight. Auto-resume: re-run the same command and it continues from
<output>/state.pt (adapter + optimizer + scaler + group index).

Anti-collapse (SA-6 run 2, after run 1 collapsed to one-line `return` bodies):
  --kl-beta B          adds B * KL(policy || init) to the loss. The reference is the init itself
                       (the LoRA adapter disabled), and KL uses the k3 per-token estimator on the
                       sampled tokens.
  --checkpoint-every N writes a merged <output>/checkpoint-G every N groups and, with
                       --probe-limit K > 0, runs a greedy HumanEval/MBPP pass@1 probe on the first K
                       tasks of each set (scripts/bench_passk.py subprocess, training paused, its own
                       VRAM cap = fresh free - 0.75 GiB). Results go to <output>/probe_log.jsonl.

Task distribution (SA-6 run 3: KL alone only traded MBPP for HumanEval; the bodies stayed one-line):
  --docstring-tasks N  adds N extra rl-split instances of every multi-line `write` sub-skill,
                       rendered HumanEval-style: `def` header, then a docstring holding the
                       description and one `>>>` example, and the completion is the indented body.
                       The example is an extra case that is not graded, so hardcoding it earns
                       nothing. With 0 (the default), the pool is exactly what run 2 used.

  & .\\.venv\\Scripts\\python.exe scripts\\rl_smollm2.py --init runs/sft_smollm2_cpt_pg/final `
      --output runs/rl_smollm2 --groups 2000 --vram-cap-gib 4.5
  & .\\.venv\\Scripts\\python.exe scripts\\rl_smollm2.py --init ... --output scratch/rl_dry --dry-run
"""
from __future__ import annotations

import argparse
import copy
import json
import random
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path

import psutil
import torch

ROOT = Path(__file__).resolve().parents[1]
NEST = ROOT / "glm-5.3-flash-from-scratch"
sys.path.insert(0, str(NEST))
sys.path.insert(0, str(NEST / "scripts"))
from glm53_flash.playground import POOL_TIERS, make_playground_task, playground_pool  # noqa: E402
from glm53_flash.sandbox import SandboxRunner  # noqa: E402
from train_rl import leave_one_out, reward_for  # noqa: E402

MIN_FREE_RAM_GIB = 8.0


DOCSTRING_INDEX_OFFSET = 500  # docstring instances never reuse a comment-format instance's cases


def docstring_task(sub_skill, index: int):
    """A HumanEval-shaped instance: case 0 becomes the docstring example; cases 1-3 are graded."""
    base = make_playground_task(sub_skill, split="rl", index=DOCSTRING_INDEX_OFFSET + index, cases=4)
    (example_args, example_value), graded = base.cases[0], base.cases[1:]
    description = base.prompt.split("\n")[1].removeprefix("# ")
    call = f"{base.entry_point}({', '.join(repr(arg) for arg in example_args)})"
    prompt = (f"def {base.entry_point}({sub_skill.arguments}):\n"
              f'    """{description}\n\n    >>> {call}\n    {example_value!r}\n    """')
    # No trailing "\n": the SmolLM2 tokenizer merges "\n" with the next indent, so a prompt that
    # ends in a bare newline makes the model emit EOS at once (same rule as bench_passk.model_prompt).
    return replace(base, task_id=base.task_id.replace("rl-", "rl-doc-", 1), prompt=prompt,
                   reference_completion=sub_skill.body, cases=graded)


def build_tasks(tier: str, per_sub_skill: int, docstring_tasks: int = 0) -> list[tuple]:
    entries = []
    for sub_skill in playground_pool(tier):
        for index in range(per_sub_skill):
            entries.append((make_playground_task(sub_skill, split="rl", index=index),
                            sub_skill.capabilities()))
        if sub_skill.kind == "write" and sub_skill.body.strip("\n").count("\n") >= 1:
            for index in range(docstring_tasks):
                entries.append((docstring_task(sub_skill, index), sub_skill.capabilities()))
    return entries


def schedule(count: int, groups: int, seed: int) -> list[int]:
    order, epoch = [], 0
    while len(order) < groups:
        block = list(range(count))
        random.Random(seed + epoch * 1009).shuffle(block)
        order.extend(block)
        epoch += 1
    return order[:groups]


def encode(tokenizer, text: str) -> list[int]:
    """Same encoding as the battery's HfArm (scratch/bench_playground_batched.py)."""
    ids = list(tokenizer.encode(text))
    if tokenizer.bos_token_id is not None and (not ids or ids[0] != tokenizer.bos_token_id):
        ids = [tokenizer.bos_token_id] + ids
    return ids


def cut_at_eos(ids: list[int], eos_id: int) -> list[int]:
    """Keep the first eos (the model must learn to stop); drop everything after it."""
    for position, token in enumerate(ids):
        if token == eos_id:
            return ids[:position + 1]
    return ids


def completion_log_probs(model, prompt: list[int], completions: list[list[int]], pad_id: int,
                         device) -> tuple[torch.Tensor, torch.Tensor]:
    """Per-token log-probabilities of each completion and their mask, one forward pass per group."""
    width = max(map(len, completions))
    rows = [prompt + c + [pad_id] * (width - len(c)) for c in completions]
    sequence = torch.tensor(rows, dtype=torch.long, device=device)
    lengths = torch.tensor([len(c) for c in completions], device=device)
    mask = torch.arange(width, device=device).unsqueeze(0) < lengths.unsqueeze(1)
    attention = torch.cat([torch.ones(len(rows), len(prompt), dtype=torch.long, device=device),
                           mask.long()], dim=1)
    with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=device.type == "cuda"):
        logits = model(input_ids=sequence[:, :-1], attention_mask=attention[:, :-1]).logits
    start = len(prompt) - 1
    selected = logits[:, start:start + width].float()
    targets = sequence[:, len(prompt):]
    token_lp = torch.log_softmax(selected, dim=-1).gather(-1, targets.unsqueeze(-1)).squeeze(-1)
    return token_lp, mask


def probe(checkpoint: Path, limit: int, device) -> dict:
    """Greedy pass@1 on the first `limit` HumanEval / MBPP-sanitized tasks (training is paused)."""
    free = torch.cuda.mem_get_info(device)[0] / 2 ** 30 if device.type == "cuda" else 0.0
    cap = round(free - 0.75, 2)
    if device.type == "cuda" and cap < 1.0:
        return {"skipped": f"free VRAM {free:.2f} GiB too low for a probe"}
    out = checkpoint / "probe_passk.json"
    cmd = [sys.executable, str(ROOT / "scripts" / "bench_passk.py"), "--arm", f"ckpt={checkpoint}",
           "--limit", str(limit), "--device", device.type, "--batch", "16", "--workers", "4",
           "--out", str(out)] + (["--vram-cap-gib", str(cap)] if device.type == "cuda" else [])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if result.returncode != 0 or not out.is_file():
        return {"error": (result.stderr or result.stdout)[-400:]}
    per_set = json.loads(out.read_text(encoding="utf-8"))["arms"]["ckpt"]["per_set"]
    return {name: {"passed": row["passed"], "tasks": row["tasks"], "eos_rate": row["eos_rate"]}
            for name, row in per_set.items()} | {"vram_cap_gib": cap}


def ram_guard(floor: float = MIN_FREE_RAM_GIB) -> None:
    free = psutil.virtual_memory().available / 2 ** 30
    if free < floor:
        raise SystemExit(f"free RAM {free:.1f} GiB < {floor} GiB guard; aborting")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", type=Path, required=True, help="merged HF final dir to start from")
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--groups", type=int, default=2000)
    ap.add_argument("--group-size", type=int, default=8)
    ap.add_argument("--tier", choices=POOL_TIERS, default="all")  # SA-B: + breadth/wide/fix/tool
    ap.add_argument("--per-sub-skill", type=int, default=8, help="rl-split instances per sub-skill")
    ap.add_argument("--docstring-tasks", type=int, default=0,
                    help="HumanEval-style instances per multi-line write sub-skill (0 = off)")
    ap.add_argument("--max-new-tokens", type=int, default=128)
    ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--learning-rate", type=float, default=2e-5)
    ap.add_argument("--lora-r", type=int, default=16)
    ap.add_argument("--lora-alpha", type=int, default=32)
    ap.add_argument("--reward-mode", choices=("case-fraction", "binary"), default="case-fraction")
    ap.add_argument("--invalid-penalty", type=float, default=-0.1)
    ap.add_argument("--exact-bonus", type=float, default=0.0)
    ap.add_argument("--brevity-weight", type=float, default=0.0)
    ap.add_argument("--sandbox", choices=("off", "on"), default="on")
    ap.add_argument("--sandbox-timeout", type=float, default=2.0)
    ap.add_argument("--save-every", type=int, default=100, help="groups between state saves")
    ap.add_argument("--min-free-ram-gib", type=float, default=MIN_FREE_RAM_GIB,
                    help="abort when available host RAM drops below this")
    ap.add_argument("--kl-beta", type=float, default=0.0, help="KL(policy || init) weight, 0 = off")
    ap.add_argument("--checkpoint-every", type=int, default=0, help="groups between merged checkpoints")
    ap.add_argument("--probe-limit", type=int, default=0, help="HumanEval/MBPP tasks per set per probe")
    ap.add_argument("--seed", type=int, default=31415)
    ap.add_argument("--vram-cap-gib", type=float, default=0.0)
    ap.add_argument("--max-seconds", type=float, default=0.0)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--dry-run", action="store_true", help="build tasks + score references, no model")
    args = ap.parse_args()
    if args.group_size < 2:
        raise SystemExit("--group-size must be >= 2 (leave-one-out baseline)")

    tasks = build_tasks(args.tier, args.per_sub_skill, args.docstring_tasks)
    runner = SandboxRunner(timeout=args.sandbox_timeout) if args.sandbox == "on" else None
    if args.dry_run:  # the reward must give the reference full marks, or RL chases noise
        bad = []
        for task, caps in tasks:
            reward, ev = reward_for(task, task.reference_completion, args.reward_mode,
                                    invalid_penalty=args.invalid_penalty, exact_bonus=args.exact_bonus,
                                    capabilities=caps, runner=runner)
            if not ev["passed"]:
                bad.append((task.task_id, ev["status"]))
        print(f"[dry-run] {len(tasks)} rl-split tasks; reference fails: {len(bad)} {bad[:5]}")
        return 1 if bad else 0

    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer

    device = torch.device(args.device)
    if device.type == "cuda" and device.index is None:
        device = torch.device("cuda", 0)
    if device.type == "cuda" and args.vram_cap_gib > 0:
        total = torch.cuda.get_device_properties(device).total_memory / 2 ** 30
        torch.cuda.set_per_process_memory_fraction(min(1.0, args.vram_cap_gib / total), device)
    torch.manual_seed(args.seed)
    tokenizer = AutoTokenizer.from_pretrained(args.init)
    eos_id = tokenizer.eos_token_id
    pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else eos_id
    base = AutoModelForCausalLM.from_pretrained(args.init, dtype=torch.float32,
                                                attn_implementation="sdpa").to(device)
    model = get_peft_model(base, LoraConfig(r=args.lora_r, lora_alpha=args.lora_alpha,
                                            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
                                            bias="none", task_type="CAUSAL_LM"))
    trainable = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(trainable, lr=args.learning_rate, weight_decay=0.0)
    scaler = torch.amp.GradScaler("cuda", enabled=device.type == "cuda")

    args.output.mkdir(parents=True, exist_ok=True)
    state_path, log_path = args.output / "state.pt", args.output / "rl_log.jsonl"
    probe_path = args.output / "probe_log.jsonl"
    order = schedule(len(tasks), args.groups, args.seed)
    start = 0
    if state_path.is_file():
        state = torch.load(state_path, map_location=device, weights_only=False)
        model.load_state_dict(state["adapter"], strict=False)
        optimizer.load_state_dict(state["optimizer"])
        scaler.load_state_dict(state["scaler"])
        start = state["group"]
        print(f"[resume] from group {start}", flush=True)

    def save(group: int) -> None:
        adapter = {k: v for k, v in model.state_dict().items() if "lora_" in k}
        tmp = state_path.with_suffix(".tmp")
        torch.save({"adapter": adapter, "optimizer": optimizer.state_dict(),
                    "scaler": scaler.state_dict(), "group": group, "args": vars(args) | {
                        "init": str(args.init), "output": str(args.output)}}, tmp)
        tmp.replace(state_path)

    def checkpoint(group: int) -> None:
        target = args.output / f"checkpoint-{group}"
        merged = copy.deepcopy(model).merge_and_unload()  # the live adapter stays unmerged
        merged.config.use_cache = True
        merged.save_pretrained(str(target))
        tokenizer.save_pretrained(str(target))
        del merged
        if device.type == "cuda":
            torch.cuda.empty_cache()
        row = {"group": group, "checkpoint": str(target)}
        if args.probe_limit > 0:
            row |= probe(target, args.probe_limit, device)
        with open(probe_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(row) + "\n")
        print(f"[checkpoint {group}] {json.dumps(row)}", flush=True)

    began = time.time()
    group = start
    with open(log_path, "a", encoding="utf-8") as log:
        for group in range(start, args.groups):
            if args.max_seconds and time.time() - began > args.max_seconds:
                break
            if group % 25 == 0:
                ram_guard(args.min_free_ram_gib)
            task, caps = tasks[order[group]]
            prompt = encode(tokenizer, task.prompt)
            model.eval()
            with torch.no_grad(), torch.autocast(device_type=device.type, dtype=torch.float16,
                                                 enabled=device.type == "cuda"):
                out = model.generate(torch.tensor([prompt], device=device),
                                     attention_mask=torch.ones(1, len(prompt), dtype=torch.long, device=device),
                                     do_sample=True, temperature=args.temperature, top_k=0,
                                     max_new_tokens=args.max_new_tokens,
                                     num_return_sequences=args.group_size,
                                     eos_token_id=eos_id, pad_token_id=pad_id)
            completions = [cut_at_eos(row[len(prompt):].tolist(), eos_id) or [eos_id] for row in out]
            rewards, statuses = [], []
            for ids in completions:
                text = tokenizer.decode([t for t in ids if t != eos_id])
                reward, ev = reward_for(task, text, args.reward_mode, invalid_penalty=args.invalid_penalty,
                                        exact_bonus=args.exact_bonus, brevity_weight=args.brevity_weight,
                                        capabilities=caps, runner=runner)
                rewards.append(reward)
                statuses.append(ev["status"] if not ev["passed"] else "passed")
            advantages = leave_one_out(rewards)
            loss_value, kl_value = None, None
            if any(abs(a) > 1e-8 for a in advantages):  # a flat group carries no gradient
                model.train()
                token_lp, mask = completion_log_probs(model, prompt, completions, pad_id, device)
                lengths = mask.sum(dim=1)
                adv = torch.tensor(advantages, device=device, dtype=torch.float32)
                objective = -(adv * (token_lp * mask).sum(dim=1) / lengths).mean()
                if args.kl_beta > 0:
                    with torch.no_grad(), model.disable_adapter():
                        ref_lp, _ = completion_log_probs(model, prompt, completions, pad_id, device)
                    delta = ref_lp - token_lp  # k3: exp(d) - d - 1 >= 0, unbiased for KL(pi || ref)
                    kl = (((torch.exp(delta) - delta - 1) * mask).sum(dim=1) / lengths).mean()
                    objective = objective + args.kl_beta * kl
                    kl_value = float(kl.detach())
                optimizer.zero_grad(set_to_none=True)
                scaler.scale(objective).backward()
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(trainable, 1.0)
                scaler.step(optimizer)
                scaler.update()
                loss_value = float(objective.detach())
            log.write(json.dumps({"group": group, "task_id": task.task_id, "rewards": rewards,
                                  "passed": statuses.count("passed"), "statuses": statuses,
                                  "policy_loss": loss_value, "kl": kl_value, "seconds": round(time.time() - began, 1)}) + "\n")
            log.flush()
            if (group + 1) % args.save_every == 0:
                save(group + 1)
                print(f"[group {group + 1}] saved; last pass {statuses.count('passed')}/{args.group_size}",
                      flush=True)
            if args.checkpoint_every and (group + 1) % args.checkpoint_every == 0 \
                    and not (args.output / f"checkpoint-{group + 1}").is_dir():
                save(group + 1)
                checkpoint(group + 1)
    done = group + 1 if args.groups > start else start
    save(done)
    if done >= args.groups:
        final = args.output / "final"
        merged = model.merge_and_unload()
        merged.config.use_cache = True
        merged.save_pretrained(str(final))
        tokenizer.save_pretrained(str(final))
        print(f"[final] merged -> {final}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
