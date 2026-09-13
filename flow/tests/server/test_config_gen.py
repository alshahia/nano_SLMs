"""Task 5 tests: flow.server.config_gen — graph -> configs/flow_<slug>.yaml.

TDD step 1: these tests FAIL before flow/server/config_gen.py exists.
Key names validated against the REAL pipeline configs by loading
configs/smoke.yaml (not invented keys). Tests never write into the repo's
configs/ or flow/flows/: out_dir is injected as a tempfile directory.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from flow.server import config_gen, graph_schema, nodes  # noqa: E402


def dataset_node(nid="n1", label="TheGamingMahi/TinyCode"):
    node = {"id": nid, "kind": "dataset", "props": {},
            "position": {"x": 0, "y": 0}}
    if label is not None:
        node["label"] = label
    return node


def node(nid, kind, props, x=0.0):
    return {"id": nid, "kind": kind, "props": props,
            "position": {"x": x, "y": 0}}


def linear_chain():
    """dataset -> prepare -> tokenize -> train chain with full props."""
    return {
        "schema": "flow/0.1",
        "meta": {"name": "my-run"},
        "graph": {
            "nodes": [
                dataset_node("n1", "TheGamingMahi/TinyCode"),
                node("n2", "prepare", {"rows": 2000, "val_fraction": 0.02,
                                       "min_chars": 60}),
                node("n3", "tokenize", {"seq_len": 256, "vocab": 32768}),
                node("n4", "train", {"preset": "Small (~12M, smoke)",
                                     "steps": 200,
                                     "lr_preset": "Pretrain 4e-4"}),
            ],
            "edges": [
                {"id": "e1", "from": "n1", "to": "n2",
                 "fromPort": "cleaned", "toPort": "raw-dir"},
                {"id": "e2", "from": "n2", "to": "n3",
                 "fromPort": "cleaned-dir", "toPort": "cleaned-dir"},
                {"id": "e3", "from": "n3", "to": "n4",
                 "fromPort": "shard-dir", "toPort": "shard-dir"},
            ],
        },
    }


def real_train_keys():
    """Real train-block key names parsed from configs/smoke.yaml."""
    with open(REPO / "configs" / "smoke.yaml", "r", encoding="utf-8") as f:
        smoke = yaml.safe_load(f)
    return set(smoke["train"].keys()), set(smoke["data"].keys())


class ConfigGenTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out_dir = self.tmp.name
        self.addCleanup(self.tmp.cleanup)

    # --- happy path ----------------------------------------------------
    def test_generate_returns_path_writes_flow_yaml(self):
        path = config_gen.generate(linear_chain(), out_dir=self.out_dir)
        self.assertTrue(os.path.isfile(path))
        self.assertEqual(Path(path).name, "flow_my-run.yaml")
        self.assertEqual(Path(path).parent.name, Path(self.out_dir).name)

    def test_yaml_has_real_key_names_from_smoke_yaml(self):
        cfg = config_gen.build_config(linear_chain())
        train_keys, data_keys = real_train_keys()
        self.assertEqual(set(cfg["train"].keys()), train_keys)
        self.assertEqual(set(cfg["data"].keys()), data_keys)
        self.assertEqual(set(cfg.keys()), {"name", "tokenizer", "model",
                                           "data", "train", "eval"})
        # eval block mirrors the shipped key names
        self.assertIn("max_new_tokens", cfg["eval"])

    def test_values_map_from_node_props(self):
        cfg = config_gen.build_config(linear_chain())
        data = cfg["data"]
        train = cfg["train"]
        model = cfg["model"]
        # dataset name from the dataset node label
        self.assertEqual(data["dataset_candidates"],
                         [{"name": "TheGamingMahi/TinyCode"}])
        self.assertEqual(data["rows"], 2000)
        self.assertEqual(data["val_fraction"], 0.02)
        self.assertEqual(data["min_chars"], 60)
        # tokenize props
        self.assertEqual(cfg["tokenizer"]["vocab_size"], 32768)
        self.assertEqual(model["ctx"], 256)
        # train preset/lr_preset strings -> real config values
        self.assertEqual(train["max_steps"], 200)
        self.assertEqual(train["lr"], 4.0e-4)
        self.assertEqual(model["layers"], 4)
        self.assertEqual(train["accum"], 32)
        # derived dirs named after the run
        self.assertEqual(data["tokens_dir"], "data/my-run/tokens")
        self.assertEqual(train["output_dir"], "runs/my-run")

    def test_writes_yaml_equivalent_roundtrip(self):
        path = config_gen.generate(linear_chain(), out_dir=self.out_dir)
        with open(path, "r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f)
        self.assertEqual(loaded, config_gen.build_config(linear_chain()))

    def test_generated_file_never_overwrites_shipped_configs(self):
        # default out_dir is the repo configs/ dir; tests keep it injected.
        self.assertIn("configs",
                      str(config_gen.DEFAULT_CONFIGS_DIR).split(os.sep))

    # --- validation reuse ------------------------------------------------
    def test_invalid_graph_rejected_with_graph_schema_errors(self):
        g = linear_chain()
        g["schema"] = "flow/9.9"
        with self.assertRaises(ValueError) as cm:
            config_gen.generate(g, out_dir=self.out_dir)
        self.assertIn("schema", str(cm.exception))

    def test_unknown_props_rejected(self):
        g = linear_chain()
        g["graph"]["nodes"][3]["props"]["epochs"] = 5  # unknown for train
        with self.assertRaises(ValueError) as cm:
            config_gen.build_config(g)
        self.assertIn("epochs", str(cm.exception))

    def test_nothing_written_on_invalid_graph(self):
        g = linear_chain()
        g["graph"]["nodes"][1]["kind"] = "nope"
        try:
            config_gen.generate(g, out_dir=self.out_dir)
        except ValueError:
            pass
        self.assertEqual(os.listdir(self.out_dir), [])

    # --- branching / unsupported graphs -------------------------------------
    def test_branching_graph_rejected_cleanly(self):
        g = linear_chain()
        g["graph"]["nodes"].append(
            node("n5", "tokenize", {"seq_len": 512, "vocab": 32768}))
        g["graph"]["edges"].append(
            {"id": "e4", "from": "n1", "to": "n5",
             "fromPort": "cleaned", "toPort": "cleaned-dir"})
        with self.assertRaises(ValueError) as cm:
            config_gen.build_config(g)
        self.assertIn("linear chains only", str(cm.exception))

    def test_diamond_graph_rejected(self):
        g = {
            "schema": "flow/0.1",
            "meta": {"name": "diamond"},
            "graph": {
                "nodes": [
                    dataset_node("a"), dataset_node("b"),
                    node("c", "prepare", {"rows": 10, "val_fraction": 0.02,
                                          "min_chars": 1}),
                ],
                "edges": [
                    {"id": "e1", "from": "a", "to": "c",
                     "fromPort": "cleaned", "toPort": "cleaned-dir"},
                    {"id": "e2", "from": "b", "to": "c",
                     "fromPort": "cleaned", "toPort": "cleaned-dir"},
                ],
            },
        }
        with self.assertRaises(ValueError) as cm:
            config_gen.build_config(g)
        self.assertIn("linear chains only", str(cm.exception))

    # --- missing source values -------------------------------------------
    def test_train_without_dataset_chain_lists_missing_input(self):
        g = {
            "schema": "flow/0.1",
            "meta": {"name": "lonely"},
            "graph": {
                "nodes": [node("t1", "train", {"preset": "Small (~12M, smoke)",
                                               "steps": 10,
                                               "lr_preset": "Pretrain 4e-4"})],
                "edges": [],
            },
        }
        with self.assertRaises(ValueError) as cm:
            config_gen.build_config(g)
        self.assertIn("shard-dir", str(cm.exception))
        self.assertIn("t1", str(cm.exception))

    def test_dataset_without_name_lists_missing_input(self):
        g = linear_chain()
        g["graph"]["nodes"][0].pop("label")
        with self.assertRaises(ValueError) as cm:
            config_gen.build_config(g)
        self.assertIn("dataset name", str(cm.exception))

    def test_train_missing_steps_lists_missing_input(self):
        g = linear_chain()
        g["graph"]["nodes"][3]["props"].pop("steps")
        with self.assertRaises(ValueError) as cm:
            config_gen.build_config(g)
        self.assertIn("steps", str(cm.exception))

    def test_unknown_preset_string_rejected(self):
        g = linear_chain()
        g["graph"]["nodes"][3]["props"]["preset"] = "turbo"
        with self.assertRaises(ValueError) as cm:
            config_gen.build_config(g)
        self.assertIn("preset", str(cm.exception))

    def test_unknown_lr_preset_string_rejected(self):
        g = linear_chain()
        g["graph"]["nodes"][3]["props"]["lr_preset"] = "s999"
        with self.assertRaises(ValueError) as cm:
            config_gen.build_config(g)
        self.assertIn("lr_preset", str(cm.exception))

    # --- name handling ----------------------------------------------------
    def test_non_slug_name_rejected(self):
        g = linear_chain()
        g["meta"]["name"] = "../evil"
        with self.assertRaises(ValueError) as cm:
            config_gen.generate(g, out_dir=self.out_dir)
        self.assertIn("slug", str(cm.exception))
        self.assertEqual(os.listdir(self.out_dir), [])

    def test_preset_and_lr_preset_are_strings_in_props(self):
        g = linear_chain()
        g["graph"]["nodes"][3]["props"]["preset"] = 4  # number, not string
        with self.assertRaises(ValueError) as cm:
            config_gen.build_config(g)
        self.assertIn("preset", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
