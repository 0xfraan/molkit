# PyMOL — Mapa Funkcjonalności z Perspektywy Użytkownika

> 345 komend, 696 ustawień, 18 typów reprezentacji, 25+ wizardów.
> Poniżej wszystko pogrupowane wg tego CO CHCESZ ZROBIĆ, nie wg wewnętrznej organizacji kodu.

---

## 1. WCZYTAJ STRUKTURĘ

**Co to robi:** Ładujesz plik z białkiem/molekułą żeby ją zobaczyć w 3D.

| Akcja | Komenda | Uwagi |
|-------|---------|-------|
| Otwórz plik z dysku | `load plik.pdb` | PDB, CIF, SDF, MOL2, MAE, XYZ i ~15 innych formatów |
| Pobierz z internetu (RCSB) | `fetch 1ATP` | Podajesz 4-literowy kod PDB |
| Wczytaj trajektorię (symulacja MD) | `load_traj traj.dcd` | DCD, XTC, TRR, DTR |
| Wczytaj mapę gęstości elektronowej | `load mapa.ccp4` | CCP4, BRIX, DSN6, MRC, DX |
| Wczytaj dane krystalograficzne | `load_mtz plik.mtz` | Wymaga wyboru kolumn amplitud/faz |
| Wczytaj sesję PyMOL | `load sesja.pse` | Przywraca cały stan programu |
| Wczytaj wszystkie pliki z folderu | `loadall *.pdb` | Glob pattern |

**Wspierane formaty importu:** PDB, PDBx/mmCIF, bcif, SDF, MOL, MOL2, XYZ, MAE, MMOD, CC1, RST, CCP4, BRIX, DSN6, DX, MRC, Spider, MTZ, PSE, PML

---

## 2. POKAŻ / UKRYJ REPREZENTACJE

**Co to robi:** Zmienia JAK molekuła wygląda. To samo białko można pokazać jako wstążkę, kulki, patyczki itd.

### Dostępne reprezentacje (18 typów):

| Reprezentacja | Komenda | Kiedy używać |
|--------------|---------|--------------|
| **Cartoon** (wstążka) | `show cartoon` | Struktura drugorzędowa białek (helisy, arkusze β) |
| **Ribbon** (cienka wstążka) | `show ribbon` | Prostsza wersja cartoon |
| **Sticks** (patyczki) | `show sticks` | Wiązania chemiczne, ligandy |
| **Lines** (linie) | `show lines` | Szybki podgląd wiązań (lekkie) |
| **Spheres** (sfery) | `show spheres` | Model van der Waalsa, CPK |
| **Surface** (powierzchnia) | `show surface` | Powierzchnia molekularna (SAS/SES) |
| **Mesh** (siatka) | `show mesh` | Siatka powierzchni (przezroczysta) |
| **Dots** (kropki) | `show dots` | Kropkowa powierzchnia |
| **Ball-and-stick** | preset | Klasyczny model kulka-patyczek |
| **Nonbonded** | `show nonbonded` | Cząsteczki wody, jony |
| **Labels** | `show labels` | Nazwy atomów/reszt |
| **Ellipsoids** | `show ellipsoids` | Elipsoidy anizotropowe (B-factor) |

### Komendy sterujące:

| Akcja | Komenda | Przykład |
|-------|---------|---------|
| Pokaż reprezentację | `show typ, selekcja` | `show cartoon, chain A` |
| Ukryj reprezentację | `hide typ, selekcja` | `hide lines, all` |
| Pokaż TYLKO tę reprezentację | `as typ, selekcja` | `as sticks, resn LIG` |
| Przełącz widoczność | `toggle typ, selekcja` | `toggle surface` |
| Włącz/wyłącz cały obiekt | `enable/disable nazwa` | `disable solvent` |

---

## 3. KOLOROWANIE

**Co to robi:** Zmienia kolory atomów, wiązań, powierzchni.

### Kolorowanie wg właściwości:

