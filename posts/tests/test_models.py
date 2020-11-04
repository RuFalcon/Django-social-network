from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

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
        # Создаем клиент и авторизуем пользователя
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_add_and_remove_follower(self):
        self.assertEqual(self.user.follower.count(), 0)
        self.authorized_client.get(reverse(
            'profile_follow', kwargs={'username': self.second_user.username}))
        self.assertEqual(self.user.follower.count(), 1)
        self.authorized_client.get(
            reverse(
                'profile_unfollow', kwargs={
                    'username': self.second_user.username}))
        self.assertEqual(self.user.follower.count(), 0)
