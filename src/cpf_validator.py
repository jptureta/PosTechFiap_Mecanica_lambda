import re


def validar_cpf(cpf: str) -> bool:
    """Valida CPF usando algoritmo oficial dos dígitos verificadores."""
    cpf = re.sub(r"\D", "", cpf)

    if len(cpf) != 11:
        return False

    # Rejeita sequências triviais (000...0, 111...1, etc.)
    if cpf == cpf[0] * 11:
        return False

    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto

    if int(cpf[9]) != digito1:
        return False

    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto

    return int(cpf[10]) == digito2


def normalizar_cpf(cpf: str) -> str:
    """Remove formatação, mantendo apenas dígitos."""
    return re.sub(r"\D", "", cpf)

