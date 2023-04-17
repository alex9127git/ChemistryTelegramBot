import sys
from atoms import *
from substance import *
from database_searcher import *
from exception_files import *


history_path = "query_history.txt"
bg_path = os.path.join(BASE_DIR, "bg.png")


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
    """Функция, которая возвращает продукты реакции, получающиеся из исходных веществ, или ошибку, если не получилось
    расшифровать формулу вещества, подобрать продукты реакции, или если реакция не проходит."""
    try:
        substance1 = get_substance(reagent1)
        substance2 = get_substance(reagent2)
    except IndexError:
        raise SubstanceDecodeError("Не получилось расшифровать формулу вещества")
    if substance1.__class__ == Oxide:
        if substance1.oxide_type() == "кислотный":
            if reagent2 == "H2O":
                try:
                    # кислотный оксид + вода = кислота
                    acid = get_acid_from_oxide(reagent1)
                    return str(acid), ""
                except QueryNotFoundError:
                    raise AutoCompletionError("Не получилось автозаполнить реакцию")
            elif substance2.__class__ == Base:
                try:
                    # кислотный оксид + основание = соль + вода
                    acid = get_substance(get_acid_from_oxide(reagent1))
                    salt = Salt(substance2.cation, substance2.cation_charge, acid.anion)
                    return str(salt), "H2O"
                except QueryNotFoundError:
                    raise AutoCompletionError("Не получилось автозаполнить реакцию")
            elif substance2.__class__ == Oxide and substance2.oxide_type() == "основный":
                try:
                    # кислотый оксид + основный оксид = соль
                    acid = get_substance(get_acid_from_oxide(reagent1))
                    salt = Salt(substance2.cation, substance2.cation_charge, acid.anion)
                    return str(salt), ""
                except QueryNotFoundError:
                    raise AutoCompletionError("Не получилось автозаполнить реакцию")
        elif substance1.oxide_type() == "основный":
            if reagent2 == "H2O" and get_element_type(substance1.cation) in (
                    "щелочный металл", "щелочно-земельный металл"):
                # основный оксид + вода = основание, если металл оксида из IA или IIA группы
                base = Base(substance1.cation, substance1.cation_charge)
                return str(base),
            elif substance2.__class__ == Oxide and substance2.oxide_type() == "кислотный":
                try:
                    # основный оксид + кислотный оксид = соль
                    acid = get_substance(get_acid_from_oxide(reagent2))
                    salt = Salt(substance1.cation, substance1.cation_charge, acid.anion)
                    return str(salt), ""
                except QueryNotFoundError:
                    raise AutoCompletionError("Не получилось автозаполнить реакцию")
            elif substance2.__class__ == Acid:
                # основный оксид + кислота = соль + вода
                salt = Salt(substance1.cation, substance1.cation_charge, substance2.anion)
                return str(salt), "H2O"
    elif substance1.__class__ == Acid:
        if substance2.__class__ == str:
            if compare_reactivity(substance2, substance1.cation) > 0:
                # кислота + металл = соль + водород
                salt = Salt(substance2, get_cation_charge(substance2), substance1.anion)
                return str(salt), "H2"
            else:
                raise InvalidReactionError("Металл не может вытеснить водород из кислоты")
        elif (substance2.__class__ == Oxide and substance2.oxide_type() == "основный") or \
                (substance2.__class__ == Base):
            # кислота + основный оксид или основание = соль + вода
            salt = Salt(substance2.cation, substance2.cation_charge, substance1.anion)
            return str(salt), "H2O"
        elif substance2.__class__ == Salt:
            # кислота + соль = кислота' + соль' (осадок или газ)
            acid = Acid(substance2.anion)
            salt = Salt(substance2.cation, substance2.cation_charge, substance1.anion)
            if str(acid) not in ("H2CO3", "H2SO3"):
                try:
                    if get_solubility(salt) == "Р" and get_solubility(acid) == "Р":
                        raise InvalidReactionError("Один из продуктов реакции должен быть нерастворим")
                except QueryNotFoundError:
                    raise AutoCompletionError("Не получилось автозаполнить реакцию")
            return str(acid), str(salt)
    elif substance1.__class__ == Base:
        if substance2.__class__ == Oxide and substance2.oxide_type() == "кислотный":
            try:
                # основание + кислотный оксид = соль + вода
                acid = get_substance(get_acid_from_oxide(reagent1))
                salt = Salt(substance2.cation, substance2.cation_charge, acid.anion)
                return str(salt), "H2O"
            except QueryNotFoundError:
                raise AutoCompletionError("Не получилось автозаполнить реакцию")
        elif substance2.__class__ == Acid:
            # основание + кислота = соль + вода
            salt = Salt(substance1.cation, substance1.cation_charge, substance2.anion)
            return str(salt), "H2O"
        elif substance2.__class__ == Salt:
            try:
                # основание + соль = основание' + соль' (осадок или газ)
                if get_solubility(substance1) == "Р" and get_solubility(substance2) == "Р":
                    salt = Salt(substance1.cation, substance1.cation_charge, substance2.anion)
                    base = Base(substance2.cation, substance2.cation_charge)
                    if get_solubility(salt) == "Р" and get_solubility(base) == "Р":
                        raise InvalidReactionError("Один из продуктов реакции должен быть нерастворим")
                    return str(base), str(salt)
            except QueryNotFoundError:
                raise AutoCompletionError("Не получилось автозаполнить реакцию")
        elif substance2 == "":
            try:
                # нерастворимоеоснование = оксид + вода
                if get_solubility(substance1) == "Р":
                    raise InvalidReactionError("Основание должно быть нерастворимо")
                oxide = Oxide(substance1.cation, substance1.cation_charge)
                return str(oxide), "H2O"
            except QueryNotFoundError:
                raise AutoCompletionError("Не получилось автозаполнить реакцию")
    elif substance1.__class__ == Salt:
        if substance2.__class__ == Acid:
            # соль + кислота = соль' + кислота' (осадок или газ)
            acid = Acid(substance1.anion)
            salt = Salt(substance1.cation, substance1.cation_charge, substance2.anion)
            if str(acid) not in ("H2CO3", "H2SO3"):
                try:
                    if get_solubility(salt) == "Р" and get_solubility(acid) == "Р":
                        raise InvalidReactionError("Один из продуктов реакции должен быть нерастворим")
                except QueryNotFoundError:
                    raise AutoCompletionError("Не получилось автозаполнить реакцию")
            return str(acid), str(salt)
        elif substance2.__class__ == Base:
            # соль + основание = соль' + основание' (осадок или газ)
            try:
                if get_solubility(substance2) == "Р" and get_solubility(substance1) == "Р":
                    salt = Salt(substance2.cation, substance2.cation_charge, substance1.anion)
                    base = Base(substance1.cation, substance1.cation_charge)
                    if get_solubility(salt) == "Р" and get_solubility(base) == "Р":
                        raise InvalidReactionError("Один из продуктов реакции должен быть нерастворим")
                    return str(base), str(salt)
            except QueryNotFoundError:
                raise AutoCompletionError("Не получилось автозаполнить реакцию")
        elif substance2.__class__ == Salt:
            # соль + соль = соль' + соль' (осадок или газ)
            try:
                if get_solubility(substance2) == "Р" and get_solubility(substance1) == "Р":
                    result_salt1 = Salt(substance2.cation, substance2.cation_charge, substance1.anion)
                    result_salt2 = Salt(substance1.cation, substance1.cation_charge, substance2.anion)
                    if get_solubility(result_salt1) == "Р" and get_solubility(result_salt2) == "Р":
                        raise InvalidReactionError("Один из продуктов реакции должен быть нерастворим")
                    return str(result_salt1), str(result_salt2)
            except QueryNotFoundError:
                raise AutoCompletionError("Не получилось автозаполнить реакцию")
        elif substance2.__class__ == str:
            # соль + металл = соль' + металл'
            if compare_reactivity(substance2, substance1.cation) > 0:
                salt = Salt(substance2, get_cation_charge(substance2), substance1.anion)
                return str(salt), str(substance1.cation)
            else:
                raise InvalidReactionError("Металл недостаточно активен, чтобы вытеснить металл из соли")


