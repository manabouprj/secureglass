"""
Connector registry — single place that knows about all connectors.
Adding a 4th+ connector means: write the class, import it, add it here.
"""
from __future__ import annotations
from .base import BaseConnector
from .crowdstrike import CrowdStrikeConnector
from .mimecast import MimecastConnector
from .qualys import QualysConnector


def all_connectors() -> list[BaseConnector]:
    return [
        CrowdStrikeConnector(),
        MimecastConnector(),
        QualysConnector(),
        # Phase 2 cont'd: WizConnector(), VectraConnector(), SaltConnector(), ...
    ]


def configured_connectors() -> list[BaseConnector]:
    return [c for c in all_connectors() if c.is_configured()]
