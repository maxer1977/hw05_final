from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        group = PostModelTest.group
        expected_post = post.text[:15]
        expected_group = group.title
        self.assertEqual(expected_post, str(post))
        self.assertEqual(expected_group, str(group))

    def test_post_model_verbose_name(self):
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст сообщения:',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа интересов:'
        }
        for field, expected in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(post._meta.get_field(field).verbose_name,
                                 expected)

    def test_post_model_help_text(self):
        post = PostModelTest.post
        field_help_txt = {
            'text': 'Поле для текста Вашего сообщения ! ОБЯЗАТЕЛЬНОЕ поле !',
            'group':
            'Выбор из списка группы интересов ! НЕобязательное поле !',
        }
        for field, expected in field_help_txt.items():
            with self.subTest(field=field):
                self.assertEqual(post._meta.get_field(field).help_text,
                                 expected)
