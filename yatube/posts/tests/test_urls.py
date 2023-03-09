from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from http import HTTPStatus
from django.core.cache import cache

from ..models import Post, Group

User = get_user_model()


class AccessUrlsTest(TestCase):
    """
    Тестирование приложения posts на доступность страниц и
    корректность шаблонов в зависимости от статуса пользователя.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(
            title='Тестовое название группы!',
            description='Тестовое описание группы!',
            slug='test_slug')

        cls.test_user = User.objects.create_user(username='Max')
        cls.test_user_author = User.objects.create_user(username='Leo')

        cls.post = Post.objects.create(
            text='Тестовый текст!',
            group=cls.group,
            author=cls.test_user_author,)

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client(self.test_user)
        self.authorized_client.force_login(self.test_user)

        self.authorized_author = Client(self.test_user_author)
        self.authorized_author.force_login(self.test_user_author)
        cache.clear()

    def test_unexisting_page_author(self):
        """
        Проверка доступности НЕсуществующей страницы
        для НЕавторизованного пользователя
        """
        response = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_unexisting_page_404(self):
        """Проверка шаблона НЕсуществующей страницы."""

        response = self.authorized_client.get('/unexisting_page/')
        template = 'core/404.html'

        self.assertEqual(response.templates[0].name, template)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_access_page_author(self):
        """
        Проверка доступности страниц для
        авторизованного пользователя-автора
        """

        pages_dict = {'/': 'posts/index.html',
                      f'/group/{self.group.slug}/':
                      'posts/group_list.html',
                      f'/profile/{self.post.author}/':
                      'posts/profile.html',
                      f'/posts/{self.post.id}/':
                      'posts/post_detail.html',
                      '/create/': 'posts/create_post.html',
                      f'/posts/{self.post.id}/edit/':
                      'posts/create_post.html', }
        for way in pages_dict.keys():
            with self.subTest(way=way):
                response = self.authorized_author.get(way)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_access_page_authorized_client(self):
        """
        Проверка доступности страниц для
        авторизованного пользователя (НЕавтора)
        """

        pages_dict = {'/': 'posts/index.html',
                      f'/group/{self.group.slug}/':
                      'posts/group_list.html',
                      f'/profile/{self.post.author}/':
                      'posts/profile.html',
                      f'/posts/{self.post.id}/':
                      'posts/post_detail.html',
                      '/create/': 'posts/create_post.html', }
        for way in pages_dict.keys():
            with self.subTest(way=way):
                response = self.authorized_client.get(way)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_access_page_guest_client(self):
        """Проверка доступности страниц для НЕавторизованного пользователя"""

        pages_dict = {'/': 'posts/index.html',
                      f'/group/{self.group.slug}/':
                      'posts/group_list.html',
                      f'/profile/{self.post.author}/':
                      'posts/profile.html',
                      f'/posts/{self.post.id}/':
                      'posts/post_detail.html', }

        for way in pages_dict.keys():
            with self.subTest(way=way):
                response = self.guest_client.get(way)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_template_author(self):
        """Проверка шаблонов страниц для авторизованного пользователя-автора"""

        pages_dict = {'/': 'posts/index.html',
                      f'/group/{self.group.slug}/':
                      'posts/group_list.html',
                      f'/profile/{self.post.author}/':
                      'posts/profile.html',
                      f'/posts/{self.post.id}/':
                      'posts/post_detail.html',
                      '/create/': 'posts/create_post.html',
                      f'/posts/{self.post.id}/edit/':
                      'posts/create_post.html', }

        for way, template in pages_dict.items():
            with self.subTest(way=way):
                response = self.authorized_author.get(way)
                self.assertEqual(response.templates[0].name, template)

    def test_template_guest_client(self):
        """Проверка шаблонов страниц для Неавторизованного пользователя"""

        pages_dict = {'/': 'posts/index.html',
                      f'/group/{self.group.slug}/':
                      'posts/group_list.html',
                      f'/profile/{self.post.author}/':
                      'posts/profile.html',
                      f'/posts/{self.post.id}/':
                      'posts/post_detail.html', }
        for way, template in pages_dict.items():
            with self.subTest(way=way):
                response = self.guest_client.get(way)
                self.assertEqual(response.templates[0].name, template)
