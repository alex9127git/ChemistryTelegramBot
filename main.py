import sys
from atoms import *
from substance import *
from database_searcher import *


history_path = "query_history.txt"
bg_path = os.path.join(BASE_DIR, "bg.png")


class CoefficientCalculationError(Exception):
    pass


def initialize():
    """Инициализация окна программы."""
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    elements = cur.execute(
        """select symbol, name, element_types.type, mass from elements 
        left join element_types on element_types.id = elements.type"""
    ).fetchall()
    solubility_data = cur.execute(
        """select anions.formula, anions.charge, "H+1", "Li+1", "K+1", "Na+1", "NH4+1", "Ba+2", 
        "Ca+2", "Mg+2", "Sr+2", "Al+3", "Cr+3", "Fe+2", "Fe+3", "Ni+2", "Co+2", "Mn+2", "Zn+2", 
        "Ag+1", "Hg+2", "Pb+2", "Sn+2", "Cu+2" 
        from solubility left join anions on solubility.anion_id = anions.id"""
    ).fetchall()
    solubility = []
    cations = ("H+1", "Li+1", "K+1", "Na+1", "NH4+1", "Ba+2", "Ca+2", "Mg+2", "Sr+2", "Al+3",
               "Cr+3", "Fe+2", "Fe+3", "Ni+2", "Co+2", "Mn+2", "Zn+2", "Ag+1", "Hg+2", "Pb+2",
               "Sn+2", "Cu+2")
    for anion in solubility_data:
        solubility.append(
            (anion[0], anion[1], {cations[x]: anion[2 + x] for x in range(len(anion[2:]))})
        )
    print(elements)
    print(solubility)
    return elements, solubility