| Schemat | Komenda | Co pokazuje |
|---------|---------|-------------|
| Wg elementu | `util.cbag selekcja` | C=zielony, N=niebieski, O=czerwony, S=żółty |
| Wg łańcucha | `util.cbc` | Każdy łańcuch inny kolor |
| Wg struktury 2° | `util.ss selekcja` | Helisy, arkusze, pętle |
| Tęcza (N→C) | `util.rainbow selekcja` | Gradient od N-końca do C-końca |
| Tęcza wg łańcucha | `util.chainbow` | Tęcza osobno w każdym łańcuchu |
| Wg B-factora | `spectrum b, selekcja` | Ruchliwość atomów (niebieski=sztywny, czerwony=ruchliwy) |
| Wg ładunku | `spectrum pc, selekcja` | Ładunek cząstkowy |
| Wg SASA | `spectrum area` | Dostępność rozpuszczalnika |
| Jeden kolor | `color red, selekcja` | 60+ named colors |
| Własny kolor RGB | `set_color mycolor, [R,G,B]` | Wartości 0.0-1.0 |

### Palety kolorów (38+):
`rainbow`, `rainbow_rev`, `rainbow2`, `blue_yellow`, `red_green`, `blue_white_red`, `green_white_magenta`, `cyan_white_yellow`, `gcbmry`, `yrmbcg` i wiele więcej.

---

## 4. SELEKCJE (WYBIERANIE ATOMÓW)

**Co to robi:** Wybierasz podzbiór atomów na których chcesz operować. To KLUCZOWY koncept — prawie każda komenda przyjmuje selekcję.

### Składnia selekcji:

| Selektor | Przykład | Co wybiera |
|----------|---------|------------|
| `all` | `all` | Wszystkie atomy |
| `resn` | `resn ALA` | Reszty o danej nazwie (alanina) |
| `resi` | `resi 42` | Reszta numer 42 |
| `chain` | `chain A` | Łańcuch A |
| `name` | `name CA` | Atomy o nazwie CA (Cα) |
| `elem` | `elem C` | Atomy węgla |
| `hetatm` | `hetatm` | Heteroatomy (ligandy, woda, jony) |
| `organic` | `organic` | Małe cząsteczki organiczne (ligandy) |
| `solvent` | `solvent` | Woda |
| `polymer` | `polymer` | Polimery (białka, DNA) |
| `polymer.protein` | `polymer.protein` | Tylko białka |
| `polymer.nucleic` | `polymer.nucleic` | Tylko kwasy nukleinowe |
| `ss h` | `ss h` | Helisy |
| `ss s` | `ss s` | Arkusze β |
| `br.` | `br. resi 42` | Cała reszta zawierająca atom |
| `byres` | `byres (...)` | Rozszerz do pełnych reszt |
| `around X` | `around 5` | Atomy w promieniu X Å |
| `within X of` | `within 4 of resn LIG` | W promieniu od selekcji |
| `beyond X of` | `beyond 10 of center` | Dalej niż X od selekcji |
| `and/or/not` | `chain A and resi 1-50` | Operatory logiczne |

### Komendy selekcji:

| Akcja | Komenda |
|-------|---------|
| Utwórz nazwaną selekcję | `select moja_sel, chain A and resi 1-50` |
| Wyczyść selekcję | `deselect` |
| Usuń pick-selection | `unpick` |

---

## 5. POMIARY I ANALIZA

**Co to robi:** Mierzysz odległości, kąty, analizujesz strukturę.

| Akcja | Komenda | Wynik |
|-------|---------|-------|
| Odległość między 2 atomami | `distance d1, /obj/A/42/CA, /obj/A/50/CA` | Linia z wartością w Å |
| Kąt między 3 atomami | `angle a1, atom1, atom2, atom3` | Kąt w stopniach |
| Kąt dihedralny (4 atomy) | `dihedral d1, a1, a2, a3, a4` | Kąt torsyjny |
| Policz atomy | `count_atoms selekcja` | Liczba atomów |
| Powierzchnia SASA | `get_area selekcja` | Å² |
| Kąty φ/ψ | `phi_psi selekcja` | Ramachandran |
| Interakcje π | `pi_interactions` | π-π i π-kation |
| Wiązania wodorowe | wizard distance → h-bonds | Automatyczne wykrycie |
| Kontakty polarne | wizard distance → polar contacts | Automatyczne wykrycie |

---

## 6. DOPASOWANIE STRUKTUR (ALIGNMENT)

**Co to robi:** Nakładasz dwie struktury na siebie żeby porównać.

| Metoda | Komenda | Jak działa |
|--------|---------|-----------|
| Align (sekwencja) | `align mobile, target` | Dopasowanie sekwencyjne + RMSD |
| Super (struktura) | `super mobile, target` | Superpozycja bez sekwencji |
| CEalign | `cealign target, mobile` | Combinatorial Extension |
| Fit (po atomach) | `fit mobile, target` | RMS minimalizacja |
| Pair fit | `pair_fit a1, b1, a2, b2...` | Dopasowanie par atomów |
| Morph | `morph obj, s1, s2` | Animacja przejścia między stanami |

