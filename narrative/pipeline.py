"""Narrative pipeline: PathResolver -> NarrativeLexer -> NarrativeParser -> VCC IR pipeline."""

from __future__ import annotations

import sys
import os

# Import VCC's IR utilities from the upstream monolith
_VCC_DIR = os.path.join(os.path.dirname(__file__), "..",
                        "skills", "conversation-compiler", "scripts")
if _VCC_DIR not in sys.path:
    sys.path.insert(0, _VCC_DIR)

import VCC as _vcc

from narrative.path_resolver import PathResolver
from narrative.lexer import NarrativeLexer
from narrative.parser import NarrativeParser


class NarrativePipeline:
    """PathResolver -> NarrativeLexer -> NarrativeParser -> VCC IR -> VCC Lowering -> VCC Emitter."""

    def __init__(self, tree_root: str):
        self.resolver = PathResolver(tree_root)
        self.lexer = NarrativeLexer()
        self.parser = NarrativeParser()

    def compile(self, target_node_id: str, grep: str | None = None,
                view: str = "ui") -> str:
        """Compile the ancestor chain for target_node_id into a rendered view.

        Args:
            target_node_id: The leaf node to compile context for.
            grep: Optional tag expression or substring for filtering.
            view: 'full' | 'brief' | 'adaptive' (grep-filtered).

        Returns:
            Rendered text output.
        """
        # Stage 1: resolve path and emit annotated stream
        stream = self.resolver.emit_stream(target_node_id)

        # Stage 2: lex and parse into IR
        tokens = self.lexer.lex(stream)
        ir = self.parser.parse(tokens)

        # Stage 3: VCC IR pipeline — assign stable line numbers
        _vcc.assign_lines(ir)

        # Stage 4: lowering + emission based on requested view
        if view == "brief":
            _vcc.lower_brief(ir, truncate=128, filename=f"{target_node_id}.txt")
            lines = _vcc.emit(ir, "content_brief")
        elif view == "adaptive" and grep:
            import re
            _vcc.lower_brief(ir, truncate=128, filename=f"{target_node_id}.txt")
            try:
                pattern = re.compile(grep)
            except re.error:
                pattern = re.compile(re.escape(grep))
            _vcc.lower_view(ir, filename=f"{target_node_id}.txt",
                            grep_pattern=pattern)
            lines = _vcc.emit(ir, "content_view")
        else:
            # 'full' or 'ui' — emit the full content
            lines = _vcc.emit(ir, "content")

        return "\n".join(lines)

    def compile_ir(self, target_node_id: str) -> list[dict]:
        """Compile and return raw IR (for testing and downstream use)."""
        stream = self.resolver.emit_stream(target_node_id)
        tokens = self.lexer.lex(stream)
        ir = self.parser.parse(tokens)
        _vcc.assign_lines(ir)
        return ir
