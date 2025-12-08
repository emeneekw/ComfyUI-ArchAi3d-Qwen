"""
ComfyUI-ArchAi3d-Qwen
Advanced Qwen-VL nodes for ComfyUI with organized submenus

Author: Amir Ferdos (ArchAi3d)
Email: Amir84ferdos@gmail.com
LinkedIn: https://www.linkedin.com/in/archai3d/
GitHub: https://github.com/amir84ferdos
Version: 3.0.0
License: Dual License (Free for personal use, Commercial license required for business use)
"""

# ============================================================================
# ULTIMATE NODES
# ============================================================================
from .nodes.archai3d_ultimate_nodes import ArchAi3D_Ultimate_Prompt, ArchAi3D_Ultimate_Encoder

# ============================================================================
# NODE CLASS MAPPINGS
# ============================================================================

NODE_CLASS_MAPPINGS = {
    # ULTIMATE NODES
    "ArchAi3D_Ultimate_Prompt": ArchAi3D_Ultimate_Prompt,
    "ArchAi3D_Ultimate_Encoder": ArchAi3D_Ultimate_Encoder,
}

# ============================================================================
# DISPLAY NAMES
# ============================================================================

NODE_DISPLAY_NAME_MAPPINGS = {
    # ULTIMATE NODES
    "ArchAi3D_Ultimate_Prompt": "🌟 Ultimate ArchViz Prompt",
    "ArchAi3D_Ultimate_Encoder": "🌟 Ultimate ArchViz Encoder",
}

# ============================================================================
# WEB DIRECTORY (for custom UI elements)
# ============================================================================

import os
WEB_DIRECTORY = os.path.join(os.path.dirname(__file__), "web")

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']
__version__ = "3.0.0"
__author__ = "Amir Ferdos (ArchAi3d)"

# ============================================================================
# STARTUP MESSAGE
# ============================================================================

print("=" * 70)
print(f"[ArchAi3d-Qwen v{__version__}] Loading nodes...")
print(f"  🌟 ULTIMATE: 2 All-in-One Nodes (Prompt + Encoder)")
print(f"  ✅ Total: {len(NODE_CLASS_MAPPINGS)} nodes loaded!")
print(f"")
print(f"  ⭐ NEW: Ultimate Nodes to simplify ArchViz workflows!")
print(f"  📚 Documentation: ./docs/")
print(f"  ⚖️  License: Dual (Free personal, Commercial available)")
print("=" * 70)
