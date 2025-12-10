import json
import random

class WorkflowBuilder:
    def __init__(self):
        self.nodes_list = []
        self.nodes_map = {}
        self.links = []
        self.last_link_id = 0
        self.last_node_id = 0
        self.groups = []

    def get_id(self):
        self.last_node_id += 1
        return self.last_node_id

    def get_link_id(self):
        self.last_link_id += 1
        return self.last_link_id

    def add_node(self, node_type, pos, inputs=None, widgets_values=None, title=None):
        node_id = self.get_id()
        node = {
            "id": node_id,
            "type": node_type,
            "pos": pos,
            "size": {"0": 300, "1": 100},
            "flags": {},
            "order": node_id,
            "mode": 0,
            "inputs": [],
            "outputs": [],
            "properties": {},
            "widgets_values": widgets_values if widgets_values else []
        }
        if title:
            node["title"] = title

        self.nodes_map[node_id] = node
        self.nodes_list.append(node)

        if inputs:
            for name, link_info in inputs.items():
                if link_info:
                    source_node_id = link_info[0]
                    source_slot_index = link_info[1]

                    link_id = self.get_link_id()
                    self.links.append([link_id, source_node_id, source_slot_index, node_id, len(node["inputs"]), name])
                    node["inputs"].append({"name": name, "type": "*", "link": link_id})

                    if source_node_id in self.nodes_map:
                        source_node = self.nodes_map[source_node_id]
                        if source_slot_index < len(source_node["outputs"]):
                             source_node["outputs"][source_slot_index]["links"].append(link_id)
                else:
                     node["inputs"].append({"name": name, "type": "*", "link": None})

        return node_id, node

    def add_group(self, title, bounding):
        self.groups.append({
            "title": title,
            "bounding": bounding,
            "color": "#3f789e",
            "font_size": 24
        })

    def save(self, filename):
        workflow = {
            "last_node_id": self.last_node_id,
            "last_link_id": self.last_link_id,
            "nodes": self.nodes_list,
            "links": self.links,
            "groups": self.groups,
            "config": {},
            "extra": {},
            "version": 0.4
        }
        with open(filename, 'w') as f:
            json.dump(workflow, f, indent=2)

builder = WorkflowBuilder()

# =================================================================================================
# GROUP 1: Shared Inputs (Ultimate Prompt & Image)
# =================================================================================================
builder.add_group("Shared Inputs", [10, 10, 600, 600])

# Input Image
image_node_id, image_node = builder.add_node(
    "LoadImage",
    [50, 50],
    widgets_values=["example.png", "image"],
    title="Input Image"
)
image_node["outputs"] = [
    {"name": "IMAGE", "type": "IMAGE", "links": []},
    {"name": "MASK", "type": "MASK", "links": []}
]

# Ultimate Prompt Generator
prompt_node_id, prompt_node = builder.add_node(
    "ArchAi3D_Ultimate_Prompt",
    [50, 300],
    inputs={},
    widgets_values=[
        "Camera: Object Focus (Product/Arch)",  # mode
        "modern interior with large windows",   # main_subject
        "soft lighting, high detail",           # scene_context
        # Camera
        "Medium Shot (MS)", "Eye Level", "Static (No Movement)", "Normal (50mm)",
        # Person
        "eye_level_front", "strict", "none",
        # Room
        "Remove + Paint All", "construction debris/tools",
        # Material
        "stone", "custom",
        # Style
        "ice",
        # Debug
        False
    ],
    title="🌟 Ultimate ArchViz Prompt"
)
prompt_node["outputs"] = [
    {"name": "prompt", "type": "STRING", "links": []},
    {"name": "system_prompt", "type": "STRING", "links": []}
]

# =================================================================================================
# GROUP 2: SDXL Pipeline (Qwen Enhanced)
# =================================================================================================
builder.add_group("SDXL Pipeline (Qwen Enhanced)", [700, 10, 1000, 800])

# SDXL Loaders
sdxl_unet_id, sdxl_unet_node = builder.add_node(
    "UnetLoaderGGUF", [750, 50], widgets_values=["sd_xl_base_1.0.gguf"], title="SDXL Unet (GGUF)"
)
sdxl_unet_node["outputs"] = [{"name": "MODEL", "type": "MODEL", "links": []}]

