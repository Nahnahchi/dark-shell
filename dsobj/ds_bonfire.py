
class DSBonfire:

    def __init__(self, source: str):
        source = source.split()
        self.bonfire_id = int(source[0])
        self.bonfire_name = " ".join(source[1:])

    def get_id(self):
        return self.bonfire_id

    def get_name(self):
        return self.bonfire_name
