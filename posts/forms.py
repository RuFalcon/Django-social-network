from django.forms import ModelForm
from .models import Post, Comment
from django.contrib.auth import get_user_model

User = get_user_model()


class PostForm(ModelForm):

    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        labels = {
            'group': 'Категория',
            'text': 'Текст',
            'image': 'Изображение',
        }
        help_texts = {'text': "Поле обязательно для заполнения"}


class CommentForm(ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст сообщения',
        }
        help_texts = {'text': "Поле обязательно для заполнения"}
