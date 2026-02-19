"""Batch apply speech bubbles to all 16 greeting scene images.

Each scene has custom bubble positions based on where the speakers
appear in the generated image. Positions are (x_frac, y_frac) where
(0,0) = top-left, (1,1) = bottom-right.
"""

from pathlib import Path
from overlay import overlay_bubbles

OUTPUT_DIR = Path("output")
FINAL_DIR = Path("output/final")
FINAL_DIR.mkdir(parents=True, exist_ok=True)

# Each entry: (input_file, output_name, left_text, right_text, pos_left, pos_right)
# Positions are tuned per-image based on where speakers appear.
SCENES = [
    # 1. migwọ - Urhobo bride kneeling before father at traditional marriage
    (
        "20260218_210849_An_Urhobo_traditional_marriage_scene_in.png",
        "01_migwo_morning.png",
        "migwọ", None,
        (0.30, 0.25), None,
    ),
    # 2. migwọ - young Urhobo man receiving gift from grandmother
    (
        "20260218_211024_A_young_Urhobo_man_from_Nigerias_Niger.png",
        "02_migwo_receiving.png",
        None, "migwọ",
        None, (0.30, 0.25),
    ),
    # 3. migwọ - young Urhobo woman serving food to elder in fedora
    (
        "20260218_211046_A_young_Urhobo_woman_from_Nigeria_servin.png",
        "03_migwo_serving.png",
        None, "migwọ",
        None, (0.65, 0.20),
    ),
    # 4. migwọ - young man on left bowing, elder man on right, street scene
    (
        "20260216_143341_A_young_Nigerian_Urhobo_man_slightly_bow.png",
        "04_migwo_head_bow.png",
        "migwọ", None,
        (0.39, 0.35), None,
    ),
    # 5. migwọ/Vrẹndo - Urhobo marriage: bride kneeling, elder woman responding
    (
        "20260218_211310_An_Urhobo_traditional_marriage_scene_fro.png",
        "05_migwo_vrendo.png",
        "migwọ", "Vrẹndo",
        (0.28, 0.25), (0.85, 0.2),
    ),
    # 6. Oma ganre - woman on left, man on right, market scene
    (
        "20260216_143553_Two_Nigerian_Urhobo_adults_meeting_at_a.png",
        "06_oma_ganre.png",
        "Oma ganre?", "E Omamẹ ganre",
        (0.30, 0.25), (0.72, 0.25),
    ),
    # 7. Mavọ/Merọ - woman on left, man on right, campus handshake
    (
        "20260216_143609_Two_young_Nigerian_Urhobo_friends_greeti.png",
        "07_mavo_mero.png",
        "Mavọ?", "Merọ",
        (0.28, 0.45), (0.72, 0.40),
    ),
    # 8. Obuwevwi Dori - NEW clean image, woman on left visiting, woman on right at door
    (
        "20260216_145035_Two_middle-aged_Nigerian_Urhobo_women_ha_1.png",
        "08_obuwevwi_dori.png",
        "Obuwevwi Dori?", "E Odori gangan",
        (0.34, 0.25), (0.79, 0.29),
    ),
    # 9. Good morning - two women on a village path, left and right
    (
        "20260216_143649_Two_Nigerian_Urhobo_women_meeting_on_a_p.png",
        "09_good_morning.png",
        "Omamọ urhiọke!", None,
        (0.30, 0.25), None,
    ),
    # 10. Good afternoon - man on left waving, man on right at shop
    (
        "20260216_143709_Two_Nigerian_Urhobo_men_greeting_each_ot.png",
        "10_good_afternoon.png",
        "Omamọ Oghẹruvo!", "Omamọ Oghẹruvo!",
        (0.28, 0.40), (0.75, 0.40),
    ),
    # 11. Good evening - man arriving center, elder seated on left, veranda
    (
        "20260216_143727_A_Nigerian_Urhobo_family_gathering_on_a.png",
        "11_good_evening.png",
        "Omamọ Ovwọvwọn!", None,
        (0.40, 0.27), None,
    ),
    # 12. Good night - woman in doorway on right, person walking away on left
    (
        "20260216_144051_A_Nigerian_Urhobo_woman_standing_at_the.png",
        "12_good_night.png",
        None, "Todẹ!",
        None, (0.72, 0.35),
    ),
    # 13. Thank you - young woman on left receiving food, older woman on right giving
    (
        "20260216_143809_A_young_Nigerian_Urhobo_woman_gratefully.png",
        "13_thank_you.png",
        "do!", None,
        (0.75, 0.150), None,
    ),
    # 14. Sorry please - man on left helping, woman on right with dropped items
    (
        "20260216_143838_A_Nigerian_Urhobo_man_apologetically_app.png",
        "14_sorry_please.png",
        "do biko!", None,
        (0.30, 0.12), None,
    ),
    # 15. Safe journey - elder on left waving, young man on right at bus
    (
        "20260216_143906_A_Nigerian_Urhobo_elder_waving_goodbye_t.png",
        "15_safe_journey.png",
        "ra wọ rhe!", None,
        (0.30, 0.40), None,
    ),
    # 16. Goodbye - two friends at crossroads, left waving, right walking away
    (
        "20260216_143924_Two_Nigerian_Urhobo_friends_saying_goodb.png",
        "16_goodbye.png",
        "yere obuwevwi!", None,
        (0.30, 0.45), None,
    ),
]


def main():
    for input_file, output_name, left, right, pos_l, pos_r in SCENES:
        input_path = OUTPUT_DIR / input_file
        output_path = FINAL_DIR / output_name

        if not input_path.exists():
            print(f"  SKIP (not found): {input_file}")
            continue

        overlay_bubbles(input_path, output_path,
                        left_text=left, right_text=right,
                        pos_left=pos_l, pos_right=pos_r)
        print(f"  OK: {output_name}")

    print(f"\nDone! {len(SCENES)} images saved to {FINAL_DIR}/")


if __name__ == "__main__":
    main()
