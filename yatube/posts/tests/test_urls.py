from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(title='Название',
                                         slug='test-slug',
                                         description='Описание')
        cls.author = User.objects.create_user(username='Author')
        cls.no_author = User.objects.create_user(username='NoAuthor')
        cls.post = Post.objects.create(author=cls.author,
                                       text='Пост')
        cls.templates_url_names = {
            'index.html': reverse('index'),
            'group.html': reverse('group_posts',
                                  kwargs={'slug': cls.group.slug}),
            'new.html': reverse('new_post'),
            'profile.html': reverse(
                'profile',
                kwargs={'username': cls.author.username}
            ),
            'post.html': reverse(
                'post',
                kwargs={'username': cls.author.username,
                        'post_id': cls.post.id}
            ),
        }

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

        self.no_author_client = Client()
        self.no_author_client.force_login(self.no_author)

    def test_urls_uses_template(self):
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_url_for_guest(self):
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                if reverse_name == reverse('new_post'):
                    response = self.guest_client.get(reverse_name)
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
                else:
                    response = self.guest_client.get(reverse_name)
                    self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.guest_client.get(
            reverse('post_edit',
                    kwargs={'username': self.author.username,
                            'post_id': self.post.id}),
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_url_for_author(self):
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_for_no_author(self):
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest():
                if reverse_name == reverse(
                        'post_edit',
                        kwargs={'username': self.author.username,
                                'post_id': self.post.id}, ):
                    response = self.no_author_client.get(reverse_name)
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
                else:
                    response = self.no_author_client.get(reverse_name)
                    self.assertEqual(response.status_code, HTTPStatus.OK)
