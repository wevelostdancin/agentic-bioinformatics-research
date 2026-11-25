from agentic_bioinformatics.harness import HarnessAdapter


def test_dummy_adapter_satisfies_protocol():
    class Dummy:
        def run(self, config: dict) -> dict:
            return config

    assert isinstance(Dummy(), HarnessAdapter)