def fill_coefficients(in1, in2, out1, out2):
    """Заполняет коэффициенты реакции. Принимает на вход четыре вещества (могут присутствовать пустые строки -
    это значит, что вещество пропущено)"""
    try:
        substance1 = get_substance(in1)
        substance2 = get_substance(in2)
    except IndexError:
        pass
    else:
        if substance1.__class__ == Acid:
            if substance2.__class__ == str:
                if compare_reactivity(substance2, substance1.cation) <= 0:
                    raise InvalidReactionError("Металл не может вытеснить водород из кислоты")
            elif substance2.__class__ == Salt:
                acid = Acid(substance2.anion)
                salt = Salt(substance2.cation, substance2.cation_charge, substance1.anion)
                if str(acid) not in ("H2CO3", "H2SO3"):
                    try:
                        if get_solubility(salt) == "Р" and get_solubility(acid) == "Р":
                            raise InvalidReactionError("Один из продуктов реакции должен быть нерастворим")
                    except QueryNotFoundError:
                        pass
        elif substance1.__class__ == Base:
            if substance2.__class__ == Salt:
                try:
                    if get_solubility(substance1) == "Р" and get_solubility(substance2) == "Р":
                        salt = Salt(substance1.cation, substance1.cation_charge, substance2.anion)
                        base = Base(substance2.cation, substance2.cation_charge)
                        if get_solubility(salt) == "Р" and get_solubility(base) == "Р":
                            raise InvalidReactionError("Один из продуктов реакции должен быть нерастворим")
                except QueryNotFoundError:
                    pass
            elif substance2 == "":
                try:
                    if get_solubility(substance1) == "Р":
                        raise InvalidReactionError("Основание должно быть нерастворимо")
                except QueryNotFoundError:
                    pass
        elif substance1.__class__ == Salt:
            if substance2.__class__ == Acid:
                acid = Acid(substance1.anion)
                salt = Salt(substance1.cation, substance1.cation_charge, substance2.anion)
                if str(acid) not in ("H2CO3", "H2SO3"):
                    try:
                        if get_solubility(salt) == "Р" and get_solubility(acid) == "Р":
                            raise InvalidReactionError("Один из продуктов реакции должен быть нерастворим")
                    except QueryNotFoundError:
                        pass
            elif substance2.__class__ == Base:
                try:
                    if get_solubility(substance2) == "Р" and get_solubility(substance1) == "Р":
                        salt = Salt(substance2.cation, substance2.cation_charge, substance1.anion)
                        base = Base(substance1.cation, substance1.cation_charge)
                        if get_solubility(salt) == "Р" and get_solubility(base) == "Р":
                            raise InvalidReactionError("Один из продуктов реакции должен быть нерастворим")
                except QueryNotFoundError:
                    pass
            elif substance2.__class__ == Salt:
                try:
                    if get_solubility(substance2) == "Р" and get_solubility(substance1) == "Р":
                        result_salt1 = Salt(substance2.cation, substance2.cation_charge, substance1.anion)
                        result_salt2 = Salt(substance1.cation, substance1.cation_charge, substance2.anion)
                        if get_solubility(result_salt1) == "Р" and get_solubility(result_salt2) == "Р":
                            raise InvalidReactionError("Один из продуктов реакции должен быть нерастворим")
                except QueryNotFoundError:
                    pass
            elif substance2.__class__ == str:
                if compare_reactivity(substance2, substance1.cation) <= 0:
                    raise InvalidReactionError("Металл недостаточно активен, чтобы вытеснить металл из соли")
    try:
        coeffs = calculate_coefficients(in1, in2, out1, out2)
    except CoefficientCalculationError:
        return "Не получилось расставить коэффициенты"
    else:
        coeff1, coeff2, coeff3, coeff4 = coeffs
        str1 = f"{coeff1} {in1}" if in1 else ""
        str2 = f"{coeff2} {in2}" if in2 else ""
        if out1 == "H2CO3":
            str3 = f"{coeff3} H2O + {coeff3} CO2"
        elif out1 == "H2SO3":
            str3 = f"{coeff3} H2O + {coeff3} SO2"
        else:
            str3 = f"{coeff3} {out1}" if out1 else ""
        if out2 == "H2CO3":
            str4 = f"{coeff4} H2O + {coeff4} CO2"
        elif out2 == "H2SO3":
            str4 = f"{coeff4} H2O + {coeff4} SO2"
        else:
            str4 = f"{coeff4} {out2}" if out2 else ""
        part1 = " + ".join(filter(lambda x: x, (str1, str2)))
        part2 = " + ".join(filter(lambda x: x, (str3, str4)))
        ionic = get_ionic_equation((in1, in2, out1, out2), coeffs)
        return f"Коэффициенты в реакции расставлены:\n" \
               f"{part1} -> {part2}\n" + \
               (f"Ионное уравнение: {ionic}" if ionic else "Ионное уравнение не составляется")


