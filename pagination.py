from math import ceil

class Pagination(object):

    def __init__(self,  total_count, page, page_size=5):
        self.page = page
        self.page_size = page_size
        self.total_count = total_count

    def pages_count(self):
        return int(ceil(self.total_count / float(self.page_size)))

    def has_next(self):
        return self.page < self.pages_count()

    def has_previous(self):
        return self.page > 1


