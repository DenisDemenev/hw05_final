from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='DenisD')
        cls.Post = Post.objects.create(
            text='Тестовый пост',
            id='198',
            author=cls.user
        )
        cls.post = Post.objects.get(id='198')
        cls.Group = Group.objects.create(
            title='Тестовая группа',
            slug='slug-test',
            description='Тестовое описание сообщества',
        )
        cls.group = Group.objects.get(slug='slug-test')

    def test_verbose_name(self):
        post = PostModelTest.post
        group = PostModelTest.group
        field_verboses_post = {
            'text': 'Тест поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор поста',
            'group': 'Сообщество',
        }
        for field, expected_value in field_verboses_post.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)
        field_verboses_group = {
            'title': 'Название',
            'slug': 'Ссылка',
            'description': 'Описание сообщества',
        }
        for field, expected_value in field_verboses_group.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name, expected_value)

    def test_help_text(self):
        post = PostModelTest.post
        group = PostModelTest.group
        field_help_texts_post = {
            'text': 'Здесь напишите текст вашего поста',
            'group': 'Выберите сообщество',
        }
        for field, expected_value in field_help_texts_post.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)
        field_help_texts_group = {
            'title': 'Напишите название сообщества',
            'description': 'Здесь напишите описание',
        }
        for field, expected_value in field_help_texts_group.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).help_text, expected_value)

    def test_str_Post(self):
        post = PostModelTest.post
        self.assertEqual(post.text, 'Тестовый пост')

    def test_str_Group(self):
        group = PostModelTest.group
        self.assertEqual(group.title, 'Тестовая группа')
