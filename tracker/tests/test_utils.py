import django

django.setup()

from asgiref.sync import async_to_sync
from django.test import TestCase
from faker import Faker

from tracker.choices import Roles
from tracker.models import CustomUser, Repository, TelegramUser
from tracker.utils import get_all_repostitories, get_user

fake = Faker()

telagram_id = fake.random_int(min=100000000, max=9999999999)


class TestGetAllRepositories(TestCase):
    def setUp(self):
        self.custom_user = CustomUser.objects.create(
            email=fake.email, role=Roles.CONTRIBUTOR
        )

        self.user = TelegramUser.objects.create(
            telegram_id=telagram_id, user_id=self.custom_user.id
        )

        self.repo1 = Repository.objects.create(user=self.custom_user, name="TestRepo1")
        self.repo2 = Repository.objects.create(user=self.custom_user, name="TestRepo2")

    def test_get_all_repositories_valid_user(self):
        """Test valid telegram ID fetching repositories."""
        result = async_to_sync(get_all_repostitories)(tele_id=telagram_id)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "TestRepo1")
        self.assertEqual(result[1]["name"], "TestRepo2")

    def test_get_all_repositories_invalid_user(self):
        """Test invalid telegram ID raises exception."""
        with self.assertRaises(TelegramUser.DoesNotExist):
            async_to_sync(get_all_repostitories)(tele_id="987654321")


class TestGetUser(TestCase):
    def setUp(self):
        """Set up test data."""
        self.custom_user = CustomUser.objects.create(
            email=fake.email(),
            role=Roles.CONTRIBUTOR
        )
        self.user_id = str(self.custom_user.id)

    def test_get_user_valid_uuid(self):
        """Test retrieving user with valid UUID."""
        result = async_to_sync(get_user)(uuid=self.user_id)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.custom_user)

    def test_get_user_invalid_uuid(self):
        """Test retrieving user with invalid UUID raises exception."""
        invalid_uuid = "00000000-0000-0000-0000-000000000000"
        with self.assertRaises(CustomUser.DoesNotExist):
            async_to_sync(get_user)(uuid=invalid_uuid)