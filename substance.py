import math
from database_searcher import get_anion_charge, get_element_type, get_anion, QueryNotFoundError


class Substance:
    """Базовый класс химических веществ с катионом и анионом."""
    def __init__(self, cation, cation_charge, anion, anion_charge):
        """Инициализирует вещество по катиону, аниону и их зарядам."""
        self.formula = ""
        self.cation = cation
        self.cation_charge = cation_charge
        self.anion = anion
        self.anion_charge = anion_charge
        self.cation_count = -self.anion_charge
        self.anion_count = self.cation_charge
        gcd = math.gcd(self.cation_count, self.anion_count)
        self.cation_count //= gcd
        self.anion_count //= gcd
        self.formula = self.get_cation_formula() + self.get_anion_formula()

    def __str__(self):
        """Возвращает формулу вещества."""
        return self.formula

    def get_cation_formula(self):
        """Возвращает формулу катиона."""
        if len(list(filter(lambda x: x.isupper(), self.cation))) > 1 and self.cation_count > 1:
            return f"({self.cation}){self.cation_count}"
        else:
            return f"{self.cation}{self.cation_count if self.cation_count > 1 else ''}"

    def get_anion_formula(self):
        """Возвращает формулу аниона."""
        if len(list(filter(lambda x: x.isupper(), self.anion))) > 1 and self.anion_count > 1:
            return f"({self.anion}){self.anion_count}"
        else:
            return f"{self.anion}{self.anion_count if self.anion_count > 1 else ''}"


class Oxide(Substance):
    """Оксиды - это вещества, где анионом является кислород."""
    def __init__(self, cation, valency):
        super(Oxide, self).__init__(cation, valency, "O", -2)

    def oxide_type(self):
        """Возвращает тип оскида."""
        if self.formula in ("CO", "N2O", "NO", "SiO", "S2O"):
            return "несолеобразующий"
        if 5 <= self.cation_charge or get_element_type(self.cation) == "неметалл":
            return "кислотный"
        if 3 <= self.cation_charge <= 4 or (self.cation in ("Zn", "Be", "Pb", "Sn") and
                                            self.cation_charge == 2):
            return "амфотерный"
        if self.cation_charge <= 2:
            return "основный"


class Acid(Substance):
    """Кислоты - это вещества, где катионом является водород."""
    def __init__(self, anion):
        super(Acid, self).__init__("H", 1, anion, get_anion_charge(anion))


class Base(Substance):
    """Основания - это вещества, где анионом является гидроксильная группа (OH)."""
    def __init__(self, cation, valency):
        super(Base, self).__init__(cation, valency, "OH", -1)


class Salt(Substance):
    """Соли - это вещества, где катионами являются металлы."""
    def __init__(self, cation, valency, anion):
        super(Salt, self).__init__(cation, valency, anion, get_anion_charge(anion))


def get_substance(formula):
    """Возвращает вещество по его строковой формуле."""
    if formula == "":
        return ""
    try:
        get_element_type(formula)
        return formula
    except QueryNotFoundError:
        pass
    if formula.startswith("H"):
        if formula[1].isnumeric():
            cation_count = int(formula[1])
            index = 2
            while formula[index].isnumeric():
                cation_count = cation_count * 10 + formula[index]
                index += 1
            anion = formula[index:]
        else:
            anion = formula[1:]
        return Acid(anion)
    elif "OH" in formula:
        if formula.endswith("OH"):
            cation = formula[:-2]
            return Base(cation, 1)
        else:
            index = formula.index("OH")
            cation = formula[:index - 1]
            cation_charge = int(formula[index + 3:])
            return Base(cation, cation_charge)
    elif "O" in formula and get_anion(formula) == "O":
        index = formula.index("O")
        if formula[index - 1] == "2":
            cation = formula[:index - 1]
            cation_charge = 1 if formula.endswith("O") else int(formula[index + 1:])
        else:
            cation = formula[:index]
            cation_charge = (1 if formula.endswith("O") else int(formula[index + 1:])) * 2
        return Oxide(cation, cation_charge)
    else:
        return get_salt(formula)


def get_salt(formula):
    """Часть функции get_substance(). Возвращает соль по её строковой формуле."""
    anion = get_anion(formula)
    anion_index = formula.index(anion)
    if len(list(filter(lambda x: x.isupper(), anion))) >= 2:
        if formula[anion_index - 1] == "(":
            anion_count = int(formula[anion_index + len(anion) + 1])
            cation_part = formula[:anion_index - 1]
        else:
            anion_count = 1
            cation_part = formula[:anion_index]
    else:
        if formula.endswith(anion):
            anion_count = 1
        else:
            anion_count = int(formula[anion_index + len(anion)])
        cation_part = formula[:anion_index]
    if "(" in cation_part:
        cation = cation_part[1:cation_part.index(")")]
        cation_count = int(cation_part[cation_part.index(")") + 1])
    elif len(list(filter(lambda x: x.isupper(), cation_part))) >= 2:
        cation = cation_part
        cation_count = 1
    else:
        i = -1
        index = ""
        while cation_part[i].isdigit():
            index = cation_part[i] + index
            i -= 1
        cation = cation_part[:i+1] if i != -1 else cation_part
        cation_count = int(index) if index else 1
    anion_total = -get_anion_charge(anion) * anion_count
    return Salt(cation, anion_total // cation_count, anion)


if __name__ == "__main__":
    print("Testing creating substances")
    print(Oxide("Ba", 2))
    print(Oxide("Fe", 3))
    print(Oxide("K", 1))
    print(Oxide("P", 5))
    print(Acid("SiO3"))
    print(Acid("SO4"))
    print(Acid("PO4"))
    print(Base("K", 1))
    print(Base("Ba", 2))
    print(Base("Al", 3))
    print(Salt("Al", 3, "SO4"))
    print(Salt("Ba", 2, "Cl"))
    print(Salt("Ba", 2, "NO3"))
    print(Salt("NH4", 1, "SO4"))
    print(Salt("Ba", 2, "SO4"))
    print("-----")
    print("Testing getting substances from formula")
    acid1 = get_substance("H3PO4")
    print(acid1.__class__)
    print(acid1)
    acid1 = get_substance("HCl")
    print(acid1.__class__)
    print(acid1)
    base1 = get_substance("KOH")
    print(base1.__class__)
    print(base1)
    base2 = get_substance("Ba(OH)2")
    print(base2.__class__)
    print(base2)
    oxide1 = get_substance("N2O")
    print(oxide1.__class__)
    print(oxide1)
    print(oxide1.oxide_type())
    oxide2 = get_substance("K2O")
    print(oxide2.__class__)
    print(oxide2)
    print(oxide2.oxide_type())
    oxide3 = get_substance("ZnO")
    print(oxide3.__class__)
    print(oxide3)
    print(oxide3.oxide_type())
    oxide4 = get_substance("SO2")
    print(oxide4.__class__)
    print(oxide4)
    print(oxide4.oxide_type())
    print(get_substance("Al2(SO4)3"))
    print(get_substance("BaCl2"))
    print(get_substance("Ba(NO3)2"))
    print(get_substance("(NH4)2SO4"))
    print(get_substance("BaSO4"))
