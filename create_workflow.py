import json
import random

class WorkflowBuilder:
    def __init__(self):
        self.nodes = []
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

        # Add input slots based on definition (simplified for this script, we assume knowledge of inputs)
        if inputs:
            for name, link_info in inputs.items():
                # link_info is [source_node_id, source_output_index]
                if link_info:
                    link_id = self.get_link_id()
                    self.links.append([link_id, link_info[0], link_info[1], node_id, len(node["inputs"]), name])
                    node["inputs"].append({"name": name, "type": "*", "link": link_id})
                else:
                     node["inputs"].append({"name": name, "type": "*", "link": None})

        self.nodes.append(node)
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
            "nodes": self.nodes,
            "links": self.links,
            "groups": self.groups,
            "config": {},
            "extra": {},
            "version": 0.4
        }
        with open(filename, 'w') as f:
            json.dump(workflow, f, indent=2)

builder = WorkflowBuilder()

# 1. Loaders Group
builder.add_group("Loaders & Models", [10, 10, 600, 600])

# Checkpoint Loader (Standard SDXL)
ckpt_node_id, ckpt_node = builder.add_node(
    "CheckpointLoaderSimple",
    [50, 100],
    widgets_values=["sd_xl_base_1.0.safetensors"]
)
ckpt_node["outputs"] = [
    {"name": "MODEL", "type": "MODEL", "links": []},
    {"name": "CLIP", "type": "CLIP", "links": []},
    {"name": "VAE", "type": "VAE", "links": []}
]

# Qwen CLIP Loader
qwen_clip_node_id, qwen_clip_node = builder.add_node(
    "CLIPLoader",
    [50, 300],
    widgets_values=["qwen_vl_clip.safetensors"],
    title="Qwen-VL CLIP Loader"
)
qwen_clip_node["outputs"] = [
    {"name": "CLIP", "type": "CLIP", "links": []}
]

# Input Image
image_node_id, image_node = builder.add_node(
    "LoadImage",
    [50, 500],
    widgets_values=["example.png", "image"],
    title="Input Image (Room/Object)"
)
image_node["outputs"] = [
    {"name": "IMAGE", "type": "IMAGE", "links": []},
    {"name": "MASK", "type": "MASK", "links": []}
]

# 2. Scaling Group
builder.add_group("Image Scaling", [700, 100, 400, 300])

# Qwen Image Scale
scale_node_id, scale_node = builder.add_node(
    "ArchAi3D_Qwen_Image_Scale",
    [750, 150],
    inputs={"image": [image_node_id, 0]},
    # Widgets: aspect_mode, preferred_ratio, vl_target, vl_div, latent_target, latent_div, tol, use_latent_src, ign_let, ign_crop, vl_up, vl_crop, vl_let, lat_up, lat_crop, lat_let, debug
    widgets_values=[
        "auto", "16:9 (Panorama)", 147456, 32, 1763584, 32, 0.3, True, True, True, "area", "disabled", False, "lanczos", "center", False, True
    ]
)
scale_node["outputs"] = [
    {"name": "image_vl", "type": "IMAGE", "links": []},
    {"name": "image_latent", "type": "IMAGE", "links": []},
    {"name": "debug_text", "type": "STRING", "links": []}
]


# 3. Prompting & Camera Group
builder.add_group("Prompt & Camera Control", [700, 500, 800, 600])

# Object Focus Camera V7
camera_node_id, camera_node = builder.add_node(
    "ArchAi3D_Object_Focus_Camera_V7",
    [750, 550],
    inputs={},
    # Widgets: target_object, shot_size, camera_angle, camera_movement, height, direction, framing_mode, distance, auto_facing, lens, lang, focus_mode, explain, material, quality, details
    widgets_values=[
        "modern interior", # target_object
        "Wide Shot (WS)", # shot_size
        "Eye Level", # camera_angle
        "Static (No Movement)", # camera_movement
        "slightly_above", # height
        "front", # direction
        "Shot Size Presets", # framing_mode
        2.0, # distance
        True, # auto_facing
        "Wide Angle (24-35mm)", # lens_type
        "English (Universal)", # prompt_language
        "Focus Transition (Reposition to Object)", # focus_transition_mode
        "Detailed (Full cinematography explanation)", # add_detailed_explanation
        "None (Manual entry)", # material_detail_preset
        "Cinematic Quality", # photography_quality_preset
        "" # show_details
    ],
    title="Main Camera Control (V7)"
)
camera_node["outputs"] = [
    {"name": "prompt", "type": "STRING", "links": []},
    {"name": "system_prompt", "type": "STRING", "links": []},
    {"name": "description", "type": "STRING", "links": []}
]