def get_ionic_equation(reagents, coeffs):
    try:
        substances = list(map(lambda r: get_substance(r), reagents))
    except IndexError:
        return ""
    equation = []
    for i, (substance, coeff) in enumerate(zip(substances, coeffs)):
        if not substance:
            continue
        try:
            if isinstance(substance, Substance) and not isinstance(substance, Oxide) and \
                    str(substance) != "H2O" and get_solubility(substance) == "Р":
                equation.append(f"{coeff * substance.cation_count} "
                                f"{substance.cation}({substance.cation_charge}+) + ")
                equation.append(f"{coeff * substance.anion_count} {substance.anion}({abs(substance.anion_charge)}-)")
            else:
                equation.append(f"{coeff} {substance}")
            if i != 3:
                equation.append(" -> " if i % 2 else " + ")
        except QueryNotFoundError:
            return ""
    return "".join(equation).strip(" + ")


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


def calculate_mass(substance, element):
    """Рассчитывает массовую долю выбранного элемента в выбранном веществе."""
    try:
        get_element_type(element)
    except QueryNotFoundError:
        return "Не получилось найти элемент"
    substance_atoms = Atoms(substance)
    substance_mass, expression = substance_atoms.calculate_molecular_mass()
    element_mass = get_element_mass(element) * substance_atoms.atoms.get(element, 0)
    msg = f"Молекулярная масса вещества: {expression}\n"
    msg += f"Молекулярная масса элемента: {element_mass}\n"
    mass_fraction = element_mass / substance_mass
    msg += f"Расчёт массовой доли элемента: {element_mass} / {substance_mass} = {mass_fraction}\n"
    msg += f"Массовая доля {element} в {substance} составляет {mass_fraction * 100:.3f}%"
    return msg


