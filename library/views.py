from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Q
from datetime import date
from .models import Book, Member, Transaction
from .forms import BookForm, MemberForm, BorrowForm

def dashboard(request):
    # Dynamically update overdue statuses on loading dashboard
    overdue_updates = Transaction.objects.filter(status='BORROWED', due_date__lt=date.today())
    if overdue_updates.exists():
        overdue_updates.update(status='OVERDUE')

    total_books = Book.objects.aggregate(Sum('total_copies'))['total_copies__sum'] or 0
    available_books = Book.objects.aggregate(Sum('available_copies'))['available_copies__sum'] or 0
    total_members = Member.objects.count()
    active_borrows = Transaction.objects.filter(status='BORROWED').count()
    overdue_loans = Transaction.objects.filter(status='OVERDUE').count()

    recent_transactions = Transaction.objects.all().order_by('-id')[:5]
    recent_books = Book.objects.all().order_by('-id')[:5]

    context = {
        'total_books': total_books,
        'available_books': available_books,
        'total_members': total_members,
        'active_borrows': active_borrows,
        'overdue_loans': overdue_loans,
        'recent_transactions': recent_transactions,
        'recent_books': recent_books,
    }
    return render(request, 'library/dashboard.html', context)


# Book Views
def book_list(request):
    query = request.GET.get('q', '')
    books = Book.objects.all()
    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(isbn__icontains=query) |
            Q(genre__icontains=query)
        )
    return render(request, 'library/book_list.html', {'books': books, 'query': query})

def book_create(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save(commit=False)
            # Default available copies to total copies if not specified or incorrect
            if book.available_copies > book.total_copies:
                book.available_copies = book.total_copies
            book.save()
            messages.success(request, f"Book '{book.title}' created successfully!")
            return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'library/book_form.html', {'form': form, 'title': 'Add New Book'})

def book_edit(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            # Adjust available_copies logic dynamically if total_copies is modified
            old_total = Book.objects.get(pk=pk).total_copies
            book = form.save(commit=False)
            diff = book.total_copies - old_total
            book.available_copies = max(0, book.available_copies + diff)
            book.save()
            messages.success(request, f"Book '{book.title}' updated successfully!")
            return redirect('book_list')
    else:
        form = BookForm(instance=book)
    return render(request, 'library/book_form.html', {'form': form, 'title': 'Edit Book'})

def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.delete()
        messages.success(request, f"Book '{book.title}' deleted successfully.")
        return redirect('book_list')
    return render(request, 'library/confirm_delete.html', {'item': book, 'type': 'Book', 'cancel_url': 'book_list'})


# Member Views
def member_list(request):
    query = request.GET.get('q', '')
    members = Member.objects.all()
    if query:
        members = members.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(membership_id__icontains=query)
        )
    return render(request, 'library/member_list.html', {'members': members, 'query': query})

def member_create(request):
    if request.method == 'POST':
        form = MemberForm(request.POST)
        if form.is_valid():
            member = form.save()
            messages.success(request, f"Member '{member.first_name} {member.last_name}' registered successfully!")
            return redirect('member_list')
    else:
        form = MemberForm()
    return render(request, 'library/member_form.html', {'form': form, 'title': 'Register New Member'})

def member_edit(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        form = MemberForm(request.POST, instance=member)
        if form.is_valid():
            member = form.save()
            messages.success(request, f"Member '{member.first_name} {member.last_name}' updated successfully!")
            return redirect('member_list')
    else:
        form = MemberForm(instance=member)
    return render(request, 'library/member_form.html', {'form': form, 'title': 'Edit Member Details'})

def member_delete(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == 'POST':
        member.delete()
        messages.success(request, f"Member '{member.first_name} {member.last_name}' deleted successfully.")
        return redirect('member_list')
    return render(request, 'library/confirm_delete.html', {'item': member, 'type': 'Member', 'cancel_url': 'member_list'})


# Transaction / Borrow / Return Views
def transaction_list(request):
    # Dynamically update overdue statuses on loading transactions list
    overdue_updates = Transaction.objects.filter(status='BORROWED', due_date__lt=date.today())
    if overdue_updates.exists():
        overdue_updates.update(status='OVERDUE')

    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    transactions = Transaction.objects.all().order_by('-id')

    if status_filter:
        transactions = transactions.filter(status=status_filter)

    if query:
        transactions = transactions.filter(
            Q(book__title__icontains=query) |
            Q(member__first_name__icontains=query) |
            Q(member__last_name__icontains=query) |
            Q(member__membership_id__icontains=query)
        )

    context = {
        'transactions': transactions,
        'query': query,
        'status_filter': status_filter,
    }
    return render(request, 'library/transaction_list.html', context)

def borrow_book(request):
    if request.method == 'POST':
        form = BorrowForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            book = transaction.book
            
            # Additional double check check if copies are available
            if book.available_copies > 0:
                book.available_copies -= 1
                book.save()
                transaction.status = 'BORROWED'
                transaction.save()
                messages.success(request, f"Book '{book.title}' successfully issued to {transaction.member}!")
                return redirect('transaction_list')
            else:
                messages.error(request, "Error: Book is currently out of stock.")
    else:
        form = BorrowForm()
    return render(request, 'library/borrow_form.html', {'form': form})

def return_book(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk)
    if transaction.status in ['BORROWED', 'OVERDUE']:
        book = transaction.book
        book.available_copies += 1
        book.save()
        
        transaction.status = 'RETURNED'
        transaction.return_date = date.today()
        transaction.save()
        messages.success(request, f"Book '{book.title}' has been successfully returned!")
    else:
        messages.warning(request, "This book has already been marked as returned.")
    return redirect('transaction_list')
