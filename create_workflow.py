import json
import random

class WorkflowBuilder:
    def __init__(self):
        self.nodes_list = [] # Keep ordered list for final JSON
        self.nodes_map = {}  # Map for quick access by ID to update outputs
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

        # Store in map and list immediately so we can reference it if needed (though usually we ref previous nodes)
        self.nodes_map[node_id] = node
        self.nodes_list.append(node)

        if inputs:
            for name, link_info in inputs.items():
                if link_info:
                    source_node_id = link_info[0]
                    source_slot_index = link_info[1]

                    link_id = self.get_link_id()

                    # Create the global link definition
                    # [id, origin_id, origin_slot, target_id, target_slot, type]
                    self.links.append([link_id, source_node_id, source_slot_index, node_id, len(node["inputs"]), name])

                    # Set link on the Target Input (current node)
                    node["inputs"].append({"name": name, "type": "*", "link": link_id})

                    # Update the Source Node Output
                    if source_node_id in self.nodes_map:
                        source_node = self.nodes_map[source_node_id]
                        # Ensure outputs array exists and is large enough
                        # Usually outputs are defined *after* add_node in this script, which is a problem.
                        # We need to make sure outputs are defined before we try to link to them,
                        # OR we defer the link update?
                        # Actually, looking at the script, outputs are set like `node["outputs"] = ...` AFTER `add_node` returns.
                        # This means when `add_node` is running for a downstream node, the upstream node
                        # DOES have its outputs set manually in the previous lines of the script.

                        if source_slot_index < len(source_node["outputs"]):
                             source_node["outputs"][source_slot_index]["links"].append(link_id)
                        else:
                            print(f"Warning: Trying to link to non-existent output slot {source_slot_index} on node {source_node_id}")
                    else:
                        print(f"Warning: Source node {source_node_id} not found in map.")

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
# Optimized for GGUF/Quantized models (requires ComfyUI-GGUF or latest ComfyUI native support)
# We assume UnetLoaderGGUF is available.
# =================================================================================================
builder.add_group("Loaders (GGUF & Qwen)", [10, 10, 600, 800])

# Unet Loader (GGUF)
unet_loader_id, unet_loader_node = builder.add_node(
    "UnetLoaderGGUF",
    [50, 50],
    widgets_values=["sd_xl_base_1.0.gguf"], # Placeholder GGUF name
    title="GGUF Unet Loader"
)
unet_loader_node["outputs"] = [{"name": "MODEL", "type": "MODEL", "links": []}]

