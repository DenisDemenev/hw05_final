from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(title='Тестовое название',
                                         slug='test-slug',
                                         description='Тестовое описание')

        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group
        )
        cls.templates_pages_names = {
            'index.html': reverse('index'),
            'group.html': reverse('group_posts',
                                  kwargs={'slug': cls.group.slug}),
            'new.html': reverse('new_post')
        }

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_use_template(self):
        for template, reverse_name in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_context_in_index(self):
        response = self.authorized_client.get(reverse('index'))
        last_post = response.context['page'][0]
        self.assertEqual(last_post, self.post)

    def test_context_in_group(self):
        response = self.authorized_client.get(
            reverse('group_posts',
                    kwargs={'slug': self.group.slug}))
        test_group = response.context['group']
        test_post = response.context['page'][0]
        self.assertEqual(test_group, self.group)
        self.assertEqual(test_post, self.post)

    def test_context_in_new_post(self):
        response = self.authorized_client.get(reverse('new_post'))

        form_fields = {'group': forms.fields.ChoiceField,
                       'text': forms.fields.CharField}

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_context_in_post_edit(self):
        response = self.authorized_client.get(
            reverse('post_edit',
                    kwargs={'username': self.user.username,
                            'post_id': self.post.id}),
        )

        form_fields = {
            'text': forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_context_in_profile(self):
        response = self.authorized_client.get(
            reverse('profile',
                    kwargs={'username': self.user.username})
        )
        context = {
            'profile': self.post.author
        }

        for value, expected in context.items():
            with self.subTest(value=value):
                context = response.context[value]
                self.assertEqual(context, expected)

    def test_context_in_post(self):
        response = self.authorized_client.get(
            reverse('post',
                    kwargs={'username': self.user.username,
                            'post_id': self.post.id})
        )

        context = {'post_count': self.user.posts.count(),
                   'profile': self.post.author,
                   'post': self.post}

        for value, expected in context.items():
            with self.subTest(value=value):
                context = response.context[value]
                self.assertEqual(context, expected)

    def test_post_no_add_another_group(self):
        response = self.authorized_client.get(reverse('index'))
        post = response.context['page'][0]
        group = post.group
        self.assertEqual(group, self.group)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test User')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        for count in range(13):
            cls.post = Post.objects.create(
                text=f'Тестовый пост {count}',
                author=cls.user)

    def test_first_page(self):
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page(self):
        response = self.authorized_client.get(
            reverse('index') + '?page=2'
        )
        self.assertEqual(len(response.context.get('page').object_list), 3)
