from django import forms

class CommentForm(forms.Form):
    # Form for submitting comments
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'w-full p-2 bg-gray-600 rounded-lg text-white',
            'placeholder': 'Type your comment...'
        }),
        max_length=500,
        required=True
    )
    # Textarea field for comment input