import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from ..models import Post, User
from django.contrib.auth import get_user_model

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CreateFormTests(TestCase):
    """Тестирование формы создания новой записи"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.test_user = User.objects.create_user(username='Leo')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_test_user = Client(self.test_user)
        self.authorized_test_user.force_login(self.test_user)

    def test_form_creates_new_post(self):
        """
        Проверяем, что валидная форма создает запись
        с картинками.
        """
        post_count = Post.objects.count()

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

        form_data = {'text': 'Тестовый текст',
                     'image': uploaded, }

        self.authorized_test_user.post(reverse('posts:post_create'),
                                       data=form_data, follow=True)

        self.assertTrue(Post.objects.filter(image='posts/small.gif').exists())
        self.assertNotEqual(Post.objects.count(), post_count)

    def test_form_edits_post(self):
        """Проверяем, что валидная форма изменяет запись."""

        post = Post.objects.create(text='Тестовый текст!',
                                   author=CreateFormTests.test_user,)
        old_text = post.text
        id_value = post.pk

        form_data = {'text': 'Другой тестовый текст', }
        self.authorized_test_user.post(reverse('posts:post_edit', kwargs={
            'post_id': id_value}), data=form_data, follow=True)

        data = Post.objects.filter(id=id_value).values_list('text')[0][0]

        self.assertNotEqual(data, old_text)

    def test_form_creates_user(self):
        """Проверяем, что форма регистрации создает нового User'a"""

        count_users = User.objects.count()
        self.test_user = Client()
        form_data = {'username': 'Leo2',
                     'password1': '123456Pmv_',
                     'password2': '123456Pmv_', }
        self.test_user.post(reverse('users:signup'),
                            data=form_data, follow=True)

        self.assertNotEqual(User.objects.count(), count_users)
