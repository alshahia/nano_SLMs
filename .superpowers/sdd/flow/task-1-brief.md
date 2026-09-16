# Task 1 brief (from docs/plans/2026-09-13-flow-editor-mvp-plan.md — read verbatim as your requirements)

## Task 1: Frontend scaffold — P1 shell compiles and serves

**Files:** Create flow/package.json, flow/vite.config.ts, flow/tsconfig.json, flow/index.html, flow/src/main.tsx, flow/src/App.tsx, flow/src/store.ts, flow/src/api.ts, flow/.gitignore.

- [ ] Step 1: Write package.json (name "flow"; deps react ^18.3.1, react-dom ^18.3.1, @xyflow/react ^12, zustand ^5; devDeps typescript ^5.6.3, vite ^5.4.11, @vitejs/plugin-react ^4.3.4, vitest ^2.1.8, @types/react, @types/react-dom, @types/node; scripts: "dev": "vite", "build": "tsc --noEmit && vite build", "test": "vitest run"; "type": "module").
- [ ] Step 2: Vite config mirrors viz/: react plugin, dev proxy `/api` → http://127.0.0.1:3010.
- [ ] Step 3: tsconfig strict, jsx react-jsx, bundler resolution (copy viz/tsconfig.json options verbatim).
- [ ] Step 4: index.html mounts #root; main.tsx renders <App/>.
- [ ] Step 5: App.tsx P1 shell: <Palette/> <FlowCanvas/> <Inspector/> in flex; each side collapsible via boolean in store. FlowCanvas minimal xyflow here (background, no nodes); Inspector renders three tabs, switch via store.state.inspectorTab.
- [ ] Step 6: store.ts: zustand create with {graph:{nodes:[],edges:[]}, selection:null, inspectorTab:"properties", runStatus:null, } + setters.
- [ ] Step 7: Run `cd flow; pnpm install; pnpm dev` → PASS: http://localhost:5174 renders shell.
- [ ] Step 8: `pnpm build` → PASS: typecheck + dist/.
- [ ] Step 9: Commit: `git add flow/ && git commit -m "flow: scaffold P1 editor shell"`.
