### Task 8: Guided tour (spec says "optional" — include; skip only with an explicit note)

**Files:**
- Modify: `webui/model_tab.py` (small generator in `_explorer_ui`)

- [ ] **Step 1: Add a tour button under the block list (after `trace_md`)**

```python
    tour_btn = gr.Button("Guided tour (walks every block)")

    def _tour(tech):
        blocks = state_blocks.value or []
        for b in blocks:
            yield _detail_md(blocks, b["id"], bool(tech))
            _time.sleep(1.6)
    tour_btn.click(_tour, [tech], detail_md)
```

- [ ] **Step 2: Verify manually (or record SKIPPED + reason), then commit**

```powershell
git add webui/model_tab.py
git commit -m "feat(webui): U12 guided tour (auto-walk blocks with explanations)"
```

---


