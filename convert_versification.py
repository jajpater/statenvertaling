#!/usr/bin/env python3
"""
Script om de OSIS versificatie te corrigeren van NRSVA naar DutSVV.

Het probleem: Verzen hebben een osisID zoals "Exod.6.1" maar aan het begin van
de verstekst staat de werkelijke versnummering tussen vierkante haken "[05:24]".

Dit script:
1. Vindt alle verse tags met een [HH:VV] patroon aan het begin
2. Vervangt de osisID met de juiste nummering uit de vierkante haken
3. Verwijdert de [HH:VV] notatie uit de tekst
"""

import re
import sys


def convert_versification(input_file: str, output_file: str) -> None:
    """Converteer de versificatie van NRSVA naar DutSVV."""

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Patroon om verse tags te vinden met [HH:VV] aan het begin
    # Voorbeeld: <verse osisID="Exod.6.1">[05:24] Toen ...
    # Moet worden: <verse osisID="Exod.5.24">Toen ...
    pattern = r'<verse osisID="([A-Za-z0-9]+)\.(\d+)\.(\d+)">\[(\d+):(\d+)\]\s*'

    def replace_verse(match):
        book = match.group(1)           # bijv. "Exod"
        old_chapter = match.group(2)    # bijv. "6" (niet gebruikt, alleen voor debug)
        old_verse = match.group(3)      # bijv. "1" (niet gebruikt, alleen voor debug)
        new_chapter = int(match.group(4))  # bijv. 5 (uit [05:24])
        new_verse = int(match.group(5))    # bijv. 24 (uit [05:24])

        return f'<verse osisID="{book}.{new_chapter}.{new_verse}">'

    # Tel het aantal wijzigingen
    num_matches = len(re.findall(pattern, content))

    # Voer de vervanging uit
    new_content = re.sub(pattern, replace_verse, content)

    # Schrijf naar het nieuwe bestand
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"Conversie voltooid: {num_matches} verzen aangepast")
    print(f"Output geschreven naar: {output_file}")


def main():
    input_file = "STV.xml"
    output_file = "STV-DutSVV.osis.xml"

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    print(f"Input: {input_file}")
    print(f"Output: {output_file}")

    convert_versification(input_file, output_file)


if __name__ == "__main__":
    main()
