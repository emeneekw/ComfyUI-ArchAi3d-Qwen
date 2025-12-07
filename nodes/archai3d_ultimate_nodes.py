"""
ArchAi3D Ultimate Nodes — The All-in-One ArchViz Solution
Combines all previous specialized nodes into two powerful master nodes.

1. ArchAi3D_Ultimate_Prompt: Handles Camera, Person, Clean Room, Material, and Style logic.
2. ArchAi3D_Ultimate_Encoder: Handles Image Scaling and Qwen Encoding in one step.

Author: Amir Ferdos (ArchAi3d)
Category: ArchAi3d/Ultimate
"""

from .camera.object_focus_camera_v7 import ArchAi3D_Object_Focus_Camera_V7
from .camera.archai3d_qwen_person_perspective import ArchAi3D_Qwen_Person_Perspective
from .core.prompts.archai3d_clean_room_prompt import ArchAi3D_Clean_Room_Prompt
from .editing.archai3d_qwen_material_changer import ArchAi3D_Qwen_Material_Changer
from .editing.archai3d_qwen_style_transfer import ArchAi3D_Qwen_Style_Transfer
from .core.encoders.archai3d_qwen_encoder_v3 import ArchAi3D_Qwen_Encoder_V3, CONDITIONING_PRESETS
from .core.utils.archai3d_qwen_image_scale import ArchAi3D_Qwen_Image_Scale, PREFERRED_ASPECT_RATIOS

