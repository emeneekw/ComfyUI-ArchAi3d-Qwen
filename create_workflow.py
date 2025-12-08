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
# GROUP 1: GGUF Model Loading
# =================================================================================================
builder.add_group("Loaders (GGUF & Qwen)", [10, 10, 600, 800])

# Unet Loader (GGUF)
unet_loader_id, unet_loader_node = builder.add_node(
    "UnetLoaderGGUF",
    [50, 50],
    widgets_values=["sd_xl_base_1.0.gguf"],
    title="GGUF Unet Loader"
)
unet_loader_node["outputs"] = [{"name": "MODEL", "type": "MODEL", "links": []}]

# CLIP Loader (Standard/Dual for SDXL)
clip_loader_id, clip_loader_node = builder.add_node(
    "DualCLIPLoader",
    [50, 250],
    widgets_values=["t5xxl_fp16.safetensors", "clip_l.safetensors", "sdxl"],
    title="SDXL CLIP Loader"
)
clip_loader_node["outputs"] = [{"name": "CLIP", "type": "CLIP", "links": []}]

# VAE Loader
vae_loader_id, vae_loader_node = builder.add_node(
    "VAELoader",
    [50, 450],
    widgets_values=["sdxl_vae.safetensors"],
    title="VAE Loader"
)
vae_loader_node["outputs"] = [{"name": "VAE", "type": "VAE", "links": []}]

# Qwen CLIP Loader (Specific for Qwen-VL)
qwen_clip_id, qwen_clip_node = builder.add_node(
    "CLIPLoader",
    [50, 650],
    widgets_values=["qwen_vl_clip.safetensors"],
    title="Qwen-VL CLIP Loader"
)
qwen_clip_node["outputs"] = [{"name": "CLIP", "type": "CLIP", "links": []}]


# =================================================================================================
# GROUP 2: Input Image
# =================================================================================================
builder.add_group("Input Image", [700, 10, 400, 400])

image_node_id, image_node = builder.add_node(
    "LoadImage",
    [750, 50],
    widgets_values=["example.png", "image"],
    title="Input Image"
)
image_node["outputs"] = [
    {"name": "IMAGE", "type": "IMAGE", "links": []},
    {"name": "MASK", "type": "MASK", "links": []}
]


# =================================================================================================
# GROUP 3: Ultimate Prompt Generator
# Consolidates all 5 previous modes (Object, Person, Room, Material, Style)
# =================================================================================================
builder.add_group("Ultimate Prompt", [1200, 10, 500, 800])

# Widgets mapping for ArchAi3D_Ultimate_Prompt (based on INPUT_TYPES order in python file)
# 1. mode
# 2. main_subject
# 3. scene_context
# ... camera params ...
# ... person params ...
# ... room params ...
# ... material params ...
# ... style params ...
# ... debug ...

# Default Mode: "Camera: Object Focus (Product/Arch)"
prompt_node_id, prompt_node = builder.add_node(
    "ArchAi3D_Ultimate_Prompt",
    [1250, 50],
    inputs={},
    widgets_values=[
        "Camera: Object Focus (Product/Arch)",  # mode
        "modern interior",                      # main_subject
        "",                                     # scene_context
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
# GROUP 4: Ultimate Encoding (Scale + Encode)
# =================================================================================================
builder.add_group("Ultimate Encoding", [1200, 900, 600, 500])

encoder_id, encoder_node = builder.add_node(
    "ArchAi3D_Ultimate_Encoder",
    [1250, 950],
    inputs={
        "image": [image_node_id, 0],
        "clip": [qwen_clip_id, 0],
        "prompt": [prompt_node_id, 0],       # Connected to Prompt
        "vae": [vae_loader_id, 0],
        "system_prompt": [prompt_node_id, 1] # Connected to System Prompt
    },
    widgets_values=[
        "16:9 (Panorama)", # aspect_ratio
        "auto",            # scale_mode
        "Balanced",        # conditioning_balance
        False              # debug_mode
    ],
    title="🌟 Ultimate ArchViz Encoder"
)
encoder_node["outputs"] = [
    {"name": "conditioning", "type": "CONDITIONING", "links": []},
    {"name": "latent", "type": "LATENT", "links": []},
    {"name": "recommended_cfg", "type": "FLOAT", "links": []},
    {"name": "scaled_image", "type": "IMAGE", "links": []}
]


# =================================================================================================
# GROUP 5: Generation (KSampler + Decode)
# =================================================================================================
builder.add_group("Generation", [1900, 900, 800, 600])

# Negative Prompt
neg_prompt_id, neg_prompt_node = builder.add_node(
    "CLIPTextEncode",
    [1950, 950],
    inputs={"clip": [clip_loader_id, 0]},
    widgets_values=["text, watermark, low quality, blurry, distorted, ugly, bad anatomy"],
    title="Negative Prompt"
)
neg_prompt_node["outputs"] = [{"name": "CONDITIONING", "type": "CONDITIONING", "links": []}]

# KSampler
ksampler_id, ksampler_node = builder.add_node(
    "KSampler",
    [1950, 1150],
    inputs={
        "model": [unet_loader_id, 0],
        "positive": [encoder_id, 0],
        "negative": [neg_prompt_id, 0],
        "latent_image": [encoder_id, 1], # Use latent from Encoder
    },
    widgets_values=[random.randint(1, 10000000), "fixed", 30, 4.0, "dpmpp_2m", "karras", 1.0],
    title="KSampler (GGUF Optimized)"
)
ksampler_node["outputs"] = [{"name": "LATENT", "type": "LATENT", "links": []}]

# VAE Decode
vae_decode_id, vae_decode_node = builder.add_node(
    "VAEDecode",
    [2300, 1150],
    inputs={
        "samples": [ksampler_id, 0],
        "vae": [vae_loader_id, 0]
    },
    title="VAE Decode"
)
vae_decode_node["outputs"] = [{"name": "IMAGE", "type": "IMAGE", "links": []}]

# Save Image
save_image_id, save_image_node = builder.add_node(
    "SaveImage",
    [2550, 1150],
    inputs={"images": [vae_decode_id, 0]},
    widgets_values=["ArchViz_Ultimate_Result"],
    title="Save Result"
)

builder.save("ultimate_archviz_workflow_gguf.json")
print("Ultimate GGUF Workflow generated successfully.")