def fill_reaction(reagent1, reagent2):
    try:
        substance1 = get_substance(reagent1)
        substance2 = get_substance(reagent2)
    except IndexError:
        print("Не получилось расшифровать формулу вещества")
        return
    if substance1.__class__ == Oxide:
        if substance1.oxide_type() == "кислотный":
            if reagent2 == "H2O":
                try:
                    acid = get_acid_from_oxide(reagent1)
                    print(f"{reagent1} + {reagent2} -> {acid}")
                except QueryNotFoundError:
                    print("Не получилось автозаполнить реакцию")
            elif substance2.__class__ == Base:
                try:
                    acid = get_substance(get_acid_from_oxide(reagent1))
                    salt = Salt(substance2.cation, substance2.cation_charge,
                                acid.anion)
                    print(f"{reagent1} + {reagent2} -> {salt} + H2O")
                except QueryNotFoundError:
                    print("Не получилось автозаполнить реакцию")
            elif substance2.__class__ == Oxide and substance2.oxide_type() == "основный":
                try:
                    acid = get_substance(get_acid_from_oxide(reagent1))
                    salt = Salt(substance2.cation, substance2.cation_charge,
                                acid.anion)
                    print(f"{reagent1} + {reagent2} -> {salt}")
                except QueryNotFoundError:
                    print("Не получилось автозаполнить реакцию")
        elif substance1.oxide_type() == "основный":
            if reagent2 == "H2O" and get_element_type(substance1.cation) in (
                    "щелочный металл", "щелочно-земельный металл"):
                base = Base(substance1.cation, substance1.cation_charge)
                print(f"{reagent1} + {reagent2} -> {base}")
            elif substance2.__class__ == Oxide and substance2.oxide_type() == "кислотный":
                try:
                    acid = get_substance(get_acid_from_oxide(reagent2))
                    salt = Salt(substance1.cation, substance1.cation_charge,
                                acid.anion)
                    print(f"{reagent1} + {reagent2} -> {salt}")
                except QueryNotFoundError:
                    print("Не получилось автозаполнить реакцию")
            elif substance2.__class__ == Acid:
                salt = Salt(substance1.cation, substance1.cation_charge, substance2.anion)
                print(f"{reagent1} + {reagent2} -> {salt} + H2O")
    elif substance1.__class__ == Acid:
        if substance2.__class__ == str:
            if compare_reactivity(substance2, substance1.cation) > 0:
                salt = Salt(substance2, get_cation_charge(substance2), substance1.anion)
                print(f"{reagent1} + {reagent2} -> {salt} + H2")
            else:
                print("Металл не может вытеснить водород из кислоты")
        elif (substance2.__class__ == Oxide and substance2.oxide_type() == "основный") or \
                (substance2.__class__ == Base):
            salt = Salt(substance2.cation, substance2.cation_charge, substance1.anion)
            print(f"{reagent1} + {reagent2} -> {salt} + H2O")
        elif substance2.__class__ == Salt:
            acid = Acid(substance2.anion)
            salt = Salt(substance2.cation, substance2.cation_charge, substance1.anion)
            if str(acid) not in ("H2CO3", "H2SO3"):
                try:
                    if get_solubility(salt) == "Р" and get_solubility(acid) == "Р":
                        print("Один из продуктов реакции должен быть нерастворим")
                        return
                except QueryNotFoundError:
                    print("Не получилось автозаполнить реакцию")
            print(f"{reagent1} + {reagent2} -> {acid} + {salt}")
    elif substance1.__class__ == Base:
        if substance2.__class__ == Oxide and substance2.oxide_type() == "кислотный":
            try:
                acid = get_substance(get_acid_from_oxide(reagent1))
                salt = Salt(substance2.cation, substance2.cation_charge,
                            acid.anion)
                print(f"{reagent1} + {reagent2} -> {salt} + H2O")
            except QueryNotFoundError:
                print("Не получилось автозаполнить реакцию")
        elif substance2.__class__ == Acid:
            salt = Salt(substance1.cation, substance1.cation_charge, substance2.anion)
            print(f"{reagent1} + {reagent2} -> {salt} + H2O")
        elif substance2.__class__ == Salt:
            try:
                if get_solubility(substance1) == "Р" and get_solubility(substance2) == "Р":
                    salt = Salt(substance1.cation, substance1.cation_charge, substance2.anion)
                    base = Base(substance2.cation, substance2.cation_charge)
                    if get_solubility(salt) == "Р" and get_solubility(base) == "Р":
                        print("Один из продуктов реакции должен быть нерастворим")
                        return
                    print(f"{reagent1} + {reagent2} -> {base} + {salt}")
            except QueryNotFoundError:
                print("Не получилось автозаполнить реакцию")
        elif substance2 == "":
            try:
                if get_solubility(substance1) == "Р":
                    print("Основание должно быть нерастворимо")
                    return
                oxide = Oxide(substance1.cation, substance1.cation_charge)
                print(f"{reagent1} + {reagent2} -> {oxide} + H2O")
            except QueryNotFoundError:
                print("Не получилось автозаполнить реакцию")
    elif substance1.__class__ == Salt:
        if substance2.__class__ == Acid:
            acid = Acid(substance1.anion)
            salt = Salt(substance1.cation, substance1.cation_charge, substance2.anion)
            if str(acid) not in ("H2CO3", "H2SO3"):
                try:
                    if get_solubility(salt) == "Р" and get_solubility(acid) == "Р":
                        print("Один из продуктов реакции должен быть нерастворим")
                        return
                except QueryNotFoundError:
                    print("Не получилось автозаполнить реакцию")
            print(f"{reagent1} + {reagent2} -> {acid} + {salt}")
        elif substance2.__class__ == Base:
            try:
                if get_solubility(substance2) == "Р" and get_solubility(substance1) == "Р":
                    salt = Salt(substance2.cation, substance2.cation_charge, substance1.anion)
                    base = Base(substance1.cation, substance1.cation_charge)
                    if get_solubility(salt) == "Р" and get_solubility(base) == "Р":
                        print(
                            "Один из продуктов реакции должен быть нерастворим")
                        return
                    print(f"{reagent1} + {reagent2} -> {base} + {salt}")
            except QueryNotFoundError:
                print("Не получилось автозаполнить реакцию")
        elif substance2.__class__ == Salt:
            try:
                if get_solubility(substance2) == "Р" and get_solubility(substance1) == "Р":
                    result_salt1 = Salt(
                        substance2.cation, substance2.cation_charge, substance1.anion)
                    result_salt2 = Salt(
                        substance1.cation, substance1.cation_charge, substance2.anion)
                    if get_solubility(result_salt1) == "Р" and get_solubility(
                            result_salt2) == "Р":
                        print(
                            "Один из продуктов реакции должен быть нерастворим")
                        return
                    print(f"{reagent1} + {reagent2} -> {result_salt1} + {result_salt2}")
            except QueryNotFoundError:
                print("Не получилось автозаполнить реакцию")
        elif substance2.__class__ == str:
            if compare_reactivity(substance2, substance1.cation) > 0:
                salt = Salt(substance2, get_cation_charge(substance2), substance1.anion)
                print(f"{reagent1} + {reagent2} -> {salt} + {substance1.cation}")
            else:
                print("Металл недостаточно активен, чтобы вытеснить металл из соли")