**Metryki:** RMSD (Root Mean Square Deviation) — im mniejsza wartość, tym bardziej podobne struktury.

---

## 7. EDYCJA MOLEKUŁ

**Co to robi:** Modyfikujesz strukturę — dodajesz/usuwasz atomy, mutujesz reszty, budujesz od zera.

### Budowanie:

| Akcja | Komenda/Narzędzie |
|-------|-------------------|
| Zbuduj peptyd | `fab ACDEFG, mypeptide` (sekwencja 1-literowa) |
| Zbuduj kwas nukleinowy | `fnab ACGT, mydna` |
| Dodaj pseudoatom | `pseudoatom ps1, pos=[x,y,z]` |
| Dodaj fragment chemiczny | Builder panel → Fragments (acetylen, amid, cykliczne, halogeny) |
| Dodaj resztę aminokwasową | Builder panel → Residues (20 aminokwasów) |

### Modyfikacja:

| Akcja | Komenda |
|-------|---------|
| Dodaj wodory | `h_add selekcja` |
| Dodaj wodory polarne | `h_add selekcja` + `remove (elem H and not (neighbor (elem N+O)))` |
| Usuń wodory | `remove hydrogens` |
| Usuń atomy | `remove selekcja` |
| Utwórz wiązanie | `bond atom1, atom2` |
| Usuń wiązanie | `unbond atom1, atom2` |
| Zmień walencję | `cycle_valence` |
| Inwertuj stereo | `invert` |
| Mutacja (wizard) | `wizard mutagenesis` → wybierz resztę → wybierz rotamer |
| Selenomet → Met | `mse2met` |
| Zmień właściwość atomu | `alter selekcja, "wyrażenie"` np. `alter all, b=20` |

### Ochrona:

| Akcja | Komenda |
|-------|---------|
| Zablokuj atomy przed edycją | `protect selekcja` |
| Odblokuj | `deprotect selekcja` |

---

## 8. KAMERA I WIDOK

**Co to robi:** Obracasz, przybliżasz, ustawiasz kamerę.

| Akcja | Komenda | Alternatywa (mysz) |
|-------|---------|-------------------|
| Przybliż do selekcji | `zoom selekcja` | Scroll |
| Wycentruj na selekcji | `center selekcja` | Middle-click na atom |
| Optymalne ustawienie | `orient selekcja` | — |
| Reset widoku | `reset` | — |
| Obrót kamery | `turn x, 90` | Left-drag |
| Przesunięcie kamery | `move x, 5` | Middle-drag |
| Clipping (przekrój) | `clip near, -5` | Scroll + Shift |
| Widok ortograficzny | `set orthoscopic, 1` | — |
| Głębia ostrości | `set depth_cue, 1` | — |
| Kolor tła | `bg_color white` | — |
| Stereo | `stereo crosseye` | 11 trybów stereo |
| Zapisz widok | `get_view` → `set_view [...]` | — |
| Patrz na cel | `look_at selekcja` | — |

### Sceny (zapisane widoki):

| Akcja | Komenda |
|-------|---------|
| Zapisz scenę | `scene nowa, store` |
| Przywróć scenę | `scene nowa, recall` |
| Lista scen | klawisz F1-F12 |

---

## 9. RENDEROWANIE I EKSPORT

**Co to robi:** Generujesz obrazki/filmy publikacyjnej jakości.

### Obrazy:

| Akcja | Komenda | Uwagi |
|-------|---------|-------|
| Screenshot (OpenGL) | `draw width, height` → `png plik.png` | Szybki |
| Ray-tracing | `ray width, height` → `png plik.png` | Wolny, piękny |
| Bezpośredni PNG | `png plik.png, width, height, ray=1` | Jedno polecenie |

### Ustawienia jakości ray-tracingu:

| Ustawienie | Komenda |
|------------|---------|
| Antyaliasing | `set antialias, 2` (0-4x) |
| Cienie | `set ray_shadows, 1` |
| Ambient occlusion | `set ambient_occlusion_mode, 1` |
| Przezroczystość | `set ray_trace_mode, 1` (0-3) |
| Fog | `set ray_trace_fog, 1` |

### Eksport 3D:

