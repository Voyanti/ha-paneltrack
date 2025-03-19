def slugify(text):
    return text.replace(' ', '_').replace('(', '').replace(')', '').replace('/', 'OR').replace('&', ' ').replace(':', '').replace('.', '').lower()
