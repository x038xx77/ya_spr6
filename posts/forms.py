from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ['group', 'text', 'image']
        labels = {
            'group': ('Групка'),
        }
        help_texts = {
            'group': ('Справочный текст поля'),
        }


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ['text']
        text = forms.CharField(widget=forms.Textarea)