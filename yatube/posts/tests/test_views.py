import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django import forms
from django.core.cache import cache

from ..models import Post, Group, Comment, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class TemplateUrlsTest(TestCase):
    """Тестирование шаблонов приложения posts """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(
            title='Тестовое название группы!',
            description='Тестовое описание группы!',
            slug='test_slug')

        cls.test_user_author = User.objects.create_user(username='Leo')

        cls.post = Post.objects.create(
            text='Тестовый текст!',
            group=TemplateUrlsTest.group,
            author=TemplateUrlsTest.test_user_author, )

    def setUp(self):
        self.authorized_author = Client(self.test_user_author)
        self.authorized_author.force_login(self.test_user_author)
        cache.clear()

    def test_url_template_auth_user(self):
        """
        View-функция использует соответствующий шаблон
        для авторизованного пользователя-автора.
        """

        templates_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={
                    'slug': f"{self.group.slug}"}):
                        'posts/group_list.html',
            reverse('posts:profile', kwargs={
                    "username": f"{self.post.author.username}"}):
                        'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                    "post_id": f"{self.post.id}"}):
                        'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={
                    "post_id": f"{self.post.id}"}):
                        'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html', }

        for reverse_name, template in templates_names.items():
            with self.subTest(template=template):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PageContextTest(TestCase):
    """Тестирование контекста приложения posts """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(
            title='Тестовое название группы!',
            description='Тестовое описание группы!',
            slug='test_slug')

        cls.test_user_author = User.objects.create_user(username='Leo')

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            text='Тестовый текст!',
            group=cls.group,
            author=cls.test_user_author,
            image=uploaded)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_author = Client(self.test_user_author)
        self.authorized_author.force_login(self.test_user_author)
        cache.clear()

    def test_image_index_context(self):
        """
        Проверка изображения в контекста на страницах:
        index, group_list, profile, post_detail
        """

        response_index = self.authorized_author.get(reverse('posts:index'))
        index = response_index.context['page_obj'][0].image

        response_group = self.authorized_author.get(reverse(
            'posts:group_list', kwargs={
                "slug": f"{self.group.slug}"}))
        group = response_group.context['page_obj'][0].image

        response_profile = self.authorized_author.get(reverse(
            'posts:profile', kwargs={
                "username": f"{self.post.author.username}"}))
        profile = response_profile.context['page_obj'][0].image

        response_detail = self.authorized_author.get(
            reverse('posts:post_detail', kwargs={
                "post_id": f"{self.post.id}"}))
        detail = response_detail.context['post'].image

        self.assertTrue(Post.objects.filter(
                        image='posts/small.gif').exists())
        self.assertEqual(index, self.post.image)
        self.assertEqual(group, self.post.image)
        self.assertEqual(profile, self.post.image)
        self.assertEqual(detail, self.post.image)

    def test_index_context(self):
        """Проверка контекста на странице index"""

        response = self.authorized_author.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        text = first_object.text
        date = first_object.pub_date
        author = first_object.author.username

        self.assertEqual(text, self.post.text)
        self.assertEqual(date, self.post.pub_date)
        self.assertEqual(author, self.post.author.username)

    def test_group_context(self):
        """Проверка контекста на странице group_list"""

        response = self.authorized_author.get(reverse(
            'posts:group_list', kwargs={
                "slug": f"{self.group.slug}"}))

        first_object = response.context['page_obj'][0]
        text = first_object.text
        date = first_object.pub_date
        author = first_object.author.username
        group = first_object.group.title

        self.assertEqual(text, self.post.text)
        self.assertEqual(date, self.post.pub_date)
        self.assertEqual(author, self.post.author.username)
        self.assertEqual(group, self.post.group.title)

    def test_profile_context(self):
        """Проверка контекста на странице profile"""

        response = self.authorized_author.get(reverse(
            'posts:profile', kwargs={
                "username": f"{self.post.author.username}"}))

        first_object = response.context['page_obj'][0]
        text = first_object.text
        date = first_object.pub_date
        author = first_object.author.username
        group = first_object.group.title

        self.assertEqual(text, self.post.text)
        self.assertEqual(date, self.post.pub_date)
        self.assertEqual(author, self.post.author.username)
        self.assertEqual(group, self.post.group.title)

    def test_detail_context(self):
        """Проверка контекста на странице post_detail"""

        response = self.authorized_author.get(
            reverse('posts:post_detail', kwargs={
                "post_id": f"{self.post.id}"}))

        object = response.context['post']
        id_ = object.id
        text = object.text
        date = object.pub_date
        author = object.author.username
        group = object.group.title

        self.assertEqual(text, self.post.text)
        self.assertEqual(date, self.post.pub_date)
        self.assertEqual(author, self.post.author.username)
        self.assertEqual(group, self.post.group.title)
        self.assertEqual(id_, self.post.id)

    def test_edit_form_correct_context(self):
        """Страница редактирования сформирована с правильным контекстом."""

        response = self.authorized_author.get(reverse(
            'posts:post_edit', kwargs={
                "post_id": f"{self.post.id}"}))

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField, }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_form_correct_context(self):
        """Страница редактирования сформирована с правильным контекстом."""

        response = self.authorized_author.get(reverse('posts:post_create'))

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField, }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)


