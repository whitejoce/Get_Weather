class Book:
    def __init__(self, title, author, isbn):
        self.title = title
        self.author = author
        self.isbn = isbn

class LibrarySystem:
    def __init__(self):
        self.books = []

    def add_book(self, book):
        self.books.append(book)
        print(f"Added book: {book.title}")

    def remove_book(self, isbn):
        for book in self.books:
            if book.isbn == isbn:
                self.books.remove(book)
                print(f"Removed book: {book.title}")
                return
        print("Book not found")

    def find_book(self, isbn):
        for book in self.books:
            if book.isbn == isbn:
                return book
        print("Book not found")
        return None

# 示例用法
if __name__ == "__main__":
    library = LibrarySystem()
    book1 = Book("1984", "George Orwell", "1234567890")
    book2 = Book("To Kill a Mockingbird", "Harper Lee", "0987654321")

    library.add_book(book1)
    library.add_book(book2)

    found_book = library.find_book("1234567890")
    if found_book:
        print(f"Found book: {found_book.title}")

    library.remove_book("1234567890")
    library.remove_book("1111111111")