def calculate_formula(elements_dict):
    """Рассчитывает формулу вещества по массовым долям его элементов."""
    try:
        for element in elements_dict.keys():
            get_element_type(element)
    except QueryNotFoundError:
        return "Не получилось найти один из элементов"
    if len(elements_dict) < 2:
        return "Нужно определить как минимум два элемента"
    elements = list(elements_dict.keys())
    percentages = list(elements_dict.values())
    if sum(percentages) != 100:
        return "Процентные соотношения в сумме должны давать 100%"
    masses = list(map(lambda x: round(get_element_mass(x)), elements))
    quantity = len(elements)
    coeffs = [1] * quantity
    percent = list(map(lambda x: masses[x] * coeffs[x] / percentages[x], range(quantity)))
    while len(set(percent)) > 1:
        index = percent.index(min(percent))
        coeffs[index] += 1
        percent = list(map(lambda x: masses[x] * coeffs[x] / percentages[x], range(quantity)))
    return f"Формула вещества рассчитана:\n" \
           f"{' : '.join(elements)} = {' : '.join(map(str, coeffs))}"


def calculate_equation(reagent1, reagent2, reagent3, reagent4, known_reagent, mass, found_reagent):
    reagents = [reagent1, reagent2, reagent3, reagent4]
    if known_reagent not in reagents or found_reagent not in reagents or known_reagent == "" \
            or found_reagent == "":
        return "Известное или искомое вещество не находится в уравнении"
    try:
        coeffs = calculate_coefficients(*reagents)
    except CoefficientCalculationError:
        return "Не получилось расставить коэффициенты"
    coeff1, coeff2, coeff3, coeff4 = coeffs
    str1 = f"{coeff1} {reagent1}" if reagent1 else ""
    str2 = f"{coeff2} {reagent2}" if reagent2 else ""
    str3 = f"{coeff3} {reagent3}" if reagent3 else ""
    str4 = f"{coeff4} {reagent4}" if reagent4 else ""
    part1 = " + ".join(filter(lambda x: x, (str1, str2)))
    part2 = " + ".join(filter(lambda x: x, (str3, str4)))
    msg = f"Уравнение с коэффициентами: {part1} -> {part2}\n"
    k_atoms = Atoms(known_reagent)
    r_atoms = Atoms(found_reagent)
    mol_mass, _ = k_atoms.calculate_molecular_mass()
    k_mol = mass / round(mol_mass)
    msg += f"Количество {known_reagent}: {mass:.3f} / {round(mol_mass)} = {k_mol:.3f} моль\n"
    kc = coeffs[reagents.index(known_reagent)]
    rc = coeffs[reagents.index(found_reagent)]
    msg += f"Мольное соотношение {known_reagent} к {found_reagent}: {kc}:{rc}\n"
    r_mol = k_mol / kc * rc
    mol_mass, _ = r_atoms.calculate_molecular_mass()
    r_mass = r_mol * round(mol_mass)
    msg += f"Масса {found_reagent}: {r_mol:.3f} * {round(mol_mass)} = {r_mass:.3f} г"
    return msg


