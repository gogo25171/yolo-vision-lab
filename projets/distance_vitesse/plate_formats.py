"""Formats de plaques par pays : validation, correction OCR et mise en forme.

L'OCR (fast-plate-ocr, modèle « global ») lit les caractères et prédit le pays.
Cette couche, facultative, s'appuie sur la syntaxe officielle d'un pays pour :

- corriger les confusions classiques lettre/chiffre selon la position
  (``0``/``O``/``D``, ``8``/``B``, ``5``/``S``…) ;
- rejeter les lectures impossibles ;
- afficher la plaque au format local (``AB123CD`` -> ``AB-123-CD``).

Ajouter un pays = ajouter une entrée à ``FORMATS`` (voir docs/plaques.md).
Un « gabarit » décrit chaque position : ``L`` = lettre, ``D`` = chiffre,
``X`` = l'un ou l'autre ; ``display`` donne la mise en forme (``{0}`` = groupe 1…).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

TO_DIGIT = {"O": "0", "Q": "0", "D": "0", "U": "0", "I": "1", "L": "1", "T": "1", "Z": "2", "S": "5",
            "B": "8", "G": "6", "A": "4"}
TO_LETTER = {"0": "O", "1": "I", "2": "Z", "4": "A", "5": "S", "6": "G", "8": "B"}


@dataclass(frozen=True)
class PlateFormat:
    name: str
    template: str                 # ex. "LLDDDLL"
    pattern: str                  # regex de validation finale (sur le texte sans séparateurs)
    groups: tuple[int, ...]       # longueurs des groupes pour l'affichage
    separator: str = "-"
    letter_fix: dict | None = None  # corrections spécifiques (ex. lettres interdites)

    def fix(self, text: str) -> str | None:
        if len(text) != len(self.template):
            return None
        chars = []
        for char, slot in zip(text, self.template, strict=True):
            if slot == "D" and not char.isdigit():
                char = TO_DIGIT.get(char, char)
            elif slot == "L" and not char.isalpha():
                char = TO_LETTER.get(char, char)
            if slot == "L" and self.letter_fix:
                char = self.letter_fix.get(char, char)
            chars.append(char)
        candidate = "".join(chars)
        return candidate if re.fullmatch(self.pattern, candidate) else None

    def display(self, text: str) -> str:
        parts, index = [], 0
        for size in self.groups:
            parts.append(text[index:index + size])
            index += size
        return self.separator.join(parts)


# France — SIV (depuis 2009) : AA-123-AA. Les lettres I, O et U sont exclues ; SS et WW
# ne sont pas attribués en début de plaque (WW = immatriculation provisoire, on l'accepte).
_FR_LETTERS = "A-HJ-NP-TV-Z"
FR_SIV = PlateFormat(
    name="France (SIV)",
    template="LLDDDLL",
    pattern=rf"(?!SS)[{_FR_LETTERS}]{{2}}(?!000)\d{{3}}[{_FR_LETTERS}]{{2}}",
    groups=(2, 3, 2),
    letter_fix={"O": "D", "I": "T", "U": "V"},   # lettres interdites -> plus proche visuellement
)
# France — FNI (avant 2009, encore en circulation) : 1234 AB 75 / 123 ABC 2A.
FR_FNI_PATTERNS = [
    PlateFormat("France (FNI)", "DDDDLLDD", r"\d{4}[A-Z]{2}\d{2}", (4, 2, 2), " "),
    PlateFormat("France (FNI)", "DDDLLLDD", r"\d{3}[A-Z]{3}\d{2}", (3, 3, 2), " "),
    PlateFormat("France (FNI)", "DDDLLDD", r"\d{3}[A-Z]{2}\d{2}", (3, 2, 2), " "),
    PlateFormat("France (FNI)", "DDLLLDD", r"\d{2}[A-Z]{3}\d{2}", (2, 3, 2), " "),
]

# Clé = nom de région renvoyé par l'OCR (voir plate_regions dans la config du modèle).
FORMATS: dict[str, list[PlateFormat]] = {
    "France": [FR_SIV, *FR_FNI_PATTERNS],
    "Monaco": [PlateFormat("Monaco", "XXXX", r"[A-Z0-9]{4}", (4,), "")],
    "Belgium": [PlateFormat("Belgique", "DLLLDDD", r"\d[A-Z]{3}\d{3}", (1, 3, 3), "-")],
    "Spain": [PlateFormat("Espagne", "DDDDLLL", r"\d{4}[B-DF-HJ-NP-TV-Z]{3}", (4, 3), " ")],
    "Italy": [PlateFormat("Italie", "LLDDDLL", r"[A-HJ-NPR-TV-Z]{2}\d{3}[A-HJ-NPR-TV-Z]{2}", (2, 3, 2), " ")],
    "United Kingdom": [PlateFormat("Royaume-Uni", "LLDDLLL", r"[A-Z]{2}\d{2}[A-Z]{3}", (4, 3), " ")],
}

# Pays testés quand l'OCR n'a pas prédit de région.
DEFAULT_COUNTRIES = ["France"]


def normalize(text: str, region: str | None, fallback: list[str] | None = None) -> tuple[str, str | None]:
    """Renvoie (plaque mise en forme, pays). Si aucun format ne colle, le texte brut est conservé.

    Une région prédite mais sans format connu (ex. République tchèque) est conservée
    telle quelle : on ne force pas une plaque étrangère dans un format français.
    """
    if region:
        candidates = [region] if region in FORMATS else []
    else:
        candidates = list(fallback or DEFAULT_COUNTRIES)
    for country in candidates:
        for plate_format in FORMATS.get(country, []):
            fixed = plate_format.fix(text)
            if fixed:
                return plate_format.display(fixed), country
    return text, region
