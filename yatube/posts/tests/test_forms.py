from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='DenisD')
        cls.not_author_user = User.objects.create(
            username='not_author'
        )
        cls.group = Group.objects.create(
            title='Название',
            slug='test_slug',
            description='Описание группы'
        )
        cls.test_user = User.objects.create(
            username='test_user'
        )
        cls.test_group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='test-group',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group
        )
        cls.test_post = Post.objects.create(
            text='Тестовый текст записи',
            author=cls.test_user,
            group=cls.test_group,
        )

    def setUp(self):
        self.not_author_client = Client()
        self.not_author_client.force_login(self.not_author_user)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.guest_client = Client()

    def test_form_create_new_post(self):
        posts_count = Post.objects.count()
        form_data = {'text': 'Тестовый пост из формы', 'group': self.group.id}
        new_text_form = form_data['text']
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(
            text=new_text_form,
            group=self.group.id,
            author=self.author
        ).exists())
        last_object = Post.objects.order_by('id').last()
        self.assertEqual(last_object.text, form_data['text'])
        self.assertRedirects(response, reverse('index'))

    def test_edit_post_in_form(self):
        new_text = 'Новый текст'
        form_data = {'text': new_text, 'group': self.group.id}
        self.authorized_client.post(
            reverse('post_edit',
                    kwargs={'username': self.author.username,
                            'post_id': self.post.id}),
            data=form_data
        )
        response = self.authorized_client.get(
            reverse('post',
                    kwargs={'username': self.author.username,
                            'post_id': self.post.id})
        )
        self.assertEqual(response.context['post'].text, new_text)
        self.assertTrue(Post.objects.filter(
            text=new_text,
            group=self.group.id
        ).exists())

    def test_create_post_guest(self):
        form_data = {
            'text': 'Гость создаeт запись в группе',
            'group': self.test_group.id,
        }
        posts_count = Post.objects.count()
        response = self.guest_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post_not_author(self):
        form_data_edit = {
            'text': 'Исправленный не автором текст записи',
            'group': self.test_group.id,
        }
        response = self.not_author_client.post(
            reverse('post_edit', kwargs={'username': self.test_user,
                                         'post_id': self.test_post.id}),
            data=form_data_edit,
            follow=True
        )
        self.test_post.refresh_from_db()
        self.assertNotEqual(self.test_post.text, form_data_edit['text'])
        self.assertEqual(self.test_post.group, self.test_group)
        self.assertEqual(self.test_post.author, self.test_user)
        self.assertEqual(response.status_code, HTTPStatus.OK)