def fill_coefficients(reagent1, reagent2, reagent3, reagent4):
    """Заполняет коэффициенты реакции."""
    try:
        substance1 = get_substance(reagent1)
        substance2 = get_substance(reagent2)
    except IndexError:
        print("Не получилось расшифровать формулу вещества")
    else:
        if substance1.__class__ == Acid:
            if substance2.__class__ == str:
                if compare_reactivity(substance2, substance1.cation) <= 0:
                    print("Металл не может вытеснить водород из кислоты")
                    return
            elif substance2.__class__ == Salt:
                acid = Acid(substance2.anion)
                salt = Salt(substance2.cation, substance2.cation_charge, substance1.anion)
                if str(acid) not in ("H2CO3", "H2SO3"):
                    try:
                        if get_solubility(salt) == "Р" and get_solubility(acid) == "Р":
                            print("Один из продуктов реакции должен быть нерастворим")
                            return
                    except QueryNotFoundError:
                        pass
        elif substance1.__class__ == Base:
            if substance2.__class__ == Salt:
                try:
                    if get_solubility(substance1) == "Р" and get_solubility(substance2) == "Р":
                        salt = Salt(substance1.cation, substance1.cation_charge, substance2.anion)
                        base = Base(substance2.cation, substance2.cation_charge)
                        if get_solubility(salt) == "Р" and get_solubility(base) == "Р":
                            print("Один из продуктов реакции должен быть нерастворим")
                            return
                except QueryNotFoundError:
                    pass
            elif substance2 == "":
                try:
                    if get_solubility(substance1) == "Р":
                        print("Основание должно быть нерастворимо")
                        return
                except QueryNotFoundError:
                    print("Не получилось автозаполнить реакцию")
        elif substance1.__class__ == Salt:
            if substance2.__class__ == Acid:
                acid = Acid(substance1.anion)
                salt = Salt(substance1.cation, substance1.cation_charge, substance2.anion)
                if str(acid) not in ("H2CO3", "H2SO3"):
                    try:
                        if get_solubility(salt) == "Р" and get_solubility(acid) == "Р":
                            print("Один из продуктов реакции должен быть нерастворим")
                            return
                    except QueryNotFoundError:
                        pass
            elif substance2.__class__ == Base:
                try:
                    if get_solubility(substance2) == "Р" and get_solubility(substance1) == "Р":
                        salt = Salt(substance2.cation, substance2.cation_charge, substance1.anion)
                        base = Base(substance1.cation, substance1.cation_charge)
                        if get_solubility(salt) == "Р" and get_solubility(base) == "Р":
                            print("Один из продуктов реакции должен быть нерастворим")
                            return
                except QueryNotFoundError:
                    pass
            elif substance2.__class__ == Salt:
                try:
                    if get_solubility(substance2) == "Р" and get_solubility(substance1) == "Р":
                        result_salt1 = Salt(
                            substance2.cation, substance2.cation_charge, substance1.anion)
                        result_salt2 = Salt(
                            substance1.cation, substance1.cation_charge, substance2.anion)
                        if get_solubility(result_salt1) == "Р" and get_solubility(result_salt2) == "Р":
                            print("Один из продуктов реакции должен быть нерастворим")
                            return
                except QueryNotFoundError:
                    pass
            elif substance2.__class__ == str:
                if compare_reactivity(substance2, substance1.cation) <= 0:
                    print("Металл недостаточно активен, чтобы вытеснить металл из соли")
                    return
    print("")
    try:
        coeffs = self.calculate_coefficients(reagent1, reagent2, reagent3, reagent4)
    except CoefficientCalculationError:
        print("Не получилось расставить коэффициенты")
    else:
        coeff1, coeff2, coeff3, coeff4 = coeffs
        str1 = f"{coeff1} {reagent1}" if reagent1 else ""
        str2 = f"{coeff2} {reagent2}" if reagent2 else ""
        if reagent3 == "H2CO3":
            str3 = f"{coeff3} H2O + {coeff3} CO2"
        elif reagent3 == "H2SO3":
            str3 = f"{coeff3} H2O + {coeff3} SO2"
        else:
            str3 = f"{coeff3} {reagent3}" if reagent3 else ""
        if reagent4 == "H2CO3":
            str4 = f"{coeff4} H2O + {coeff4} CO2"
        elif reagent4 == "H2SO3":
            str4 = f"{coeff4} H2O + {coeff4} SO2"
        else:
            str4 = f"{coeff4} {reagent4}" if reagent4 else ""
        part1 = " + ".join(filter(lambda x: x, (str1, str2)))
        part2 = " + ".join(filter(lambda x: x, (str3, str4)))
        print(f"{part1} -> {part2}")


