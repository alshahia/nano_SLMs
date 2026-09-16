### Task 3: `webui/explorer.py` — SVG renderer (TDD)

**Files:**
- Modify: `webui/explorer.py` (append)
- Modify: `tests/test_explorer.py` (append one test before the `__main__` block)

- [ ] **Step 1: Add the failing test**

```python
def t_render_svg():
    dims, header = _smoke_dims_header()
    blocks = E.build_graph(dims, header, label="smoke/final", lora=None)
    svg = E.render_svg(blocks, selected_id="L1.attn")
    assert "L1.attn" in svg and "data-bid" in svg, "no clickable ids"
    assert "http" not in svg, "external asset leaked into SVG"
    assert svg.count("<svg") == 1
```

- [ ] **Step 2: Run to verify it fails**

Run: `& .\.venv\Scripts\python.exe tests\test_explorer.py`
Expected: FAIL — `AttributeError: ... no attribute 'render_svg'`.

- [ ] **Step 3: Implement `render_svg` (append to `webui/explorer.py`)**

```python
def render_svg(blocks, selected_id: str = "") -> str:
    """Self-contained inline SVG stack (no external assets; clicking is
    wired by model_tab.py's shim — data-bid carries the block id). The
    layer owning the selected block is expanded; others collapse."""
    sel_layer = next((b["layer"] for b in blocks if b["id"] == selected_id), None)
    expand = sel_layer if sel_layer is not None else 0
    rows: list[tuple[str, str, str, bool]] = []  # (bid, label, color, is_sel)
    for b in blocks:
        if b["layer"] is None:
            rows.append((b["id"], b["title"], KIND_COLOR[b["kind"]],
                         b["id"] == selected_id))
        elif b["id"].endswith("pre_attn_norm"):
            rows.append((f"L{b['layer']}",
                         f"Layer {b['layer']}: norm - attn - norm - ffn (click to expand)",
                         "#475569", False))
        if b["layer"] == expand:
            rows.append((b["id"], b["title"].split(" - ", 1)[1],
                         KIND_COLOR[b["kind"]], b["id"] == selected_id))
    W, RH, GAP = 330, 30, 6
    H = len(rows) * (RH + GAP) + 8
    parts = ['<svg viewBox="0 0 %d %d" style="width:100%%;max-width:350px;'
             'font-family:ui-sans-serif,system-ui,sans-serif">' % (W, H)]
    y = 4
    for bid, label, color, sel in rows:
        disp = label if len(label) <= 44 else label[:43] + "..."
        parts.append(
            f'<g class="blk" data-bid="{bid}" style="cursor:pointer" '
            f'onclick="window.__dshtModelSelect && '
            f"window.__dshtModelSelect('{bid}')\">"
            f'<rect x="4" y="{y}" width="{W - 8}" height="{RH}" rx="6" '
            f'fill="{color}" fill-opacity="{"1" if sel else "0.85"}" '
            f'stroke="#0f172a" stroke-width="{"2" if sel else "1"}"/>'
            f'<text x="14" y="{y + 20}" font-size="12.5" fill="white">{disp}</text>'
            f"</g>")
        y += RH + GAP
    parts.append("</svg>")
    return "".join(parts)
```

- [ ] **Step 4: Run tests to green**

Run: `& .\.venv\Scripts\python.exe tests\test_explorer.py`
Expected: `6/6 checks passed`.

- [ ] **Step 5: Commit**

```powershell
git add webui/explorer.py tests/test_explorer.py
git commit -m "feat(webui): U12 SVG architecture renderer (self-contained, clickable ids)"
```

---