# CLIP Loader (Standard/Dual for SDXL)
clip_loader_id, clip_loader_node = builder.add_node(
    "DualCLIPLoader", # Or standard CLIPLoader
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
# GROUP 2: Input & Preprocessing
# =================================================================================================
builder.add_group("Input & Scaling", [700, 10, 400, 400])

# Input Image
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

# Qwen Image Scale
# NOTE: inputs are defined in add_node, which tries to update source links immediately.
# So sources MUST have their "outputs" defined before this is called.
# 'image_node' was just defined above with outputs, so this is safe.
scale_node_id, scale_node = builder.add_node(
    "ArchAi3D_Qwen_Image_Scale",
    [750, 300],
    inputs={"image": [image_node_id, 0]},
    widgets_values=["auto", "16:9 (Panorama)", 147456, 32, 1763584, 32, 0.3, True, True, True, "area", "disabled", False, "lanczos", "center", False, True],
    title="Smart Image Scale"
)
scale_node["outputs"] = [
    {"name": "image_vl", "type": "IMAGE", "links": []},
    {"name": "image_latent", "type": "IMAGE", "links": []},
    {"name": "debug_text", "type": "STRING", "links": []}
]


# =================================================================================================
# GROUP 3: Mode 1 - Cinematic Object Focus (DEFAULT CONNECTED)
# Use: Product photography, detailed object shots
# =================================================================================================
builder.add_group("Mode 1: Object Focus (Camera V7)", [1200, 10, 400, 500])

camera_node_id, camera_node = builder.add_node(
    "ArchAi3D_Object_Focus_Camera_V7",
    [1250, 50],
    inputs={},
    widgets_values=[
        "modern interior", "Wide Shot (WS)", "Eye Level", "Static (No Movement)", "slightly_above", "front",
        "Shot Size Presets", 2.0, True, "Wide Angle (24-35mm)", "English (Universal)",
        "Focus Transition (Reposition to Object)", "Detailed (Full cinematography explanation)",
        "None (Manual entry)", "Cinematic Quality", ""
    ],
    title="Object Focus Camera"
)
camera_node["outputs"] = [
    {"name": "prompt", "type": "STRING", "links": []},
    {"name": "system_prompt", "type": "STRING", "links": []},
    {"name": "description", "type": "STRING", "links": []}
]


# =================================================================================================
# GROUP 4: Mode 2 - Room Transformation (BYPASSED)
# Use: Empty room creation, renovation, cleaning
# =================================================================================================
builder.add_group("Mode 2: Room Transform", [1200, 600, 400, 500])

clean_room_id, clean_room_node = builder.add_node(
    "ArchAi3D_Clean_Room_Prompt",
    [1250, 650],
    inputs={},
    # mode, img_ref, objects_to_remove, scene_context, remove_watermark, wm_type, wm_loc, floor_mat, floor_cust, wall_mat, wall_cust, ceiling_mat, ceiling_cust, photo_style, lighting, quality_toggles..., system_preset, custom_sys
    widgets_values=[
        "Remove + Paint All", "image1", "construction debris/tools", "modern office", False, "watermark", "anywhere",
        "Keep Original", "", "Keep Original", "", "Keep Original", "",
        "Real Estate", "Natural Daylight", True, True, True, True, True,
        "Room Transform Specialist", ""
    ],
    title="Clean Room Prompt"
)
clean_room_node["outputs"] = [
    {"name": "user_prompt", "type": "STRING", "links": []},
    {"name": "system_prompt", "type": "STRING", "links": []}
]


# =================================================================================================
# GROUP 5: Mode 3 - Material Changer (BYPASSED)
# Use: Quick material swaps for floors, walls, furniture
# =================================================================================================
builder.add_group("Mode 3: Material Changer", [1700, 10, 400, 500])

material_id, material_node = builder.add_node(
    "ArchAi3D_Qwen_Material_Changer",
    [1750, 50],
    inputs={},
    # object_preset, custom_object, material_category, material_preset, custom_material, scene_context, preserve_rest, debug_mode
    widgets_values=[
        "the kitchen countertop", "", "stone", "custom", "white Carrara marble", "modern kitchen", True, False
    ],
    title="Material Changer"
)
material_node["outputs"] = [
    {"name": "prompt", "type": "STRING", "links": []},
    {"name": "material_description", "type": "STRING", "links": []},
    {"name": "system_prompt", "type": "STRING", "links": []}
]


# =================================================================================================
# GROUP 6: Mode 4 - Style Transfer (BYPASSED)
# Use: Artistic effects (Ice, Cloud, etc.)
# =================================================================================================
builder.add_group("Mode 4: Style Transfer", [1700, 600, 400, 500])

style_id, style_node = builder.add_node(
    "ArchAi3D_Qwen_Style_Transfer",
    [1750, 650],
    inputs={},
    # object_preset, custom_object, style, scene_context, debug_mode
    widgets_values=[
        "the house", "", "ice", "architectural exterior", False
    ],
    title="Style Transfer"
)
style_node["outputs"] = [
    {"name": "prompt", "type": "STRING", "links": []},
    {"name": "style_description", "type": "STRING", "links": []},
    {"name": "system_prompt", "type": "STRING", "links": []}
]


# =================================================================================================
# GROUP 7: Mode 5 - Person Perspective (BYPASSED)
# Use: Portrait/Character angles with identity preservation
# =================================================================================================
builder.add_group("Mode 5: Person Perspective", [2200, 10, 400, 500])

person_id, person_node = builder.add_node(
    "ArchAi3D_Qwen_Person_Perspective",
    [2250, 50],
    inputs={},
    # preset, identity, psycho, focal, body, context, bg_adapt, light, comp, detail, prompt_style, custom, debug
    widgets_values=[
        "low_angle_worms_eye", "strict", "power", "auto", "natural", "outdoor city street", True, True, True, "high", "balanced", "", False
    ],
    title="Person Perspective"
)
person_node["outputs"] = [
    {"name": "perspective_prompt", "type": "STRING", "links": []},
    {"name": "full_prompt", "type": "STRING", "links": []},
    {"name": "preservation_hints", "type": "STRING", "links": []},
    {"name": "system_prompt", "type": "STRING", "links": []}
]


# =================================================================================================
# GROUP 8: Encoding & Generation
# =================================================================================================
builder.add_group("Qwen Encoding & Generation", [1200, 1200, 1000, 600])

# Qwen Encoder V3
encoder_id, encoder_node = builder.add_node(
    "ArchAi3D_Qwen_Encoder_V3",
    [1250, 1250],
    inputs={
        "clip": [qwen_clip_id, 0],
        "prompt": [camera_node_id, 0],        # Default connected to Camera V7 (Mode 1)
        "vae": [vae_loader_id, 0],            # Connected to VAE Loader
        "image1_vl": [scale_node_id, 0],      # Connected to Scaling VL
        "image2_vl": None,
        "image3_vl": None,
        "image1_latent": [scale_node_id, 1],  # Connected to Scaling Latent
        "image2_latent": None,
        "image3_latent": None,
        "system_prompt": [camera_node_id, 1], # Default connected to Camera V7 system prompt
        "conditioning_balance_override": None
    },
    widgets_values=["", "Balanced", "", 1.0, 1.0, "Image 1", "Image 2", "Image 3", 1.0, 1.0, 1.0, False],
    title="Qwen Encoder V3"
)
encoder_node["outputs"] = [
    {"name": "conditioning", "type": "CONDITIONING", "links": []},
    {"name": "latent", "type": "LATENT", "links": []},
    {"name": "formatted_prompt", "type": "STRING", "links": []},
    {"name": "recommended_cfg", "type": "FLOAT", "links": []}
]

# Negative Prompt
neg_prompt_id, neg_prompt_node = builder.add_node(
    "CLIPTextEncode",
    [1600, 1250],
    inputs={"clip": [clip_loader_id, 0]}, # SDXL CLIP
    widgets_values=["text, watermark, low quality, blurry, distorted, ugly, bad anatomy"],
    title="Negative Prompt"
)
neg_prompt_node["outputs"] = [{"name": "CONDITIONING", "type": "CONDITIONING", "links": []}]

# KSampler
ksampler_id, ksampler_node = builder.add_node(
    "KSampler",
    [1600, 1500],
    inputs={
        "model": [unet_loader_id, 0], # GGUF Unet
        "positive": [encoder_id, 0],
        "negative": [neg_prompt_id, 0],
        "latent_image": [encoder_id, 1],
    },
    widgets_values=[random.randint(1, 10000000), "fixed", 30, 4.0, "dpmpp_2m", "karras", 1.0],
    title="KSampler (GGUF Optimized)"
)
ksampler_node["outputs"] = [{"name": "LATENT", "type": "LATENT", "links": []}]

# VAE Decode
vae_decode_id, vae_decode_node = builder.add_node(
    "VAEDecode",
    [1950, 1500],
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
    [2200, 1500],
    inputs={"images": [vae_decode_id, 0]},
    widgets_values=["ArchViz_GGUF_Result"],
    title="Save Result"
)

# Note about routing:
# The user can manually reconnect the inputs of 'Qwen Encoder V3' ('prompt' and 'system_prompt')
# to the outputs of other mode groups (Clean Room, Material Changer, etc.) to switch modes.
# This workflow sets Mode 1 (Camera) as the default active connection.

builder.save("ultimate_archviz_workflow_gguf.json")
print("GGUF Workflow generated successfully.")
