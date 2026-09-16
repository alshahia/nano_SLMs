### Task 7: SVG click shim (enhancement; the Dataset click is the always-working path)

**Files:**
- Modify: `webui/model_tab.py` (append one static `gr.HTML` inside `_explorer_ui`, after `shim_btn`)

- [ ] **Step 1: Append the shim**

```python
    gr.HTML(
        "<script>window.__dshtModelSelect=function(bid){"
        "var ta=document.querySelector('#model_tab_sel textarea');"
        "if(ta){ta.value=bid;"
        "ta.dispatchEvent(new Event('input',{bubbles:true}));}"
        "var btn=document.querySelector('#model_tab_sel_btn button');"
        "if(btn){btn.click();}};</script>", visible=False)
```

- [ ] **Step 2: Manual verify (browser)**

Click a block in the SVG: the detail panel must switch (same as Dataset
clicks). If the shim does not fire in Gradio 6.26 (programmatic input events
can be swallowed by the Svelte binding), REMOVE the shim entirely — the
clickable `gr.Dataset` layer list already satisfies the U12 PASS gate
("click any block -> details"). Record which path shipped in the final
report.

- [ ] **Step 3: Commit (or revert if shim dropped)**

```powershell
git add webui/model_tab.py
git commit -m "feat(webui): U12 SVG click shim (dataset-list fallback retained)"
```

---


