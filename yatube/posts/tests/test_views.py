from http import HTTPStatus

from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(title='Тестовое название',
                                         slug='test-slug',
                                         description='Тестовое описание')

        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
            image=uploaded
        )
        cls.templates_pages_names = {
            'index.html': reverse('index'),
            'group.html': reverse('group_posts',
                                  kwargs={'slug': cls.group.slug}),
            'new.html': reverse('new_post')
        }

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
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
                       'text': forms.fields.CharField,
                       'image': forms.fields.ImageField}

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
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
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

    def test_page_not_found(self):
        response_page_not_found = self.guest_client.get('/tests_url/')
        self.assertEqual(response_page_not_found.status_code,
                         HTTPStatus.NOT_FOUND)

    def not_authorized_user_cant_comment(self):
        response = self.guest_client.post(reverse(
            'add_comment', kwargs={self.author.username,
                                   self.post.id})
        )
        self.assertRedirects(response, reverse(
            'post', kwargs={self.author.username,
                            self.post.id})
        )

    def authorized_user_can_comment(self):
        self.form_data = {'text': 'test comment'}
        self.authorized_client.post(reverse(
            'add_comment', kwargs={self.author.username, self.post.id}),
            data=self.form_data, follow=True
        )
        self.assertTrue(
            Comment.objects.filter(text='test comment').exists()
        )

    def test_index_page_cash(self):
        post_count = Post.objects.count()
        response_1 = self.guest_client.get(reverse('index'))
        Post.objects.create(author=PostPagesTests.user, text=self.post.text)
        self.assertTrue(Post.objects.count, post_count + 1)
        response_2 = self.guest_client.get(reverse('index'))
        self.assertCountEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.guest_client.get(reverse('index'))
        self.assertNotEqual(response_2.content, response_3.content)

    def test_img_on_pages_in_context(self):
        urls = {
            'index': reverse('index'),
            'profile': reverse('profile',
                               kwargs={'username': self.user.username}),
            'group': reverse('group_posts',
                             kwargs={'slug': self.group.slug}),
            'post': reverse('post', kwargs={'username': self.user.username,
                            'post_id': self.post.id}),
        }
        for name, url in urls.items():
            with self.subTest():
                response = self.authorized_client.get(url)
                self.assertContains(response, '<img ')
                page = response.context.get('page')
                if page is not None:
                    image = page[0].image
                else:
                    image = response.context['post'].image
                self.assertEqual(image, self.post.image)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
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