def calculate_mass(substance, element):
    """Рассчитывает массовую долю выбранного элемента в выбранном веществе."""
    try:
        get_element_type(element)
    except QueryNotFoundError:
        print("Не получилось найти элемент")
        return
    substance_atoms = Atoms(substance)
    substance_mass, expression = substance_atoms.calculate_molecular_mass()
    element_mass = get_element_mass(element) * substance_atoms.atoms.get(element, 0)
    self.substance_mass_edit.setText(expression)
    self.element_mass_edit.setText(f"{element_mass}")
    mass_fraction = element_mass / substance_mass
    self.mass_calculation_lbl.setText(
        f"{element_mass} / {substance_mass} = {mass_fraction}"
    )
    print(f"Массовая доля {element} в {substance} составляет {mass_fraction * 100:.3f}%")


def calculate_formula(self):
    """Рассчитывает формулу вещества по массовым долям его элементов."""
    edits = (self.element1_edit, self.element2_edit, self.element3_edit, self.element4_edit)
    spin_boxes = (self.element1_spinbox, self.element2_spinbox, self.element3_spinbox,
                  self.element4_spinbox)
    self.formula_error_lbl.setText("")
    try:
        element1 = self.element1_edit.text()
        if element1:
            get_element_type(element1)
        element2 = self.element2_edit.text()
        if element2:
            get_element_type(element2)
        element3 = self.element3_edit.text()
        if element3:
            get_element_type(element3)
        element4 = self.element4_edit.text()
        if element4:
            get_element_type(element4)
    except QueryNotFoundError:
        self.formula_error_lbl.setText("Не получилось найти один из элементов")
        return
    if len(list(filter(lambda x: x == "", (element1, element2, element3, element4)))) > 2:
        self.formula_error_lbl.setText("Нужно определить как минимум два элемента")
        return
    for i in range(4):
        if edits[i].text() == "":
            spin_boxes[i].setValue(0)
    elements = list(filter(lambda x: x != "", map(lambda x: x.text(), edits)))
    percentages = list(filter(lambda x: x > 0, map(lambda x: x.value(), spin_boxes)))
    if sum(percentages) != 100:
        self.formula_error_lbl.setText("Процентные соотношения в сумме должны давать 100%")
        return
    masses = list(map(lambda x: round(get_element_mass(x)), elements))
    quantity = len(elements)
    coeffs = [1] * quantity
    percent = list(map(lambda x: masses[x] * coeffs[x] / percentages[x], range(quantity)))
    while len(set(percent)) > 1:
        index = percent.index(min(percent))
        coeffs[index] += 1
        percent = list(map(lambda x: masses[x] * coeffs[x] / percentages[x], range(quantity)))
    self.output_formula_lbl.setText(f"{' : '.join(elements)} = {' : '.join(map(str, coeffs))}")
    with open("query_history.txt", "a", encoding="utf-8") as history:
        history.write(
            "Расчет формулы: " +
            '; '.join(map(
                lambda x: f'{elements[x]} = {percentages[x]}', range(len(elements)))
            ) + "\n"
        )
    self.update_history()


