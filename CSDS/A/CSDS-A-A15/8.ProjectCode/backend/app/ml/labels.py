"""Defect taxonomy and static metadata for the inspection model."""

CLASS_NAMES = [
    "crazing",
    "inclusion",
    "patches",
    "pitted_surface",
    "rolled-in_scale",
    "scratches",
]

DEFECT_INFO = {
    "crazing": {
        "display_name": "Crazing",
        "description": (
            "A fine, interconnected network of surface cracks resembling a spider-web pattern."
        ),
        "likely_causes": [
            "Uneven cooling rate across the strip width after hot rolling",
            "Thermal stress from rapid temperature fluctuations at the roll surface",
            "Residual stress concentration from prior forming stages",
        ],
        "corrective_actions": [
            "Recalibrate the run-out table cooling profile for uniform strip cooling",
            "Inspect and stabilize roll surface temperature control loops",
            "Reduce cooling rate gradient between strip edge and center",
        ],
        "severity_baseline": "medium",
    },
    "inclusion": {
        "display_name": "Inclusion",
        "description": (
            "Non-metallic particles (oxides, slag, or refractory fragments) embedded in the surface."
        ),
        "likely_causes": [
            "Contamination of molten steel with slag or refractory erosion products",
            "Insufficient filtration or degassing during casting",
            "Poor ladle-to-tundish transfer practice",
        ],
        "corrective_actions": [
            "Improve slag detection and skimming before casting",
            "Inspect refractory lining condition and replace worn sections",
            "Tighten filtration/degassing process controls at the caster",
        ],
        "severity_baseline": "high",
    },
    "patches": {
        "display_name": "Patches",
        "description": (
            "Irregular, discolored surface patches typically linked to scale formation."
        ),
        "likely_causes": [
            "Incomplete descaling before hot rolling",
            "Non-uniform oxide scale buildup in the reheat furnace",
            "Furnace atmosphere (O2 content) out of specification",
        ],
        "corrective_actions": [
            "Recalibrate descaling nozzle pressure and coverage pattern",
            "Audit reheat furnace atmosphere and residence time",
            "Increase descaling pass count for affected coil sections",
        ],
        "severity_baseline": "low",
    },
    "pitted_surface": {
        "display_name": "Pitted Surface",
        "description": (
            "Small, localized pits or craters caused by debris or rolled-in particles."
        ),
        "likely_causes": [
            "Debris or loose scale rolled into the strip surface",
            "Worn or locally damaged work-roll surface",
            "Inadequate pre-rolling surface cleaning",
        ],
        "corrective_actions": [
            "Inspect and recondition or replace the affected work roll",
            "Improve strip surface cleaning before the rolling stand",
            "Increase scale-breaker and brush maintenance frequency",
        ],
        "severity_baseline": "medium",
    },
    "rolled-in_scale": {
        "display_name": "Rolled-in Scale",
        "description": (
            "Primary oxide scale that was pressed into the strip surface during hot rolling."
        ),
        "likely_causes": [
            "Inadequate high-pressure descaling before the first rolling stand",
            "Excessive time between reheat furnace exit and descaling",
            "Descaling nozzle blockage or misalignment",
        ],
        "corrective_actions": [
            "Increase descaling water pressure and verify nozzle alignment",
            "Reduce furnace-to-descaler transfer time",
            "Schedule preventive maintenance for descaling headers",
        ],
        "severity_baseline": "high",
    },
    "scratches": {
        "display_name": "Scratches",
        "description": (
            "Linear surface marks caused by mechanical contact during handling or rolling."
        ),
        "likely_causes": [
            "Misaligned guide plates or tension rollers",
            "Damaged or worn conveyor/transport rollers",
            "Improper coil handling during transfer",
        ],
        "corrective_actions": [
            "Inspect and realign guide plates and tension rollers",
            "Replace worn conveyor rollers in the affected line section",
            "Review and retrain handling procedures for coil transfer",
        ],
        "severity_baseline": "low",
    },
}
