"""UK dataset modules: EPC, PIPR, ASHE, Census, Geography, Construction."""

from src.datasets.uk.ashe import ashe_dataset
from src.datasets.uk.census import census_dataset
from src.datasets.uk.construction import construction_dataset
from src.datasets.uk.epc import epc_dataset
from src.datasets.uk.geography import uk_geography_dataset
from src.datasets.uk.pipr import pipr_dataset

__all__ = [
    "epc_dataset",
    "pipr_dataset",
    "ashe_dataset",
    "census_dataset",
    "uk_geography_dataset",
    "construction_dataset",
]
