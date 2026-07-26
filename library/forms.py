from django import forms
from .models import Book, Member, Transaction
from datetime import date, timedelta

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'genre', 'description', 'published_date', 'total_copies', 'available_copies']
        widgets = {
            'published_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['first_name', 'last_name', 'email', 'phone', 'membership_id', 'is_active']


class BorrowForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['book', 'member', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show books that have copies available
        self.fields['book'].queryset = Book.objects.filter(available_copies__gt=0)
        # Only show active members
        self.fields['member'].queryset = Member.objects.filter(is_active=True)
        # Set default due date to 14 days from now
        self.fields['due_date'].initial = date.today() + timedelta(days=14)

    def clean(self):
        cleaned_data = super().clean()
        book = cleaned_data.get('book')
        member = cleaned_data.get('member')

        if book and book.available_copies <= 0:
            raise forms.ValidationError("This book is currently not available for borrowing.")

        if member and not member.is_active:
            raise forms.ValidationError("This member's account is suspended or inactive.")

        return cleaned_data