class ArchAi3D_Ultimate_Prompt:
    """
    The Ultimate Prompt Generator.
    Combines functionality of:
    - Object Focus Camera V7
    - Person Perspective
    - Clean Room Prompt
    - Material Changer
    - Style Transfer

    Select a 'Mode' to activate the relevant logic.
    """

    MODES = [
        "Camera: Object Focus (Product/Arch)",
        "Camera: Person Perspective (Portrait)",
        "Edit: Clean Room / Redesign",
        "Edit: Material Changer",
        "Edit: Style Transfer"
    ]

    @classmethod
    def INPUT_TYPES(cls):
        # We gather inputs from all sub-nodes.
        # To avoid naming conflicts, we prefix them or rely on unique names.

        # --- Camera V7 Inputs ---
        cam_inputs = ArchAi3D_Object_Focus_Camera_V7.INPUT_TYPES()["required"]

        # --- Person Perspective Inputs ---
        person_inputs = ArchAi3D_Qwen_Person_Perspective.INPUT_TYPES()["required"]

        # --- Clean Room Inputs ---
        room_inputs = ArchAi3D_Clean_Room_Prompt.INPUT_TYPES()["required"]
        room_opt = ArchAi3D_Clean_Room_Prompt.INPUT_TYPES()["optional"]

        # --- Material Changer Inputs ---
        mat_inputs = ArchAi3D_Qwen_Material_Changer.define_schema().inputs
        # Helper to extract combos/options from schema objects would be complex,
        # so we'll just manually define the key ones based on our reading of the files.

        return {
            "required": {
                "mode": (cls.MODES, {"default": "Camera: Object Focus (Product/Arch)"}),

                # SHARED / GENERIC INPUTS
                "main_subject": ("STRING", {"multiline": True, "default": "", "placeholder": "Target Object / Person / Room Context"}),
                "scene_context": ("STRING", {"multiline": True, "default": "", "placeholder": "Environment / Context / Background"}),

                # --- CAMERA (OBJECT) ---
                "cam_shot_size": cam_inputs["shot_size"],
                "cam_angle": cam_inputs["camera_angle"],
                "cam_movement": cam_inputs["camera_movement"],
                "cam_lens": cam_inputs["lens_type"],

                # --- CAMERA (PERSON) ---
                "person_preset": person_inputs["perspective_preset"],
                "person_identity": person_inputs["identity_preservation"],
                "person_effect": person_inputs["psychological_effect"],

                # --- EDIT (ROOM) ---
                "room_action": (["Remove + Paint All", "Remove Only", "Remove + Paint Selective"], {"default": "Remove + Paint All"}),
                "room_remove_list": ("STRING", {"multiline": True, "default": "construction debris/tools", "placeholder": "Objects to remove"}),

                # --- EDIT (MATERIAL) ---
                "mat_category": (["stone", "wood", "metal", "fabric", "paint", "tile", "custom"], {"default": "stone"}),
                "mat_preset": ("STRING", {"default": "custom", "placeholder": "Material description or preset name"}),

                # --- EDIT (STYLE) ---
                "style_preset": (["ice", "cloud", "chinese_lantern", "wooden", "blue_white_porcelain", "fluffy", "weaving", "balloon"], {"default": "ice"}),
            },
            "optional": {
                 # Advanced Camera
                 "cam_height": cam_inputs["height"],
                 "cam_direction": cam_inputs["direction"],
                 "cam_framing": cam_inputs["framing_mode"],
                 "cam_distance": cam_inputs["distance_meters"],
                 "cam_auto_facing": cam_inputs["auto_facing"],
                 "cam_focus_trans": cam_inputs["focus_transition_mode"],
                 "cam_detail": cam_inputs["add_detailed_explanation"],
                 "cam_mat_detail": cam_inputs["material_detail_preset"],
                 "cam_photo_qual": cam_inputs["photography_quality_preset"],

                 # Advanced Person
                 "person_focal": person_inputs["focal_point"],
                 "person_body": person_inputs["body_proportion"],

                 # Advanced Room
                 "room_floor": room_opt["floor_material"],
                 "room_wall": room_opt["wall_material"],
                 "room_ceil": room_opt["ceiling_material"],
                 "room_style": room_opt["photography_style"],
                 "room_light": room_opt["lighting_preset"],

                 # Shared Options
                 "debug_mode": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("prompt", "system_prompt")
    FUNCTION = "generate"
    CATEGORY = "ArchAi3d/Ultimate"

    def generate(self, mode, main_subject, scene_context,
                 # Camera
                 cam_shot_size, cam_angle, cam_movement, cam_lens,
                 cam_height="slightly_above", cam_direction="front", cam_framing="Shot Size Presets", cam_distance=2.0,
                 cam_auto_facing=True, cam_focus_trans="Standard", cam_detail="Detailed",
                 cam_mat_detail="None", cam_photo_qual="Cinematic Quality",
                 # Person
                 person_preset="eye_level_front", person_identity="strict", person_effect="none",
                 person_focal="auto", person_body="natural",
                 # Room
                 room_action="Remove + Paint All", room_remove_list="construction debris",
                 room_floor="Polished Black Marble", room_wall="Flat White", room_ceil="Flat White",
                 room_style="Real Estate", room_light="Natural Daylight",
                 # Material
                 mat_category="stone", mat_preset="custom",
                 # Style
                 style_preset="ice",
                 # Misc
                 debug_mode=False
                 ):

        # Instantiate helper classes
        cam_node = ArchAi3D_Object_Focus_Camera_V7()
        person_node = ArchAi3D_Qwen_Person_Perspective()
        room_node = ArchAi3D_Clean_Room_Prompt()
        mat_node = ArchAi3D_Qwen_Material_Changer()
        style_node = ArchAi3D_Qwen_Style_Transfer()

        prompt = ""
        system_prompt = ""

        if mode == "Camera: Object Focus (Product/Arch)":
            # Map inputs to Camera V7
            # target_object <- main_subject
            # We assume "English" as default language for Ultimate node
            p, sys, desc = cam_node.generate_cinematography_prompt(
                target_object=main_subject,
                shot_size=cam_shot_size,
                camera_angle=cam_angle,
                camera_movement=cam_movement,
                height=cam_height,
                direction=cam_direction,
                framing_mode=cam_framing,
                distance_meters=cam_distance,
                auto_facing=cam_auto_facing,
                lens_type=cam_lens,
                prompt_language="English (Universal)",
                focus_transition_mode=cam_focus_trans,
                add_detailed_explanation=cam_detail,
                material_detail_preset=cam_mat_detail,
                photography_quality_preset=cam_photo_qual,
                show_details=scene_context # Use context as extra details
            )
            prompt = f"{p}. {desc}"
            system_prompt = sys

        elif mode == "Camera: Person Perspective (Portrait)":
            # person_preset, identity, effect, focal, body, context, bg_adapt, light, comp, detail, style, custom, debug
            # Output: perspective_prompt, full_prompt, preservation_hints, system_prompt
            out = person_node.execute(
                perspective_preset=person_preset,
                identity_preservation=person_identity,
                psychological_effect=person_effect,
                focal_point=person_focal,
                body_proportion=person_body,
                scene_context=scene_context,
                background_adaptation=True, # Defaults
                lighting_reinforcement=True,
                composition_centering=True,
                detail_showcase="high",
                prompt_style="balanced",
                custom_additions=main_subject, # Append subject details
                debug_mode=debug_mode
            )
            # io.NodeOutput(perspective_prompt, full_prompt, preservation_hints, system_prompt)
            # The .execute returns io.NodeOutput object which behaves like a tuple or has attributes?
            # Looking at source, io.NodeOutput takes *args. ComfyUI usually expects tuple return from execute.
            # But here we are calling it directly. Let's assume it returns the tuple defined in RETURN_TYPES or the object.
            # Wait, `io.ComfyNode` execute usually returns a tuple matching RETURN_TYPES.
            # The class `ArchAi3D_Qwen_Person_Perspective` returns `io.NodeOutput`.
            # We need to unpack it.
            # If it's a tuple subclass:
            prompt = out[1] # full_prompt
            system_prompt = out[3]

        elif mode == "Edit: Clean Room / Redesign":
            # mode, image_ref, remove_list, context, remove_wm, wm_type, wm_loc, floor..., wall..., ceil..., photo..., light..., preserve..., system_preset...
            # We simplify inputs here.
            p, sys = room_node.build_prompt(
                mode=room_action,
                image_reference="image", # Standard placeholder
                objects_to_remove=room_remove_list,
                scene_context=scene_context,
                floor_material=room_floor, floor_custom="",
                wall_material=room_wall, wall_custom="",
                ceiling_material=room_ceil, ceiling_custom="",
                photography_style=room_style,
                lighting_preset=room_light,
                system_preset="Room Transform Specialist"
            )
            prompt = p
            system_prompt = sys

        elif mode == "Edit: Material Changer":
            # object_preset, custom_obj, cat, mat_preset, custom_mat, context, preserve, debug
            # We map main_subject -> custom_object
            # mat_preset -> custom_material if not in list, but we have a text input.
            # The original node logic is complex about presets.
            # We will use 'custom' preset and pass our text as custom_material/object.
            out = mat_node.execute(
                object_preset="custom",
                custom_object=main_subject,
                material_category=mat_category,
                material_preset="custom",
                custom_material=mat_preset,
                scene_context=scene_context,
                preserve_rest=True,
                debug_mode=debug_mode
            )
            prompt = out[0]
            system_prompt = out[2]

        elif mode == "Edit: Style Transfer":
            # object_preset, custom, style, context, debug
            out = style_node.execute(
                object_preset="custom",
                custom_object=main_subject,
                style=style_preset,
                scene_context=scene_context,
                debug_mode=debug_mode
            )
            prompt = out[0]
            system_prompt = out[2]

        if debug_mode:
            print(f"[Ultimate Prompt] Mode: {mode}")
            print(f"Prompt: {prompt}")
            print(f"System: {system_prompt}")

        return (prompt, system_prompt)


class ArchAi3D_Ultimate_Encoder:
    """
    The Ultimate Encoder.
    Combines Image Scaling and Qwen Encoding.
    1. Scales Input Image to Qwen-preferred aspect ratio.
    2. Encodes using Qwen Encoder V3 logic.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "clip": ("CLIP",),
                "prompt": ("STRING", {"multiline": True, "forceInput": True}),
                "vae": ("VAE",), # Required for V3 latent logic

                # Scaling Options
                "aspect_ratio": (list(PREFERRED_ASPECT_RATIOS.keys()), {"default": "16:9 (Panorama)"}),
                "scale_mode": (["auto", "manual"], {"default": "auto"}),

                # Encoder Options
                "conditioning_balance": (list(CONDITIONING_PRESETS.keys()), {"default": "Balanced"}),
            },
            "optional": {
                "system_prompt": ("STRING", {"multiline": True, "forceInput": True}),
                "debug_mode": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("CONDITIONING", "LATENT", "FLOAT", "IMAGE")
    RETURN_NAMES = ("conditioning", "latent", "recommended_cfg", "scaled_image")
    FUNCTION = "process"
    CATEGORY = "ArchAi3d/Ultimate"

    def process(self, image, clip, prompt, vae, aspect_ratio, scale_mode, conditioning_balance, system_prompt="", debug_mode=False):

        # 1. Scale Image
        scaler = ArchAi3D_Qwen_Image_Scale()
        # process returns (image_vl, image_latent, debug_text)
        # We generally want to use the scaled image for both VL and Latent input to Encoder V3
        # Encoder V3 takes 'image1_vl' and 'image1_latent'.
        # 'image_vl' from scaler is optimized for CLIP/Vision.
        # 'image_latent' from scaler is optimized for VAE.

        scaled_vl, scaled_latent_img, _ = scaler.process(
            image=image,
            aspect_ratio_mode=scale_mode,
            preferred_aspect_ratio=aspect_ratio,
            debug=debug_mode
        )

        # 2. Encode
        # Encoder V3 inputs: clip, prompt, vae, image1_vl, image1_latent, system_prompt...
        encoder = ArchAi3D_Qwen_Encoder_V3()
        out = encoder.execute(
            clip=clip,
            prompt=prompt,
            vae=vae,
            image1_vl=scaled_vl,
            image1_latent=scaled_latent_img,
            system_prompt=system_prompt,
            conditioning_balance=conditioning_balance,
            debug_mode=debug_mode,
            auto_label=True
        )

        # Encoder returns io.NodeOutput(conditioning, combined_latent, formatted_prompt, recommended_cfg)
        # We need to unpack.
        # io.NodeOutput behaves like a tuple (cond, latent, prompt, cfg) based on RETURN_TYPES order in Encoder V3.
        # Encoder V3 RETURN_TYPES: ("CONDITIONING", "LATENT", "STRING", "FLOAT")
        # So: [0]=cond, [1]=latent, [2]=prompt, [3]=cfg

        return (out[0], out[1], out[3], scaled_latent_img)