sdxl_clip_id, sdxl_clip_node = builder.add_node(
    "DualCLIPLoader", [750, 200], widgets_values=["t5xxl_fp16.safetensors", "clip_l.safetensors", "sdxl"], title="SDXL CLIP"
)
sdxl_clip_node["outputs"] = [{"name": "CLIP", "type": "CLIP", "links": []}]

sdxl_vae_id, sdxl_vae_node = builder.add_node(
    "VAELoader", [750, 350], widgets_values=["sdxl_vae.safetensors"], title="SDXL VAE"
)
sdxl_vae_node["outputs"] = [{"name": "VAE", "type": "VAE", "links": []}]

qwen_clip_id, qwen_clip_node = builder.add_node(
    "CLIPLoader", [750, 500], widgets_values=["qwen_vl_clip.safetensors"], title="Qwen CLIP"
)
qwen_clip_node["outputs"] = [{"name": "CLIP", "type": "CLIP", "links": []}]

# Ultimate Encoder (SDXL-specific)
encoder_id, encoder_node = builder.add_node(
    "ArchAi3D_Ultimate_Encoder",
    [1050, 200],
    inputs={
        "image": [image_node_id, 0],
        "clip": [qwen_clip_id, 0],
        "prompt": [prompt_node_id, 0],
        "vae": [sdxl_vae_id, 0],
        "system_prompt": [prompt_node_id, 1]
    },
    widgets_values=["16:9 (Panorama)", "auto", "Balanced", False],
    title="🌟 Ultimate Encoder"
)
encoder_node["outputs"] = [
    {"name": "conditioning", "type": "CONDITIONING", "links": []},
    {"name": "latent", "type": "LATENT", "links": []},
    {"name": "recommended_cfg", "type": "FLOAT", "links": []},
    {"name": "scaled_image", "type": "IMAGE", "links": []}
]

# Negative Prompt
sdxl_neg_id, sdxl_neg_node = builder.add_node(
    "CLIPTextEncode", [1050, 550], inputs={"clip": [sdxl_clip_id, 0]},
    widgets_values=["text, watermark, low quality"], title="Negative"
)
sdxl_neg_node["outputs"] = [{"name": "CONDITIONING", "type": "CONDITIONING", "links": []}]

# KSampler SDXL
sdxl_sample_id, sdxl_sample_node = builder.add_node(
    "KSampler", [1400, 200],
    inputs={
        "model": [sdxl_unet_id, 0],
        "positive": [encoder_id, 0],
        "negative": [sdxl_neg_id, 0],
        "latent_image": [encoder_id, 1]
    },
    widgets_values=[random.randint(1, 100000), "fixed", 30, 4.0, "dpmpp_2m", "karras", 1.0],
    title="SDXL Sampler"
)
sdxl_sample_node["outputs"] = [{"name": "LATENT", "type": "LATENT", "links": []}]

# Decode & Save
sdxl_decode_id, sdxl_decode_node = builder.add_node(
    "VAEDecode", [1400, 500], inputs={"samples": [sdxl_sample_id, 0], "vae": [sdxl_vae_id, 0]}, title="SDXL Decode"
)
sdxl_decode_node["outputs"] = [{"name": "IMAGE", "type": "IMAGE", "links": []}]

builder.add_node("SaveImage", [1400, 650], inputs={"images": [sdxl_decode_id, 0]}, widgets_values=["SDXL_Result"], title="Save SDXL")


# =================================================================================================
# GROUP 3: Chroma Pipeline (FLUX Architecture)
# =================================================================================================
builder.add_group("Chroma Pipeline (FLUX)", [700, 850, 1000, 600])

# Chroma Loaders
chroma_unet_id, chroma_unet_node = builder.add_node(
    "UNETLoader", [750, 900], # FLUX usually uses UNETLoader or CheckpointLoader
    widgets_values=["chroma-unlocked-v33.safetensors"], title="Chroma Model (FLUX)"
)
chroma_unet_node["outputs"] = [{"name": "MODEL", "type": "MODEL", "links": []}]

# CLIP for Chroma (T5 + CLIP_L)
chroma_clip_id, chroma_clip_node = builder.add_node(
    "DualCLIPLoader", [750, 1050],
    widgets_values=["t5xxl_fp8_e4m3fn_scaled.safetensors", "clip_l.safetensors", "flux"], # 'flux' type if available
    title="Chroma CLIP (T5+L)"
)
chroma_clip_node["outputs"] = [{"name": "CLIP", "type": "CLIP", "links": []}]

