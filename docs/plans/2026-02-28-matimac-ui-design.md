# MolKit UI Design — PyMOL Friendly Interface

## Cel
Plugin PySide6/Qt do PyMOL open-source, ktory zamienia PyMOL w przyjazne narzedzie dla poczatkujacych. Zero CLI na widoku — wszystko przez graficzny interfejs.

## Architektura
- **Plugin Qt** do istniejacego PyMOL — dockable sidebar panel
- **PySide6 natywnie** — ten sam framework co PyMOL, zero dodatkowych zaleznosci
- Pod spodem wywoluje `pymol.cmd.*` API
- CLI schowane, dostepne przez toggle dla power userow

## Layout
```
┌─────────────────────┬──────────────────────────────────┐
│   Sidebar (Left)    │        3D Viewport (PyMOL)       │
│   Accordion panels  │                                  │
└─────────────────────┴──────────────────────────────────┘
```

Welcome screen zamiast pustego viewportu — PDB search, file open, przykladowe struktury.

## Sidebar Sekcje

### 1. Struktura (obiekt manager)
- Lista zaladowanych obiektow z toggle widocznosci
- Info: lancuchy, liczba reszt, ligandy, woda
- [+ Dodaj kolejna] → loader (PDB kod / plik / drag & drop)
- Prawy klik: rename, delete, duplicate, split chains

### 2. Widok (reprezentacje)
- Dropdown: Cartoon / Sticks / Spheres / Surface / Ball-and-stick / Lines
- Osobno dla: bialko, ligandy, woda/jony
- Presety: Publication, Binding site, B-factor, itp.
- Toggle: wodory, woda, heteroatomy
- Tlo: color picker

### 3. Kolory
- Dropdown: Wg elementu / lancucha / struktury 2° / B-factor / tecza / jeden kolor
- Color picker dla custom kolorow
- Osobno dla: bialko, ligandy, selekcja

### 4. Selekcje (wizualny builder)
- Dropdown "Co wybrac": lancuch / reszty / atomy / ligandy / woda
- Dropdown "Ktory": A / B / C... albo zakres reszt
- Slider "W promieniu" od czegos
- Podglad: "Zaznaczono 142 atomy"
- Lista zapisanych selekcji

### 5. Pomiary
- Buttony: Odleglosc / Kat / Kat dihedralny
- Tryb: "Kliknij na 2/3/4 atomy"
- Przycisk: "Pokaz H-bondy" / "Pokaz kontakty polarne"
- Lista pomiarow z wartosciami

### 6. Edycja
- Mutacja reszty
- Dodaj/usun wodory
- Dopasowanie struktur (align)

### 7. Eksport
- Screenshot + ray-trace z quality slider
- Zapisz sesje
- Eksport pliku (PDB/CIF/MOL2)

### 8. Zaawansowane (domyslnie zwiniete)
### 9. Konsola (domyslnie zwinieta) — surowy CLI

## Fazy
1. **MVP (teraz)**: Welcome/Loader + Sidebar z Widok/Kolory/podstawowe Selekcje + Eksport
2. **V2**: Pomiary, Edycja, Smart Presets, Selekcje zaawansowane
3. **V3**: MCP Server + Chat panel z AI

## Stack
- PySide6 (natywny Qt, to samo co PyMOL)
- Python 3.9+
- pymol.cmd API pod spodem