# Alternative: Clean Room Prompt (Placed nearby but disconnected by default, or connectable)
clean_room_node_id, clean_room_node = builder.add_node(
    "ArchAi3D_Clean_Room_Prompt",
    [750, 950],
    inputs={},
    # Widgets: mode, img_ref, remove_list, scene_ctx, rm_watermark, wm_type, wm_loc, floor_mat, floor_cust, wall_mat, ...
    widgets_values=[
        "Remove + Paint All", "image1", "construction debris/tools", "modern office", False, "watermark", "anywhere",
        "Keep Original", "", "Keep Original", "", "Keep Original", "",
        "Real Estate", "Natural Daylight", True, True, True, True, True,
        "Room Transform Specialist", ""
    ],
    title="Alternative: Clean Room Prompt"
)
clean_room_node["outputs"] = [
    {"name": "user_prompt", "type": "STRING", "links": []},
    {"name": "system_prompt", "type": "STRING", "links": []}
]

# 4. Encoder Group
builder.add_group("Qwen Encoding", [1200, 100, 500, 600])

# Qwen Encoder V3
encoder_node_id, encoder_node = builder.add_node(
    "ArchAi3D_Qwen_Encoder_V3",
    [1250, 150],
    inputs={
        "clip": [qwen_clip_node_id, 0],
        "prompt": [camera_node_id, 0],        # Connected to Camera V7 prompt
        "vae": [ckpt_node_id, 2],            # Standard VAE
        "image1_vl": [scale_node_id, 0],
        "image2_vl": None,
        "image3_vl": None,
        "image1_latent": [scale_node_id, 1],
        "image2_latent": None,
        "image3_latent": None,
        "system_prompt": [camera_node_id, 1], # Connected to Camera V7 system prompt
        "conditioning_balance_override": None
    },
    # Widgets: system_prompt_text, balance, override_text, man_ctx, man_usr, lbl1, lbl2, lbl3, str1, str2, str3, debug
    # Note: system_prompt input is a STRING widget in the class definition if not connected, but here we connect it.
    # The 'system_prompt' in INPUT_TYPES is a String Input widget. In ComfyUI, string widgets can be converted to inputs.
    # In the JSON, we represent this as an input link if connected.
    widgets_values=[
        "", "Balanced", "", 1.0, 1.0, "Image 1", "Image 2", "Image 3", 1.0, 1.0, 1.0, False
    ],
    title="Qwen Encoder V3"
)
encoder_node["outputs"] = [
    {"name": "conditioning", "type": "CONDITIONING", "links": []},
    {"name": "latent", "type": "LATENT", "links": []},
    {"name": "formatted_prompt", "type": "STRING", "links": []},
    {"name": "recommended_cfg", "type": "FLOAT", "links": []}
]

# 5. Generation Group
builder.add_group("Generation", [1800, 100, 600, 500])

# Negative Prompt (Standard)
neg_prompt_node_id, neg_prompt_node = builder.add_node(
    "CLIPTextEncode",
    [1850, 150],
    inputs={"clip": [ckpt_node_id, 1]}, # Standard CLIP
    widgets_values=["text, watermark, low quality, blurry, distorted, ugly"],
    title="Negative Prompt"
)
neg_prompt_node["outputs"] = [
    {"name": "CONDITIONING", "type": "CONDITIONING", "links": []}
]

# KSampler
ksampler_node_id, ksampler_node = builder.add_node(
    "KSampler",
    [1850, 400],
    inputs={
        "model": [ckpt_node_id, 0],
        "positive": [encoder_node_id, 0],
        "negative": [neg_prompt_node_id, 0],
        "latent_image": [encoder_node_id, 1],
    },
    # Widgets: seed, control_after_generate, steps, cfg, sampler_name, scheduler, denoise
    # Note: CFG input is widget, but Encoder V3 outputs recommended_cfg.
    # To connect CFG programmatically in ComfyUI, one usually needs to convert the widget to input.
    # Here we will simulate that connection by adding a link to an input named "cfg" if supported,
    # or just set a default value.
    # Standard KSampler doesn't have CFG input by default unless converted.
    # I will assume the user might need to convert it, OR I use a custom KSampler/primitive.
    # For now, I'll set a static CFG, but note that V3 recommends one.
    widgets_values=[random.randint(1, 10000000), "fixed", 30, 4.0, "dpmpp_2m", "karras", 1.0]
)
ksampler_node["outputs"] = [
    {"name": "LATENT", "type": "LATENT", "links": []}
]

# VAE Decode
vae_decode_id, vae_decode_node = builder.add_node(
    "VAEDecode",
    [1850, 700],
    inputs={
        "samples": [ksampler_node_id, 0],
        "vae": [ckpt_node_id, 2]
    }
)
vae_decode_node["outputs"] = [
    {"name": "IMAGE", "type": "IMAGE", "links": []}
]

# Save Image
save_image_id, save_image_node = builder.add_node(
    "SaveImage",
    [2100, 700],
    inputs={"images": [vae_decode_id, 0]},
    widgets_values=["ArchViz_Result"]
)

# Connect recommended CFG?
# Standard KSampler doesn't support float input for CFG easily without widget conversion.
# I'll leave it as a value 4.0 which is "Balanced" default.

builder.save("ultimate_archviz_workflow.json")
print("Workflow generated successfully.")