chroma_vae_id, chroma_vae_node = builder.add_node(
    "VAELoader", [750, 1200], widgets_values=["ae.safetensors"], title="Chroma VAE"
)
chroma_vae_node["outputs"] = [{"name": "VAE", "type": "VAE", "links": []}]

# Empty Latent for Chroma (Flux usually needs specific sizing)
# We can use the Ultimate Encoder's scaled image logic to get dimensions, or just a simple EmptyLatent
empty_latent_id, empty_latent_node = builder.add_node(
    "EmptyLatentImage", [750, 1350], widgets_values=[1024, 1024, 1], title="Empty Latent (Chroma)"
)
empty_latent_node["outputs"] = [{"name": "LATENT", "type": "LATENT", "links": []}]

# Prompt Encoding for Chroma
# We use the text from Ultimate Prompt, but encoded via standard CLIP for Chroma/Flux
chroma_pos_id, chroma_pos_node = builder.add_node(
    "CLIPTextEncode", [1050, 1050],
    inputs={"clip": [chroma_clip_id, 0]},
    widgets_values=[""], # Will be manually connected to Prompt Output
    title="Chroma Positive"
)
# Manual link from Prompt Node to Widget? No, ComfyUI allows converting widget to input.
# The script here assumes standard inputs.
# We'll map the text input of CLIPTextEncode to the output of UltimatePrompt.
# NOTE: Standard CLIPTextEncode doesn't have a string input unless converted.
# To support this in the script, we treat 'text' as an input link if possible.
# In ComfyUI JSON, if 'text' is a widget, it's a string. If converted to input, it's a link.
# We will simulate this by adding a Primitive node or assuming the user will connect it.
# Or better: Use a node that accepts string input, like "CLIPTextEncode (Advanced)" or primitive routing.
# For simplicity in this script, we will define it as an input link here.
chroma_pos_node["inputs"].append({"name": "text", "type": "STRING", "link": [prompt_node_id, 0]}) # Manual link hack for script generator
# Update links list manually for this special case
link_id = builder.get_link_id()
builder.links.append([link_id, prompt_node_id, 0, chroma_pos_id, len(chroma_pos_node["inputs"])-1, "text"])
chroma_pos_node["inputs"][-1]["link"] = link_id
chroma_pos_node["outputs"] = [{"name": "CONDITIONING", "type": "CONDITIONING", "links": []}]


chroma_neg_id, chroma_neg_node = builder.add_node(
    "CLIPTextEncode", [1050, 1200],
    inputs={"clip": [chroma_clip_id, 0]},
    widgets_values=["text, watermark, low quality"],
    title="Chroma Negative"
)
chroma_neg_node["outputs"] = [{"name": "CONDITIONING", "type": "CONDITIONING", "links": []}]


# KSampler Chroma
chroma_sample_id, chroma_sample_node = builder.add_node(
    "KSampler", [1400, 1050],
    inputs={
        "model": [chroma_unet_id, 0],
        "positive": [chroma_pos_id, 0],
        "negative": [chroma_neg_id, 0],
        "latent_image": [empty_latent_id, 0]
    },
    widgets_values=[random.randint(1, 100000), "fixed", 20, 3.5, "euler", "simple", 1.0], # Flux settings
    title="Chroma Sampler"
)
chroma_sample_node["outputs"] = [{"name": "LATENT", "type": "LATENT", "links": []}]


# Decode & Save Chroma
chroma_decode_id, chroma_decode_node = builder.add_node(
    "VAEDecode", [1400, 1300], inputs={"samples": [chroma_sample_id, 0], "vae": [chroma_vae_id, 0]}, title="Chroma Decode"
)
chroma_decode_node["outputs"] = [{"name": "IMAGE", "type": "IMAGE", "links": []}]

builder.add_node("SaveImage", [1400, 1450], inputs={"images": [chroma_decode_id, 0]}, widgets_values=["Chroma_Result"], title="Save Chroma")


builder.save("ultimate_archviz_workflow_chroma_sdxl.json")
print("Workflow generated successfully.")