| Format | Komenda | Zastosowanie |
|--------|---------|-------------|
| VRML 2 | `save plik.wrl` | 3D printing |
| COLLADA | `save plik.dae` | 3D modeling |
| GLTF | `save plik.gltf` | Web 3D |
| STL | `save plik.stl` | 3D printing |
| POV-Ray | `save plik.pov` | Zaawansowane renderowanie |

### Film/Animacja:

| Akcja | Komenda |
|-------|---------|
| Definiuj klatki | `mset 1 x60` (60 klatek) |
| Komenda na klatce | `mdo 1, turn y, 6` |
| Nagraj film | `mpng frame` → zewnętrzny encoder |
| Obrót 360° | `movie.roll` |
| Kołysanie | `movie.rock` |
| Nutacja | `movie.nutate` |

---

## 10. SESJA I SKRYPTY

**Co to robi:** Zapisujesz/wczytujesz stan pracy, automatyzujesz zadania.

| Akcja | Komenda |
|-------|---------|
| Zapisz sesję | `save sesja.pse` |
| Wczytaj sesję | `load sesja.pse` |
| Uruchom skrypt PyMOL | `run skrypt.pml` |
| Uruchom skrypt Python | `run skrypt.py` |
| Loguj komendy | `log_open log.pml` |
| Zakończ logowanie | `log_close` |
| Zdefiniuj alias | `alias mojcmd, zoom; orient` |
| Rozszerz język | `extend mojakmd, funkcja_python` |
| Undo/Redo | `undo` / `redo` |
| Reinicjalizuj | `reinitialize` |

---

## 11. MAPY I OBJĘTOŚCI (KRYSTALOGRAFIA / CRYO-EM)

**Co to robi:** Wizualizacja danych gęstości elektronowej z eksperymentów.

| Akcja | Komenda |
|-------|---------|
| Wczytaj mapę | `load mapa.ccp4` |
| Utwórz izopowierzchnię | `isosurface surf1, mapa, level` |
| Utwórz siatkę | `isomesh mesh1, mapa, level` |
| Utwórz kropki | `isodot dot1, mapa, level` |
| Utwórz objętość | `volume vol1, mapa` |
| Zmień level konturu | `isolevel mesh1, 1.5` |
| Nowa mapa z danych | `map_new mapname, type, grid, selection` |
| Operacje na mapach | `map_set` (mnożenie, dodawanie, itp.) |
| Gradient mapy | `gradient grad1, mapa` |
| Rampa kolorów | `ramp_new ramp1, mapa, range, colors` |

---

## 12. SYMETRIA I KOMÓRKA ELEMENTARNA

**Co to robi:** Krystalografia — generujesz symetryczne kopie, pokazujesz komórkę.

| Akcja | Komenda |
|-------|---------|
| Generuj kopie symetryczne | `symexp prefix, object, selection, cutoff` |
| Ustaw symetrię | `set_symmetry obj, a, b, c, α, β, γ, spacegroup` |
| Kopiuj symetrię | `symmetry_copy source, target` |
| Zawijanie PBC | `pbc_wrap` |
| Rozwijanie PBC | `pbc_unwrap` |
| Pokaż komórkę elementarną | `show cell` |

---

## 13. ELEKTROSTATYKA

**Co to robi:** Wizualizacja potencjału elektrostatycznego na powierzchni białka.

| Akcja | Komenda |
|-------|---------|
| Potencjał kontaktowy białka | Menu: Action → Vacuum electrostatics |
| Pokaż na powierzchni | `ramp_new` + `set surface_color` |

---

## 14. PRESETY WIZUALIZACJI

**Co to robi:** Jednym kliknięciem ustawiasz popularną kombinację reprezentacji i kolorów.

| Preset | Co robi |
|--------|---------|
| **Simple** | Wstążka + patyczki dla ligandów |
| **Simple (no solvent)** | j.w. bez wody i jonów |
| **Ball and stick** | Kulki + patyczki |
| **B-factor putty** | Cartoon z grubością wg B-factora |
| **Technical** | Pełen detal atomowy |
| **Ligands** | Fokus na ligandzie z kontaktami |
| **Ligand sites** | Powierzchnia wokół liganda |
| **Ligand sites (transparent)** | Przezroczysta powierzchnia |
| **Pretty** | Ładna wizualizacja |
| **Publication** | Jakość do publikacji |
| **Interface** | Interfejs białko-białko |
| **Default** | Domyślna reprezentacja |

