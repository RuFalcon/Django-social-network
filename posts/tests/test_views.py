from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Post, Group
from django.urls import reverse
import time
from django.core.cache import cache

User = get_user_model()


class ViewTests(TestCase):
    # Метод класса должен быть декорирован
    @classmethod
    def setUpClass(cls):
        # Вызываем родительский метод, чтобы не перезаписывать его полностью, а
        # расширить
        super().setUpClass()
        # Устанавливаем данные для тестирования
        # Создаём пользователя
        cls.user = User.objects.create_user(username='StasBasov')
        cls.second_user = User.objects.create_user(username='Trump')
        cls.third_user = User.objects.create_user(username='Biden')
        # Создаем клиент и авторизуем пользователя
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.unauthorized_client = Client()

        cls.third_authorized_client = Client()
        cls.third_authorized_client.force_login(cls.third_user)

        cls.test_group = Group.objects.create(
            title='Лeв Толстой', slug='tolstoy', description='Лёва Блогер')

        cls.group_url = reverse('group', kwargs={'slug': cls.test_group.slug})

        cls.second_test_group = Group.objects.create(
            title='Фёдор Достоевский',
            slug='dostoevsky',
            description='Записки от Фёдора')

        cls.second_group_url = reverse(
            'group', kwargs={
                'slug': cls.second_test_group.slug})

        cls.test_post = Post.objects.create(
            text='Тестовая публикация', author=cls.user, group=cls.test_group)
        cls.test_post.save()

        cls.second_test_post = Post.objects.create(
            text='Make America Great Again',
            author=cls.second_user,
            group=cls.test_group)
        cls.second_test_post.save()

        cls.url_edit = reverse(
            'post_edit',
            kwargs={
                'username': cls.user.username,
                'post_id': cls.test_post.id})

    def urls(self, post):
        main_page = reverse('index')
        profile_page = reverse(
            'profile', kwargs={'username': self.user.username})
        post_page = reverse(
            'post',
            kwargs={
                'username': self.user.username,
                'post_id': post.id})
        group_page = self.group_url

        return [main_page, profile_page, post_page, group_page]

    def check_urls(self, text, post):
        cache.clear()
        # Вспомогательная функция для прохода по урлам
        for url in self.urls(post):
            response = self.authorized_client.get(url)
            self.assertContains(response, text)
        for url in self.urls(post):
            response = self.unauthorized_client.get(url)
            self.assertContains(response, text)

    def check_index_with_cache(self, text, post):
        # Вспомогательная функция для прохода по урлам
        response = self.authorized_client.get(reverse('index'))
        self.assertNotContains(response, text)
        response = self.unauthorized_client.get(reverse('index'))
        self.assertNotContains(response, text)
        time.sleep(21)
        response = self.authorized_client.get(reverse('index'))
        self.assertContains(response, text)
        response = self.unauthorized_client.get(reverse('index'))
        self.assertContains(response, text)

    def test_text_on_pages(self):
        # Проверяем наличие текста созданного поста на страницах
        self.check_urls(self.test_post.text, self.test_post)
        self.authorized_client.post(
            self.url_edit,
            {'text': 'Отредактированный текст', 'group': self.test_group.id},
            follow=True)

        self.check_urls('Отредактированный текст', self.test_post)
        self.authorized_client.post(
            self.url_edit,
            {'text': 'Смена группы', 'group': self.second_test_group.id},
            follow=True)
        response = self.authorized_client.get(self.group_url)
        self.assertNotContains(response, 'Смена группы')
        response = self.authorized_client.get(self.second_group_url)
        self.assertContains(response, 'Смена группы')

    def test_img_on_pages(self):
        with open('media/posts/tractor.jpg', 'rb') as img:
            self.authorized_client.post(
                self.url_edit, {
                    'text': 'Отредактированный текст',
                    'group': self.test_group.id,
                    'image': img})
        self.check_urls('<img', self.test_post)

    def test_cache_posts(self):
        self.authorized_client.post(
            self.url_edit,
            {'text': 'Это тест кэша', 'group': self.test_group.id},
            follow=True)
        self.check_index_with_cache('Это тест кэша', self.test_post)

    def test_add_and_remove_follower_posts(self):
        response = self.authorized_client.get(reverse('follow_index'))
        self.assertNotContains(response, self.second_test_post.text)
        self.authorized_client.get(reverse(
            'profile_follow', kwargs={'username': self.second_user.username}))
        response = self.authorized_client.get(reverse('follow_index'))
        self.assertContains(response, self.second_test_post.text)
        self.authorized_client.get(
            reverse(
                'profile_unfollow', kwargs={
                    'username': self.second_user.username}))
        response = self.authorized_client.get(reverse('follow_index'))
        self.assertNotContains(response, self.second_test_post.text)
        response = self.third_authorized_client.get(reverse('follow_index'))
        self.assertNotContains(response, self.second_test_post.text)

    def test_authorized_user_add_comment(self):
        self.authorized_client.post(
            reverse(
                'add_comment', kwargs={
                    'username': self.user.username,
                    'post_id': self.test_post.id
                }),
            {
                'text': 'Тестовый комментарий'
            }, follow=True)
        response = self.authorized_client.get(reverse(
            'post',
            kwargs={
                'username': self.user.username,
                'post_id': self.test_post.id}))
        self.assertContains(response, 'Тестовый комментарий')
