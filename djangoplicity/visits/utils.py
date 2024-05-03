def obfuscate_email(email):
    if "@" not in email:
        return email

    name, domain = email.split('@')
    name = name[0] + '*' * (len(name) - 1)
    domain = domain[0] + '*' * (len(domain.split('.')[0]) - 1) + '.' + domain.split('.')[1]
    return f"{name}@{domain}"


def obfuscate_phone(phone):
    if len(phone) < 4:
        return phone

    return '*' * (len(phone) - 4) + phone[-4:]