class PaginatorTest(TestCase):
    """Тестирование Paginator на страницах приложения posts """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(
            title='Тестовое название группы!',
            description='Тестовое описание группы!',
            slug='test_slug')

        cls.test_user_author = User.objects.create_user(username='Leo')

        for i in range(1, 14):
            cls.post = Post.objects.create(
                text='Тестовый текст!',
                group=cls.group,
                author=cls.test_user_author,)

    def setUp(self):
        self.authorized_author = Client(self.test_user_author)
        self.authorized_author.force_login(self.test_user_author)
        cache.clear()

    def test_page_contains_ten_records(self):
        """
        Количество записей на 1-й странице = 10
        для index, group_list и profile
        """

        response_index = self.authorized_author.get(reverse('posts:index'))
        response_group_list = self.authorized_author.get(reverse(
            'posts:group_list', kwargs={
                "slug": f"{self.group.slug}"}))
        response_profile = self.authorized_author.get(reverse(
            'posts:profile', kwargs={
                "username": f"{self.post.author.username}"}))

        self.assertEqual(len(response_index.context['page_obj']), 10)
        self.assertEqual(len(response_group_list.context['page_obj']), 10)
        self.assertEqual(len(response_profile.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """
        Количество записей на 2-й странице = 3
        для index, group_list и profile
        """

        response_index = self.authorized_author.get(reverse('posts:index')
                                                    + '?page=2')
        response_group_list = self.authorized_author.get(reverse(
            'posts:group_list', kwargs={"slug": f"{self.group.slug}"})
            + '?page=2')
        response_profile = self.authorized_author.get(reverse(
            'posts:profile',
            kwargs={"username": f"{self.post.author.username}"})
            + '?page=2')

        self.assertEqual(len(response_index.context['page_obj']), 3)
        self.assertEqual(len(response_group_list.context['page_obj']), 3)
        self.assertEqual(len(response_profile.context['page_obj']), 3)


class AddPostTest(TestCase):
    """Тестирование появления нового поста на страницах приложения post"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(
            title='Тестовое название группы!',
            description='Тестовое описание группы!',
            slug='test_slug')

        cls.another_group = Group.objects.create(
            title='Другое тестовое название группы!',
            description='Другое тестовое описание группы!',
            slug='another_slug')

        cls.test_user_author = User.objects.create_user(username='Leo')

        cls.post = Post.objects.create(
            text='Тестовый текст!',
            group=cls.group,
            author=cls.test_user_author,)

    def setUp(self):
        self.guest_client = Client()

        self.authorized_author = Client(self.test_user_author)
        self.authorized_author.force_login(self.test_user_author)
        cache.clear()

    def test_added_post_appears(self):
        """Добавленный пост с группой проявляется на всех страницах"""

        response_index = self.authorized_author.get(reverse('posts:index'))
        index = response_index.context.get('page_obj').object_list[0].group

        response_group_list = self.authorized_author.get(reverse(
            'posts:group_list', kwargs={
                "slug": f"{self.group.slug}"}))
        group = response_group_list.context['page_obj'][0].group

        response_profile = self.authorized_author.get(reverse(
            'posts:profile', kwargs={
                "username": self.test_user_author}))
        profile = response_profile.context.get('page_obj').object_list[0].group

        self.assertEqual(index, self.group)
        self.assertEqual(group, self.group)
        self.assertEqual(profile, self.group)

    def test_added_post_not_appear(self):
        """
        Добавленный пост не проявляется
        на страницах других групп и авторов
        """

        self.another_test_user_author = User.objects.create_user(
            username='Max')
        self.another_authorized_author = Client(
            self.another_test_user_author)
        self.another_authorized_author.force_login(
            self.another_test_user_author)

        self.post = Post.objects.create(
            text='Другой тестовый текст!',
            group=self.another_group,
            author=self.another_test_user_author,)

        response_index = self.authorized_author.get(reverse('posts:index'))
        index = len(response_index.context.get('page_obj').object_list)

        response_group_list = self.authorized_author.get(reverse(
            'posts:group_list', kwargs={
                "slug": f"{self.group.slug}"}))
        group = len(response_group_list.context.get('page_obj').object_list)

        response_profile = self.authorized_author.get(reverse(
            'posts:profile', kwargs={
                "username": self.test_user_author}))
        profile = len(response_profile.context.get('page_obj').object_list)

        self.assertNotEqual(index, group)
        self.assertNotEqual(index, profile)

    def test_add_comments(self):
        """
        Добавить комментарий может только
        авторизованный пользователь
        """
        count_comments = Comment.objects.count()

        form_data = {'text': 'Комментарий!', }

        self.guest_client.post(reverse('posts:add_comment', kwargs={
            'post_id': self.post.pk, }), data=form_data, follow=True)
        self.assertEqual(Comment.objects.count(), count_comments)

        self.authorized_author.post(reverse('posts:add_comment', kwargs={
            'post_id': self.post.pk, }), data=form_data, follow=True)
        self.assertNotEqual(Comment.objects.count(), count_comments)

    def test_comment_appears(self):
        """
        Добавленный комментарий появляется
        на странице поста
        """

        comment = Comment.objects.create(
            text='КомментАрий!',
            author=self.test_user_author,
            post=self.post,
        )

        response = self.authorized_author.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk, }))

        commment_response = response.context.get('comments')[0].text
        self.assertEqual(commment_response, comment.text)


class CacheTest(TestCase):
    """Тестирование кэширования."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(
            title='Тестовое название группы!',
            description='Тестовое описание группы!',
            slug='test_slug')

        cls.test_user_author = User.objects.create_user(username='Leo')

        for i in range(1, 5):
            cls.post = Post.objects.create(
                text='Тестовый текст!',
                group=cls.group,
                author=cls.test_user_author,)

    def setUp(self):
        self.authorized_author = Client(self.test_user_author)
        self.authorized_author.force_login(self.test_user_author)
        cache.clear()

    def test_index_cache(self):
        """
        Проверка работы cache на странице index
        (декоратор добавлен в view)
        """

        response = self.authorized_author.get(reverse('posts:index'))
        old_content = response.content
        old_count_posts = Post.objects.count()

        Post.objects.create(
            text='Тестовый текст!',
            group=self.group,
            author=self.test_user_author,)

        response = self.authorized_author.get(reverse('posts:index'))
        new_content = response.content
        new_count_posts = Post.objects.count()

        self.assertEqual(old_content, new_content)
        self.assertNotEqual(new_count_posts, old_count_posts)

        cache.clear()

        response = self.authorized_author.get(reverse('posts:index'))
        new_content_clear = response.content

        self.assertNotEqual(old_content, new_content_clear)


class FollowTest(TestCase):
    """Тестирование подписок на авторов"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(
            title='Тестовое название группы!',
            description='Тестовое описание группы!',
            slug='test_slug')

        cls.user = User.objects.create_user(username='Max')
        cls.another_user = User.objects.create_user(username='Andy')
        cls.author = User.objects.create_user(username='Leo')

        cls.post = Post.objects.create(
            text='Тестовый текст!',
            group=cls.group,
            author=cls.author,)

    def setUp(self):
        self.authorized_user = Client(self.user)
        self.authorized_user.force_login(self.user)

        self.authorized_another_user = Client(self.another_user)
        self.authorized_another_user.force_login(self.another_user)

    def test_follow_unfollow(self):
        """
        Авторизованный пользователь может создавать
        и удалять подписки
        """
        count_follows = Follow.objects.count()
        self.authorized_user.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.author.username}))

        self.assertEqual(Follow.objects.count(), count_follows + 1)

        self.authorized_user.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.author.username}))

        self.assertEqual(Follow.objects.count(), count_follows)

    def test_follow_post_list(self):
        """
        Новая запись появляется в ленте авторизованного подписчика
        и не появляется в ленте других авторизованных пользователей
        """

        count_follows = Follow.objects.count()

        Follow.objects.create(
            user=self.user,
            author=self.author,)

        response = self.authorized_user.get(reverse(
            'posts:follow_index'),)
        response_user = response.content

        response = self.authorized_another_user.get(reverse(
            'posts:follow_index'),)
        response_another_user = response.content

        self.assertEqual(Follow.objects.count(), count_follows + 1)
        self.assertNotEqual(response_user, response_another_user)