if __name__ == '__main__':
    print(fill_coefficients("AgNO3", "NaCl", "AgCl", "NaNO3"))
    print(fill_coefficients("CuSO4", "NaOH", "Cu(OH)2", "Na2SO4"))
    print(fill_coefficients("Na2CO3", "HCl", "H2CO3", "NaCl"))
    print(fill_coefficients("CuSO4", "Al", "Al2(SO4)3", "Cu"))
    print(fill_coefficients("Cu3(PO4)2", "K", "K3PO4", "Cu"))
    print(fill_coefficients("CuSO4", "Ba(OH)2", "Cu(OH)2", "BaSO4"))
    print(fill_coefficients("NaOH", "H3PO4", "Na3PO4", "H2O"))
    print(fill_coefficients("Na2O", "SO2", "Na2SO3", ""))
    print(fill_coefficients("LiOH", "CuSO4", "Cu(OH)2", "Li2SO4"))
    print(fill_coefficients("NaOH", "CO2", "NaHCO3", ""))
    print(calculate_mass("Al2(SO4)3", "S"))
    print(calculate_mass("Al2(SO4)3", "Al"))
    print(calculate_formula({"Cu": 80.0, "O": 20.0}))
    print(calculate_formula({"Cu": 40.0, "S": 20.0, "O": 40.0}))
    print(calculate_equation("CuSO4", "KOH", "K2SO4", "Cu(OH)2", "KOH", 10.0, "K2SO4"))
    print(calculate_equation("CuSO4", "Al", "Al2(SO4)3", "Cu", "Al", 130.0, "Al2(SO4)3"))