def calculate_coefficients(reagent1, reagent2, reagent3, reagent4):
    atoms1 = Atoms(reagent1)
    atoms2 = Atoms(reagent2)
    atoms3 = Atoms(reagent3)
    atoms4 = Atoms(reagent4)
    coeff1 = coeff2 = coeff3 = coeff4 = 1
    if (atoms1 + atoms2).disparity(atoms3 + atoms4) == "too different":
        raise CoefficientCalculationError("Не получилось расставить коэффициенты")
    else:
        while atoms1 * coeff1 + atoms2 * coeff2 != atoms3 * coeff3 + atoms4 * coeff4:
            element = (atoms1 * coeff1 + atoms2 * coeff2).disparity(
                atoms3 * coeff3 + atoms4 * coeff4)
            count1 = (atoms1 * coeff1 + atoms2 * coeff2).atoms[element]
            count2 = (atoms3 * coeff3 + atoms4 * coeff4).atoms[element]
            lcc = lcm(count1, count2)
            c1 = lcc // count1
            c2 = lcc // count2
            if element in atoms1:
                coeff1 *= c1
            if element in atoms2:
                coeff2 *= c1
            if element in atoms3:
                coeff3 *= c2
            if element in atoms4:
                coeff4 *= c2
    return [coeff1, coeff2, coeff3, coeff4]


def calculate_equation(self):
    self.equation_error_lbl.setText("")
    reagent1 = self.eq_primary_input_edit.text()
    reagent2 = self.eq_secondary_input_edit.text()
    reagent3 = self.eq_primary_output_edit.text()
    reagent4 = self.eq_secondary_output_edit.text()
    reagents = [reagent1, reagent2, reagent3, reagent4]
    known_reagent = self.eq_substance1_edit.text()
    found_reagent = self.eq_substance2_edit.text()
    if known_reagent not in reagents or found_reagent not in reagents or known_reagent == "" \
            or found_reagent == "":
        self.equation_error_lbl.setText(
            "Известное или искомое вещество не находится в уравнении")
        return
    try:
        mass = float(self.eq_mass_edit.text().replace(",", "."))
    except ValueError:
        self.equation_error_lbl.setText("Не получилось прочитать массу")
        return
    try:
        coeffs = self.calculate_coefficients(*reagents)
    except CoefficientCalculationError:
        self.equation_error_lbl.setText("Не получилось расставить коэффициенты")
        return
    coeff1, coeff2, coeff3, coeff4 = coeffs
    str1 = f"{coeff1} {reagent1}" if reagent1 else ""
    str2 = f"{coeff2} {reagent2}" if reagent2 else ""
    str3 = f"{coeff3} {reagent3}" if reagent3 else ""
    str4 = f"{coeff4} {reagent4}" if reagent4 else ""
    part1 = " + ".join(filter(lambda x: x, (str1, str2)))
    part2 = " + ".join(filter(lambda x: x, (str3, str4)))
    self.equation_lbl.setText(
        f"Уравнение с коэффициентами: {part1} -> {part2}"
    )
    k_atoms = Atoms(known_reagent)
    r_atoms = Atoms(found_reagent)
    mol_mass, _ = k_atoms.calculate_molecular_mass()
    k_mol = mass / round(mol_mass)
    self.substance1_qty_lbl.setText(
        f"Количество известного вещества: {mass:.3f} / {round(mol_mass)} = {k_mol:.3f} моль")
    kc = coeffs[reagents.index(known_reagent)]
    rc = coeffs[reagents.index(found_reagent)]
    self.mol_fraction_lbl.setText(
        f"Мольное соотношение известного вещества к неизвестному: {kc}:{rc}")
    r_mol = k_mol / kc * rc
    mol_mass, _ = r_atoms.calculate_molecular_mass()
    r_mass = r_mol * round(mol_mass)
    self.substance2_mass_lbl.setText(
        f"Масса неизвестного вещества: {r_mol:.3f} * {round(mol_mass)} = {r_mass:.3f} г")
    self.output_equation_lbl.setText(f"Масса {found_reagent} = {r_mass:.3f}")
    with open("query_history.txt", "a", encoding="utf-8") as history:
        history.write(
            f"Расчет массы элемента {found_reagent}; m({known_reagent}) = {mass} г; " +
            f"{reagent1} + {reagent2} -> {reagent3} + {reagent4}\n"
        )
    self.update_history()


if __name__ == '__main__':
    elements_table, solubility_table = initialize()
