from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Post, Group
from .test_views import ViewTests
from django.urls import reverse

User = get_user_model()


class StaticURLTests(TestCase):
    # Метод класса должен быть декорирован
    @classmethod
    def setUpClass(cls):
        # Вызываем родительский метод, чтобы не перезаписывать его полностью, а
        # расширить
        super().setUpClass()
        # Устанавливаем данные для тестирования
        # Создаём пользователя
        cls.user = User.objects.create_user(username='StasBasov')
        # Создаем клиент и авторизуем пользователя
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        # Создаём второй клиент, без авторизации
        cls.unauthorized_client = Client()
        cls.test_group = Group.objects.create(
            title='Лeв Толстой', slug='tolstoy', description='Тестовая группа')

        cls.group_url = reverse('group', kwargs={'slug': cls.test_group.slug})

        cls.test_post = Post.objects.create(
            text='Тестовая публикация', author=cls.user, group=cls.test_group)
        cls.test_post.save()

        cls.posts_count = Post.objects.count()
        cls.url_edit = reverse(
            'post_edit',
            kwargs={
                'username': cls.user.username,
                'post_id': cls.test_post.id})

    urls = ViewTests.urls
    check_urls = ViewTests.check_urls

    def test_homepage(self):
        # Делаем запрос к главной странице и проверяем статус
        response = self.unauthorized_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_new_post(self):
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            '/new/',
            {'text': 'Это текст публикации', 'group': self.test_group.id},
            follow=True)
        self.assertEqual(response.status_code, 200)

        new_post = Post.objects.get(text='Это текст публикации')

        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.check_urls(new_post.text, new_post)

    def test_force_login(self):
        response = self.authorized_client.get('/new/')
        self.assertEqual(response.status_code, 200)

    # Проверка доступности страницы /new/ для неавторизованного пользователя
    def test_unauthorized_user_newpage(self):
        response = self.unauthorized_client.get('/new/')
        # Тестируем редирект: правильно ли идёт переадресация и правильный ли
        # статус
        self.assertRedirects(response, '/auth/login/?next=/new/',
                             status_code=302, target_status_code=200)

    def test_signup_profile_exist(self):
        # Проверяем существование страницы после регистрации
        response = self.authorized_client.get('/StasBasov/')
        self.assertEqual(response.status_code, 200)

    def test_404_page(self):
        response = self.authorized_client.get('/non-existent/')
        self.assertEqual(response.status_code, 404)

    def test_upload_not_image_file(self):
        with open('media/posts/test.txt', 'rb') as file:
            self.authorized_client.post(
                self.url_edit, {
                    'text': 'Отредактированный текст',
                    'group': self.test_group.id,
                    'image': file
                })
        self.assertEqual(Post.objects.count(), self.posts_count)

    def test_new_post_unauthorized_user(self):
        self.unauthorized_client.post(
            '/new/', {'text': 'Это текст публикации'}, follow=True)
        self.assertEqual(Post.objects.count(), self.posts_count)

    def test_unauthorized_user_follow(self):
        response = self.unauthorized_client.get(reverse(
            'profile_follow', kwargs={'username': self.user.username}))
        self.assertRedirects(response, '/auth/login/?next=/StasBasov/follow/',
                             status_code=302, target_status_code=200)

    def test_unauthorized_user_add_comment(self):
        response = self.unauthorized_client.post(
            reverse(
                'add_comment', kwargs={
                    'username': self.user.username,
                    'post_id': self.test_post.id
                }),
            {'text': 'Тестовый комментарий'}, follow=True)
        self.assertRedirects(
            response,
            '/auth/login/?next=/StasBasov/1/comment/',
            status_code=302,
            target_status_code=200)
