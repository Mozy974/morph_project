"""
Tests unitaires pour AutoDocGeneratorAgent (Level 7.0 Meta-Learning).
"""

import pytest
from orchestrator.agents.auto_doc_generator import AutoDocGeneratorAgent


def test_inspect_module_ast():
    agent = AutoDocGeneratorAgent()
    sample_code = '''
class Calculator:
    """Calculatrice simple."""
    def add(self, a, b):
        return a + b

def main():
    """Point d'entrée."""
    pass
'''
    info = agent.inspect_module_ast(sample_code)
    assert len(info["classes"]) == 1
    assert info["classes"][0]["name"] == "Calculator"
    assert info["classes"][0]["methods"] == ["add"]
    assert len(info["functions"]) == 1
    assert info["functions"][0]["name"] == "main"
