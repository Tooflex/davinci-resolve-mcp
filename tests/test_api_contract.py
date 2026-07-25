import ast
import pathlib
import unittest

from resolve_api import ResolveAPI


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]


class FakeNode:
    def __init__(self):
        self.inputs = {}

    def SetInput(self, key, value):
        self.inputs[key] = value


class FakeComposition:
    def __init__(self):
        self.calls = []
        self.node = FakeNode()

    def AddTool(self, node_type, x, y):
        self.calls.append((node_type, x, y))
        return self.node


class ResolveAPIContractTests(unittest.TestCase):
    def test_every_server_api_call_exists_on_resolve_api(self):
        server_tree = ast.parse(
            (PROJECT_ROOT / "server.py").read_text(encoding="utf-8")
        )
        called_methods = {
            node.func.attr
            for node in ast.walk(server_tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "resolve_api"
        }

        missing_methods = sorted(
            name for name in called_methods if not hasattr(ResolveAPI, name)
        )
        self.assertEqual(missing_methods, [])

    def test_create_fusion_node_uses_supplied_composition(self):
        api = ResolveAPI.__new__(ResolveAPI)
        composition = FakeComposition()

        node = api.create_fusion_node(
            composition,
            "Blur",
            {"Size": 0.5},
        )

        self.assertIs(node, composition.node)
        self.assertEqual(composition.calls, [("Blur", 0, 0)])
        self.assertEqual(node.inputs, {"Size": 0.5})


if __name__ == "__main__":
    unittest.main()
