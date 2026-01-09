import hashlib


class Link:

    def __init__(self, data, name, description, category, tags, organization, themes=[]) -> None:
        self.data = data
        self.name = name
        self.description = description
        self.category = category
        self.type = "link"
        self.tags = tags
        self.isPrivate = False
        self.organization = organization
        self.thems = themes
        self.hash_link()

    # Creates a hash value of the title and the link for this to be unique in our database
    def hash_link(self):
        # Change this keys with caution, because this might change everything
        obj = {"url": self.data, "title": self.name}
        hash_object = hashlib.sha256()

        hash_object.update(bytes(f'{obj}', 'utf-8'))
        self.hash_value = hash_object.hexdigest()
