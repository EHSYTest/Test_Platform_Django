from django.test import TestCase


class IndexPageTest(TestCase):

    def test_index_page_renders_index_template(self):
        response = self.client.get('127.0.0.1:8000/index/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    #def test_login_action(self):
     #   response = self.client.get('')