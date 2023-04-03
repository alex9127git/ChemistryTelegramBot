from math import gcd
from database_searcher import get_element_mass


class Atoms:
    """Класс, объекты которого представляют список атомов. Нужен для уравнивания коэффициентов."""
    def __init__(self, formula):
        """Инициализирует список атомов вещества по формуле."""
        self.atoms = {}
        symbol = ""
        parentheses = ""
        parentheses_level = 0
        parentheses_atoms = None
        index = 0
        for letter in formula + " ":
            if parentheses_level:
                if letter not in "()":
                    parentheses += letter
            else:
                if letter.isupper() or letter == " ":
                    if symbol:
                        self.add(symbol, index if index else 1)
                        symbol = ""
                        index = 0
                    if parentheses_atoms is not None and parentheses_atoms.atoms:
                        self.add_from(parentheses_atoms * (index if index else 1))
                        parentheses_atoms = None
                        symbol = ""
                        index = 0
                    symbol += letter
                if letter.islower():
                    symbol += letter
                if letter.isdigit():
                    if index == 0:
                        index = int(letter)
                    else:
                        index = index * 10 + int(letter)
            if letter == "(":
                if symbol:
                    self.add(symbol, index if index else 1)
                    symbol = ""
                    index = 0
                if parentheses_atoms is not None and parentheses_atoms.atoms:
                    self.add_from(parentheses_atoms * (index if index else 1))
                    symbol = ""
                    index = 0
                if parentheses_level:
                    parentheses += letter
                parentheses_level += 1
            if letter == ")":
                parentheses_level -= 1
                if parentheses_level:
                    parentheses += letter
                else:
                    parentheses_atoms = Atoms(parentheses)

    def add(self, element, count):
        """Добавляет атом в список."""
        if element not in self.atoms:
            self.atoms[element] = 0
        self.atoms[element] += count

    def copy(self):
        """Копирует список атомов в новый объект."""
        a = Atoms("")
        a.atoms = self.atoms.copy()
        return a

    def add_from(self, atoms_obj):
        """Добавляет все атомы из списка."""
        for atom in atoms_obj.atoms:
            self.add(atom, atoms_obj.atoms[atom])

    def __mul__(self, other):
        """Умножает количество всех атомов на какое-то число и возвращает полученный объект."""
        a = self.copy()
        for atom in a.atoms.keys():
            a.atoms[atom] *= other
        return a

    def __str__(self):
        """Выводит количество всех атомов в списке."""
        result = []
        for atom in self.atoms.keys():
            result.append(f"{atom}: {self.atoms[atom]}")
        return "\n".join(result)

    def __add__(self, other):
        """Складывает два списка. Возвращает новый."""
        a = self.copy()
        a.add_from(other)
        return a

    def __eq__(self, other):
        """Проверяет два списка на равенство."""
        return self.atoms == other.atoms

    def __ne__(self, other):
        """Проверяет два списка на неравенство."""
        return not self == other

    def __contains__(self, item):
        """Проверяет есть ли атом в списке."""
        return item in self.atoms.keys()

    def disparity(self, other):
        """Возвращает атом, который находится в двух списках в разном количестве. Если списки равны,
        возвращает пустую строку. Если какой-то атом есть только в одном списке, возвращает строку
        "too different". Если атомов с разными количествами несколько, возвращает тот, для которого
        нужно меньше усилий, чтобы уравнять его с помощью коэффициентов УХР."""
        if self == other:
            return ""
        else:
            if self.atoms.keys() != other.atoms.keys():
                return "too different"
            else:
                lcc = 0
                result = ""
                for element in self.atoms.keys():
                    if self.atoms[element] != other.atoms[element]:
                        m = lcm(self.atoms[element], other.atoms[element])
                        if lcc == 0 or m < lcc:
                            result = element
                            lcc = m
                return result

    def calculate_molecular_mass(self):
        """Вычисляет молекулярную массу атомов в списке."""
        mass = 0
        expression = []
        for atom in self.atoms:
            mass += get_element_mass(atom) * self.atoms[atom]
            expression.append(f"{get_element_mass(atom)} x {self.atoms[atom]}")
        return mass, " + ".join(expression) + f" = {mass:.1f}"


def lcm(*integers):
    """Функция, возвращающая наименьшее общее кратное нескольких чисел."""
    result = 1
    for i in integers:
        result *= i
    return result // gcd(*integers)


if __name__ == "__main__":
    print("Testing conversion")
    from substance import *
    oxide1 = Oxide("Fe", 3)
    atoms = Atoms(oxide1.formula)
    print(atoms)
    print()
    acid1 = Acid("PO4")
    atoms = Atoms(acid1.formula)
    print(atoms)
    print()
    salt1 = Salt("Ag", 1, "SO4")
    atoms = Atoms(salt1.formula)
    print(atoms)
    print()
    base1 = Base("Ba", 2)
    atoms = Atoms(base1.formula)
    print(atoms)
    print()
    salt2 = Salt("Al", 3, "SO4")
    atoms = Atoms(salt2.formula)
    print(atoms)
    print()
    salt3 = Salt("NH4", 1, "SO4")
    atoms = Atoms(salt3.formula)
    print(atoms)
    print()
    atoms_2 = Atoms("Ba(OH(OH)2)2")
    print(atoms + atoms_2)
    print(atoms)
    print(atoms_2)