---

## 15. MYSZ I INTERAKCJA

**Co to robi:** Co robią przyciski myszy i klawiatura.

### Domyślny tryb myszy (3-button viewing):

| Akcja | Sterowanie |
|-------|-----------|
| Obrót | Lewy przycisk + przeciągnij |
| Translacja | Środkowy przycisk + przeciągnij |
| Zoom | Prawy przycisk + przeciągnij / Scroll |
| Clipping (przekrój) | Scroll + Shift |
| Picking (wybór atomu) | Lewy klik na atom |
| Menu kontekstowe | Prawy klik na atom/obiekt |
| Centering | Środkowy klik na atom |
| Slab (grubość przekroju) | Scroll + Ctrl |

### Tryby myszy:

| Tryb | Do czego |
|------|---------|
| 3-Button Viewing | Domyślny — obracanie/zoom |
| 3-Button Editing | Edycja atomów — przeciąganie, obracanie fragmentów |
| 2-Button Viewing | Dla myszy bez środkowego przycisku |
| 1-Button Viewing | Laptop/touchpad |

---

## 16. WIZARDY (INTERAKTYWNE NARZĘDZIA)

**Co to robi:** Krokowe, interaktywne narzędzia do złożonych zadań.

| Wizard | Co robi |
|--------|---------|
| **Measurement** | Pomiary: odległości, kąty, dihedral, kontakty polarne, H-bondy |
| **Mutagenesis** | Mutacja reszt aminokwasowych z wyborem rotameru |
| **Sculpting** | Interaktywna optymalizacja geometrii z polem siłowym |
| **Density** | Eksploracja map gęstości elektronowej |
| **Annotation** | Dodawanie adnotacji tekstowych |
| **Label** | Interaktywne etykietowanie |
| **Pair fit** | Dopasowanie struktur przez wybór par atomów |
| **Filter** | Filtrowanie selekcji |
| **Box** | Definiowanie regionów przestrzennych |
| **Charge** | Wizualizacja ładunków |
| **Demo** | Pokazy demonstracyjne |

---

## PODSUMOWANIE — GŁÓWNE WORKFLOW UŻYTKOWNIKA

```
┌─────────────────────────────────────────────────────────┐
│                    TYPOWY WORKFLOW                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. WCZYTAJ        fetch 1ATP / load plik.pdb           │
│       ↓                                                 │
│  2. POKAŻ          as cartoon / show sticks, organic    │
│       ↓                                                 │
│  3. POKOLORUJ      util.cbc / spectrum b                │
│       ↓                                                 │
│  4. WYSELEKCJONUJ  select site, byres(organic around 5) │
│       ↓                                                 │
│  5. ANALIZUJ       distance / align / get_area          │
│       ↓                                                 │
│  6. EKSPORTUJ      ray 2400, 1800 / png obraz.png       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Poziomy złożoności użytkownika:

```
NOOB          → Load, Show/Hide, Color, Zoom, Screenshot
                (10 komend wystarczy)

INTERMEDIATE  → + Selekcje, Pomiary, Presety, Align, Sesje
                (30 komend)

ADVANCED      → + Edycja, Mapy, Scripting, Ray-tracing,Movie
                (100+ komend)

EXPERT        → + Elektrostatyka, Symetria, Plugin API, Custom shaders
                (345 komend, 696 ustawień)
```

---

## CO JEST TRUDNE W OBECNYM UI

1. **Selekcje** — składnia jest potężna ale trzeba ją ZNAĆ. Brak wizualnego buildera selekcji.
2. **Odkrywalność** — 345 komend ukrytych za CLI. Menu kontekstowe są zagnieżdżone 4-5 poziomów.
3. **Presety** — jest ich mało (16). Brak prostego "chcę zobaczyć binding site".
4. **Kolorowanie** — wymaga znajomości nazw schematów i komend `spectrum`/`util.*`.
5. **Renderowanie** — ray-tracing wymaga ustawienia ~10 parametrów dla dobrego wyniku.
6. **Porównanie struktur** — align/super/cealign — który wybrać? Brak guidance.
7. **Pomiary** — trzeba ręcznie pickować atomy jeden po drugim.
8. **Mapy gęstości** — skomplikowany workflow load → isomesh → isolevel.
9. **Brak undo** — większość operacji jest nieodwracalna (poza konformacyjnymi).
10. **Eksport** — brak jednego "Export for publication" buttona.
